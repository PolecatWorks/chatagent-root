from customer.hams import HamsApp
from customer.mcp_server import mcp_init
from fastmcp.server.http import create_sse_app
from contextlib import asynccontextmanager
from fastapi import FastAPI
from customer.config import ServiceConfig
import logging


import yaml
from .middleware.config import ConfigMiddleware

logger = logging.getLogger(__name__)


def app_init(config: ServiceConfig):
    """
    Start the service with the given configuration file
    """

    logger.info(f"CONFIG\n{(yaml.dump(config.model_dump(), sort_keys=False))}")

    fastmcp_app = mcp_init(config.mcp)

    hams_app = HamsApp(config.hams)

    config_middleware = ConfigMiddleware(config)
    fastmcp_app.add_middleware(config_middleware)

    @asynccontextmanager
    async def app_lifespace(app: FastAPI):
        print(f"App lifespan started {app}")
        yield
        print(f"App lifespan ended {app}")

    fastmcp_app_http = fastmcp_app.http_app()
    fastmcp_app_sse = create_sse_app(fastmcp_app, "/messages", "/mcp")

    @asynccontextmanager
    async def combined_lifespan(app: FastAPI):

        async with app_lifespace(app):
            print(f"App lifespan started {app}")

            await hams_app.start()
            # hams_config = uvicorn.Config(
            #     hams_app, host="0.0.0.0", port=9000, log_level="info"
            # )
            # hams_server = uvicorn.Server(hams_config)

            # hams_task = asyncio.create_task(hams_server.serve())

            async with fastmcp_app_http.lifespan(app):
                print(f"FastMCP lifespan started {app}")
                async with fastmcp_app_sse.lifespan(app):
                    print(f"SSE lifespan started {app}")
                    # pdb.set_trace()
                    yield
                    print(f"SSE lifespan ended {app}")
                print(f"FastMCP lifespan ended {app}")

            await hams_app.stop()
            print(f"App lifespan ended {app}")

    app = FastAPI(lifespan=combined_lifespan)
    app.mount("/mcp/http", fastmcp_app_http)
    app.mount("/sse", fastmcp_app_sse)

    return app
