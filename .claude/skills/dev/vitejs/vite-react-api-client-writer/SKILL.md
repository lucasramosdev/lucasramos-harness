---
name: vite-react-api-client-writer
description: Create or modify a typed Vite React API client module for an existing frontend request or response contract.
---

# Frontend API Client Writer

## Purpose

Create or modify the transport boundary between the React frontend and the backend.

Typical targets are:

```text
projects/frontend/src/lib/<domain>.ts
projects/frontend/src/lib/apiClient.ts
```

## Sources of Truth

Before editing, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/frontend-standard.md`;
3. `docs/engineering/frontend-style.md`;
4. `docs/engineering/frontend-example.md` when an example is needed;
5. the relevant `.ai/task-contract/front/<task_name>.md`;
6. backend DTOs, routes, and existing frontend API modules.

## Scope

This skill handles only API client code and transport types. It may:

- add or modify request and response types;
- add typed GET, POST, PUT, PATCH, or DELETE functions;
- preserve the backend's field names and envelopes;
- parse or validate uncertain response data at the transport boundary;
- reuse the centralized auth-aware API client;
- expose typed upload, download, or file operations when required.

Do not implement pages, visual components, hooks, forms, backend changes, or mock-only contracts unless explicitly requested.

## Rules

- Reuse `src/lib/apiClient.ts` and existing domain modules.
- Do not put raw HTTP calls in pages or visual components.
- Match the backend contract exactly; do not invent normalization that changes meaning.
- Keep backend `snake_case` at the transport boundary when that is the API contract.
- Type request envelopes, response envelopes, query parameters, and validation errors.
- Keep auth headers and token persistence centralized.
- Use `unknown` plus refinement at uncertain external boundaries; avoid `any`.
- Keep storage upload transport separate from authenticated API transport when the repository does so.

## Workflow

1. Locate the existing client and closest domain module.
2. Confirm the route, method, envelope, fields, optionality, and error shape from the backend.
3. Reuse existing types and helpers where the contract is identical.
4. Implement the smallest typed client change.
5. Add or update focused client tests when the module has them.

Do not expand the change to a hook merely because the new client function will be consumed by one.

## Validation

Run the repository's focused tests, then from `projects/frontend` run:

```bash
pnpm run lint
pnpm run build
```
