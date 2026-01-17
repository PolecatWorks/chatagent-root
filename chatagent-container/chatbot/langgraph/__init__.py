import asyncio
import base64
from typing import Any
from collections.abc import Sequence, Callable  # For List and Callable
from chatbot.config import MyAiConfig, ServiceConfig
from aiohttp import web
from chatbot import keys
from dataclasses import dataclass
from abc import ABC, abstractmethod
from chatbot.hams import config

from chatbot.langgraph.handler import LanggraphHandler
from chatbot.mcp_client import MCPObjects
from chatbot.config import LangchainConfig




from langchain_core.messages.base import BaseMessage





from chatbot.tools import mytools
from langchain.chat_models import init_chat_model
import httpx


from pydantic import BaseModel

import logging

# Set up logging
logger = logging.getLogger(__name__)





async def bind_tools_when_ready(app: web.Application):
    """
    Wait for the mcptools to be constructed then bind to them
    """
    # TODO: Do we need to wait for the mcpobjects to be ready?
    # This is called on startup, so we expect the mcpobjects to be set by
    # the mcp_app_create function before this is called.

    if keys.mcpobjects not in app:
        # If the mcpobjects key is not in the app, we cannot proceed
        logger.error("MCPObjects not found in app context. Cannot bind tools.")
        raise ValueError("MCPObjects not found in app context.")

    langgraph_handler: LanggraphHandler = app[keys.langgraph_handler]

    mcpObjects: MCPObjects = app[keys.mcpobjects]

    langgraph_handler.register_tools(mcpObjects.tools)
    langgraph_handler.bind_tools()
    langgraph_handler.compile()



def llm_model(config: LangchainConfig):
    httpx_client = httpx.Client(verify=config.httpx_verify_ssl)

    match config.model_provider:
        case "google_genai":
            from langchain_google_genai import ChatGoogleGenerativeAI

            model = ChatGoogleGenerativeAI(
                model=config.model,
                google_api_key=config.google_api_key.get_secret_value(),
                # http_client=httpx_client,
            )
        case "azure_openai":
            from langchain_openai import AzureChatOpenAI

            # https://python.langchain.com/api_reference/openai/llms/langchain_openai.llms.azure.AzureOpenAI.html#langchain_openai.llms.azure.AzureOpenAI.http_client
            model = AzureChatOpenAI(
                model=config.model,
                azure_endpoint=str(config.azure_endpoint),
                api_version=config.azure_api_version,
                api_key=config.azure_api_key.get_secret_value(),
                http_client=httpx_client,
            )
        case _:
            raise ValueError(
                f"Unsupported model provider: {config.model_provider}"
            )

    return model



def langgraph_app_create(app: web.Application, config: ServiceConfig):
    """
    Initialize the AI client and add it to the aiohttp application context.
    """
    if keys.metrics not in app:
        logger.error("Metrics registry not found in app context. Cannot initialize LLMConversationHandler.")
        raise ValueError("Metrics registry not found in app context.")


    model = llm_model(config.aiclient)

    # use bind_tools_when_ready to move some of the constructions funtions to an async runtime
    app.on_startup.append(bind_tools_when_ready)


    langgraph_handler = LanggraphHandler(config.myai, model, registry=app[keys.metrics])
    langgraph_handler.register_tools(mytools)

    app[keys.langgraph_handler] = langgraph_handler
