from dataclasses import dataclass, field
import logging

from customer.config import ServiceConfig

logger = logging.getLogger(__name__)


@dataclass
class MCPObjects:
    tools: list[StructuredTool] = field(default_factory=list)
    resources: dict[str, list[Blob]] = field(default_factory=dict)
    prompts: dict[str, list[HumanMessage | AIMessage]] = field(default_factory=dict)


async def connect_to_mcp_server(app):
    """
    Establishes a connection to the MCP server
    """

    config: ServiceConfig = app[keys.config]

    toolbox_config = config.myai.toolbox

    client = MultiServerMCPClient(
        {
            mcp.name: {"url": str(mcp.url), "transport": mcp.transport.value}
            for mcp in toolbox_config.mcps
        }
    )

    mcpObjects = MCPObjects(
        tools=await client.get_tools(),
        resources={
            mcp.name: await client.get_resources(mcp.name)
            for mcp in toolbox_config.mcps
        },
        prompts={
            mcp.name: {
                prompt: await client.get_prompt(mcp.name, prompt)
                for prompt in mcp.prompts
            }
            for mcp in toolbox_config.mcps
        },
    )

    logger.info(f"MCP Objects = {mcpObjects}")

    app[keys.mcpobjects] = mcpObjects
