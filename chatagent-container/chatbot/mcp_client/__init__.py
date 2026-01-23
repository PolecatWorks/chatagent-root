from dataclasses import dataclass, field
import logging
from aiohttp import web
from chatbot.config import ServiceConfig
from langchain_mcp_adapters.client import MultiServerMCPClient
from chatbot import keys
from langchain_core.tools.structured import StructuredTool
from langchain_core.documents.base import Blob
from langchain_core.messages import AIMessage, HumanMessage

logger = logging.getLogger(__name__)


@dataclass
class MCPObjects:
    """Container for MCP server objects, tracking tools per server"""
    tools_by_mcp: dict[str, list[StructuredTool]] = field(default_factory=dict)
    all_tools: list[StructuredTool] = field(default_factory=list)
    resources: dict[str, list[Blob]] = field(default_factory=dict)
    prompts: dict[str, dict[str, list[HumanMessage | AIMessage]]] = field(default_factory=dict)

    def get_tools_for_mcp(self, mcp_name: str) -> list[StructuredTool]:
        """Get tools for a specific MCP server"""
        return self.tools_by_mcp.get(mcp_name, [])


async def connect_to_mcp_server(app):
    """
    Establishes a connection to the MCP server
    """

    config: ServiceConfig = app[keys.config]

    toolbox_config = config.myai.toolbox

    # Create the multi-server MCP client
    try:
        client = MultiServerMCPClient(
            {
                mcp.name: {"url": str(mcp.url), "transport": mcp.transport.value}
                for mcp in toolbox_config.mcps
            }
        )
    except Exception as e:
        error_msg = f"Failed to create MCP client: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Track tools per MCP and all tools
    tools_by_mcp = {}
    all_tools = []

    # Get configured tool names for warning about removed tools
    configured_tool_names = {tool.name for tool in toolbox_config.tools if tool.name is not None}

    # Connect to each MCP server individually
    for mcp in toolbox_config.mcps:
        try:
            logger.info(f"Connecting to MCP server '{mcp.name}' at {mcp.url}")

            # Get tools from this specific MCP
            mcp_tools = await client.get_tools(server_name=mcp.name)

            # Check if MCP returned no tools
            if not mcp_tools:
                logger.warning(
                    f"MCP server '{mcp.name}' at {mcp.url} returned no tools"
                )
            else:
                logger.info(
                    f"MCP server '{mcp.name}' returned {len(mcp_tools)} tools: "
                    f"{[tool.name for tool in mcp_tools]}"
                )

            # Check for configured tools that are no longer available
            mcp_tool_names = {tool.name for tool in mcp_tools}
            for configured_tool in configured_tool_names:
                if configured_tool not in mcp_tool_names:
                    # This tool was configured but not returned by this MCP
                    # We can't be 100% sure it came from this MCP, but log a warning
                    logger.debug(
                        f"Tool '{configured_tool}' is configured but not available from MCP server '{mcp.name}'"
                    )

            # Store tools for this MCP
            tools_by_mcp[mcp.name] = mcp_tools
            all_tools.extend(mcp_tools)

        except Exception as e:
            error_msg = f"""Failed to connect to MCP server '{mcp.name}' at {mcp.url}
Error: {str(e)}

The application cannot start without connecting to all configured MCP servers.
"""
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    # Get resources and prompts (these are per-MCP already)
    resources = {}
    prompts = {}

    for mcp in toolbox_config.mcps:
        try:
            resources[mcp.name] = await client.get_resources(mcp.name)
        except Exception as e:
            logger.warning(f"Failed to get resources from MCP '{mcp.name}': {str(e)}")
            resources[mcp.name] = []

        try:
            prompts[mcp.name] = {
                prompt: await client.get_prompt(mcp.name, prompt)
                for prompt in mcp.prompts
            }
        except Exception as e:
            logger.warning(f"Failed to get prompts from MCP '{mcp.name}': {str(e)}")
            prompts[mcp.name] = {}

    mcpObjects = MCPObjects(
        tools_by_mcp=tools_by_mcp,
        all_tools=all_tools,
        resources=resources,
        prompts=prompts,
    )

    logger.info(
        f"MCP initialization complete. Total tools: {len(all_tools)}, "
        f"MCPs: {list(tools_by_mcp.keys())}"
    )

    app[keys.mcpobjects] = mcpObjects


def mcp_app_create(app: web.Application, config: ServiceConfig) -> web.Application:

    app.on_startup.append(connect_to_mcp_server)

    return app
