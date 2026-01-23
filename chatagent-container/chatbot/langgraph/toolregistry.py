from dataclasses import dataclass
from typing import Literal
from collections.abc import Sequence
from chatbot.config.tool import ToolBoxConfig, ToolConfig, ToolModeEnum
from langchain_core.messages.tool import ToolCall, ToolMessage
from langchain_core.tools.structured import StructuredTool
import logging
import asyncio
from prometheus_client import REGISTRY, CollectorRegistry, Summary
from ruamel.yaml import YAML

yaml = YAML()


logger = logging.getLogger(__name__)


@dataclass
class ToolRegistrationContext:
    """Context for tool registration to track source and mode"""

    source: Literal["local", "mcp"]
    mcp_name: str | None = None
    mcp_mode: ToolModeEnum | None = None
    default_config: ToolConfig | None = None


@dataclass
class ToolDefinition:
    """Dataclass to hold function definition and its associated tool."""

    name: str
    definition: ToolConfig
    tool: StructuredTool


class ToolRegistry:
    def __init__(
        self,
        toolboxConfig: ToolBoxConfig,
        registry: CollectorRegistry | None = REGISTRY,
    ):
        self.registry: dict[str, ToolDefinition] = {}
        self.toolboxConfig = toolboxConfig
        # Load the tool definition as dict from the list form
        # (List form is easier to manage in k8s (ie lists enable replace vs change))
        self.tool_definition_dict = {tool.name: tool for tool in self.toolboxConfig.tools if tool.name is not None}
        self.prometheus_registry = registry
        self.tool_usage_metric = Summary(
            "tool_usage",
            "Summary of tool usage",
            ["tool_name"],
            registry=registry,
        )

    def all_tools(self) -> Sequence[StructuredTool]:
        logger.debug(f"ToolRegistry.all_tools: {list(self.registry.keys())}")
        return [mytool.tool for mytool in self.registry.values()]

    def _merge_tool_config(
        self,
        tool_name: str,
        explicit: ToolConfig | None,
        default: ToolConfig,
    ) -> ToolConfig:
        """Merge explicit config with defaults, explicit takes precedence"""
        if explicit is None:
            # Use all defaults
            return ToolConfig(
                name=tool_name,
                max_instances=default.max_instances,
                timeout=default.timeout,
            )

        # Merge: explicit values override defaults
        return ToolConfig(
            name=tool_name,
            max_instances=explicit.max_instances,
            timeout=explicit.timeout,
        )

    def register_tools(
        self,
        tools: Sequence[StructuredTool],
        context: ToolRegistrationContext | None = None,
    ) -> None:
        """Registers multiple tools with the client."""
        for tool in tools:
            self.register_tool(tool, context=context)

    def register_tool(self, tool: StructuredTool, context: ToolRegistrationContext | None = None) -> None:
        """Registers a tool with the client.

        Args:
            tool: The tool to register
            context: Registration context containing source and mode information

        Raises:
            ValueError: If tool is not configured in strict mode
        """
        tool_name = tool.name

        # Determine if this is a local tool (no context or source is local)
        is_local_tool = context is None or context.source == "local"

        # Local tools always use strict mode
        if is_local_tool:
            if tool_name not in self.tool_definition_dict:
                error_msg = f"""Tool '{tool_name}' (local tool) is not configured in the toolbox.

Local tools must always be explicitly configured in myai.toolbox.tools.

Configured tools: {list(self.tool_definition_dict.keys())}
"""
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Register with explicit configuration
            tool_config = self.tool_definition_dict[tool_name]
            logger.debug(f"Tool '{tool_name}' (local) registered with explicit configuration")

        # MCP tools - check mode
        elif context.source == "mcp":
            if context.mcp_mode == ToolModeEnum.strict:
                # Strict mode: tool MUST be configured
                if tool_name not in self.tool_definition_dict:
                    error_msg = f"""Tool '{tool_name}' from MCP server '{context.mcp_name}' \
is not configured in the toolbox.

MCP Server: {context.mcp_name}
Mode: strict
Missing Tool: {tool_name}

Configured tools: {list(self.tool_definition_dict.keys())}

To resolve:
1. Add the tool to myai.toolbox.tools in your configuration, OR
2. Change the MCP server mode to 'dynamic' and provide default_tool_config
"""
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                # Register with explicit configuration
                tool_config = self.tool_definition_dict[tool_name]
                logger.debug(f"Tool '{tool_name}' from MCP '{context.mcp_name}' " f"(strict mode) registered with explicit configuration")

            elif context.mcp_mode == ToolModeEnum.dynamic:
                # Dynamic mode: use defaults if not configured
                explicit_config = self.tool_definition_dict.get(tool_name)

                if explicit_config is not None:
                    # Tool is configured - merge with defaults
                    tool_config = self._merge_tool_config(tool_name, explicit_config, context.default_config)
                    logger.debug(f"Tool '{tool_name}' from MCP '{context.mcp_name}' " f"(dynamic mode) configuration merged: " f"explicit={explicit_config}, " f"default={context.default_config}, final={tool_config}")
                else:
                    # Tool not configured - use defaults
                    tool_config = self._merge_tool_config(tool_name, None, context.default_config)
                    logger.info(f"Tool '{tool_name}' from MCP '{context.mcp_name}' " f"not explicitly configured, " f"using default configuration (" f"max_instances={tool_config.max_instances}, " f"timeout={tool_config.timeout})")
            else:
                raise ValueError(f"Unknown mode: {context.mcp_mode}")
        else:
            raise ValueError(f"Unknown source: {context.source}")

        # Register the tool
        self.registry[tool_name] = ToolDefinition(
            name=tool_name,
            tool=tool,
            definition=tool_config,
        )

        logger.debug(f"Tool registered: {tool_name}")

    async def perform_tool_actions(self, parts: Sequence[ToolCall]) -> Sequence[ToolMessage]:
        """Performs actions using the registered tools.
        Reply back with an array to match what was called
        """
        semaphore = asyncio.Semaphore(self.toolboxConfig.max_concurrent)

        async def sem_task(tool: ToolCall) -> ToolMessage:
            async with semaphore:
                return await self.perform_tool_action(tool)

        tasks = [sem_task(part) for part in parts]
        return await asyncio.gather(*tasks)

    async def perform_tool_action(self, tool_call: ToolCall) -> ToolMessage:
        """Performs an action using a single tool call part."""

        logger.debug(f"Received tool call: {tool_call}")

        tool_name = tool_call["name"]

        try:
            # Get the function from the registry
            declaration = self.registry.get(tool_name)

            logger.debug(f"Tool declaration found: {declaration}")

            # Call the function with its arguments
            with self.tool_usage_metric.labels(tool_name).time():
                result = await declaration.tool.ainvoke(tool_call["args"])

            return ToolMessage(
                content=result,
                tool_call_id=tool_call["id"],
                status="success",
            )

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return ToolMessage(
                content=f"Error executing tool: {str(e)}",
                tool_call_id=tool_call["id"],
                status="error",
            )
