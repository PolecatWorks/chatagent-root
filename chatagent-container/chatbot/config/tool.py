from datetime import timedelta
from pydantic import BaseModel, Field
from pydantic import HttpUrl
from enum import Enum


class TransportEnum(str, Enum):
    streamable_http = "streamable_http"
    sse = "sse"


class McpConfig(BaseModel):
    """Configuration of MCP Endpoints"""

    name: str = Field(
        description="Name of the MCP tool, used to identify it in the system"
    )

    url: HttpUrl = Field(description="Host to connect to for MCP")
    transport: TransportEnum
    prompts: list[str] = []


class ToolConfig(BaseModel):
    """Configuration for tool execution."""

    name: str = Field(description="Name of the tool, used to identify it in the system")

    max_instances: int = Field(
        default=5,
        description="Default maximum number of concurrent instances for tools",
    )

    timeout: timedelta = Field(
        default=timedelta(seconds=30), description="Default timeout for tools"
    )

    instance_counts: int = Field(
        default=5,
        description="Current count of running instances for each tool",
    )


class ToolBoxConfig(BaseModel):
    """Configuration for tool execution."""

    tools: list[ToolConfig] = Field(
        description="Per-tool configuration with default settings"
    )
    max_concurrent: int = Field(
        description="Default maximum number of concurrent instances for tools"
    )

    mcps: list[McpConfig] = Field(description="MCP configuration")
