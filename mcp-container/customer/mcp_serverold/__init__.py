# Provides the tools and resources that are available to the MCP server


from customer.config import ServiceConfig

from customer import keys

import logging

# Set up logging
logger = logging.getLogger(__name__)


from .tools import mcp


def mcp_init(config: ServiceConfig) -> web.Application:
    """
    Create the service with the given configuration file
    """

    app[keys.mcp] = mcp
    setup_mcp_subapp(app, app[keys.mcp], prefix="/mcp")

    logger.info(f"MCP: Initialised at /mcp")

    return app
