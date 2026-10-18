---
name: vite-react-page-writer
description: Create or modify a Vite React route-level page that coordinates params, hooks, auth, navigation, and feature composition.
---

# Frontend Page Writer

## Purpose

Create or modify a route-level page in the frontend.

Typical targets are:

```text
projects/frontend/src/pages/<Page>.tsx
projects/frontend/src/pages/<Area>/<Page>.tsx
```

## Sources of Truth

Before editing, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/frontend-standard.md`;
3. `docs/engineering/frontend-style.md`;
4. `docs/engineering/frontend-example.md` when an example is needed;
5. the relevant `.ai/task-contract/front/<task_name>.md`;
6. the existing route registration, neighboring pages, hooks, auth guards, and layout.

## Scope

This skill handles page orchestration. It may:

- read route and search parameters;
- compose data hooks and feature components;
- coordinate auth state and existing guards;
- manage page-level filters and navigation;
- connect form submission to mutations;
- render loading, empty, error, guest, owner, and non-owner states;
- preserve existing layout and responsive behavior.

Do not implement transport functions, reusable domain components, hook internals, backend logic, or route registration unless explicitly requested.

## Rules

- Start from the user-visible route/workflow and its contract.
- Keep pages as orchestration layers, not large visual components.
- Do not call `fetch`, `axios`, or the API client directly from a page.
- Do not set auth tokens or create parallel auth state.
- Keep raw API envelopes and optimistic-update internals out of JSX.
- Extract repeated or domain-specific UI into named components.
- Navigate after obvious successful operations when the established workflow requires it.
- Preserve existing route paths, permissions, and backend contracts.

## Workflow

1. Locate the route, page, layout, and auth boundary.
2. Define params, required data, mutations, states, and success navigation.
3. Reuse existing hooks and components before adding new ones.
4. Implement page orchestration with explicit props and state.
5. Verify desktop/mobile and all relevant async/auth states.

## Validation

From `projects/frontend`, run focused tests and:

```bash
pnpm run lint
pnpm run build
```
