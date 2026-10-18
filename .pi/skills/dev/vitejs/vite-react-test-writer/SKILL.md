---
name: vite-react-test-writer
description: Create or modify focused Vite React frontend tests using the repository's Vitest and Testing Library conventions.
---

# Frontend Test Writer

## Purpose

Create or modify tests for frontend behavior at the correct boundary.

Typical targets are:

```text
projects/frontend/src/**/*.test.ts
projects/frontend/src/**/*.test.tsx
```

## Sources of Truth

Before editing, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/frontend-standard.md`;
3. `docs/engineering/frontend-style.md`;
4. the relevant `.ai/task-contract/front/<task_name>.md`;
5. existing Vitest setup, test helpers, fixtures, and tests at the same layer.

## Scope

This skill handles frontend test implementation. It may add or modify:

- API/client unit tests;
- hook tests;
- component interaction and accessibility tests;
- page/workflow tests;
- route/auth behavior tests;
- fixtures and test helpers local to the tested boundary.

Do not change production behavior merely to satisfy a test, replace the test framework, or add backend tests.

## Rules

- Use Vitest and the existing Testing Library setup.
- Test observable behavior and contracts, not implementation details.
- Prefer accessible queries and user interactions.
- Mock network boundaries using the repository's existing approach.
- Cover success, validation/error, pending/disabled, empty/loading, and auth states when relevant.
- Keep test data typed and realistic.
- Do not use `any` in fixtures or assertions without an unavoidable documented boundary.
- Keep tests deterministic; do not depend on real backend services or wall-clock timing unnecessarily.

## Workflow

1. Identify the architectural boundary and user-visible behavior.
2. Read the closest existing tests and shared setup.
3. Define realistic typed fixtures and arrange the required providers.
4. Write focused behavior assertions.
5. Run the focused test, then from `projects/frontend` run:

```bash
pnpm run lint
pnpm run build
```
