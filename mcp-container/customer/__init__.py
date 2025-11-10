from aiohttp import web
from customer.config import ServiceConfig
from customer.llmconversationhandler import langchain_app_create
from pydantic_yaml import to_yaml_str
import logging
from customer.hams import Hams, hams_app_create
from customer.service import service_app_create
from customer.mcp_server import mcp_server_app_create
from .tools import tools_app_create
from customer import keys

logger = logging.getLogger(__name__)


def app_init(app: web.Application, config: ServiceConfig):
    """
    Initialize the service with the given configuration file
    This is seperated from service_init as it is also used from the adev dev server
    """

    logger.info(f"CONFIG\n{to_yaml_str(config, indent=2)}")

    hams_app_create(app, config.hams)
    service_app_create(app, config)
    mcp_server_app_create(app, config)
    tools_app_create(app, config)

    langchain_app_create(app, config)

    return app


def app_start(config: ServiceConfig):
    """
    Start the service with the given configuration file
    """
    app = web.Application()

    app_init(app, config)

    web.run_app(
        app,
        host=app[keys.config].webservice.url.host,
        port=app[keys.config].webservice.url.port,
        # TODO: Review the custom logging and replace into config
        access_log_format='%a "%r" %s %b "%{Referer}i" "%{User-Agent}i"',
        access_log=logger,
    )

    logger.info(f"Service stopped")
