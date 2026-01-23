from a2a.server import agent_execution
from a2a.types import AgentCard, AgentSkill
from mya2a.config import ServiceConfig
# from mya2a.llmconversationhandler import langchain_app_create
from pydantic_yaml import to_yaml_str

from fastapi import FastAPI
import logging
# from mya2a.hams import Hams, hams_app_create
import httpx
import uvicorn

from a2a.server.apps import A2AFastAPIApplication, A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler, request_handler
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from mya2a.agent import CurrencyAgent
from mya2a.agent_executor import CurrencyAgentExecutor
from a2a.types import AgentCapabilities
from fastapi import APIRouter



logger = logging.getLogger(__name__)




def app_init(app: FastAPI, config: ServiceConfig):
    """
    Initialize the service with the given configuration file
    """

    dynamic_router = APIRouter(prefix="/dynamic", tags=["Dynamic"])

    @dynamic_router.get("/status")
    async def get_dynamic_status():
        """A dynamically added endpoint to check current time."""
        return {
            "message": "This endpoint was added dynamically!",
            "current_timestamp": time.time(),
            "server_version": "1.0"
        }

    # Include the new router into the main application instance
    app.include_router(dynamic_router)

    return app


def a2a_init(app: FastAPI, config: ServiceConfig):


    capabilities = AgentCapabilities(streaming=True, push_notifications=True)
    skill = AgentSkill(
        id='convert_currency',
        name='Currency Exchange Rates Tool',
        description='Helps with exchange values between various currencies',
        tags=['currency conversion', 'currency exchange'],
        examples=['What is exchange rate between USD and GBP?'],
    )
    agent_card = AgentCard(
        name='Currency Agent',
        description='Helps with exchange rates for currencies',
        url=f'http://{config.webservice.url.host}:{config.webservice.url.port}/',
        version='1.0.0',
        default_input_modes=CurrencyAgent.SUPPORTED_CONTENT_TYPES,
        default_output_modes=CurrencyAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )

    httpx_client = httpx.AsyncClient()
    push_config_store = InMemoryPushNotificationConfigStore()
    push_sender = BasePushNotificationSender(httpx_client=httpx_client,
                    config_store=push_config_store)
    request_handler = DefaultRequestHandler(
        agent_executor=CurrencyAgentExecutor(config.currency),
        task_store=InMemoryTaskStore(),
        push_config_store=push_config_store,
        push_sender= push_sender
    )

    a2a_server = A2AFastAPIApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    a2a_server.add_routes_to_app(app)


    return app


def app_start(config: ServiceConfig):
    """
    Start the service with the given configuration file
    """
    # app = web.Application()

    # app_init(app, config)

    # web.run_app(
    #     app,
    #     host=app[keys.config].webservice.url.host,
    #     port=app[keys.config].webservice.url.port,
    #     # TODO: Review the custom logging and replace into config
    #     access_log_format='%a "%r" %s %b "%{Referer}i" "%{User-Agent}i"',
    #     access_log=logger,
    # )

    capabilities = AgentCapabilities(streaming=True, push_notifications=True)
    skill = AgentSkill(
        id='convert_currency',
        name='Currency Exchange Rates Tool',
        description='Helps with exchange values between various currencies',
        tags=['currency conversion', 'currency exchange'],
        examples=['What is exchange rate between USD and GBP?'],
    )
    agent_card = AgentCard(
        name='Currency Agent',
        description='Helps with exchange rates for currencies',
        url=f'http://{config.webservice.url.host}:{config.webservice.url.port}/',
        version='1.0.0',
        default_input_modes=CurrencyAgent.SUPPORTED_CONTENT_TYPES,
        default_output_modes=CurrencyAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )

    httpx_client = httpx.AsyncClient()
    push_config_store = InMemoryPushNotificationConfigStore()
    push_sender = BasePushNotificationSender(httpx_client=httpx_client,
                    config_store=push_config_store)
    request_handler = DefaultRequestHandler(
        agent_executor=CurrencyAgentExecutor(config.currency),
        task_store=InMemoryTaskStore(),
        push_config_store=push_config_store,
        push_sender= push_sender
    )

    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    uvicorn.run(server.build(), host=config.webservice.url.host, port=config.webservice.url.port)

    logger.info(f"Service stopped")
