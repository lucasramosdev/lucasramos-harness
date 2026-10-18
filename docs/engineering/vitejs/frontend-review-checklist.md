# Frontend Review Checklist

> **Status:** Review aid
> **Source of truth:** `frontend-standard.md` and `frontend-style.md`

Use this checklist after reading the standard and style guide, before approving frontend changes. It is not a substitute for the task contract or architectural documents.

## Route / Workflow

- [ ] The feature starts from a clear route or user-visible workflow.
- [ ] Route params are used as resource identity where relevant.
- [ ] Search params or filter state are handled consistently.
- [ ] Navigation after create/update/delete/login/logout is handled when obvious.
- [ ] The page is an orchestration layer, not a giant component.

## shadcn/ui + Tailwind

- [ ] shadcn/ui primitives are used where appropriate.
- [ ] Tailwind utility classes are used for styling.
- [ ] No unnecessary raw CSS files were added.
- [ ] No unnecessary inline styles were added.
- [ ] No new design system was invented.
- [ ] shadcn/ui components are imported from the shared UI path.
- [ ] Feature folders do not copy shared UI primitives.

## TypeScript

- [ ] React files are `.tsx`.
- [ ] Non-React files are `.ts`.
- [ ] No JavaScript files were added.
- [ ] Component props are typed.
- [ ] Hook inputs/results are typed.
- [ ] API envelopes are typed.
- [ ] Form values are typed.
- [ ] Mutation variables are typed.
- [ ] Optimistic rollback contexts are typed.
- [ ] No unjustified `any` exists.

## Data Fetching

- [ ] GET logic lives in query hooks.
- [ ] Raw HTTP calls are in API clients.
- [ ] Query keys include resource identity.
- [ ] Query keys include effective filters.
- [ ] Param-dependent queries use `enabled`.
- [ ] Hooks provide stable placeholder/default data when useful.
- [ ] Components do not contain unsafe casts for API data.
- [ ] Loading, empty, and error states exist.

## Mutations

- [ ] Mutations use purpose-specific hooks.
- [ ] Visible affected queries are invalidated or updated.
- [ ] Fast toggles use optimistic updates when expected.
- [ ] Optimistic updates snapshot previous cache.
- [ ] Rollback happens on error.
- [ ] Settled invalidation happens.
- [ ] Validation errors are mapped back to forms.
- [ ] Success navigation/toast behavior is handled.

## Forms

- [ ] Initial values are explicit and complete.
- [ ] Edit forms reinitialize when async source data arrives.
- [ ] Submit controls are disabled while submitting.
- [ ] API validation errors are rendered.
- [ ] Repeated error markup is centralized.
- [ ] Custom form controls are extracted.

## Auth

- [ ] Auth state comes from the existing auth hook/provider.
- [ ] Token handling is centralized.
- [ ] Protected routes use the existing guard pattern.
- [ ] Guest-only routes use the existing pattern when present.
- [ ] Guest inline actions redirect or show a callout.
- [ ] Owner/non-owner controls are represented where relevant.
- [ ] Components do not create parallel auth state.

## Mock API

- [ ] Mock API mirrors real API envelopes.
- [ ] Mock records are typed.
- [ ] Filters/pagination are implemented when the UI needs them.
- [ ] Relationships are realistic.
- [ ] Mock-only contracts do not leak into UI.
- [ ] Development mocks are separate from test-mode response control.

## Commands

Run commands that exist in the repository:

```bash
pnpm run lint
pnpm run test
pnpm run build
```

Equivalent package-manager commands are fine.