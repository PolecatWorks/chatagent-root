# SPEC: MCP Tool Configuration with Dynamic and Strict Modes

**Version:** 1.0
**Date:** 2026-01-23
**Status:** Draft - Awaiting Review

---

## 1. Overview

### 1.1 Purpose
Update the chatagent-container tool configuration system to support two modes for handling MCP-provided tools:
- **Strict Mode**: Tools must be explicitly configured; unconfigured tools cause startup errors
- **Dynamic Mode**: Tools not explicitly configured will use default configuration values

### 1.2 Current Behavior
Currently, all tools from MCP servers must be explicitly listed in the configuration. If a tool is returned by an MCP server but not in the config, the application raises a `ValueError` during tool registration at startup.

### 1.3 Proposed Behavior
- Each MCP server will have a **required** `mode` field (`strict` or `dynamic`)
- Each MCP server will have an **optional** `default_tool_config` for dynamic mode
- Local (non-MCP) tools will always use strict mode
- Tool configuration will be validated at startup (fail-fast approach)

---

## 2. Configuration Schema

### 2.1 Updated YAML Structure

```yaml
myai:
  toolbox:
    max_concurrent: 10

    # Explicit tool configurations for local tools and MCP tools
    tools:
      - name: sum_numbers
        max_instances: 20
        timeout: P0DT0H0M30S
      - name: multiply_numbers
        max_instances: 15
      - name: get_customer  # MCP tool with explicit config
        max_instances: 10

    mcps:
      - name: customers
        url: http://localhost:8180/mcp/http/mcp
        transport: streamable_http
        mode: dynamic  # REQUIRED: 'strict' or 'dynamic'
        default_tool_config:  # REQUIRED for dynamic mode, OPTIONAL for strict
          max_instances: 10
          timeout: P0DT0H0M30S
        prompts: []

      - name: internal-tools
        url: http://localhost:8181/mcp/http/mcp
        transport: streamable_http
        mode: strict  # REQUIRED: must explicitly configure all tools
        prompts: []
```

### 2.2 Pydantic Model Updates

#### 2.2.1 New `ToolModeEnum`
```python
class ToolModeEnum(str, Enum):
    strict = "strict"
    dynamic = "dynamic"
```

#### 2.2.2 Updated `McpConfig`
```python
class McpConfig(BaseModel):
    """Configuration of MCP Endpoints"""

    name: str = Field(
        description="Name of the MCP tool, used to identify it in the system"
    )
    url: HttpUrl = Field(description="Host to connect to for MCP")
    transport: TransportEnum
    prompts: list[str] = []

    # NEW FIELDS
    mode: ToolModeEnum = Field(
        description="Mode for handling tools: 'strict' requires all tools to be configured, 'dynamic' uses defaults for unconfigured tools"
    )
    default_tool_config: ToolConfig | None = Field(
        default=None,
        description="Default configuration for tools not explicitly listed (required if mode is 'dynamic')"
    )

    @field_validator("default_tool_config")
    @classmethod
    def validate_default_config(cls, v, info):
        """Validate that default_tool_config is provided when mode is dynamic"""
        mode = info.data.get("mode")
        if mode == ToolModeEnum.dynamic and v is None:
            raise ValueError(
                f"default_tool_config is required when mode is 'dynamic'"
            )
        return v
```

#### 2.2.3 Updated `ToolConfig`
```python
class ToolConfig(BaseModel):
    """Configuration for tool execution."""

    name: str = Field(description="Name of the tool, used to identify it in the system")

    max_instances: int = Field(
        default=5,
        description="Maximum number of concurrent instances for this tool",
    )

    timeout: timedelta = Field(
        default=timedelta(seconds=30),
        description="Timeout for tool execution"
    )

    # Remove instance_counts as it's runtime state, not configuration
```

---

## 3. Behavior Specification

### 3.1 Tool Registration Flow

#### 3.1.1 Local Tools (Non-MCP)
1. Local tools from `chatbot.tools.mytools` are registered first
2. **Always use strict mode**: Each local tool MUST be in `toolbox.tools`
3. If a local tool is not configured → **ERROR at startup**

#### 3.1.2 MCP Tools - Strict Mode
1. Connect to MCP server at startup
2. Retrieve list of tools from MCP server
3. For each tool returned by MCP:
   - Check if tool is in `toolbox.tools`
   - If **NOT configured** → **ERROR at startup** with detailed message
   - If **configured** → Register with explicit configuration
4. If MCP returns tools that were previously available but are now removed:
   - **Log WARNING**: "Tool 'X' was configured but is no longer available from MCP server 'Y'"
   - **Do not register** the missing tool

#### 3.1.3 MCP Tools - Dynamic Mode
1. Connect to MCP server at startup
2. Retrieve list of tools from MCP server
3. For each tool returned by MCP:
   - Check if tool is in `toolbox.tools`
   - If **configured** → Register with **merged configuration** (explicit config overrides defaults)
   - If **NOT configured** → Register with `default_tool_config` from MCP config
   - **Log INFO**: "Tool 'X' from MCP 'Y' not explicitly configured, using default configuration"
4. If MCP returns tools that were previously available but are now removed:
   - **Log WARNING**: "Tool 'X' was configured but is no longer available from MCP server 'Y'"
   - **Do not register** the missing tool
5. If MCP returns new tools not seen before:
   - **Log INFO**: "New tool 'X' discovered from MCP server 'Y', registering with default configuration"
   - **Register** with `default_tool_config`

### 3.2 Configuration Merging (Dynamic Mode)

When a tool is explicitly configured in `toolbox.tools` but the MCP is in dynamic mode:

```python
# Pseudo-code
explicit_config = toolbox.tools["get_customer"]  # {max_instances: 20, timeout: 60s}
default_config = mcp.default_tool_config         # {max_instances: 10, timeout: 30s}

# Merge: explicit values override defaults
final_config = {
    name: "get_customer",
    max_instances: explicit_config.max_instances,  # 20 (from explicit)
    timeout: explicit_config.timeout,              # 60s (from explicit)
}
```

### 3.3 Error Handling

#### 3.3.1 Strict Mode - Unconfigured Tool Error
**When:** Tool from MCP is not in `toolbox.tools`
**Action:** Raise `ValueError` at startup
**Error Message Format:**
```
Tool '{tool_name}' from MCP server '{mcp_name}' is not configured in the toolbox.

MCP Server: {mcp_name}
Mode: strict
Missing Tool: {tool_name}

Configured tools: [{list_of_configured_tool_names}]

To resolve:
1. Add the tool to myai.toolbox.tools in your configuration, OR
2. Change the MCP server mode to 'dynamic' and provide default_tool_config
```

#### 3.3.2 MCP Connection Failures
**When:** Cannot connect to MCP server at startup
**Action:** Raise error and **exit application**
**Error Message Format:**
```
Failed to connect to MCP server '{mcp_name}' at {url}
Error: {connection_error_details}

The application cannot start without connecting to all configured MCP servers.
```

#### 3.3.3 MCP Returns No Tools
**When:** MCP server returns empty tool list
**Action:** Log **WARNING**, continue startup
**Log Message:**
```
WARNING: MCP server '{mcp_name}' at {url} returned no tools
```

#### 3.3.4 Dynamic Mode - Missing default_tool_config
**When:** MCP mode is `dynamic` but `default_tool_config` is not provided
**Action:** Raise `ValidationError` during config loading
**Error Message:**
```
MCP server '{mcp_name}' is configured with mode='dynamic' but missing required field 'default_tool_config'
```

### 3.4 Logging Requirements

#### 3.4.1 INFO Level Logs
- Tool registered with default config (dynamic mode):
  ```
  INFO: Tool '{tool_name}' from MCP '{mcp_name}' not explicitly configured, using default configuration
  ```
- New tool discovered (dynamic mode):
  ```
  INFO: New tool '{tool_name}' discovered from MCP server '{mcp_name}', registering with default configuration
  ```

#### 3.4.2 WARNING Level Logs
- MCP returns no tools:
  ```
  WARNING: MCP server '{mcp_name}' at {url} returned no tools
  ```
- Previously configured tool no longer available:
  ```
  WARNING: Tool '{tool_name}' was configured but is no longer available from MCP server '{mcp_name}'
  ```

#### 3.4.3 DEBUG Level Logs
- Tool registered with explicit config:
  ```
  DEBUG: Tool '{tool_name}' registered with explicit configuration: {config_details}
  ```
- Configuration merge details (dynamic mode):
  ```
  DEBUG: Tool '{tool_name}' configuration merged: explicit={explicit_config}, default={default_config}, final={final_config}
  ```

---

## 4. Implementation Changes

### 4.1 Files to Modify

1. **`chatbot/config/tool.py`**
   - Add `ToolModeEnum`
   - Update `McpConfig` with `mode` and `default_tool_config`
   - Add validation for `default_tool_config` requirement
   - Remove `instance_counts` from `ToolConfig` (runtime state)

2. **`chatbot/langgraph/toolregistry.py`**
   - Update `register_tool()` to accept optional MCP context
   - Add logic to handle strict vs dynamic mode
   - Add configuration merging logic
   - Update error messages with detailed context

3. **`chatbot/mcp_client/__init__.py`**
   - Update `connect_to_mcp_server()` to pass MCP config to tool registration
   - Add error handling for connection failures
   - Add warning for empty tool lists

4. **`chatbot/langgraph/__init__.py`**
   - Update `bind_tools_when_ready()` to handle MCP-specific registration
   - Ensure local tools are always registered in strict mode

5. **`tests/test_data/config.yaml`**
   - Update example configuration with `mode` and `default_tool_config`

### 4.2 New Data Structures

```python
@dataclass
class ToolRegistrationContext:
    """Context for tool registration to track source and mode"""
    source: Literal["local", "mcp"]
    mcp_name: str | None = None
    mcp_mode: ToolModeEnum | None = None
    default_config: ToolConfig | None = None
```

---

## 5. Testing Strategy

### 5.1 Unit Tests

#### 5.1.1 Configuration Validation Tests
- ✅ Valid strict mode config (no default_tool_config)
- ✅ Valid dynamic mode config (with default_tool_config)
- ❌ Invalid: dynamic mode without default_tool_config
- ✅ Valid: strict mode with default_tool_config (optional, ignored)

#### 5.1.2 Tool Registration Tests - Strict Mode
- ✅ All MCP tools configured → success
- ❌ MCP tool not configured → error with detailed message
- ✅ Configured tool no longer in MCP → warning, not registered
- ✅ Local tool configured → success
- ❌ Local tool not configured → error

#### 5.1.3 Tool Registration Tests - Dynamic Mode
- ✅ MCP tool not configured → use default config
- ✅ MCP tool configured → merge with defaults
- ✅ New tool appears → register with defaults
- ✅ Configured tool removed → warning, not registered

#### 5.1.4 Configuration Merging Tests
- ✅ Explicit config overrides all default fields
- ✅ Explicit config overrides some default fields
- ✅ No explicit config → use all defaults

#### 5.1.5 Error Handling Tests
- ❌ MCP connection failure → exit application
- ⚠️ MCP returns no tools → warning, continue
- ❌ Strict mode + unconfigured tool → error with helpful message

### 5.2 Integration Tests

#### 5.2.1 End-to-End Scenarios
- ✅ Application starts with mixed strict/dynamic MCPs
- ✅ Application starts with only strict MCPs
- ✅ Application starts with only dynamic MCPs
- ✅ Application starts with local tools + MCP tools
- ❌ Application fails to start with connection error
- ❌ Application fails to start with strict mode violation

### 5.3 Edge Cases
- ✅ MCP returns 100 tools, only 5 configured (dynamic mode)
- ✅ MCP returns 0 tools (warning)
- ⚠️ Tool configured but not returned by MCP (warning)
- ✅ Switching from strict to dynamic mode (deployment scenario)
- ✅ Tool name collision between different MCPs
- ✅ Tool name collision between local and MCP tools

---

## 6. Backwards Compatibility

### 6.1 Breaking Changes
- **`mode` field is now REQUIRED** for all MCP configurations
- Existing deployments MUST update their YAML configs to add `mode`

### 6.2 Migration Guide

**Before (Old Config):**
```yaml
mcps:
  - name: customers
    url: http://localhost:8180/mcp/http/mcp
    transport: streamable_http
```

**After (New Config - Strict Mode):**
```yaml
mcps:
  - name: customers
    url: http://localhost:8180/mcp/http/mcp
    transport: streamable_http
    mode: strict  # ADD THIS - maintains current behavior
```

**After (New Config - Dynamic Mode):**
```yaml
mcps:
  - name: customers
    url: http://localhost:8180/mcp/http/mcp
    transport: streamable_http
    mode: dynamic  # ADD THIS - new behavior
    default_tool_config:  # ADD THIS - required for dynamic
      max_instances: 10
      timeout: P0DT0H0M30S
```

### 6.3 Deprecation Strategy
- No deprecation period - this is a breaking change
- Update documentation and README with migration guide
- Update all example configs in repository

---

## 7. Observability

### 7.1 Existing Metrics (Keep)
- `tool_usage` - Summary of tool usage by tool name (already exists)

### 7.2 New Metrics (Not Required)
- Per user request, no new metrics for tracking default vs explicit config

### 7.3 Logging Summary
- **INFO**: Tools using defaults, new tools discovered
- **WARNING**: Empty tool lists, configured tools no longer available
- **ERROR**: Connection failures, strict mode violations
- **DEBUG**: Configuration merging details, registration details

---

## 8. Security Considerations

### 8.1 Tool Discovery
- Dynamic mode allows MCP servers to introduce new tools at runtime
- Ensure MCP servers are trusted sources
- Consider adding optional tool name allowlist/denylist in future

### 8.2 Configuration Validation
- Validate all timeout and max_instances values are positive
- Validate MCP URLs are properly formatted
- Validate mode is one of allowed values

---

## 9. Future Enhancements (Out of Scope)

### 9.1 Tool Allowlist/Denylist
```yaml
mcps:
  - name: customers
    mode: dynamic
    default_tool_config: {...}
    tool_allowlist: [get_customer, create_customer]  # Only these tools
    # OR
    tool_denylist: [delete_customer]  # All except these
```

### 9.2 Runtime Tool Discovery
- Currently tools are discovered only at startup
- Future: Support hot-reloading of MCP tools without restart

### 9.3 Per-Tool Mode Override
```yaml
tools:
  - name: dangerous_tool
    max_instances: 1
    mode: strict  # Override MCP's dynamic mode for this specific tool
```

---

## 10. Acceptance Criteria

### 10.1 Functional Requirements
- ✅ MCP configs require `mode` field
- ✅ Dynamic mode requires `default_tool_config`
- ✅ Strict mode errors on unconfigured tools with helpful message
- ✅ Dynamic mode uses defaults for unconfigured tools
- ✅ Dynamic mode merges explicit config with defaults
- ✅ Local tools always use strict mode
- ✅ MCP connection failures cause application exit
- ✅ Empty tool lists generate warnings
- ✅ Tool removal generates warnings

### 10.2 Non-Functional Requirements
- ✅ All error messages are clear and actionable
- ✅ All configuration changes are logged appropriately
- ✅ Startup time impact is minimal (< 1 second additional)
- ✅ Configuration validation happens at load time (fail-fast)

### 10.3 Testing Requirements
- ✅ Unit test coverage > 90% for new code
- ✅ Integration tests cover all scenarios in section 5.2
- ✅ All edge cases in section 5.3 have tests

---

## 11. Open Questions

1. ✅ **RESOLVED**: Should tool name collisions between MCPs be allowed?
   - **Answer**: Yes, but log a warning. Last registered wins.

2. ✅ **RESOLVED**: Should we validate that configured tools actually exist in MCP?
   - **Answer**: Yes, log warning if configured tool not returned by MCP.

3. ⏳ **PENDING**: Should we support environment variable overrides for `mode`?
   - Example: `APP_MYAI__TOOLBOX__MCPS__0__MODE=dynamic`

---

## 12. Approval

**Prepared by:** Antigravity AI
**Review requested from:** Ben Greene
**Status:** ⏳ Awaiting Review

**Next Steps:**
1. Review and approve this SPEC
2. Create implementation plan
3. Review and approve implementation plan
4. Execute implementation

---

## Appendix A: Example Configurations

### A.1 Minimal Strict Mode
```yaml
myai:
  toolbox:
    max_concurrent: 10
    tools:
      - name: get_customer
        max_instances: 10
    mcps:
      - name: customers
        url: http://localhost:8180/mcp/http/mcp
        transport: streamable_http
        mode: strict
```

### A.2 Minimal Dynamic Mode
```yaml
myai:
  toolbox:
    max_concurrent: 10
    tools: []  # No explicit tools needed
    mcps:
      - name: customers
        url: http://localhost:8180/mcp/http/mcp
        transport: streamable_http
        mode: dynamic
        default_tool_config:
          max_instances: 10
          timeout: P0DT0H0M30S
```

### A.3 Mixed Mode (Recommended)
```yaml
myai:
  toolbox:
    max_concurrent: 10
    tools:
      # Local tools (always strict)
      - name: sum_numbers
        max_instances: 20

      # Override for specific MCP tool
      - name: get_customer
        max_instances: 50  # Higher limit for this tool
        timeout: P0DT0H1M0S  # 60 seconds

    mcps:
      # Trusted internal MCP - use dynamic mode
      - name: customers
        url: http://localhost:8180/mcp/http/mcp
        transport: streamable_http
        mode: dynamic
        default_tool_config:
          max_instances: 10
          timeout: P0DT0H0M30S

      # External MCP - use strict mode for security
      - name: external-api
        url: http://external.com/mcp
        transport: streamable_http
        mode: strict
```

---

**END OF SPECIFICATION**
