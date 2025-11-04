# Provides the tools and resources that are available to the MCP server


from aiohttp import web
from customer.config import ServiceConfig

from aiohttp_mcp import AiohttpMCP, setup_mcp_subapp
from customer import keys

import logging

# Set up logging
logger = logging.getLogger(__name__)


from .tools import mcp


def mcp_server_app_create(app: web.Application, config: ServiceConfig) -> web.Application:
    """
    Create the service with the given configuration file
    """

    app[keys.mcp] = mcp
    setup_mcp_subapp(app, app[keys.mcp], prefix="/mcp")

    logger.info(f"MCP: Initialised at /mcp")

    return app
