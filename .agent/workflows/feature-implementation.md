---
description: Standard workflow for implementing a new feature or complex refactor.
---

# Feature Implementation Workflow

Follow these steps to ensure consistent implementation and tracking of new features.

## 1. Initial Planning
1. Review the corresponding SPEC file in `.agent/specs/`.
2. Create an Implementation Plan in `.agent/artifacts/<feature-name>-implementation-plan.md`.
3. Break the task into logical phases (e.g., Phase 1: Models, Phase 2: Core Logic, etc.).
4. Estimate time for each phase.

## 2. Iterative Development
For each Phase defined in the plan:
1. Implement the required code changes.
// turbo
2. Run the relevant tests using the `Makefile` (e.g., `make chatagent-test`).
3. If tests fail, debug and repeat step 2.
// turbo
4. Run `make lint` to clean up the code.
// turbo
5. **CRITICAL**: Re-run tests after linting to ensure no regressions were introduced by formatting or cleanup.
6. Once tests and lint pass, update the Implementation Plan:
    - Set Status to `COMPLETE`.
    - Record Actual Time.
7. Commit the changes with a descriptive message following conventional commits.

## 3. Configuration & Documentation Sync
1. Search the codebase for all `config.yaml` files and environment overrides.
2. Update them to match the new code/schema.
3. Update `README.md` and `docs/MIGRATION_GUIDE.md`.
4. Run a final full test suite.

## 4. Final Validation
1. Perform a manual review of the changes against the original SPEC.
2. Mark the Project as `COMPLETE` in the Implementation Plan.
