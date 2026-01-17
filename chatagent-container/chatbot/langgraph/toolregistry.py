from dataclasses import dataclass
from typing import Any
from collections.abc import Sequence, Callable  # For List and Callable
from chatbot.config.tool import ToolBoxConfig
from langchain_core.messages.tool import ToolCall, ToolMessage
from langchain_core.tools.structured import StructuredTool
import logging
import asyncio
from pydantic_yaml import to_yaml_str
from prometheus_client import REGISTRY, CollectorRegistry, Summary

import io
from ruamel.yaml import YAML

yaml = YAML()


logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Dataclass to hold function definition and its associated tool."""

    name: str
    definition: Any
    tool: StructuredTool


class ToolRegistry:
    def __init__(
        self,
        toolboxConfig: ToolBoxConfig,
        registry: CollectorRegistry | None = REGISTRY,
    ):
        self.registry: dict[str, ToolDefinition] = {}
        self.toolboxConfig = toolboxConfig
        # Load the tool definition as dict from the list form (List form is easier to manage in k8s (ie lists enable replace vs change))
        self.tool_definition_dict = {
            tool.name: tool for tool in self.toolboxConfig.tools
        }
        self.prometheus_registry = registry
        self.tool_usage_metric = Summary(
            "tool_usage",
            "Summary of tool usage",
            ["tool_name"],
            registry=registry,
        )

    def all_tools(self) -> Sequence[StructuredTool]:
        print(f"ToolRegistry.all_tools: {self.registry}")

        return [mytool.tool for mytool in self.registry.values()]

    def register_tools(self, tools: Sequence[StructuredTool]) -> None:
        """Registers the tools with the Gemini client."""

        for tool in tools:
            self.register_tool(tool)

    def register_tool(self, tool: StructuredTool) -> None:
        """Registers the tools with the client."""

        # if not callable(tool):
        #     raise ValueError(f"Tool {tool} is not callable.")

        tool_name = tool.name

        if tool_name not in self.tool_definition_dict:
            logger.debug(
                f"Cannot registering tool: {tool_name}. It is not defined in the toolbox configuration."
            )
            raise ValueError(f"Tool {tool_name} is not configured")

        print(tool.tool_call_schema)
        # buf = io.StringIO()
        # yaml.dump(tool.tool_call_schema.model_json_schema(), buf)

        # logger.info(f"Registering tool: {tool_name} with schema:\n{buf.getvalue()}")

        self.registry[tool_name] = ToolDefinition(
            name=tool_name,
            tool=tool,
            definition=self.tool_definition_dict[tool_name],
        )

        logger.debug(f"Tool registered: {tool_name}")

    async def perform_tool_actions(
        self, parts: Sequence[ToolCall]
    ) -> Sequence[ToolMessage]:
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

            print(f"registry: {self.registry}")

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
