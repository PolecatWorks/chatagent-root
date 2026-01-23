# Project Rules

This document outlines the coding standards, workflows, and operational rules for the PolecatWorks chatagent-root workspace.

## 1. Implementation Tracking
- **Rule**: Every significant feature or refactor must have a corresponding Implementation Plan in `.agent/artifacts/<feature-name>-implementation-plan.md`.
- **Workflow**:
    - At the end of every task or phase, update the plan with:
        - Actual completion time.
        - Status (COMPLETE, BLOCKED, etc.).
        - Any notes or deviations from the original plan.
- **Reasoning**: This provides clear visibility into progress and helps in retrospective analysis.

## 2. Configuration Synchronization
- **Rule**: When modifying configuration schemas (e.g., Pydantic models in `chatbot/config/`), you MUST identify and update all relevant configuration files across the repository.
- **Checked Locations**:
    - `tests/test_data/config.yaml`
    - `charts/<component>/configs/config.yaml` (Templates)
    - `fluxcd-dev/app-<component>.yaml` (Environment overrides)
    - Root `HelmRelease` files (e.g., `hr-chatagent.yaml`)
- **Reasoning**: Prevents application startup failures in production and testing environments due to schema mismatches.

## 3. Testing & Quality Standards
- **Rule**: Never commit changes without running the relevant `make <target>-test` command.
- **Rule**: Run `make lint` before every commit to ensure code quality and consistent formatting.
- **Rule**: After fixing lint issues, you MUST run tests again to verify that the formatting changes didn't break functionality.
- **Rule**: Before merging to `main`, verify all relevant Docker builds are successful using `make <target>-docker`.
- **Rule**: New features should include a dedicated test file in `tests/`.
- **Reasoning**: Ensures stability and keeps the codebase clean. Running tests after linting prevents regressions caused by automatic formatters or manual cleanup.

## 4. Documentation Requirements
- **Rule**: Every configuration change that breaks backward compatibility or introduces new required fields MUST be accompanied by:
    - An update to the main `README.md`.
    - A specific `docs/MIGRATION_GUIDE.md` (or an update to the existing one).
- **Reasoning**: Ensures other developers and operators can safely upgrade their environments.

## 5. MCP Tool Logic
- **Rule**: Local tools must always be registered using **strict mode** logic (explicitly configured in the toolbox).
- **Rule**: MCP servers must specify a `mode` (strict or dynamic). If dynamic, a `default_tool_config` is mandatory.
- **Reasoning**: Maintains explicit control over tool availability and prevents unexpected tool exposure.

## 6. Naming Conventions
- **Rule**: Container directories should follow the pattern `<name>-container`.
- **Rule**: Makefile targets should follow the pattern `<name>-<action>` (e.g., `chatagent-test`).
- **Rule**: Helm charts should be located in `charts/<name>/`.
- **Rule**: FluxCD manifests in `fluxcd-dev/` should follow `app-<name>.yaml`.
- **Reasoning**: Consistency across the repository simplifies discovery and automation.

## 7. Process Management
- **Rule**: Long-running dev servers (e.g., `make chatagent-dev`) should be started and monitored using the background command tools.
- **Rule**: Always check `command_status` for background processes if suspecting environment issues.

## 8. Commit Message Standards
- **Rule**: Follow [Conventional Commits](https://www.conventionalcommits.org/).
    - `feat:` for new features.
    - `fix:` for bug fixes.
    - `chore:` for maintenance/manifest updates.
    - `docs:` for documentation-only changes.
- **Reasoning**: Improves changelog generation and commit history readability.
