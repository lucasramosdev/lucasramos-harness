---
name: migrate-vite-clean
description: Migrate a specified slice of dirty Vite code into a clean Vite React TypeScript project. Use when Codex is given a dirty Vite source folder, a requested migration scope, a good target Vite project folder, and a backend to inspect for API contracts, enums, and data types. The skill must migrate only what was requested, use vite-realworld-rules for clean frontend structure, and follow backend-defined data shapes without inventing normalization.
---

# Migrate Vite Clean

## Overview

Use this skill to migrate only a requested feature, page, route, workflow, or module from a dirty Vite codebase into a cleaner Vite React TypeScript project. Treat the dirty source as behavioral evidence, the target project as the architectural and styling destination, and the backend as the authority for API contracts, enums, and data types.

This skill is intentionally conservative. Do not perform broad cleanup, opportunistic redesign, dependency upgrades, naming rewrites, data normalization, or adjacent migrations unless the user explicitly asks for them.

## Required Inputs

Before editing code, identify these inputs from the user's request or local context:

- Dirty source folder: the Vite project containing the code to migrate from.
- Migration scope: the exact feature, route, page, component, workflow, or behavior requested.
- Target clean folder: the Vite project that should receive the migrated code.
- Backend folder: the backend project that defines endpoints, DTOs, domain types, enums, validation, and migrations.
- Validation command expectations: infer from package scripts when not stated.

If any required input cannot be inferred safely, ask one concise question before editing.

## Hard Rules

- Migrate only the requested scope. Do not migrate nearby pages, shared systems, unused helpers, unrelated routes, or "obvious" improvements outside the order.
- Use `$vite-realworld-rules` as the frontend quality standard. Load `.codex/skills/vite-realworld-rules/SKILL.md` when available and follow its TypeScript, route-first, hooks, mutation, auth, and form rules.
- Generate TypeScript only. Use `.tsx` for React components/pages and `.ts` for hooks, API clients, models, utilities, mocks, and type files.
- Use the backend as the data contract authority. Match backend enum literals, field names, DTO shapes, validation constraints, IDs, dates, nullable fields, and request/response envelopes.
- Do not "normalize" backend data shapes into new frontend concepts unless the backend already exposes that shape or the user explicitly asks for it.
- Preserve behavior from the dirty source only when it is part of the requested migration scope.
- When the user says to take only visual design from the dirty source, reproduce the requested screen's visual structure with high fidelity: layout, spacing, hierarchy, labels, visual states, logo/brand treatment, card structure, footer text, and responsive behavior. Do not import dirty behavior, state management, dependencies, or unrelated navigation unless explicitly requested.
- Prefer the target project's existing libraries, routing style, API client conventions, component system, styling system, aliases, and folder layout.
- Do not copy dirty architecture into the clean project when the same behavior can be expressed with the target project's patterns.
- Do not introduce new dependencies unless the requested scope cannot be implemented reasonably with existing target dependencies.
- Do not modify backend code unless the user explicitly requested backend changes.
- Do not delete or rewrite target project code outside the requested migration area.

## Workflow

### 1. Lock the Scope

Write down the migration boundary before editing:

- Requested feature or route.
- Dirty source files that appear relevant.
- Target destination files likely to change.
- Backend contracts that must be checked.
- Explicit exclusions: adjacent modules, unrelated cleanup, styling rewrites, and behavior not requested.

If the boundary is ambiguous, inspect first. Ask only when implementation would risk migrating too much or the wrong feature.

### 2. Inspect the Dirty Source

Read only the dirty files needed for the requested scope:

- Route definitions and navigation entry points.
- The requested page or workflow components.
- Hooks, API calls, forms, state stores, utility functions, and constants directly used by that scope.
- User-visible behavior: loading states, empty states, validation, permissions, filters, pagination, actions, and navigation.
- Visual-only requests: layout, spacing, typography scale, card/header/footer structure, brand assets, labels, placeholders, loading affordances, and responsive behavior.

Classify what to preserve as behavior, not necessarily as code structure.

### 3. Inspect the Target Project

Read target files that define the clean destination:

- Package scripts and dependencies.
- Router setup and route guard patterns.
- Existing page, component, hook, API client, type, form, and styling conventions.
- Shared UI primitives and layout components.
- Existing validation, toast, error handling, and auth helpers.

Use these conventions as the destination shape.

### 4. Inspect the Backend Contract

For every migrated API interaction or data type, inspect the backend before defining frontend types:

- HTTP handlers/routes for endpoints, methods, path params, query params, and status behavior.
- DTOs for request and response payloads.
- Domain types and enums for exact values.
- Validators for required fields, constraints, and error shapes.
- Database migrations only when they clarify enum values, nullable fields, identifiers, relationships, or date types.

Frontend enums and union types must follow backend values exactly. Do not rename enum members, collapse values, convert numeric/string enum types, or change nullable behavior for "cleanliness."

### 5. Design the Migration

Create a short implementation plan before editing:

- Dirty behavior to preserve.
- Dirty visual design to reproduce, when visual migration was requested.
- Backend contracts to mirror.
- Target files to add or edit.
- Types to create or reuse.
- Page, component, hook, API, form, and route boundaries needed under `$vite-realworld-rules`.
- Validation commands to run.

Keep the plan proportional. For small migrations, a concise internal checklist is enough.

### 6. Implement in the Target Project

Apply the migration with these priorities:

- Express the migrated behavior using target project patterns.
- Split route pages, components, hooks, API calls, and types according to `$vite-realworld-rules`.
- Do not leave a migrated feature in one large page or app file when it contains separable concerns. At minimum, use a route/page component for orchestration, presentational components for UI sections, hooks for form or mutation state, and API/type files for backend calls.
- Keep component props, API envelopes, form values, filters, and mutation contexts explicitly typed.
- Preserve backend field names and payload shapes at API boundaries.
- Keep mapping logic minimal and transparent when UI names differ from backend fields.
- Reuse existing target utilities before creating new ones.
- Add route entries, navigation links, permissions, and exports only when required by the requested migration.
- Leave dirty source files unchanged unless the user requested source cleanup.

### 7. Validate

Run target project validation commands relevant to the migration:

- Lint when configured.
- Typecheck when configured.
- Build when feasible.
- Focused tests when configured and related to the migrated scope.

If validation cannot run because dependencies are missing or scripts do not exist, state that clearly and report the next best check performed.

### 8. Report

Final response must include:

- What was migrated.
- What target files changed.
- Backend contracts used for enums/data types.
- How the migrated feature was separated into page, components, hooks, API/types, and styles.
- Validation commands and results.
- Explicit note of anything intentionally not migrated because it was outside scope.

## Scope Discipline Checklist

Before editing and before final response, verify:

- The user explicitly requested every migrated route, page, component, API call, type, and behavior.
- No unrelated cleanup or "while here" refactor was included.
- No backend enum or data type was invented from frontend assumptions.
- No source-only workaround was carried into the target when the target has a cleaner existing pattern.
- No broad normalization layer was introduced.
- The dirty source was used as behavior evidence, not as the architecture to reproduce.
- Visual-only migrations preserve the requested screen's visual design without importing unrelated dirty behavior.
- The migrated feature is split across appropriate page, component, hook, and API/type boundaries instead of being concentrated in one file.
