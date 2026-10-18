---
name: vite-react-component-writer
description: Create or modify a typed Vite React domain component using the existing shadcn/ui primitives and Tailwind conventions.
---

# Frontend Component Writer

## Purpose

Create or modify a focused visual component for a frontend feature.

Typical targets are:

```text
projects/frontend/src/components/<area>/<Component>.tsx
projects/frontend/src/components/ui/<Primitive>.tsx
```

## Sources of Truth

Before editing, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/frontend-standard.md`;
3. `docs/engineering/frontend-style.md`;
4. `docs/engineering/frontend-example.md` when an example is needed;
5. the relevant `.ai/task-contract/front/<task_name>.md`;
6. nearby components, shared UI primitives, tokens, and tests.

## Scope

This skill handles focused React visual components. It may:

- create or modify typed `.tsx` components;
- compose shared shadcn/ui primitives;
- apply Tailwind layout, spacing, responsive, focus, and state classes;
- render loading, empty, error, disabled, pending, and auth-dependent states;
- expose intent-focused typed props and callbacks;
- add focused component tests when the repository has them.

Do not implement API clients, data hooks, page orchestration, route registration, or backend changes unless explicitly requested.

## Rules

- Use `.tsx` for React components and TypeScript for all source.
- Name components by domain role, not generic layout (`TruckCard`, not `Box`).
- Type every public prop; avoid `any` and unsafe casts.
- Prefer existing shadcn/ui primitives from `src/components/ui`.
- Use Tailwind and existing design tokens; do not create a parallel design system.
- Do not create feature CSS, inline styles, or copied shared primitives without a concrete repository reason.
- Keep data fetching outside presentational components unless the component is intentionally data-aware and reusable.
- Keep local action pending state close to the action when appropriate.
- Use the shared toast facade for transient feedback; keep field errors and persistent page states inline.
- Preserve accessibility: labels, focus behavior, keyboard interaction, semantic roles, and disabled states.

## Workflow

1. Identify the component's domain responsibility and consumer.
2. Inspect the closest existing component and available UI primitives.
3. Define a small, intent-focused prop contract.
4. Implement visual and interaction states with existing tokens.
5. Add or update focused tests for important interaction and accessibility behavior.

## Validation

From `projects/frontend`, run the focused test and:

```bash
pnpm run lint
pnpm run build
```
