# MCP Tool Configuration Migration Guide

This guide describes how to migrate your `config.yaml` to support the new MCP tool configuration schema introduced in version 0.4.0.

## Overview of Changes

1. **`mode` field is now REQUIRED** for all MCP server configurations.
2. **`strict` mode** enforces that every tool from an MCP server must be listed in `myai.toolbox.tools`.
3. **`dynamic` mode** allows using tools without explicit configuration, but requires a `default_tool_config`.
4. **`instance_counts`** has been removed from `ToolConfig` (it was internal state, not configuration).

---

## Migration Steps

### Step 1: Add `mode` to MCP Configurations

For each entry in `myai.toolbox.mcps`, you must add a `mode` field.

**If you want to maintain existing behavior (Strict Mode):**
Set `mode: strict`. This ensures that only tools you have explicitly configured are used.

**Before:**
```yaml
mcps:
  - name: customers
    url: http://localhost:8180/mcp
    transport: streamable_http
```

**After (Strict):**
```yaml
mcps:
  - name: customers
    url: http://localhost:8180/mcp
    transport: streamable_http
    mode: strict  # <-- ADD THIS
```

### Step 2: (Optional) adopt Dynamic Mode

If you want to automatically accept all tools from an MCP server without listing them individually, use `mode: dynamic`. You MUST provide a `default_tool_config`.

**After (Dynamic):**
```yaml
mcps:
  - name: customers
    url: http://localhost:8180/mcp
    transport: streamable_http
    mode: dynamic  # <-- ADD THIS
    default_tool_config:  # <-- ADD THIS (Required for dynamic mode)
      max_instances: 5
      timeout: P0DT0H0M30S
```

### Step 3: Remove `instance_counts`

If you have `instance_counts` in your `myai.toolbox.tools` list, remove it. This field is no longer valid in configuration.

**Before:**
```yaml
tools:
  - name: sum_numbers
    max_instances: 10
    instance_counts: 0  # <-- REMOVE THIS
```

**After:**
```yaml
tools:
  - name: sum_numbers
    max_instances: 10
```

---

## Troubleshooting

### Error: `default_tool_config is required when mode is 'dynamic'`
You set `mode: dynamic` but forgot to add the `default_tool_config` block. Add it to your MCP configuration.

### Error: `Tool 'X' from MCP server 'Y' is not configured in the toolbox`
You are using `mode: strict` but the MCP server returned a tool (`X`) that isn't listed in `myai.toolbox.tools`.
**Fix:** either add the tool to your config OR switch to `mode: dynamic`.

### Error: `Failed to connect to MCP server 'X'`
The application now enforces that all configured MCP servers must be reachable at startup. Ensure your MCP servers are running.
