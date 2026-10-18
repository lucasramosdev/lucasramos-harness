---
name: vite-react-data-hook-writer
description: Create or modify a typed Vite React data hook for queries, domain workflows, mutations, and cache or refresh behavior.
---

# Frontend Data Hook Writer

## Purpose

Create or modify hooks that own reusable asynchronous or domain workflow behavior.

Typical targets are:

```text
projects/frontend/src/hooks/use<Feature>.ts
projects/frontend/src/hooks/use<Feature>.test.tsx
```

## Sources of Truth

Before editing, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/frontend-standard.md`;
3. `docs/engineering/frontend-style.md`;
4. `docs/engineering/frontend-example.md` when an example is needed;
5. the relevant `.ai/task-contract/front/<task_name>.md`;
6. the existing hook, API client, auth, state, and refresh/invalidation patterns.

## Scope

This skill handles only data hooks and their direct tests. It may:

- create or modify query and mutation hooks;
- call typed API client functions;
- expose loading, error, submitting, and result state;
- coordinate refetch, callback-based refresh, or query-cache invalidation according to the existing library;
- normalize responses at the hook boundary without changing backend semantics;
- map typed validation errors to a reusable form-facing shape;
- implement optimistic updates only when the task contract and existing data library support them.

Do not implement API transport, pages, visual components, forms, routes, or backend code unless explicitly requested.

## Rules

- Reuse the project's current data strategy. Do not introduce React Query or another library by assumption.
- Keep raw HTTP calls in `src/lib` API modules.
- Use purpose-specific hook names and explicit parameter/result types.
- Include required identifiers and effective filters in query keys when a query library is present.
- Use `enabled` or an equivalent guard for incomplete route-dependent input.
- Expose stable empty/loading/error shapes where the existing UI expects them.
- For optimistic updates, snapshot, rollback on error, and refresh affected data after settlement.
- Do not store a second auth state or scatter token handling through hooks.
- Avoid `any`, unsafe casts, and transport envelopes leaking into unrelated components.

## Workflow

1. Identify the hook contract and existing consumer.
2. Inspect the API function and neighboring hooks.
3. Define variables, result, errors, and state transitions explicitly.
4. Implement the smallest hook change using existing conventions.
5. Add focused tests for success, loading/pending, failure, and refresh behavior as applicable.

Do not redesign the page or API client to compensate for a hook change.

## Validation

From `projects/frontend`, run the focused test and:

```bash
pnpm run lint
pnpm run build
```
