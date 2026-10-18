---

name: component-writer
description: Create or modify a Go application component using the task specification, target module, service contracts, mapper, dependencies, and integrated backend source-of-truth context.
---

# Backend Component Writer

## Purpose

Create or modify a backend Component.

The target is typically a `component.go` inside the corresponding domain package.

Examples:

```text
internal/domain/<module>/component.go
```

or:

```text
internal/domain/<module>/<subentity>/component.go
```

Adapt the location to the actual project structure.

A Component coordinates application behavior using the Services, Mapper and other application-level dependencies required by the operation.

Do not repeat or reinterpret rules already defined by the backend sources of truth.

---

## Sources of Truth

Before creating or reviewing a component, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/golang/backend-standard.md`;
3. `docs/engineering/golang/backend-style.md`;
4. `docs/engineering/golang/backend-example.md`;
5. the specification or task contract describing the required orchestration behavior, if needed.

---

## Scope

This skill handles Component implementation.

Typical work includes:

* creating `component.go`;
* modifying an existing Component;
* defining the dependencies required by the Component;
* wiring the local Service;
* wiring Services from other modules when required;
* wiring Validators or application helpers;
* wiring the Mapper;
* defining narrow Service interfaces when appropriate;
* orchestrating calls between Services;
* coordinating cross-domain operations;
* invoking Mapper transformations;
* assembling the final result returned to the caller.

Do not expand the task into Service, Repository, Route, DTO, Entity, Mapper implementation, or migration changes unless explicitly requested.

---

# Workflow

## 1. Locate the Component

Identify:

```text
module
package
component.go
local Service
Mapper
external Services
validators/helpers
```

If `component.go` already exists, use it as the starting point.

---

## 2. Inspect the Required Dependencies

Before writing the Component, inspect:

1. the existing Component, if present;
2. the local Service;
3. the Mapper;
4. input and output DTOs used by the operation;
5. external Services required by the workflow;
6. Validators or helpers already used by the module;
7. nearby Components implementing similar orchestration;
8. the task specification.

Determine the smallest set of dependencies required by the Component.

Do not add dependencies for speculative future use.

---

# Component Structure

A Component should explicitly declare the dependencies required by its operations.

Example:

```go
type Component struct {
	Service Service
	Mapper  Mapper
}
```

A Component with multiple dependencies may look like:

```go
type Component struct {
	Service           ChecklistService
	TruckService      TruckService
	ObligationService ObligationService
	Validator         FileValidator
	Mapper            Mapper
}
```

Use the actual dependency types and names from the current project.

Do not introduce a generic dependency container.

---

# Local Service

The Component should expose the local module Service through a clearly named field.

Typical form:

```go
type Component struct {
	Service Service
	Mapper  Mapper
}
```

When the project uses an interface instead:

```go
type Component struct {
	Service EntityService
	Mapper  Mapper
}
```

preserve that convention.

Do not create an additional abstraction when the existing module already defines the appropriate dependency style.

---

# External Services

When the operation requires behavior b
eyond this Component's boundary, the Component imports the owning domain's Service (or Component) and orchestrates the call — it does not reimplement the behavior locally.

Cross-domain orchestration belongs to the domain that owns the concept. When an operation is primarily about another domain's concept, the logic lives in the owning domain — e.g. maintenance-plan alert evaluation lives in `alerts/maintenance_alerts` — and this module's Component only applies its own validations, fetches and enriches its own entities, then delegates.

Pass dependencies concretely: ready data (structs of values), existing interfaces (`transaction.Runner`, domain `ServiceInterface`), or a struct of bound methods when the callee cannot import this module without creating a cycle. Do not invent new interfaces to work around an import boundary.

# Component File Layout

A module has exactly one `component.go`. Orchestration methods, narrow contracts consumed by other domains, and Component helpers all live there — never in `component_<feature>.go` sidecar files.

Adapters for external machinery (scheduler jobs, pub/sub subscribers) live in the domain package that owns the behavior they adapt, not in this module.
