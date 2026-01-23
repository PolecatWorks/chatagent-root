from chatbot.config import ServiceConfig, LangchainConfig
from aiohttp import web
from chatbot import keys
from chatbot.langgraph.handler import LanggraphHandler
from chatbot.langgraph.toolregistry import ToolRegistrationContext
from chatbot.mcp_client import MCPObjects


from chatbot.tools import mytools
import httpx

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

    config: ServiceConfig = app[keys.config]
    langgraph_handler: LanggraphHandler = app[keys.langgraph_handler]
    mcpObjects: MCPObjects = app[keys.mcpobjects]

    # Register tools from each MCP server with appropriate context
    for mcp_config in config.myai.toolbox.mcps:
        mcp_tools = mcpObjects.get_tools_for_mcp(mcp_config.name)

        if not mcp_tools:
            logger.debug(f"No tools to register from MCP '{mcp_config.name}'")
            continue

        # Create context for this MCP
        mcp_context = ToolRegistrationContext(
            source="mcp",
            mcp_name=mcp_config.name,
            mcp_mode=mcp_config.mode,
            default_config=mcp_config.default_tool_config,
        )

        logger.info(f"Registering {len(mcp_tools)} tools from MCP '{mcp_config.name}' " f"in {mcp_config.mode.value} mode")

        langgraph_handler.register_tools(mcp_tools, context=mcp_context)

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
            raise ValueError(f"Unsupported model provider: {config.model_provider}")

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

    # Register local tools with strict mode context
    local_context = ToolRegistrationContext(source="local")
    langgraph_handler.register_tools(mytools, context=local_context)

    app[keys.langgraph_handler] = langgraph_handler
