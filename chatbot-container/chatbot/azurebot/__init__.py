
import sys
from typing import Optional
from aiohttp import web
import traceback
import re
from chatbot.azurebot.webview import AzureBotView
from chatbot.config import ChatBotConfig
from chatbot import keys

from chatbot.langgraphhandler import LanggraphHandler
from microsoft_agents.hosting.core import (
    Authorization,
    AgentApplication,
    TurnState,
    TurnContext,
    MemoryStorage,
    StoreItem,
)
from chatbot.config import ServiceConfig
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter


import logging
import asyncio

from pydantic import BaseModel
from langchain_core.messages.base import BaseMessage

# Set up logging
logger = logging.getLogger(__name__)


class ChatHistory(BaseModel):
    messages: list[BaseMessage] = []


class ChatHistoryStoreItem(StoreItem):

    def __init__(self, chat_history: Optional[ChatHistory] = None):
        logger.info("Initializing ChatHistoryStoreItem")
        self.chat_history = chat_history or ChatHistory()

    def store_item_to_json(self) -> dict:
        return self.chat_history.model_dump()

    @staticmethod
    def from_json_to_store_item(json_data: dict) -> "ChatHistoryStoreItem":
        chat_history = ChatHistory.model_validate(json_data)
        return ChatHistoryStoreItem(chat_history)



def azure_app_create(app: web.Application, config: ServiceConfig)  -> web.Application:
    """Create the Azure Bot related routes and handlers."""


    if keys.langgraph_handler not in app:
        raise RuntimeError("langgraph_handler is missing from app; ensure it's registered before calling azure_app_create.")

    langgraph_handler: LanggraphHandler = app[keys.langgraph_handler]

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
    async def on_message(context: TurnContext, state: TurnState):
        context.streaming_response.queue_informative_update(
            "Working on a response for you..."
        )
        chat_history_store_item = state.get_value(
            "ConversationState.chatHistory", lambda: ChatHistoryStoreItem(), target_cls=ChatHistoryStoreItem
        )

        # Check whether langgraph_handler has attribute 'graph'
        if not hasattr(langgraph_handler, "graph"):
            await context.send_activity("LanggraphHandler is missing the attribute 'graph'.")
        else:
            graph = getattr(langgraph_handler, "graph")
            logger.debug("langgraph_handler.graph found: %s", type(graph))
            await context.send_activity("I was able to find the hanlder and graph")

        response = await langgraph_handler.invoke_agent(context.activity.text, chat_history_store_item.chat_history.messages)
        await context.send_activity(response)

        await context.send_activity(f"you said: {context.activity.text}")

        state.set_value("ConversationState.chatHistory", chat_history_store_item)

        await context.send_activity("This is where you would integrate with the LLMConversationHandler.")


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
