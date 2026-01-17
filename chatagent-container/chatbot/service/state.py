from dataclasses import dataclass
from datetime import datetime

from chatbot.config import EventConfig
from prometheus_client import REGISTRY, CollectorRegistry, Gauge

import logging

logger = logging.getLogger(__name__)


@dataclass
class Events:
    config: EventConfig
    lastTime: datetime
    # If time is after lastTime then subtract one from chunkCount (if greater than 0). Then schedule for
    chunkCount: int

    def __init__(
        self,
        config: EventConfig,
        lastTime: datetime,
        chunkCount: int,
        registry: CollectorRegistry | None = REGISTRY,
    ):

        self.config = config
        self.lastTime = lastTime
        # If time is after lastTime then subtract one from chunkCount (if greater than 0). Then schedule for
        self.chunkCount = chunkCount
        self.prometheus_registry = registry
        self.chunkGauge = Gauge(
            "chunk_gauge", "Count of chunks remaining", registry=registry
        )

    def updateChunk(self, time: datetime) -> int:
        if self.lastTime < time:
            if self.chunkCount > 0:
                self.chunkCount -= 1
                self.chunkGauge.set(self.chunkCount)

                self.lastTime = time + self.config.chunkDuration
                logger.info(
                    f"Chunks remaining {self.chunkCount}{" FULL" if self.chunkCount>self.config.maxChunks else ""}"
                )
                return self.config.chunkDuration.total_seconds()
            else:
                return self.config.checkTime.total_seconds()
        else:
            return self.config.checkTime.total_seconds()

    def addChunks(self, chunks: int) -> int:
        self.chunkCount += chunks
        self.chunkGauge.set(self.chunkCount)
        return self.chunkCount

    def spareCapacity(self) -> bool:
        return self.chunkCount <= self.config.maxChunks
