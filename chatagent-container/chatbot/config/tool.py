from datetime import timedelta
from pydantic import BaseModel, Field, field_validator
from pydantic import HttpUrl
from enum import Enum
from typing import Self


class TransportEnum(str, Enum):
    streamable_http = "streamable_http"
    sse = "sse"


class ToolModeEnum(str, Enum):
    """Mode for handling MCP tools"""

    strict = "strict"
    dynamic = "dynamic"


class ToolConfig(BaseModel):
    """Configuration for tool execution."""

    name: str | None = Field(default=None, description="Name of the tool, used to identify it in the system")

    max_instances: int = Field(
        default=5,
        description="Maximum number of concurrent instances for this tool",
    )

    timeout: timedelta = Field(default=timedelta(seconds=30), description="Timeout for tool execution")


class McpConfig(BaseModel):
    """Configuration of MCP Endpoints"""

    name: str = Field(description="Name of the MCP tool, used to identify it in the system")

    url: HttpUrl = Field(description="Host to connect to for MCP")
    transport: TransportEnum
    prompts: list[str] = []

    mode: ToolModeEnum = Field(description="Mode for handling tools: 'strict' requires all tools to be configured, 'dynamic' uses defaults for unconfigured tools")

    default_tool_config: ToolConfig | None = Field(
        default=None,
        description="Default configuration for tools not explicitly listed (required if mode is 'dynamic')",
    )

    @field_validator("default_tool_config")
    @classmethod
    def validate_default_config(cls, v, info):
        """Validate that default_tool_config is provided when mode is dynamic"""
        mode = info.data.get("mode")
        if mode == ToolModeEnum.dynamic and v is None:
            raise ValueError("default_tool_config is required when mode is 'dynamic'")
        return v


class ToolBoxConfig(BaseModel):
    """Configuration for tool execution."""

    tools: list[ToolConfig] = Field(description="Per-tool configuration with default settings")
    max_concurrent: int = Field(description="Default maximum number of concurrent instances for tools")

    mcps: list[McpConfig] = Field(description="MCP configuration")
