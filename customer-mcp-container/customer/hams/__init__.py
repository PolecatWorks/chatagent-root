import asyncio
import uvicorn
from fastapi import FastAPI
from .config import HamsConfig
import logging

logger = logging.getLogger(__name__)


class HamsApp:
    def __init__(self, config: HamsConfig):
        self.config = config

        mgmt_app = FastAPI(title="Management API")

        @mgmt_app.get("/hams/alive")
        async def alive():
            return {"status": "ok"}

        @mgmt_app.get("/hams/ready")
        async def ready():
            return {"status": "ok"}

        @mgmt_app.get("/hams/shutdown")
        async def shutdown():
            return {"status": "ok"}

        @mgmt_app.get("/hams/metrics")
        async def metrics():
            return "# metrics go here"

        self.app = mgmt_app

    async def start(self):
        if self.config.url.port is None:
            raise ValueError("Port is required to be configured")

        if self.config.url.host is None:
            raise ValueError("Host is required to be configured")

        self.app_config = uvicorn.Config(
            self.app,
            host=self.config.url.host,
            port=self.config.url.port,
            log_level="info",
        )
        self.server = uvicorn.Server(self.app_config)

        self.task = asyncio.create_task(self.server.serve())
        logger.info("Hams started on port 9000")

    async def stop(self):
        self.server.should_exit = True
        await self.task
