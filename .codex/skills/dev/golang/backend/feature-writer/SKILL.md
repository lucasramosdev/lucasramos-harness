---
name: feature-writer
description: Plan and implement a Go backend feature by identifying the affected architectural layers and coordinating the specialized backend writer skills required by the task.
---

# Backend Feature Writer

## Purpose

Implement a backend feature that may span multiple architectural layers.

This skill is an orchestration skill.

It does not replace the specialized skills responsible for individual backend artifacts.

Its primary responsibilities are:

- understand the feature specification;
- inspect the existing module;
- determine which layers are actually affected;
- identify the dependencies between required changes;
- apply the appropriate specialized writer skill to each affected artifact;
- keep the implementation coherent across layers;
- avoid changes to layers that are not required by the feature.

A feature may involve any combination of:

```text
migration
entity
DTO
mapper
repository
service
component
controller
tests
```

Do not assume every feature requires every layer.

---

## Sources of Truth

Before creating or reviewing a feature, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/golang/backend-standard.md`;
3. `docs/engineering/golang/backend-style.md`;
4. `docs/engineering/golang/backend-example.md`;
5. the specification or task contract describing the required feature behavior.

---

## Specialized Skills

Use the specialized backend skill that owns each artifact.

```text
database schema / migration
-> database-migration

domain entity
-> entity-writer

request / response contract
-> dto-writer

DTO / domain representation conversion
-> mapper-writer

persistence behavior
-> repository-writer

domain / business behavior
-> service-writer

application orchestration
-> component-writer

HTTP boundary
-> controller-writer

behavioral tests
-> test-writer
```

The Feature Writer coordinates these skills.

It must not duplicate their detailed implementation instructions.

---

# Workflow

## 1. Understand the Feature

Read the complete task or specification before modifying code.

Extract:

```text
required behavior
inputs
outputs
business rules
persistence requirements
HTTP behavior
relationships
error behavior
test scenarios
```

Separate explicit requirements from assumptions.

Do not begin implementation from a single requested file when the behavior clearly spans multiple layers.

---

## 2. Locate the Target Module

Identify:

```text
module
submodule, if applicable
existing entity
existing DTOs
existing mapper
existing repository
existing service
existing component
existing controller/routes
existing migrations
existing tests
```

Inspect the current implementation before deciding which files must change.

Prefer extending the existing module over creating parallel structures.

---

## 3. Build the Feature Impact Map

Determine which architectural artifacts are affected.

Use a map such as:

```text
Migration   : required / not required
Entity      : required / not required
DTO         : required / not required
Mapper      : required / not required
Repository  : required / not required
Service     : required / not required
Component   : required / not required
Controller  : required / not required
Tests       : required / not required
```

For every artifact marked as required, identify the concrete reason.

Example:

```text
Migration
-> new persisted column is required

Entity
-> persisted field must be represented

DTO
-> API accepts the new field

Mapper
-> request field must be mapped to the domain

Repository
-> new custom lookup is required

Service
-> new business rule depends on persisted state

Component
-> workflow coordinates another Service

Controller
-> new endpoint exposes the operation

Tests
-> specification introduces new observable behavior
```

Do not create or modify a layer merely because it exists in the architecture.

---

## 4. Identify Existing Capabilities

Before adding new code, determine whether the feature can reuse:

```text
existing DTO
existing Mapper method
base Repository behavior
existing custom Repository method
base Service behavior
existing Service method
existing Component orchestration
existing Controller helper
existing test fake
existing shared response or pagination type
```

Prefer reuse when the existing behavior represents the same contract.

Do not create aliases or wrappers that add no behavior.

---

## 5. Determine Change Dependencies

Identify dependencies between changes before implementation.

Typical dependencies may include:

```text
database schema
-> Entity representation

DTO
-> Mapper

Entity + Repository contract
-> Service

Services + Mapper
-> Component

DTO + Component API
-> Controller

implemented behavior
-> Tests
```

This dependency map determines a safe implementation order.

---

# Default Implementation Order

When a feature spans the full backend stack, a useful default order is:

```text
1. persistence/schema requirements
2. Entity
3. DTOs
4. Mapper
5. Repository
6. Service
7. Component
8. Controller
9. Tests
```

This is a coordination order, not a requirement to create all artifacts.

Existing code may allow steps to be skipped.

The task specification and actual module dependencies take precedence over this default sequence.

---

# Persistence Changes

When the feature changes persistent structure or database invariants:

```text
Feature Writer
-> database-migration
```

After the persistence contract is understood, coordinate any corresponding Entity or Repository changes.

Do not create a migration for a feature that does not change persistence structure or required persisted data.

---

# Entity Changes

When persisted or domain state changes:

```text
Feature Writer
-> entity-writer
```

Entity changes should reflect the persistence/domain requirements of the feature.

Do not modify the Entity solely because an API response changed.

---

# DTO Changes

When the API request or response contract changes:

```text
Feature Writer
-> dto-writer
```

Determine whether the feature requires:

```text
new request DTO
new response DTO
updated existing DTO
new query/filter DTO
no DTO change
```

Do not copy Entity fields into DTOs automatically.

---

# Mapper Changes

When representation boundaries change:

```text
Feature Writer
-> mapper-writer
```

Typical causes include:

```text
new request field
new response field
new DTO
new nested response
new identifier representation
new collection mapping
```

If the feature changes no representation boundary, a Mapper change may not be required.

---

# Repository Changes

When the feature requires persistence behavior not already available:

```text
Feature Writer
-> repository-writer
```

First determine whether the existing base Repository or current module Repository already supports the operation.

Only add custom persistence behavior when required by the feature.

---

# Service Changes

When the feature introduces or changes domain/business behavior:

```text
Feature Writer
-> service-writer
```

Examples include:

```text
business rules
state transitions
domain invariants
business decisions based on repository state
module-specific create/update behavior
```

Do not move application orchestration into the Service merely to keep the feature in fewer files.

---

# Component Changes

When the feature requires application orchestration:

```text
Feature Writer
-> component-writer
```

Examples include:

```text
DTO/domain mapping orchestration
multiple Service calls
cross-domain Service coordination
validators
multi-step workflows
response assembly
```

A simple domain rule that belongs entirely to one Service does not automatically require new Component behavior beyond the existing call path.

---

# Controller Changes

When the feature changes or introduces HTTP behavior:

```text
Feature Writer
-> controller-writer
```

Examples include:

```text
new endpoint
new HTTP method
new route parameter
new query parameter
new request body
new response status
new Component invocation
```

Internal backend behavior that is not exposed through HTTP does not require a Controller change.

---

# Test Changes

Every new observable behavior introduced by the feature should be represented by the appropriate BDD specifications.

Use:

```text
Feature Writer
-> test-writer
```

The test strategy depends on the affected layer.

Typical mapping:

```text
Repository behavior
-> Repository specs

business rule
-> Service specs

application orchestration
-> Component specs

HTTP contract
-> Controller / Route specs

significant mapping behavior
-> Mapper specs
```

Use the project's Ginkgo v2 + Gomega conventions.

Do not duplicate the same behavioral scenario across layers unless each layer exposes a distinct contract that needs coverage.

---

# Feature Change Matrix

Before implementation, it is useful to produce an internal change matrix.

Example:

```text
Requirement:
Create maintenance category.

Migration:
Yes — new table.

Entity:
Yes — new persisted domain model.

DTO:
Yes — create request and response contracts.

Mapper:
Yes — request -> entity and entity -> response.

Repository:
No custom query initially — inherited persistence behavior is sufficient.

Service:
Yes — creation business behavior.

Component:
Yes — map request, invoke Service, map response.

Controller:
Yes — expose POST endpoint.

Tests:
Yes — Service, Component, Controller, and persistence behavior required by the task.
```

The matrix should be derived from the actual task.

Do not force this exact shape into user-facing output unless useful.

---

# Existing Feature Modification

When changing an existing feature:

1. trace the existing execution flow;
2. identify the layer that currently owns the behavior;
3. identify downstream or upstream contracts affected by the change;
4. modify the smallest set of artifacts required;
5. preserve unrelated behavior;
6. update existing tests that represent changed behavior;
7. add new specifications only for newly introduced behavior.

Do not regenerate the entire module because one behavior changed.

---

# New Feature Creation

For a new backend feature, inspect similar existing modules before creating structure.

Determine whether the project already has conventions for:

```text
module layout
subentities
constructor names
DTO naming
Mapper naming
Repository interfaces
Service interfaces
Component dependencies
route registration
test suite organization
```

Use the closest valid module as the implementation reference.

Do not mechanically copy an unrelated module.

---

# Cross-Domain Features

A feature may involve more than one domain.

Before modifying multiple modules, identify ownership of each behavior.

Example:

```text
Feature:
Create child resource linked to parent.

Parent domain:
existing lookup/access behavior

Child domain:
creation behavior

Component:
coordinates Parent Service + Child Service

Repository:
each domain keeps its own persistence behavior
```

Use specialized skills inside each domain boundary.

Do not centralize unrelated domain behavior into one Repository or Service merely because the feature spans them.

Ownership also fixes dependency direction: orchestration of a domain's concept lives in that domain, and the calling Component passes dependencies concretely — ready data, existing interfaces, or a struct of bound methods when the callee cannot import the caller — without inventing interfaces to cross an import boundary.

---

# API-Only Changes

Some features change only transport representation.

Example:

```text
response adds an already-available field
```

Possible impact:

```text
DTO       -> yes
Mapper    -> yes
Controller -> maybe no
Service   -> no
Repository -> no
Migration  -> no
```

Do not propagate an API-only change into persistence or business layers unnecessarily.

---

# Persistence-Only Changes

Some tasks affect persistence without changing public behavior.

Possible impact:

```text
Migration  -> yes
Entity     -> maybe
Repository -> maybe
Service    -> no
Component  -> no
Controller -> no
DTO        -> no
```

Determine impact from the actual contract rather than assuming a full-stack change.

---

# Business-Only Changes

A business rule may require only:

```text
Service
+
Service tests
```

or:

```text
Repository custom query
+
Service
+
tests
```

Do not modify DTOs, Controllers, or migrations when their contracts remain unchanged.

---

# HTTP-Only Changes

An HTTP contract adjustment may involve:

```text
DTO
Mapper
Controller
Controller tests
```

without requiring changes to persistence or business behavior.

Trace the actual data flow before modifying deeper layers.

---

# Avoid Parallel Implementations

Do not create a new method in another layer simply to avoid changing the correct owner.

Avoid patterns such as:

```text
Controller implements mapping because Mapper method is missing

Component queries persistence because Repository method is missing

Service manually maps DTO because Mapper change was skipped

Repository implements a business decision because Service change was skipped
```

Use the specialized skill that owns the missing behavior.

---

# No Unrelated Refactoring

A feature implementation should not become a general cleanup task.

Avoid:

```text
renaming unrelated types
moving unrelated files
rewriting constructors
changing established interfaces without need
reformatting unrelated modules
replacing existing abstractions
```

Keep deviations from the requested feature narrow.

---

# Missing Information

Stop feature implementation when a required contract cannot be determined safely.

Examples:

- expected business behavior is ambiguous;
- API request or response contract is undefined;
- persistence semantics are unclear;
- relationship ownership cannot be determined;
- expected error behavior is missing;
- feature requirements conflict with the current architecture;
- a required cross-domain operation has no clear owner.

Identify the missing or conflicting requirement rather than inventing behavior.

---

## Review Evidence (For Reviewer Agents Only)

When reporting a feature-level issue, identify:

```text
requirement
-> affected layer
-> affected file / method
-> observed implementation
-> consequence
-> expected correction
```

Example:

```text
Requirement:

Creating a child resource requires resolving the parent before child creation.

Affected layer:

Component

Observed:

The Controller calls the child Service directly and no parent Service
operation occurs.

Impact:

The required application workflow is bypassed.

Expected:

Route through the Component and coordinate the parent and child
Services according to the feature contract.
```

Do not report a finding merely because the feature could have been implemented using another valid code organization.

Findings must be tied to:

- the specification;
- backend standards;
- actual layer ownership;
- existing module contracts;
- concrete behavioral, persistence, or API consequences.

---

## Feature Coverage Review (For Reviewer Agents Only)

Map every feature requirement to the implementation artifact that owns it.

Example:

```text
Requirement A
-> Migration
-> Entity

Requirement B
-> Repository
-> Service

Requirement C
-> DTO
-> Mapper
-> Component
-> Controller
```

Confirm that every required behavior has an implementation owner.

Look for:

```text
requirement with no implementation
implementation with no requirement
required layer skipped
unnecessary layer modified
duplicate implementation across layers
```

Do not require every architectural layer to change.

---

## Layer Ownership Review (For Reviewer Agents Only)

For each changed file, determine why that layer needed modification.

Use:

```text
changed artifact
-> requirement
-> layer responsibility
```

Report a finding when behavior is implemented in a layer that does not own it and the placement has a concrete architectural or behavioral consequence.

Do not report differences that are merely stylistic.

---

## Change Scope Review (For Reviewer Agents Only)

Compare the feature implementation with the requested behavior.

Identify:

```text
unrelated refactors
unnecessary new abstractions
duplicate methods
unnecessary DTO changes
unnecessary persistence changes
unnecessary constructor changes
unrelated module modifications
```

A finding should explain why the extra change creates risk, inconsistency, or unsupported behavior.

---

## Cross-Layer Contract Review (For Reviewer Agents Only)

Inspect the contracts between affected layers.

Typical chains include:

```text
Controller
-> Component API

Component
-> Mapper
-> Service API

Service
-> Repository contract

Repository
-> Entity / persistence schema

Mapper
-> DTO + Entity
```

Confirm that signatures, types, representations, and expected results remain compatible across the complete feature path.

Pay particular attention to a layer being changed without its dependent representation or contract being updated.

---

## End-to-End Flow Review (For Reviewer Agents Only)

Trace the complete execution path introduced or modified by the feature.

Example:

```text
HTTP request
-> Controller
-> Component
-> Mapper
-> Service
-> Repository
-> persistence

persistence result
-> Service
-> Component
-> Mapper
-> Controller
-> HTTP response
```

Only include layers actually used by the feature.

Confirm that:

- input reaches the correct owner;
- required operations execute in the correct order;
- errors interrupt the flow where expected;
- output is transformed into the required representation;
- no layer is bypassed when its behavior is required.

---

## Test Coverage Review (For Reviewer Agents Only)

Map each new observable behavior to a Ginkgo/Gomega specification.

Example:

```text
Persistence behavior
-> Repository specification

Business rule
-> Service specification

Cross-service workflow
-> Component specification

HTTP contract
-> Controller specification
```

Check that tests exercise behavior at the owning layer.

Do not require the same scenario to be repeated through every layer.

Use the `test-writer` conventions for detailed test review.

---

## Verification (For Reviewer Agents Only)

Run the verification commands established by the repository.

Typical commands may include:

```bash
go test ./...
```

or, when the project uses the Ginkgo CLI:

```bash
ginkgo ./...
```

Also run build, lint, migration, or project-specific checks when required by the repository instructions.

Verification should cover all packages affected by the feature.

A passing test suite does not prove that every specification requirement has been implemented.

Review the feature coverage map alongside command results.

---

# Output

When implementing a feature, modify or create only the files required by the feature.

Possible outputs may include:

```text
migration files
entity.go
DTO files
mapper.go
repository.go
service.go
component.go
controller / route files
*_test.go
*_suite_test.go
```

Do not generate empty or placeholder artifacts for unaffected layers.

When presenting the result, summarize:

```text
implemented behavior
affected layers
created/modified files
important dependencies or unresolved requirements
verification performed
```

Keep the summary focused on the feature rather than repeating every implementation detail.

---

# Execution Summary

For writer agents:

```text
Feature specification
        +
Sources of truth
        +
Existing module
        ↓
Feature impact map
        ↓
Affected layers only
        ↓
Specialized writer skills
        ↓
Cross-layer integration
        ↓
BDD specifications
        ↓
Complete feature
```

A full-stack feature may flow through:

```text
database-migration
        ↓
entity-writer
        ↓
dto-writer
        ↓
mapper-writer
        ↓
repository-writer
        ↓
service-writer
        ↓
component-writer
        ↓
controller-writer
        ↓
test-writer
```

but only include the skills required by the actual feature.

For reviewer agents:

```text
Feature specification
        +
Sources of truth
        +
Changed files
        ↓
Feature Coverage Review
        +
Layer Ownership Review
        +
Change Scope Review
        +
Cross-Layer Contract Review
        +
End-to-End Flow Review
        +
Test Coverage Review
        +
Verification
```

Coordinate the feature across the architecture without taking ownership away from the specialized layer skills.
