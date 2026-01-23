---
description: Workflow for safely rolling out configuration schema changes across the workspace.
---

# Configuration Change Rollout Recipe

Use this recipe when a Pydantic model or configuration schema is updated.

## 1. Schema Update
1. Update the Pydantic model in `chatbot/config/`.
2. Add necessary validation logic (e.g., `@field_validator`).
3. Verify the schema changes with unit tests.

## 2. Manifest Propagation
Update the following locations in order:
1. **Local Test Data**: `tests/test_data/config.yaml` - Ensure tests can run locally.
2. **Helm Templates**: `charts/<app>/configs/config.yaml` - Update the source template for deployments.
3. **FluxCD Overrides**: `fluxcd-dev/app-<app>.yaml` - Update environment-specific values.
4. **Active Environment Manifests**: Root level `hr-*.yaml` files (e.g., `hr-chatagent.yaml`).

## 3. Documentation
1. Add breaking changes or new fields to `docs/MIGRATION_GUIDE.md`.
2. Update example blocks in `README.md`.

## 4. Verification
1. Run `make <target>-test`.
2. check the application logs in a dev environment if possible to ensure the config loaded correctly.
