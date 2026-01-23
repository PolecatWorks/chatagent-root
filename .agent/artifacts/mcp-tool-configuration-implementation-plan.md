# Implementation Plan: MCP Tool Configuration with Dynamic and Strict Modes

**Version:** 1.0
**Date:** 2026-01-23
**Status:** Draft - Awaiting Review
**Related SPEC:** `/Users/bengreene/Development/polecatworks/chatagent-root/.agent/specs/mcp-tool-configuration-spec.md`

---

## Overview

This implementation plan breaks down the work into logical phases with clear dependencies. Each task includes file changes, testing requirements, and validation steps.

---

## Phase 1: Configuration Model Updates

### Task 1.1: Update `ToolConfig` Model
**File:** `chatbot/config/tool.py`

**Changes:**
- Remove `instance_counts` field (runtime state, not configuration)
- Keep `name`, `max_instances`, `timeout` fields
- Ensure defaults are appropriate

**Validation:**
- Existing configs still load correctly
- Pydantic validation works as expected

**Estimated Time:** 15 minutes

---

### Task 1.2: Add `ToolModeEnum`
**File:** `chatbot/config/tool.py`

**Changes:**
```python
class ToolModeEnum(str, Enum):
    strict = "strict"
    dynamic = "dynamic"
```

**Validation:**
- Enum can be imported and used
- String values match YAML values

**Estimated Time:** 5 minutes

---

### Task 1.3: Update `McpConfig` Model
**File:** `chatbot/config/tool.py`

**Changes:**
1. Add `mode: ToolModeEnum` field (required)
2. Add `default_tool_config: ToolConfig | None` field (optional)
3. Add `@field_validator` to ensure `default_tool_config` is provided when `mode == dynamic`

**Validation:**
- Valid strict mode config (without default_tool_config) loads successfully
- Valid dynamic mode config (with default_tool_config) loads successfully
- Invalid dynamic mode config (without default_tool_config) raises ValidationError
- Error message is clear and actionable

**Estimated Time:** 30 minutes

---

### Task 1.4: Update Test Configuration
**File:** `tests/test_data/config.yaml`

**Changes:**
- Add `mode: dynamic` to existing MCP config
- Add `default_tool_config` section with appropriate defaults
- Ensure all tools are either explicitly configured or will use defaults

**Validation:**
- Config loads without errors
- Application starts successfully with new config

**Estimated Time:** 15 minutes

---

**Phase 1 Total Time:** ~1 hour 5 minutes

---

## Phase 2: Tool Registry Updates

### Task 2.1: Create `ToolRegistrationContext` Dataclass
**File:** `chatbot/langgraph/toolregistry.py`

**Changes:**
```python
from typing import Literal
from chatbot.config.tool import ToolModeEnum

@dataclass
class ToolRegistrationContext:
    """Context for tool registration to track source and mode"""
    source: Literal["local", "mcp"]
    mcp_name: str | None = None
    mcp_mode: ToolModeEnum | None = None
    default_config: ToolConfig | None = None
```

**Validation:**
- Dataclass can be instantiated
- Type hints are correct

**Estimated Time:** 10 minutes

---

### Task 2.2: Update `ToolRegistry.__init__`
**File:** `chatbot/langgraph/toolregistry.py`

**Changes:**
- No changes needed, but review for clarity

**Validation:**
- Existing functionality still works

**Estimated Time:** 5 minutes

---

### Task 2.3: Update `register_tool` Method Signature
**File:** `chatbot/langgraph/toolregistry.py`

**Changes:**
```python
def register_tool(
    self,
    tool: StructuredTool,
    context: ToolRegistrationContext | None = None
) -> None:
    """Registers a tool with the client."""
```

**Validation:**
- Method signature updated
- Backwards compatible (context is optional)

**Estimated Time:** 5 minutes

---

### Task 2.4: Implement Strict Mode Logic in `register_tool`
**File:** `chatbot/langgraph/toolregistry.py`

**Changes:**
1. Check if `context` is provided and `context.source == "mcp"` and `context.mcp_mode == ToolModeEnum.strict`
2. If tool not in `self.tool_definition_dict`:
   - Build detailed error message with:
     - Tool name
     - MCP server name
     - Mode
     - List of configured tools
     - Suggestions for resolution
   - Raise `ValueError` with detailed message
3. If tool IS in `self.tool_definition_dict`:
   - Register with explicit configuration
   - Log DEBUG: "Tool '{tool_name}' registered with explicit configuration"

**Error Message Template:**
```python
error_msg = f"""Tool '{tool_name}' from MCP server '{context.mcp_name}' is not configured in the toolbox.

MCP Server: {context.mcp_name}
Mode: strict
Missing Tool: {tool_name}

Configured tools: {list(self.tool_definition_dict.keys())}

To resolve:
1. Add the tool to myai.toolbox.tools in your configuration, OR
2. Change the MCP server mode to 'dynamic' and provide default_tool_config
"""
```

**Validation:**
- Strict mode with unconfigured tool raises error with correct message
- Strict mode with configured tool registers successfully
- Error message includes all required information

**Estimated Time:** 30 minutes

---

### Task 2.5: Implement Dynamic Mode Logic in `register_tool`
**File:** `chatbot/langgraph/toolregistry.py`

**Changes:**
1. Check if `context` is provided and `context.source == "mcp"` and `context.mcp_mode == ToolModeEnum.dynamic`
2. If tool IS in `self.tool_definition_dict`:
   - Merge explicit config with default config
   - Use explicit values where provided, defaults otherwise
   - Log DEBUG: "Tool '{tool_name}' configuration merged: explicit={...}, default={...}, final={...}"
   - Register with merged configuration
3. If tool NOT in `self.tool_definition_dict`:
   - Use `context.default_config` for registration
   - Log INFO: "Tool '{tool_name}' from MCP '{context.mcp_name}' not explicitly configured, using default configuration"
   - Register with default configuration

**Configuration Merging Logic:**
```python
def merge_tool_config(
    explicit: ToolConfig | None,
    default: ToolConfig,
    tool_name: str
) -> ToolConfig:
    """Merge explicit config with defaults, explicit takes precedence"""
    if explicit is None:
        return default

    return ToolConfig(
        name=tool_name,
        max_instances=explicit.max_instances,
        timeout=explicit.timeout,
    )
```

**Validation:**
- Dynamic mode with unconfigured tool uses defaults
- Dynamic mode with configured tool merges correctly
- Logging messages are correct
- Merged config has correct values

**Estimated Time:** 45 minutes

---

### Task 2.6: Handle Local Tools (Always Strict)
**File:** `chatbot/langgraph/toolregistry.py`

**Changes:**
1. When `context.source == "local"` or `context is None`:
   - Always use strict mode logic
   - If tool not in `self.tool_definition_dict`, raise error:
     ```
     Tool '{tool_name}' (local tool) is not configured in the toolbox.
     Local tools must always be explicitly configured.
     ```

**Validation:**
- Local tools without config raise error
- Local tools with config register successfully

**Estimated Time:** 20 minutes

---

### Task 2.7: Update `register_tools` Method
**File:** `chatbot/langgraph/toolregistry.py`

**Changes:**
```python
def register_tools(
    self,
    tools: Sequence[StructuredTool],
    context: ToolRegistrationContext | None = None
) -> None:
    """Registers multiple tools with the client."""
    for tool in tools:
        self.register_tool(tool, context=context)
```

**Validation:**
- Batch registration works correctly
- Context is passed to each tool registration

**Estimated Time:** 10 minutes

---

**Phase 2 Total Time:** ~2 hours 5 minutes

---

## Phase 3: MCP Client Updates

### Task 3.1: Add Connection Error Handling
**File:** `chatbot/mcp_client/__init__.py`

**Changes:**
1. Wrap MCP client connection in try-except
2. On connection failure:
   - Log ERROR with details
   - Raise exception to stop application startup
3. Error message format:
   ```
   Failed to connect to MCP server '{mcp.name}' at {mcp.url}
   Error: {error_details}

   The application cannot start without connecting to all configured MCP servers.
   ```

**Validation:**
- Connection failure stops application startup
- Error message is clear and actionable
- Error includes MCP name and URL

**Estimated Time:** 20 minutes

---

### Task 3.2: Add Empty Tool List Warning
**File:** `chatbot/mcp_client/__init__.py`

**Changes:**
1. After retrieving tools from MCP, check if list is empty
2. If empty, log WARNING:
   ```
   WARNING: MCP server '{mcp.name}' at {mcp.url} returned no tools
   ```

**Validation:**
- Empty tool list generates warning
- Application continues startup
- Warning includes MCP name and URL

**Estimated Time:** 10 minutes

---

### Task 3.3: Pass MCP Context to Tool Registration
**File:** `chatbot/mcp_client/__init__.py`

**Changes:**
1. Import `ToolRegistrationContext` and `ToolModeEnum`
2. For each MCP, create context:
   ```python
   context = ToolRegistrationContext(
       source="mcp",
       mcp_name=mcp.name,
       mcp_mode=mcp.mode,
       default_config=mcp.default_tool_config
   )
   ```
3. Pass context when registering tools (will be done in Phase 4)

**Validation:**
- Context is created correctly for each MCP
- Context includes all required fields

**Estimated Time:** 15 minutes

---

### Task 3.4: Add Tool Removal Warning
**File:** `chatbot/mcp_client/__init__.py`

**Changes:**
1. Track which tools are configured in `toolbox.tools`
2. After retrieving tools from MCP, check if any configured tools are missing
3. For each missing tool, log WARNING:
   ```
   WARNING: Tool '{tool_name}' was configured but is no longer available from MCP server '{mcp.name}'
   ```

**Note:** This requires knowing which tools came from which MCP. May need to enhance tool tracking.

**Validation:**
- Missing configured tools generate warnings
- Application continues startup
- Only tools from the specific MCP are checked

**Estimated Time:** 30 minutes

---

**Phase 3 Total Time:** ~1 hour 15 minutes

---

## Phase 4: Integration Updates

### Task 4.1: Update Local Tool Registration
**File:** `chatbot/langgraph/__init__.py`

**Changes:**
1. When registering local tools (`mytools`), create context:
   ```python
   local_context = ToolRegistrationContext(source="local")
   langgraph_handler.register_tools(mytools, context=local_context)
   ```

**Validation:**
- Local tools are registered with correct context
- Local tools always use strict mode

**Estimated Time:** 10 minutes

---

### Task 4.2: Update MCP Tool Registration
**File:** `chatbot/langgraph/__init__.py`

**Changes:**
1. In `bind_tools_when_ready`, get MCP config from app
2. For each MCP's tools, create appropriate context
3. Pass context to `register_tools`

**Implementation:**
```python
async def bind_tools_when_ready(app: web.Application):
    """Wait for the mcptools to be constructed then bind to them"""

    if keys.mcpobjects not in app:
        logger.error("MCPObjects not found in app context. Cannot bind tools.")
        raise ValueError("MCPObjects not found in app context.")

    config: ServiceConfig = app[keys.config]
    langgraph_handler: LanggraphHandler = app[keys.langgraph_handler]
    mcpObjects: MCPObjects = app[keys.mcpobjects]

    # Register MCP tools with context
    # Note: We need to track which tools came from which MCP
    # This may require changes to MCPObjects structure

    for mcp_config in config.myai.toolbox.mcps:
        # Get tools for this specific MCP
        # This requires MCPObjects to track tools per MCP
        mcp_tools = mcpObjects.get_tools_for_mcp(mcp_config.name)

        context = ToolRegistrationContext(
            source="mcp",
            mcp_name=mcp_config.name,
            mcp_mode=mcp_config.mode,
            default_config=mcp_config.default_tool_config
        )

        langgraph_handler.register_tools(mcp_tools, context=context)

    langgraph_handler.bind_tools()
    langgraph_handler.compile()
```

**Note:** This requires `MCPObjects` to track which tools came from which MCP server.

**Validation:**
- MCP tools are registered with correct context
- Each MCP's mode is respected
- Default configs are passed correctly

**Estimated Time:** 45 minutes

---

### Task 4.3: Update `MCPObjects` to Track Tools per MCP
**File:** `chatbot/mcp_client/__init__.py`

**Changes:**
1. Change `MCPObjects` structure:
   ```python
   @dataclass
   class MCPObjects:
       tools_by_mcp: dict[str, list[StructuredTool]] = field(default_factory=dict)
       all_tools: list[StructuredTool] = field(default_factory=list)
       resources: dict[str, list[Blob]] = field(default_factory=dict)
       prompts: dict[str, list[HumanMessage | AIMessage]] = field(default_factory=dict)

       def get_tools_for_mcp(self, mcp_name: str) -> list[StructuredTool]:
           return self.tools_by_mcp.get(mcp_name, [])
   ```

2. Update `connect_to_mcp_server` to populate `tools_by_mcp`:
   ```python
   tools_by_mcp = {}
   all_tools = []

   for mcp in toolbox_config.mcps:
       mcp_tools = await client.get_tools(mcp.name)
       tools_by_mcp[mcp.name] = mcp_tools
       all_tools.extend(mcp_tools)

   mcpObjects = MCPObjects(
       tools_by_mcp=tools_by_mcp,
       all_tools=all_tools,
       resources={...},
       prompts={...}
   )
   ```

**Validation:**
- Tools are correctly tracked per MCP
- `get_tools_for_mcp` returns correct tools
- `all_tools` contains all tools from all MCPs

**Estimated Time:** 30 minutes

---

**Phase 4 Total Time:** ~1 hour 25 minutes

---

## Phase 5: Testing

### Task 5.1: Unit Tests - Configuration Validation
**File:** `tests/test_config_validation.py` (new file)

**Test Cases:**
1. `test_strict_mode_without_default_config` - Valid
2. `test_dynamic_mode_with_default_config` - Valid
3. `test_dynamic_mode_without_default_config` - Invalid, raises ValidationError
4. `test_strict_mode_with_default_config` - Valid (ignored)
5. `test_invalid_mode_value` - Invalid, raises ValidationError

**Estimated Time:** 45 minutes

---

### Task 5.2: Unit Tests - Tool Registration Strict Mode
**File:** `tests/test_tool_registration_strict.py` (new file)

**Test Cases:**
1. `test_strict_mode_all_tools_configured` - Success
2. `test_strict_mode_tool_not_configured` - Raises ValueError with detailed message
3. `test_strict_mode_error_message_format` - Verify error message content
4. `test_local_tool_not_configured` - Raises ValueError
5. `test_local_tool_configured` - Success

**Estimated Time:** 1 hour

---

### Task 5.3: Unit Tests - Tool Registration Dynamic Mode
**File:** `tests/test_tool_registration_dynamic.py` (new file)

**Test Cases:**
1. `test_dynamic_mode_tool_not_configured_uses_default` - Success with defaults
2. `test_dynamic_mode_tool_configured_uses_explicit` - Success with explicit config
3. `test_dynamic_mode_tool_configured_partial_merge` - Success with merged config
4. `test_dynamic_mode_logs_info_for_default_tools` - Verify INFO log
5. `test_dynamic_mode_logs_debug_for_merge` - Verify DEBUG log

**Estimated Time:** 1 hour 15 minutes

---

### Task 5.4: Unit Tests - Configuration Merging
**File:** `tests/test_config_merging.py` (new file)

**Test Cases:**
1. `test_merge_explicit_overrides_all_fields` - All explicit values used
2. `test_merge_explicit_overrides_some_fields` - Mixed explicit and default
3. `test_merge_no_explicit_uses_all_defaults` - All default values used
4. `test_merge_preserves_tool_name` - Tool name is correct

**Estimated Time:** 45 minutes

---

### Task 5.5: Integration Tests - MCP Connection
**File:** `tests/test_mcp_integration.py` (new file)

**Test Cases:**
1. `test_mcp_connection_failure_exits_app` - Application fails to start
2. `test_mcp_returns_no_tools_warning` - Warning logged, app continues
3. `test_mcp_tool_removed_warning` - Warning logged for missing tool
4. `test_multiple_mcps_different_modes` - Mixed strict/dynamic MCPs work

**Estimated Time:** 1 hour 30 minutes

---

### Task 5.6: Integration Tests - End-to-End
**File:** `tests/test_e2e_tool_configuration.py` (new file)

**Test Cases:**
1. `test_app_starts_with_strict_mcp` - Full startup with strict mode
2. `test_app_starts_with_dynamic_mcp` - Full startup with dynamic mode
3. `test_app_starts_with_mixed_mcps` - Full startup with both modes
4. `test_tool_execution_with_default_config` - Tool from dynamic MCP executes
5. `test_tool_execution_with_explicit_config` - Tool with explicit config executes

**Estimated Time:** 2 hours

---

### Task 5.7: Update Existing Tests
**Files:** Various existing test files

**Changes:**
- Update any tests that create MCP configs to include `mode` field
- Update any tests that expect specific error messages
- Ensure all tests pass with new configuration schema

**Estimated Time:** 1 hour

---

**Phase 5 Total Time:** ~8 hours 15 minutes

---

## Phase 6: Documentation and Migration

### Task 6.1: Update README
**File:** `chatagent-container/README.md`

**Changes:**
- Add section on tool configuration modes
- Add examples of strict and dynamic mode configs
- Add migration guide from old to new config

**Estimated Time:** 30 minutes

---

### Task 6.2: Update Example Configs
**Files:**
- `tests/test_data/config.yaml`
- Any other example configs in the repository

**Changes:**
- Add `mode` field to all MCP configs
- Add `default_tool_config` to dynamic mode examples
- Add comments explaining the options

**Estimated Time:** 20 minutes

---

### Task 6.3: Create Migration Guide
**File:** `chatagent-container/docs/MIGRATION_GUIDE.md` (new file)

**Content:**
- Step-by-step migration from old to new config
- Examples of before/after configs
- Common issues and solutions
- FAQ section

**Estimated Time:** 45 minutes

---

**Phase 6 Total Time:** ~1 hour 35 minutes

---

## Phase 7: Validation and Cleanup

### Task 7.1: Manual Testing
**Activities:**
1. Start application with strict mode MCP
2. Start application with dynamic mode MCP
3. Start application with mixed modes
4. Trigger each error condition manually
5. Verify all log messages are correct
6. Test tool execution with default and explicit configs

**Estimated Time:** 1 hour

---

### Task 7.2: Code Review Checklist
**Items:**
- [ ] All error messages are clear and actionable
- [ ] All logging is at appropriate levels
- [ ] No hardcoded values (use config)
- [ ] Type hints are correct
- [ ] Docstrings are updated
- [ ] No debug print statements left in code
- [ ] All TODOs are addressed or documented

**Estimated Time:** 30 minutes

---

### Task 7.3: Performance Testing
**Activities:**
1. Test startup time with 1 MCP, 10 tools
2. Test startup time with 5 MCPs, 100 tools
3. Verify startup time impact is < 1 second
4. Profile if needed

**Estimated Time:** 30 minutes

---

**Phase 7 Total Time:** ~2 hours

---

## Summary

### Total Estimated Time
- **Phase 1:** Configuration Model Updates - 1 hour 5 minutes
- **Phase 2:** Tool Registry Updates - 2 hours 5 minutes
- **Phase 3:** MCP Client Updates - 1 hour 15 minutes
- **Phase 4:** Integration Updates - 1 hour 25 minutes
- **Phase 5:** Testing - 8 hours 15 minutes
- **Phase 6:** Documentation - 1 hour 35 minutes
- **Phase 7:** Validation - 2 hours

**Total: ~17 hours 40 minutes**

### Dependency Graph

```
Phase 1 (Config Models)
    ↓
Phase 2 (Tool Registry) ← Phase 3 (MCP Client)
    ↓                           ↓
    └─────→ Phase 4 (Integration) ←─────┘
                ↓
            Phase 5 (Testing)
                ↓
            Phase 6 (Documentation)
                ↓
            Phase 7 (Validation)
```

### Risk Assessment

**High Risk:**
- Tracking tools per MCP (Task 4.3) - May require significant refactoring
- Integration testing (Task 5.5) - Complex setup with mock MCPs

**Medium Risk:**
- Configuration merging logic (Task 2.5) - Edge cases may be tricky
- Error message formatting (Task 2.4) - Must be very clear

**Low Risk:**
- Configuration model updates (Phase 1) - Straightforward Pydantic changes
- Documentation (Phase 6) - Time-consuming but low complexity

### Mitigation Strategies

1. **For Task 4.3 (MCPObjects refactoring):**
   - Start with this task early to identify issues
   - Consider alternative approaches if too complex
   - May need to refactor `MultiServerMCPClient` usage

2. **For Integration Testing:**
   - Create reusable mock MCP fixtures
   - Use pytest-aiohttp for async testing
   - Consider using docker-compose for real MCP servers

3. **For Configuration Merging:**
   - Write unit tests first (TDD approach)
   - Test all edge cases explicitly
   - Document merging behavior clearly

---

## Acceptance Criteria

Before marking this implementation complete, verify:

- [ ] All unit tests pass (>90% coverage for new code)
- [ ] All integration tests pass
- [ ] Manual testing completed successfully
- [ ] All error messages are clear and actionable
- [ ] All logging is at appropriate levels
- [ ] Documentation is complete and accurate
- [ ] Migration guide is clear and tested
- [ ] Performance impact is acceptable (< 1s startup time increase)
- [ ] Code review checklist is complete
- [ ] No regressions in existing functionality

---

## Rollback Plan

If issues are discovered after deployment:

1. **Immediate:** Revert to previous version
2. **Short-term:** Fix critical issues in hotfix branch
3. **Long-term:** Address root causes and re-deploy

**Rollback Trigger Conditions:**
- Application fails to start in production
- Critical tools are not registered
- Performance degradation > 5 seconds startup time
- Data loss or corruption

---

## Approval

**Prepared by:** Antigravity AI
**Review requested from:** Ben Greene
**Status:** ⏳ Awaiting Review

**Next Steps:**
1. Review and approve this implementation plan
2. Execute implementation in phases
3. Review code changes as they are completed
4. Deploy to test environment
5. Deploy to production

---

**END OF IMPLEMENTATION PLAN**
