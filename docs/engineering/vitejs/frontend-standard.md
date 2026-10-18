# Frontend Architecture Standard — Vite + React + TypeScript

> **Status:** Source of Truth
>
> **Scope:** Frontend architecture, routes, pages, components, data hooks, API clients, forms, authentication, styling, mocks, and reviews.
>
> **Companion documents:** `frontend-style.md` defines implementation conventions; `frontend-example.md` provides reference examples.

## Purpose

This document is the source of truth for Vite React TypeScript frontend architecture in Helu.

Use it before generating, refactoring, or reviewing frontend code.

## Stack Defaults

Use:

- Vite
- React
- TypeScript
- shadcn/ui
- Tailwind CSS

Use the repository's existing package manager, routing library, query library, form library, and auth provider.

Do not introduce new major libraries without a clear need.

## Preferred Feature Architecture

```txt
Route
  -> Page
    -> Feature Components
      -> Data Hooks
        -> API Client
          -> Backend or Mock API
```

Mutation architecture:

```txt
Page/Component
  -> Mutation Hook
    -> API Client
    -> Cache update or invalidation
    -> Toast/navigation/form error mapping
```

Auth architecture:

```txt
Route Guard / Page
  -> useAuth
    -> centralized auth actions
    -> centralized token persistence
    -> centralized auth headers
```

## Artifact Ownership

Each frontend skill owns one implementation boundary:

| Responsibility | Skill |
|---|---|
| Route registration and guards | `vite-react-route-writer` |
| Route-level page orchestration | `vite-react-page-writer` |
| Domain visual component | `vite-react-component-writer` |
| Form state, validation, and submission UI | `vite-react-form-writer` |
| API transport and contract types | `vite-react-api-client-writer` |
| Async/domain data hook | `vite-react-data-hook-writer` |
| Vitest/Testing Library behavior tests | `vite-react-test-writer` |

Use the smallest set of skills that covers the requested artifacts. A skill must not expand into another boundary merely because the artifacts are related.

## Canonical Directories

The current frontend uses the following structure:

```txt
projects/frontend/
  src/
    App.tsx
    pages/
    components/
      ui/
    hooks/
    lib/
    contexts/
    shared/
    assets/
  public/
```

Feature-specific subdirectories may be introduced only when they improve cohesion and follow the existing module conventions:

```txt
src/
  pages/
  components/
    ui/
  hooks/
  lib/
```

Rules:

- Shared shadcn/ui primitives stay in the shared UI directory.
- Feature-specific components stay close to the feature.
- API clients and hooks stay outside visual components.
- Mock API code stays separate from UI code.
- Shared types should not become a dumping ground.
- `src/lib/apiClient.ts` and domain API modules own HTTP transport and payload parsing.
- `src/hooks` owns reusable asynchronous and domain workflows already established by the application.
- `src/components/ui` is the shared primitive layer; do not duplicate it inside feature folders.

## Route-First Standard

Build from the route/workflow first.

For each feature, define:

- Route path
- Route params
- Search params
- Page responsibility
- Data needed
- Mutations available
- Auth requirement
- Guest behavior
- Owner/non-owner behavior
- Navigation after success
- Loading, empty, and error states

Pages coordinate behavior. Components render focused UI.

The route contract must be established before implementation. For a new workflow, record it in `.ai/task-contract/front/<task_name>.md`.

## Page Standard

Pages may contain:

- Route param extraction
- Search param/filter state
- Auth state reads
- Query hook composition
- Mutation hook composition
- Navigation after success
- Layout composition

Pages should not contain:

- Raw `fetch`/`axios` calls
- Token handling
- Large repeated UI blocks
- Business-specific formatting duplicated across components
- Optimistic update internals
- Raw API envelope manipulation throughout JSX

## Component Standard

Components should:

- Have explicit props.
- Be named by domain role.
- Use shadcn/ui primitives when appropriate.
- Use Tailwind classes for styling.
- Render focused visual responsibilities.
- Own small action loading state when the action is local to the component.
- Link list items to detail routes when appropriate.

Components should not:

- Fetch data directly unless intentionally designed as a data-aware reusable component.
- Set tokens.
- Mutate global auth state directly.
- Know raw transport quirks.
- Accept untyped blobs.

## shadcn/ui Standard

shadcn/ui is the default primitive layer.

Prefer shadcn/ui for:

- Buttons
- Inputs
- Textareas
- Selects
- Checkboxes
- Cards
- Dialogs
- Dropdowns
- Tables
- Tabs
- Badges
- Alerts
- Skeletons
- Forms
- Labels
- Sheets
- Popovers
- Toasts

Rules:

- Import from the existing shared UI path.
- Do not copy shadcn components into feature folders.
- Do not duplicate shadcn primitives manually.
- Use the existing `cn` helper when composing conditional classes.
- Use existing CSS variables and Tailwind tokens.
- Do not create a second design system.

## Tailwind Standard

Use Tailwind for:

- Layout
- Spacing
- Typography
- Borders
- Shadows
- Responsive behavior
- Hover/focus states
- Grid/flex
- Color tokens

Avoid:

- Feature `.css` files
- CSS modules for normal feature styling
- Inline styles
- Hardcoded arbitrary values when existing tokens work
- Large unreadable class strings

Allowed CSS files:

- Existing Tailwind global entry file.
- Existing shadcn global style file.

## TypeScript Standard

Every public boundary must be typed.

Type:

- Component props
- Hook arguments
- Hook results when inference is unclear
- API request envelopes
- API response envelopes
- Domain records
- Form values
- Filters
- Query keys
- Mutation variables
- Mutation results
- Mutation rollback context
- Mock records

Avoid `any`.

Allowed exceptions:

- A third-party boundary cannot be typed more narrowly.
- A migration/refactor explicitly accepts temporary `any`.
- The `any` is isolated and documented.

Prefer:

- `unknown` plus refinement
- Generics
- Discriminated unions
- `satisfies`
- Narrow string unions
- Explicit nullable fields

## Data Fetching Standard

GET requests should be handled by query hooks.

Rules:

- Use semantic hook names.
- Use semantic query keys.
- Include identity and filters in query keys.
- Use `enabled` when params are required.
- Use `placeholderData` for stable first render.
- Use `initialData` when existing data can seed a query.
- Keep previous data during pagination/filter changes when useful.
- Normalize API envelopes at hook/model boundaries.
- Components should consume stable shapes.

## Mutation Standard

Mutations should be handled by purpose-specific hooks.

Rules:

- Type variables and results.
- Type rollback context.
- Invalidate visible affected queries.
- Navigate on obvious success destinations.
- Map API validation errors to forms.
- Use optimistic updates for fast toggles.
- Roll back optimistic updates on error.
- Revalidate on settled.

## Form Standard

Forms must include:

- Dedicated form values type.
- Explicit complete initial values.
- Async reinitialization for edit forms.
- Disabled submit state.
- API validation error rendering.
- Reusable error rendering when repeated.
- shadcn form primitives when present.

## Auth Standard

Auth should be centralized.

Rules:

- Use the existing auth hook/provider.
- Do not create parallel auth stores.
- Do not scatter token persistence.
- Do not manually set auth headers in pages/components.
- Use route guards for protected pages.
- Use guest guards for guest-only pages.
- Redirect guests for gated inline actions.
- Show owner controls only to owners.
- Show guest callouts for visible interactions that require auth.

## Mock API Standard

Use mock API only when needed for realistic local development.

Rules:

- Mirror real API envelopes.
- Keep records typed.
- Include relational data when needed.
- Implement filters/pagination.
- Implement computed fields.
- Persist locally when useful.
- Avoid mock-only contracts.
- Keep mocks separate from test-mode request forwarding.

## Required User States

Where relevant, represent:

- Loading
- Error
- Empty
- Authenticated
- Guest
- Owner
- Non-owner
- Submitting
- Disabled
- Optimistic/pending

## Validation Commands

Run only commands that exist in the repository.

Prefer:

```bash
pnpm run lint
pnpm run test
pnpm run build
```

or equivalent package-manager commands:

```bash
pnpm typecheck
pnpm lint
pnpm test
pnpm build
```

## Approval Checklist

Approve frontend changes only when:

- Route/workflow is complete.
- shadcn/ui and Tailwind are used by default.
- No unnecessary raw CSS exists.
- No JavaScript files are added.
- Public boundaries are typed.
- `any` is avoided or justified.
- Pages do not do raw HTTP calls.
- Hooks own server interaction.
- Query keys are semantic.
- Mutations update or invalidate visible data.
- Optimistic updates have rollback.
- Forms handle async data, submitting state, and validation errors.
- Auth behavior is centralized.
- User states are explicit.
- Typecheck/build pass.