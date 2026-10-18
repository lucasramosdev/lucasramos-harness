# Frontend Style Guide and Conventions

> **Status:** Source of Truth
>
> **Scope:** Frontend implementation, generation, refactoring, tests, reviews, forms, data hooks, styling, and user feedback.
>
> **Companion documents:** `frontend-standard.md` defines architecture; `frontend-example.md` demonstrates the conventions.

Use this guide before editing the Vite React TypeScript frontend. When it conflicts with a generic framework recommendation, this guide and the existing repository pattern take precedence.

## Goals

Frontend code must be route-first, typed, cohesive, and aligned with the existing project.

Prefer:

- Vite
- React
- TypeScript
- shadcn/ui
- Tailwind CSS
- Typed data hooks
- Typed API clients
- Explicit loading, empty, error, auth, guest, owner, and non-owner states

Avoid:

- Raw CSS for feature styling
- JavaScript files
- `any`
- Inline styles
- Fetching directly inside pages/components
- New design systems
- Duplicated form error markup
- Untyped mutation/cache behavior

## File Rules

Use:

- `.tsx` for React pages, components, route guards, layouts, providers, and visual wrappers.
- `.ts` for hooks, API clients, models, schemas, utilities, mock APIs, and shared types.

Do not create:

- `.js`
- `.jsx`
- Feature-specific `.css` files

Do not change API contracts, authentication behavior, or domain rules as a side effect of visual work. Preserve backend-defined field names and envelopes, including `snake_case` where the API uses it.

Exceptions:

- Existing global Tailwind entry CSS, usually `src/index.css`, `src/globals.css`, or `src/app.css`.
- Existing shadcn global CSS setup.

## Architecture Flow

Preferred feature flow:

```txt
Route -> Page -> Components -> Hooks -> API Client -> Backend/Mock API
```

Mutation flow:

```txt
Component/Page -> Mutation Hook -> API Client -> Cache Update/Invalidation -> Navigation/Toast
```

Auth flow:

```txt
Route Guard / Page -> useAuth -> centralized auth actions/storage/API headers
```

## Route-First Rule

Start from the user-visible workflow.

For each feature, identify:

- Route path
- Route params
- Search params
- Required data
- Auth requirement
- Guest behavior
- Owner/non-owner behavior
- Create/update/delete/navigation behavior
- Loading, empty, and error states

Pages coordinate the workflow.

Pages should not contain every UI detail.

## Page Rules

Pages may coordinate:

- Route params
- Search params
- Filters
- Auth state
- Navigation
- Hook composition
- Form submission
- Layout composition

Pages must not:

- Contain raw API calls
- Contain all visual details
- Own reusable list row/card/form UI
- Scatter validation error rendering
- Contain complex optimistic update logic
- Set auth tokens directly

## Component Rules

Components should be named by domain role.

Good:

```txt
ProjectCard
ChecklistItemRow
TransactionFilters
ExpenseForm
GuestCommentCallout
OwnerActionMenu
```

Avoid:

```txt
Box
Wrapper
Thing
LeftSide
MyComponent
```

Component props must be explicit:

```tsx
type ProjectCardProps = {
  project: ProjectSummary
  onOpen: (id: string) => void
}
```

Avoid `any`.

Use intent-focused props:

- `id`
- `slug`
- `username`
- `filters`
- `favorited`
- `following`
- `isOwner`
- `onDelete`
- `onSubmit`

## shadcn/ui + Tailwind Rules

Use shadcn/ui as the default UI primitive layer.

Use Tailwind for layout and styling.

Prefer shadcn/ui components for:

- Button
- Input
- Textarea
- Select
- Checkbox
- Card
- Dialog
- AlertDialog
- DropdownMenu
- Tabs
- Badge
- Alert
- Skeleton
- Table
- Form
- Label
- Sheet
- Popover
- Toast/Sonner

Rules:

- Do not create raw CSS for normal feature styling.
- Do not use inline `style={{ ... }}` unless absolutely necessary.
- Do not hand-roll components already available in shadcn/ui.
- Do not copy shadcn/ui primitives into feature folders.
- Import shared shadcn/ui primitives from the existing UI path.
- Use existing design tokens and CSS variables.
- Keep Tailwind classes readable.
- Do not invent a new design system.

## User Feedback Rules

Use the shared Sonner integration for every transient message intended for the
user, including successful mutations, request failures, upload results and
operational warnings.

Rules:

- Import the shared `toast` facade from `src/lib/toast`.
- Use `toast.success(...)` for successful operations.
- Use `toast.error(...)` for request, validation and upload failures that must
  be communicated globally.
- Do not create custom fixed notification stacks or page-level banners for
  transient API responses.
- Keep inline messages only for field-level validation or persistent page
  states where the message is part of the content.
- Every file upload must emit a success or error toast.
- A failed file upload must not remain rendered as an attached file.
- Do not render duplicate success/error text below an attachment when Sonner
  already reports the result.

## TypeScript Rules

Explicitly type:

- Component props
- Route params
- Search params
- API envelopes
- Domain records
- Form values
- Query filters
- Query keys
- Mutation variables
- Mutation results
- Optimistic update rollback context
- Mock API records

Avoid:

- `any`
- `as any`
- `@ts-ignore`
- Unsafe casts inside components
- Untyped API responses

Use:

- Narrow types
- Discriminated unions
- Generics
- `unknown` plus refinement at external boundaries
- `satisfies` when it improves inference without widening types

## Data Hook Rules

Use purpose-named hooks:

```txt
useProjectQuery
useProjectsQuery
useCreateProjectMutation
useUpdateProjectMutation
useDeleteProjectMutation
```

Rules:

- Keep GET logic in query hooks.
- Keep mutation logic in mutation hooks.
- Keep raw HTTP calls in API clients.
- Use `enabled` for param-dependent queries.
- Use `placeholderData` for stable first render.
- Use `initialData` when existing list data can seed detail data.
- Keep previous list data during pagination/filter transitions when useful.
- Normalize nested API envelopes at hook/model boundaries.
- Components should not need unsafe casts.

## Query Key Rules

Query keys must include identity and effective filters.

Good:

```ts
export const projectKeys = {
  all: ["projects"] as const,
  lists: () => [...projectKeys.all, "list"] as const,
  list: (filters: ProjectFilters) => [...projectKeys.lists(), filters] as const,
  detail: (id: string) => [...projectKeys.all, "detail", id] as const,
}
```

Avoid:

```ts
["data"]
["list"]
["projects"]
```

when filters or identities matter.

## Mutation Rules

Use purpose-specific mutation hooks.

Invalidate the smallest useful query set.

Use optimistic updates for fast toggles such as:

- favorite
- follow
- like
- bookmark
- enable/disable

Optimistic update rules:

1. Cancel relevant in-flight queries.
2. Snapshot previous cache data.
3. Update visible caches.
4. Restore snapshot on error.
5. Invalidate affected detail/list/feed queries on settled.

Rollback context must be explicitly typed.

## Form Rules

Forms must have:

- Explicit form-values type
- Complete initial values
- Submitting state
- Validation error rendering
- API validation error mapping
- Async data reinitialization for edit forms

Prefer shadcn Form/Input/Textarea/Select/Button where available.

Extract custom controls like tag editors or complex selectors.

## Auth Rules

Use a single existing auth hook/provider.

The auth hook should expose:

- Current user
- `isAuth`
- Login action
- Logout action
- Auth check action if present

Rules:

- Do not create parallel auth state.
- Do not scatter token storage through pages.
- Do not manually set auth headers in feature components.
- Use route guards for protected routes.
- Use guest guards for login/register routes when the repo has that pattern.
- Redirect guests to login for gated inline actions.
- Swap owner/non-owner controls based on ownership.
- Render guest callouts for visible auth-only interactions.

## Local Mock API Rules

When backend is unavailable but the frontend workflow needs realistic behavior, create a mock API.

Mocks should:

- Mirror the real API shape.
- Use typed records.
- Use realistic relational data.
- Implement filters and pagination.
- Implement computed fields.
- Persist locally when useful.
- Avoid mock-only UI contracts.
- Keep test-mode request forwarding separate from development mocks.

## Review Rejection Rules

Reject frontend changes if:

- New files are JavaScript.
- React files are not `.tsx`.
- Non-React files are not `.ts`.
- `any` is used without explicit unavoidable boundary.
- Raw CSS is added for feature styling.
- Inline styles are used where Tailwind is enough.
- shadcn/ui is bypassed for common primitives.
- Pages perform raw HTTP calls.
- Components perform raw HTTP calls.
- Query keys are too generic.
- Mutations do not invalidate/update visible data.
- Optimistic updates lack rollback.
- Forms lack typed values or validation error handling.
- Auth/token behavior is scattered.
- Loading/empty/error states are missing.
- Owner/guest/non-owner states are missing where relevant.