---

name: service-writer
description: Create or modify a Go domain service using the task specification, target module, repository contract, inherited base service behavior, and integrated backend source-of-truth context.
---

# Backend Service Writer

## Purpose

Create or modify a backend Service.

The target is typically a `service.go` inside the corresponding domain package.

Examples:

```text
internal/domain/<module>/service.go
```

or:

```text
internal/domain/<module>/<subentity>/service.go
```

Adapt the location to the actual project structure.

Services must extend the generic behavior already provided by:

```go
base.Service[Entity]
```

The concrete Service should contain only module-specific business behavior that is not already supplied by the base Service.

Do not repeat or reinterpret rules already defined by the backend sources of truth.

---

## Sources of Truth

Before creating or reviewing a service, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/golang/backend-standard.md`;
3. `docs/engineering/golang/backend-style.md`;
4. `docs/engineering/golang/backend-example.md`;
5. the specification or task contract describing the required business behavior, if needed.

---

## Scope

This skill handles Service implementation.

Typical work includes:

* creating `service.go`;
* modifying an existing Service;
* embedding `base.Service[Entity]`;
* wiring the module Repository;
* defining the Repository contract required by the Service;
* implementing module-specific business operations;
* applying business rules that depend on persistence state;
* coordinating persistence operations belonging to the same module;
* translating persistence failures using the project's established error conventions;
* returning domain entities or domain-level results.

Do not expand the task into Component, Route, DTO, Mapper, Entity, Repository implementation, or migration changes unless explicitly requested.

---

# Base Service Inheritance

Every concrete Service must embed the generic base Service.

Required structure:

```go
type Service struct {
	base.Service[Entity]

	Repository RepositoryInterface
}
```

The exact Repository field type must follow the project's established pattern.

The Service must not replace inherited generic Service behavior with manually duplicated implementations.

Before adding methods, inspect:

```text
base.Service
existing module Service
Repository contract
```

to determine what functionality already exists.

---

# Base Service Contract

Before creating or modifying a Service, inspect the actual:

```text
base.Service[Entity]
```

implementation.

Do not assume its fields, methods, constructor requirements, or Repository contract from examples.

The current repository implementation is authoritative.

Common configuration may include concepts such as:

```go
base.Service[Entity]{
	Repository: repository,
	EntityName: "entity",
}
```

but use the exact structure exposed by the current project.

---

# Workflow

## 1. Locate the Service

Identify:

```text
module
package
service.go
entity
repository
base Service
```

If `service.go` already exists, use it as the starting point.

---

## 2. Inspect the Dependencies

Before writing Service code, inspect:

1. the corresponding Entity;
2. the existing Service, if present;
3. `base.Service`;
4. the module Repository;
5. the Repository interface or contract;
6. nearby Services with similar behavior;
7. the specification describing the business operation.

Determine which behavior belongs to the concrete Service and which behavior is already inherited.

---

## 3. Start From the Base Service

A typical Service begins with:

```go
type Service struct {
	base.Service[Entity]

	Repository RepositoryInterface
}
```

If the project uses a concrete Repository field instead of an interface, preserve that established convention.

Do not create a Service that bypasses the project's base Service abstraction.

---

# Repository Dependency

The Service should use the Repository contract belonging to its own module.

Example:

```go
type RepositoryInterface interface {
	base.Repository[Entity]

	FindByDocument(
		ctx context.Context,
		document string,
	) (*Entity, error)
}
```

The Service should depend only on Repository behavior it actually needs.

Do not duplicate Repository methods inside the Service.

Do not perform direct GORM or database queries from Service methods.

---

# Production Construction

Inspect how Services are instantiated in the current project.

Preserve the established production construction pattern.

A typical structure may be:

```go
var moduleService *Service

func NewService() *Service {
	if moduleService == nil {
		repository := Repository{
			RepositoryImpl: base.RepositoryImpl[Entity]{
				Conn: database.Conn,
			},
		}

		moduleService = &Service{
			Service: base.Service[Entity]{
				Repository: &repository,
				EntityName: "entity",
			},
			Repository: &repository,
		}
	}

	return moduleService
}
```

The exact:

```text
constructor name
singleton pattern
repository initialization
base Service fields
pointer/value usage
```

must come from the current project.

Do not introduce an alternative construction pattern merely for stylistic preference.

---

# Repository Wiring

Production construction should reuse the module Repository and the project's established database dependency.

The Repository supplied to:

```go
base.Service[Entity]
```

and the Repository exposed to the concrete Service should represent the same persistence implementation unless the project explicitly establishes another pattern.

Example:

```go
repository := Repository{
	RepositoryImpl: base.RepositoryImpl[Entity]{
		Conn: database.Conn,
	},
}

service := &Service{
	Service: base.Service[Entity]{
		Repository: &repository,
		EntityName: "entity",
	},
	Repository: &repository,
}
```

Adapt field names and pointer/value semantics to the actual base abstractions.

---

# Business Methods

Add a Service method when the operation represents module-specific business behavior.

Examples include:

```text
creation rules
update rules
state transitions
uniqueness checks
domain invariants
business decisions based on persisted state
domain-specific retrieval behavior
domain-specific deletion rules
```

Example:

```go
func (s *Service) CreateEntity(
	ctx context.Context,
	entity Entity,
) (*Entity, error) {
	existing, err := s.Repository.FindByDocument(
		ctx,
		entity.Document,
	)

	if err == nil && existing != nil {
		return nil, newDomainError(...)
	}

	created, err := s.Repository.SaveContext(
		ctx,
		entity,
	)
	if err != nil {
		return nil, newDatabaseError(...)
	}

	return created, nil
}
```

The exact rule and error behavior must come from the specification and current project conventions.

---

# Reuse Inherited Service Behavior

Before adding a Service method, inspect whether equivalent behavior is already supplied by:

```go
base.Service[Entity]
```

Do not create module-specific wrappers around inherited behavior without a concrete business reason.

Avoid methods whose only purpose is to rename or forward an inherited operation.

For example, avoid introducing:

```go
func (s *Service) GetEntityByID(...) (...) {
	return s.Service.GetByID(...)
}
```

when no additional domain behavior exists.

A custom method should represent actual module behavior.

---

# Persistence Access

Service methods should access persistence through:

```go
s.Repository
```

or inherited base Service behavior.

Do not access:

```text
gorm.DB
database.Conn
gorm.G
raw SQL
```

from business methods.

Database construction belongs to production wiring, not business behavior.

---

# Context

When Repository operations expose context-aware methods, propagate the context received by the Service.

Example:

```go
func (s *Service) Process(
	ctx context.Context,
	entity Entity,
) (*Entity, error) {
	result, err := s.Repository.SomeOperation(
		ctx,
		entity.Field,
	)

	// ...
}
```

Do not replace the incoming context with:

```go
context.Background()
```

inside a business operation when the caller has already supplied a context.

---

# Persistence-Dependent Business Rules

When a business rule depends on existing persistence state, retrieve that state through the module Repository.

Example flow:

```text
Service method
    -> Repository query
    -> inspect result
    -> apply business rule
    -> Repository persistence operation
```

Example:

```go
existing, err := s.Repository.FindByDocument(
	ctx,
	entity.Document,
)

if err == nil && existing != nil {
	return nil, newDomainError(...)
}
```

Keep the decision in the Service and the query in the Repository.

---

# Save Operations

When the generic Repository already provides the required save behavior, reuse it.

Example:

```go
result, err := s.Repository.SaveContext(
	ctx,
	entity,
)
```

or the equivalent method exposed by the current Repository contract.

Do not create module-specific Repository methods solely to wrap generic persistence unless specialized persistence behavior is required.

---

# Lookup Operations

Use inherited or custom Repository methods according to the persistence requirement.

For generic lookups, reuse the base Repository contract when applicable.

For domain-specific lookup behavior, use a clearly named Repository method.

Example:

```go
entity, err := s.Repository.FindByDocument(
	ctx,
	document,
)
```

The Service should consume the result and apply the business decision required by the operation.

---

# Error Translation

Use the error mechanism established by the current project.

When persistence errors must be translated before leaving the Service, use the existing shared error helpers.

Do not introduce new Service-specific error types or error mapping patterns when the project already defines them.

Distinguish between:

```text
persistence failure
missing required entity
business-rule failure
successful absence when absence is expected
```

according to the task and existing conventions.

---

# Entity Name

When `base.Service[Entity]` requires an entity name or equivalent metadata, use the established domain terminology.

Example:

```go
EntityName: "entity",
```

For a concrete domain:

```go
EntityName: "checklist",
```

Use the naming convention established by nearby Services.

Do not invent user-facing terminology independently from the existing project.

---

# Service Interfaces

Do not create a Service interface automatically.

Create one when another layer or module needs a narrow abstraction for the Service.

Example:

```go
type EntityService interface {
	CreateEntity(
		ctx context.Context,
		entity Entity,
	) (*Entity, error)
}
```

Expose only the operations actually required by the consumer.

Do not mirror every method on the concrete Service unless the complete contract is genuinely required.

---

# Same-Domain Operations

A Service may coordinate multiple Repository operations belonging to its own domain.

Example:

```text
lookup current entity
-> evaluate business state
-> update entity
-> persist entity
```

Keep the sequence focused on business behavior belonging to that Service.

Do not move a persistence query into the Service merely because multiple Repository calls are involved.

---

# Creating a New Service

A basic Service may start with:

```go
package module

import (
	"project/internal/infra/base"
	"project/internal/infra/database"
)

type Service struct {
	base.Service[Entity]

	Repository RepositoryInterface
}

var moduleService *Service

func NewService() *Service {
	if moduleService == nil {
		repository := Repository{
			RepositoryImpl: base.RepositoryImpl[Entity]{
				Conn: database.Conn,
			},
		}

		moduleService = &Service{
			Service: base.Service[Entity]{
				Repository: &repository,
				EntityName: "entity",
			},
			Repository: &repository,
		}
	}

	return moduleService
}
```

This is only a structural example.

Adapt:

```text
imports
constructor name
Repository type
pointer/value semantics
EntityName
base Service fields
database dependency
```

to the current project.

Then add only the business methods required by the module.

---

# Modifying an Existing Service

When `service.go` already exists:

1. preserve the embedded `base.Service[Entity]`;
2. inspect inherited behavior before adding new methods;
3. preserve production dependency wiring;
4. preserve existing Repository dependency style;
5. preserve unrelated business methods;
6. add only behavior required by the task;
7. avoid changing method signatures unnecessarily;
8. avoid unrelated refactoring.

Do not replace the existing Service construction pattern with a new dependency injection style.

---

# Testing-Oriented Construction

Production singleton construction should not prevent direct Service construction in tests.

The Service structure should allow dependencies to be replaced directly when required.

Example:

```go
service := &Service{
	Service: base.Service[Entity]{
		Repository: fakeRepository,
		EntityName: "entity",
	},
	Repository: fakeRepository,
}
```

Do not add test-specific constructors or mutable global hooks unless the project already uses them.

---

# Missing Information

When information required to implement a business operation is unavailable, do not invent it.

Examples:

* expected business behavior is unclear;
* required state transition is unspecified;
* expected behavior for an existing record is unknown;
* Repository capability required by the rule does not exist;
* error behavior cannot be determined;
* specification conflicts with existing domain behavior.

State which business information is missing or conflicting.

---

## Review Evidence (For Reviewer Agents Only)

When reporting a Service issue, identify:

```text
requirement
-> service file
-> affected method/construction/dependency
-> observed problem
-> business consequence
-> expected correction
```

Example:

```text
Requirement:

A document must not be duplicated.

Service:

internal/domain/customer/service.go

Method:

CreateCustomer

Observed:

The Service persists the entity without checking the existing document through the Repository.

Impact:

The business rule required by the specification is not enforced before persistence.

Expected:

Use the appropriate Repository lookup and apply the required business behavior before saving.
```

Do not report a finding merely because another valid Go implementation could have been used.

Findings must be based on:

* the specification;
* backend standards;
* existing Service conventions;
* actual Repository contracts;
* concrete business consequences.

---

## Service Inheritance Review (For Reviewer Agents Only)

Confirm that the concrete Service embeds:

```go
base.Service[Entity]
```

Check that inherited behavior was not unnecessarily reimplemented.

Confirm that production construction correctly supplies the module Repository to the base Service.

Inspect:

```text
base Service initialization
Repository dependency
EntityName or equivalent metadata
constructor pattern
database wiring
```

against the current project's established structure.

Do not report alternative constructor styles as defects when the implementation follows the repository convention.

---

## Business Rule Review (For Reviewer Agents Only)

For every new or modified Service method, map:

```text
business requirement
-> persistence state required
-> Repository operation
-> business decision
-> persistence action
-> returned result/error
```

Confirm that the method implements the complete business behavior required by the task.

Pay particular attention to:

```text
missing business conditions
business decisions performed after persistence when they must occur before it
incorrect state transitions
missing Repository lookups
incorrect handling of Repository results
business behavior accidentally moved into persistence code
unnecessary duplication of inherited Service behavior
```

Findings must describe the concrete business consequence.

---

## Repository Usage Review (For Reviewer Agents Only)

Confirm that Service persistence access occurs through the module Repository or inherited base Service behavior.

Check for:

```text
direct GORM usage
direct database connection access
raw SQL
duplicated Repository queries
Repository methods belonging to unrelated modules
```

When a custom persistence operation is required, determine whether it belongs in the Repository instead of implementing the query inside the Service.

---

## Error Review (For Reviewer Agents Only)

Review each error path against the specification and existing project conventions.

Distinguish:

```text
business-rule rejection
required entity not found
persistence failure
successful operation
```

Confirm that persistence errors are not accidentally exposed when the established Service convention requires translation.

Do not report wording preferences as defects unless the message or error type violates an explicit project convention or requirement.

---

## Verification (For Reviewer Agents Only)

When repository commands are available, use the backend verification commands defined by the project instructions.

Typical verification may include:

```bash
go test ./...
```

Run relevant Service package tests when available.

Use failures as evidence only when they relate to the Service change.

Successful compilation does not prove that the required business behavior has been implemented correctly.

Source inspection and business scenarios remain necessary.

---

# Output

When creating a Service, produce the complete resulting:

```text
service.go
```

When modifying an existing Service, return the complete resulting file unless the caller explicitly requests a diff or isolated change.

Do not include unrelated backend files.

---

# Execution Summary

For writer agents:

```text
Task specification
        +
Sources of truth
        +
Entity
        +
base.Service
        +
Repository contract
        +
Existing Service patterns
        ↓
base.Service[Entity]
        +
Repository dependency
        +
Module business behavior
        ↓
service.go
```

For reviewer agents:

```text
Task specification
        +
Sources of truth
        +
base Service behavior
        +
Repository contract
        +
Service implementation
        ↓
Review Evidence
        +
Service Inheritance Review
        +
Business Rule Review
        +
Repository Usage Review
        +
Error Review
        +
Verification
```

Always reuse inherited base Service behavior before introducing module-specific Service code.

---

# Domain Error Propagation

Domain packages do not define sentinel errors or `errors.go` files.

Repositories already return typed `api_errors` values (e.g. `EntityAlreadyExistsError`). A Service must propagate them untouched — never wrap a typed error in `NewDatabaseError`:

```go
if err := s.Repository.Save(ctx, plan); err != nil {
    var alreadyExistsErr *api_errors.EntityAlreadyExistsError
    if errors.As(err, &alreadyExistsErr) {
        return nil, alreadyExistsErr
    }
    return nil, api_errors.NewDatabaseError(err)
}
```

If the project already has a Service-level helper for this (e.g. `treatXSaveError`), reuse it.

# Leaf Services

A submodule Service is a leaf: it receives data, never dependencies on the parent module.

When an operation needs a rule owned by the parent Component (calculations, windows, guards), the parent computes the value and the Service signature takes the plain result — a baseline struct or individual fields. Do not inject a parent component, evaluator, or interface field into the Service.
