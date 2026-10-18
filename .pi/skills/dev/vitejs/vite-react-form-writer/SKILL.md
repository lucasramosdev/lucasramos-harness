---
name: vite-react-form-writer
description: Create or modify a typed Vite React form with explicit values, validation, async submission, and existing UI controls.
---

# Frontend Form Writer

## Purpose

Create or modify a form inside a page or domain component while preserving the API and validation contract.

Typical targets are:

```text
projects/frontend/src/components/<area>/<Feature>Form.tsx
projects/frontend/src/pages/<Page>.tsx
projects/frontend/src/hooks/use<Feature>Form.ts
```

## Sources of Truth

Before editing, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/frontend-standard.md`;
3. `docs/engineering/frontend-style.md`;
4. `docs/engineering/frontend-example.md` when an example is needed;
5. the relevant `.ai/task-contract/front/<task_name>.md`;
6. the existing form library, API validation shape, UI controls, and neighboring forms.

## Scope

This skill handles form state and form UI. It may:

- define explicit form value and submission types;
- create or modify controlled or `react-hook-form` forms according to local convention;
- define complete initial values;
- map field and API validation errors;
- support create/edit initialization from asynchronous data;
- disable controls during submission;
- compose existing shadcn/ui inputs, labels, selects, dialogs, and buttons;
- add focused form tests.

Do not change backend DTOs, API client transport, unrelated hooks, route structure, or business rules unless explicitly requested.

## Rules

- Match the backend request envelope and field names exactly.
- Keep form values distinct from domain/API response types when their responsibilities differ.
- Type values, props, submit variables, errors, and callbacks explicitly.
- Use complete, stable initial values; reinitialize edit forms when async source data arrives.
- Render server validation errors without swallowing details.
- Disable submit and relevant controls while pending.
- Use existing shadcn/ui primitives and Tailwind conventions.
- Keep repeated error rendering in a reusable component when the repository has one.
- Never put auth tokens or tenant identity in editable form state when those values come from authenticated context.

## Workflow

1. Inspect the request/response contract and closest form.
2. Define initial values, field rules, submit variables, and error mapping.
3. Implement the smallest form change.
4. Verify create, edit, invalid, submitting, and server-error states.
5. Add or update focused tests.
