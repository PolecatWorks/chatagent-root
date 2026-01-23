import asyncio
import logging


from chatbot.service.state import Events
from chatbot.hams import Hams, hams_app_create
from chatbot.config import ServiceConfig
from chatbot.service.webview import ChunkView, LLMChatView

from chatbot import keys
from aiohttp import web
from datetime import datetime, timezone

from prometheus_client import REGISTRY, CollectorRegistry


logger = logging.getLogger(__name__)


async def service_coroutine(app: web.Application):
    """
    Coroutine for the service
    """
    logger.info("Service: coroutine start")

    while True:
        waitTime = app[keys.events].updateChunk(datetime.now(timezone.utc))

        await asyncio.sleep(waitTime)


async def service_coroutine_cleanup(app: web.Application):
    """
    Launch the coroutine as a cleanup task
    """

    app[keys.coroutine] = asyncio.create_task(service_coroutine(app))

    logger.info("Service: coroutine running")
    yield

    app[keys.coroutine].cancel()

    logger.info("Service: coroutine cleanup")


def service_app_create(app: web.Application, config: ServiceConfig) -> web.Application:
    """
    Create the service with the given configuration file
    """
    registry = REGISTRY if keys.metrics not in app else app[keys.metrics]

    app[keys.events] = Events(app[keys.config].events, datetime.now(timezone.utc), 0, registry=registry)

    app.cleanup_ctx.append(service_coroutine_cleanup)

    print(f"Service: {app[keys.config].webservice.url.host}:{app[keys.config].webservice.url.port}/{app[keys.config].webservice.prefix}")

    app.add_routes(
        [
            web.view(f"/{config.webservice.prefix}/chunks", ChunkView),
            web.view(f"/{config.webservice.prefix}/llm/chat", LLMChatView),
        ]
    )

    app[keys.webservice] = app

    logger.info(f"Service: {app[keys.config].webservice.url.host}:{app[keys.config].webservice.url.port}/{app[keys.config].webservice.prefix}")

    return app
