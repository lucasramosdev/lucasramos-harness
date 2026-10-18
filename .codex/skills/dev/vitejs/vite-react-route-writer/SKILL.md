---
name: vite-react-route-writer
description: Create or modify Vite React route registration and route guards while preserving the application's navigation and auth conventions.
---

# Frontend Route Writer

## Purpose

Create or modify route registration and route-level guards.

Typical targets are:

```text
projects/frontend/src/App.tsx
projects/frontend/src/components/auth/<Guard>.tsx
projects/frontend/src/lib/navigation.ts
```

## Sources of Truth

Before editing, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/frontend-standard.md`;
3. `docs/engineering/frontend-style.md`;
4. the relevant `.ai/task-contract/front/<task_name>.md`;
5. the existing route table, layouts, protected/guest guards, redirects, and not-found page.

## Scope

This skill handles only route registration and guards. It may:

- add or modify a route path and element;
- define route params and nested route structure;
- apply existing protected or guest-only guards;
- preserve redirect behavior and fallback routes;
- connect a route to an existing page.

Do not implement page content, data hooks, API clients, visual components, or authentication storage.

## Rules

- Preserve existing route paths unless the task explicitly changes them.
- Use the application's established router and guard pattern.
- Keep route protection at the route boundary, not scattered through child components.
- Ensure route params match the page's typed expectations.
- Preserve the 404 route and mandatory-password-change/auth redirect behavior.
- Do not create a second auth provider or manually manage tokens in route files.

## Workflow

1. Locate the current route table and applicable guards.
2. Confirm the requested path, params, access rule, and redirect behavior.
3. Reuse the target page and existing layout.
4. Implement the smallest route change.
5. Verify authenticated, guest, redirect, parameter, and not-found behavior.
