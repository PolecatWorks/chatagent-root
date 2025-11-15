
from aiohttp import web
import traceback
import re
from chatbot.azurebot.webview import AzureBotView
from chatbot.config import ChatBotConfig
from chatbot import keys
from microsoft_agents.hosting.core import (
    Authorization,
    AgentApplication,
    TurnState,
    TurnContext,
    MemoryStorage,
)
from chatbot.config import ServiceConfig
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter

import logging

# Set up logging
logger = logging.getLogger(__name__)



def azure_app_create(app: web.Application, config: ServiceConfig)  -> web.Application:
    """Create the Azure Bot related routes and handlers."""

    agents_sdk_config=  {
        'AGENTAPPLICATION': {},
        'CONNECTIONS': {
            'SERVICE_CONNECTION': {
                'SETTINGS': {
                    'CLIENTID': config.bot.azure_bot_client.CLIENTID,
                    'CLIENTSECRET': config.bot.azure_bot_client.CLIENTSECRET.get_secret_value(),
                    'TENANTID': config.bot.azure_bot_client.TENANTID
                }
            }
        },
        'CONNECTIONSMAP': {}
    }

    STORAGE = MemoryStorage()
    CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
    ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
    AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

    app[keys.storage] = STORAGE
    app[keys.cloud_adapter] = ADAPTER


    AGENT_APP = AgentApplication[TurnState](
        storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
    )

    app[keys.agent_app] = AGENT_APP

    @AGENT_APP.conversation_update("membersAdded")
    async def on_members_added(context: TurnContext, _state: TurnState):
        await context.send_activity(
            "Welcome to the empty agent! "
            "This agent is designed to be a starting point for your own agent development."
        )
        return True


    @AGENT_APP.message(re.compile(r"^hello$"))
    async def on_hello(context: TurnContext, _state: TurnState):
        await context.send_activity("Hello!")


    @AGENT_APP.activity("message")
    async def on_message(context: TurnContext, _state: TurnState):
        await context.send_activity(f"you said: {context.activity.text}")


    @AGENT_APP.error
    async def on_error(context: TurnContext, error: Exception):
        # This check writes out errors to console log .vs. app insights.
        # NOTE: In production environment, you should consider logging this to Azure
        #       application insights.
        print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
        traceback.print_exc()

        # Send a message to the user
        await context.send_activity("The bot encountered an error or bug.")





    app.add_routes([web.view(config.bot.api_path, AzureBotView)])

    logger.info(
        f"Bot: {app[keys.config].webservice.url.host}:{app[keys.config].webservice.url.port}{app[keys.config].bot.api_path}"
    )
    return app
