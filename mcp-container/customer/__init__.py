from fastmcp.server.http import create_sse_app
import astroid.brain.brain_scipy_signal
from contextlib import asynccontextmanager
from random import random
from fastapi import FastAPI
from customer.config import ServiceConfig
import logging
from .tools import tools_app_create
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
from  random import randint
import yaml


logger = logging.getLogger(__name__)



def app_init(config: ServiceConfig):
    """
    Start the service with the given configuration file
    """

    logger.info(f"CONFIG\n{(yaml.dump(config.model_dump(), sort_keys=False))}")


    fastmcp_app = FastMCP(
        name="Access to reconciliation records to confirm status of bills and payments",
        instructions="Get the list of all active billing and payments records and confirm the status of specific records"
    )

    @fastmcp_app.tool(description="return a random number")
    def random_number():
        return randint(1, 100)


    # app = Starlette(
    #     routes=[
    #         Mount("/mcp-server", app=mcp_app),
    #         # Add other routes as needed
    #     ],
    #     lifespan=mcp_app.lifespan,
    # )

    # uvicorn.run(app, host="0.0.0.0", port=8000)


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
            async with fastmcp_app_http.lifespan(app):
                print(f"FastMCP lifespan started {app}")
                async with fastmcp_app_sse.lifespan(app):
                    print(f"SSE lifespan started {app}")
                    yield
                    print(f"SSE lifespan ended {app}")
                print(f"FastMCP lifespan ended {app}")
            print(f"App lifespan ended {app}")


    app = FastAPI(lifespan=combined_lifespan)
    app.mount("/mcp/http", fastmcp_app_http)
    app.mount("/sse", fastmcp_app_sse)

    return app
