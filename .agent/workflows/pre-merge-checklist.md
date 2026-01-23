---
description: Final checklist and verification steps before merging to the main branch.
---

# Pre-Merge Checklist

Follow these steps before merging any feature or fix branch into `main`.

## 1. Local Testing
1. Run full test suite: `make chatagent-test` and `make customer-mcp-test`.
2. Ensure all tests pass (no regressions).

## 2. Docker Verification
1. Build all modified containers:
   - `make chatagent-docker`
   - `make customer-mcp-docker`
2. Ensure builds complete without errors. This verifies dependencies and entrypoints.

## 3. Configuration & Manifest Review
1. Ensure all `config.yaml` files are updated (see `config-rollout` recipe).
2. Check `hr-*.yaml` files for any hardcoded environment values that should be removed or updated.

## 4. Documentation
1. Verify `README.md` is updated.
2. Verify `docs/MIGRATION_GUIDE.md` includes any breaking changes.

## 5. Metadata Update
1. Update the Implementation Plan to `COMPLETE`.
2. Final review of code for any `TODO` or debug statements.
