import pytest
from datetime import timedelta
from pydantic import ValidationError, HttpUrl
from typing import Optional

from chatbot.config.tool import (
    ToolBoxConfig,
    ToolConfig,
    McpConfig,
    ToolModeEnum,
    TransportEnum,
)
from chatbot.langgraph.toolregistry import (
    ToolRegistry,
    ToolRegistrationContext,
    ToolDefinition,
)
from langchain_core.tools.structured import StructuredTool


# Mock StructuredTool for testing
class MockTool(StructuredTool):
    name: str = "mock_tool"
    description: str = "A mock tool"

    def _run(self, *args, **kwargs):
        pass

    async def _arun(self, *args, **kwargs):
        pass


from pydantic import BaseModel as PydanticBaseModel


class EmptyArgs(PydanticBaseModel):
    pass


def create_mock_tool(name: str) -> MockTool:
    return MockTool(
        name=name,
        description=f"Mock tool {name}",
        func=lambda: None,
        args_schema=EmptyArgs,
    )


# --- Configuration Validation Tests ---


def test_mcp_config_strict_valid():
    """Test valid strict mode configuration (no default_tool_config needed)"""
    config = McpConfig(
        name="test_mcp",
        url=HttpUrl("http://localhost:8080"),
        transport=TransportEnum.streamable_http,
        mode=ToolModeEnum.strict,
    )
    assert config.mode == ToolModeEnum.strict
    assert config.default_tool_config is None


def test_mcp_config_dynamic_valid():
    """Test valid dynamic mode configuration (with default_tool_config)"""
    config = McpConfig(
        name="test_mcp",
        url=HttpUrl("http://localhost:8080"),
        transport=TransportEnum.streamable_http,
        mode=ToolModeEnum.dynamic,
        default_tool_config=ToolConfig(max_instances=10),
    )
    assert config.mode == ToolModeEnum.dynamic
    assert config.default_tool_config is not None
    assert config.default_tool_config.max_instances == 10


def test_mcp_config_dynamic_missing_default():
    """Test invalid dynamic mode configuration (missing default_tool_config)"""
    with pytest.raises(ValidationError) as excinfo:
        McpConfig(
            name="test_mcp",
            url=HttpUrl("http://localhost:8080"),
            transport=TransportEnum.streamable_http,
            mode=ToolModeEnum.dynamic,
            default_tool_config=None,
        )
    assert "default_tool_config is required when mode is 'dynamic'" in str(excinfo.value)


# --- ToolRegistry Logic Tests ---


@pytest.fixture
def toolbox_config():
    """Create a basic toolbox config with some configured tools"""
    return ToolBoxConfig(
        max_concurrent=5,
        tools=[
            ToolConfig(name="configured_tool_1", max_instances=5),
            ToolConfig(
                name="configured_tool_2",
                max_instances=10,
                timeout=timedelta(seconds=60),
            ),
        ],
        mcps=[],
    )


@pytest.fixture
def registry(toolbox_config):
    """Create a ToolRegistry instance"""
    return ToolRegistry(toolboxConfig=toolbox_config, registry=None)


def test_strict_mode_success(registry):
    """Test strict mode registration of a configured tool"""
    tool = create_mock_tool("configured_tool_1")
    context = ToolRegistrationContext(source="mcp", mcp_name="test_mcp", mcp_mode=ToolModeEnum.strict)

    registry.register_tool(tool, context=context)

    assert "configured_tool_1" in registry.registry
    assert registry.registry["configured_tool_1"].definition.max_instances == 5


def test_strict_mode_failure(registry):
    """Test strict mode registration of an unconfigured tool"""
    tool = create_mock_tool("unconfigured_tool")
    context = ToolRegistrationContext(source="mcp", mcp_name="test_mcp", mcp_mode=ToolModeEnum.strict)

    with pytest.raises(ValueError) as excinfo:
        registry.register_tool(tool, context=context)

    assert "not configured in the toolbox" in str(excinfo.value)
    assert "Mode: strict" in str(excinfo.value)


def test_dynamic_mode_default(registry):
    """Test dynamic mode usage of default config for unconfigured tool"""
    tool = create_mock_tool("unconfigured_tool")
    default_config = ToolConfig(max_instances=20, timeout=timedelta(seconds=90))
    context = ToolRegistrationContext(
        source="mcp",
        mcp_name="test_mcp",
        mcp_mode=ToolModeEnum.dynamic,
        default_config=default_config,
    )

    registry.register_tool(tool, context=context)

    assert "unconfigured_tool" in registry.registry
    def_config = registry.registry["unconfigured_tool"].definition
    assert def_config.max_instances == 20
    assert def_config.timeout == timedelta(seconds=90)
    assert def_config.name == "unconfigured_tool"


def test_dynamic_mode_merge(registry):
    """Test dynamic mode merging of explicit config with default config"""
    # Tool is configured with max_instances=10, timeout=60s
    tool = create_mock_tool("configured_tool_2")
    # Default is max_instances=20, timeout=90s
    default_config = ToolConfig(max_instances=20, timeout=timedelta(seconds=90))
    context = ToolRegistrationContext(
        source="mcp",
        mcp_name="test_mcp",
        mcp_mode=ToolModeEnum.dynamic,
        default_config=default_config,
    )

    registry.register_tool(tool, context=context)

    assert "configured_tool_2" in registry.registry
    def_config = registry.registry["configured_tool_2"].definition
    # Explicit should win
    assert def_config.max_instances == 10
    assert def_config.timeout == timedelta(seconds=60)
    assert def_config.name == "configured_tool_2"


def test_local_tool_strict(registry):
    """Test that local tools enforce strict mode"""
    # Success case
    tool = create_mock_tool("configured_tool_1")
    local_context = ToolRegistrationContext(source="local")
    registry.register_tool(tool, context=local_context)
    assert "configured_tool_1" in registry.registry

    # Failure case
    tool_fail = create_mock_tool("unconfigured_tool")
    with pytest.raises(ValueError) as excinfo:
        registry.register_tool(tool_fail, context=local_context)
    assert "Local tools must always be explicitly configured" in str(excinfo.value)


def test_local_tool_no_context_strict(registry):
    """Test that missing context implies local/strict mode"""
    tool_fail = create_mock_tool("unconfigured_tool")
    with pytest.raises(ValueError) as excinfo:
        registry.register_tool(tool_fail, context=None)
    assert "Local tools must always be explicitly configured" in str(excinfo.value)
