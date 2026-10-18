---

name: repository-writer
description: Create or modify a Go repository using the task specification, persistence schema, target module, inherited base repository behavior, and integrated backend source-of-truth context.
---

# Backend Repository Writer

## Purpose

Create or modify a backend Repository.

The target is typically a `repository.go` inside the corresponding domain package.

Examples:

```text
internal/domain/<module>/repository.go
```

or:

```text
internal/domain/<module>/<subentity>/repository.go
```

Adapt the location to the actual project structure.

Repositories must extend the generic persistence behavior already provided by:

```go
base.RepositoryImpl[Entity]
```

Custom Repository code must be limited to persistence operations that are not already provided by the base Repository.

Do not repeat or reinterpret rules already defined by the backend sources of truth.

---

## Sources of Truth

Before creating or reviewing a repository, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/golang/backend-standard.md`;
3. `docs/engineering/golang/backend-style.md`;
4. `docs/engineering/golang/backend-example.md`;
5. the specification or task contract describing the required persistence behavior, if needed.

---

## Scope

This skill handles Repository implementation.

Typical work includes:

* creating `repository.go`;
* modifying an existing Repository;
* embedding `base.RepositoryImpl[Entity]`;
* inheriting generic Repository behavior;
* defining module-specific persistence methods;
* defining repository interfaces when required by consumers;
* implementing custom GORM queries;
* applying persistence-specific filters;
* applying ordering when required;
* applying specialized preloads when base behavior is insufficient;
* implementing persistence operations not already covered by the base Repository.

Do not expand the task into Service, Component, Route, DTO, Entity, Mapper, or migration changes unless explicitly requested.

---

# Base Repository Inheritance

Every concrete Repository must embed the generic base implementation.

Required structure:

```go
type Repository struct {
	base.RepositoryImpl[Entity]
}
```

Example:

```go
type Repository struct {
	base.RepositoryImpl[Checklist]
}
```

This inheritance is mandatory.

Do not create a standalone Repository that manually reimplements generic persistence behavior already supplied by `base.RepositoryImpl`.

The embedded base Repository may already provide generic operations such as:

```text
Save
SaveContext

FindWithPagination
FindWithPaginationContext

FindById
FindByIdContext

FindOne
FindOneContext

Delete
DeleteContext
```

Inspect the actual base implementation before adding equivalent methods.

---

# Base Repository Contract

Before implementing any custom Repository method, inspect:

```text
base.Repository
base.RepositoryImpl
```

Do not assume method signatures from examples or previous projects.

The concrete base implementation in the current repository is authoritative.

Do not recreate equivalent methods in the concrete Repository.

---

# Workflow

## 1. Locate the Repository

Identify:

```text
module
package
repository.go
entity
database table
```

If `repository.go` already exists, use it as the starting point.

---

## 2. Inspect the Entity and Persistence Model

Before implementing the Repository, inspect:

1. the corresponding Entity;
2. the existing Repository, if present;
3. `base.Repository`;
4. `base.RepositoryImpl`;
5. the migrations defining the corresponding persistence model;
6. nearby repositories with similar custom queries;
7. the Service or consumer that requires the persistence operation.

Determine what behavior is already inherited and what actually needs a custom Repository method.

---

## 3. Start From the Base Repository

A new Repository should begin with:

```go
package module

import "project/internal/infra/base"

type Repository struct {
	base.RepositoryImpl[Entity]
}
```

Adapt the import path to the actual Go module.

Do not start by manually implementing CRUD operations.

The base Repository is the default persistence implementation.

---

## 4. Reuse Generic Operations

Before adding a method, determine whether the operation is already covered by the inherited base Repository.

Examples may include:

```text
Save
FindWithPagination
FindById
FindOne
Delete
```

and their context-aware variants.

Do not create:

```go
func (r *Repository) GetByID(...)
```

when the operation is equivalent to an existing inherited method.

Likewise, do not create wrappers around generic save, delete, lookup, or pagination behavior without a concrete persistence reason.

---

## 5. Use Context Variants When Needed

When the base Repository exposes context-aware variants, reuse them.

Example:

```go
repository.SaveContext(ctx, entity)
```

Do not duplicate a base method merely to introduce `context.Context`.

For custom persistence methods, accept and propagate `context.Context` according to the established Repository pattern.

Example:

```go
func (r *Repository) FindByDocument(
	ctx context.Context,
	document string,
) (*Entity, error) {
	// ...
}
```

---

# Custom Repository Methods

Create a custom method only when the persistence operation cannot be represented adequately by inherited base behavior.

Examples include:

```text
lookup by a domain-specific field
lookup by multiple columns
specialized aggregate query
specialized ordering
relationship-dependent query
query requiring JOIN
domain-specific existence query
persistence query with specialized predicates
```

Example:

```go
func (r *Repository) FindByDocument(
	ctx context.Context,
	document string,
) (*Entity, error) {
	result, err := gorm.G[Entity](r.Conn).
		Where(
			"document = ?",
			document,
		).
		First(ctx)

	if err != nil {
		return nil, err
	}

	return &result, nil
}
```

Do not add custom methods for speculative future use.

---

# Repository Interfaces

When a Service or another consumer requires an abstraction, define an interface exposing the required inherited and custom behavior.

When the complete base Repository contract is appropriate:

```go
type RepositoryInterface interface {
	base.Repository[Entity]

	FindByDocument(
		ctx context.Context,
		document string,
	) (*Entity, error)
}
```

Do not manually repeat every method already provided by:

```go
base.Repository[Entity]
```

Avoid:

```go
type RepositoryInterface interface {
	Save(...)
	FindById(...)
	FindOne(...)
	Delete(...)
	FindWithPagination(...)
	FindByDocument(...)
}
```

when the generic operations are already represented by:

```go
base.Repository[Entity]
```

Prefer:

```go
type RepositoryInterface interface {
	base.Repository[Entity]

	FindByDocument(...)
}
```

---

# Repository Structure

A Repository containing only inherited behavior may be:

```go
package module

import "project/internal/infra/base"

type Repository struct {
	base.RepositoryImpl[Entity]
}
```

Adapt the import path to the current project.

A Repository containing custom behavior may look like:

```go
package module

import (
	"context"

	"gorm.io/gorm"

	"project/internal/infra/base"
)

type RepositoryInterface interface {
	base.Repository[Entity]

	FindByUniqueField(
		ctx context.Context,
		uniqueField string,
	) (*Entity, error)
}

type Repository struct {
	base.RepositoryImpl[Entity]
}

func (r *Repository) FindByUniqueField(
	ctx context.Context,
	uniqueField string,
) (*Entity, error) {
	result, err := gorm.G[Entity](r.Conn).
		Where(
			"unique_field = ?",
			uniqueField,
		).
		First(ctx)

	if err != nil {
		return nil, err
	}

	return &result, nil
}
```

This is only a structural example.

Use the real Entity, fields, schema, types, package names and import paths from the current repository.

---

# Connection Ownership

The concrete Repository inherits the persistence connection through:

```go
base.RepositoryImpl[Entity]
```

When the base implementation exposes:

```go
Conn *gorm.DB
```

use the inherited:

```go
r.Conn
```

for custom queries.

Do not declare a second database connection field in the concrete Repository without an explicit architectural reason.

Avoid:

```go
type Repository struct {
	base.RepositoryImpl[Entity]
	DB *gorm.DB
}
```

when the same connection is already available through the base implementation.

---

# Generic Save Behavior

Do not implement custom create/update persistence merely to duplicate inherited `Save` behavior.

Use the inherited save operation or its context-aware equivalent when it already represents the required persistence behavior.

Create a specialized persistence method only when the operation requires behavior the inherited methods cannot represent.

---

# Generic FindById Behavior

Do not implement module methods such as:

```text
GetByID
FindEntityByID
FetchByID
LoadByID
```

solely to perform the same lookup already supplied by the base Repository.

Reuse inherited behavior.

---

# Generic FindOne Behavior

If the base Repository already provides a generic single-record lookup, use it when it represents the required persistence operation.

Create a named custom method when:

* the query is meaningfully domain-specific;
* query construction is more complex;
* the method communicates a persistence concept used by the module;
* the generic operation cannot represent the required query cleanly.

---

# Generic Pagination Behavior

If the base Repository already provides pagination behavior, reuse it.

Do not recreate:

```text
count
pagination metadata
offset
limit
generic preload handling
```

inside the concrete Repository.

Only implement specialized pagination when the inherited behavior cannot represent the required persistence query.

---

# Generic Delete Behavior

If the base Repository already provides delete behavior, reuse it.

Do not create a module-specific delete wrapper unless the persistence operation differs materially from the inherited implementation.

---

# Preloads

If the base Repository already supports generic preload behavior, reuse it when applicable.

Do not recreate generic preload iteration inside the concrete Repository.

For custom queries, add preloads only when the specific operation requires them.

---

# Query Parameters

Use parameterized conditions for runtime values.

Example:

```go
Where(
	"document = ?",
	document,
)
```

For multiple values:

```go
Where(
	"document = ? AND status = ?",
	document,
	status,
)
```

Do not interpolate runtime values directly into query strings.

---

# Entity Results

Repository methods should operate on and return domain entities.

Typical results include:

```go
*Entity
[]Entity
```

Persistence-specific scalar results may be returned when explicitly required by the operation.

Do not introduce transport DTOs into custom Repository APIs unless the project's established persistence abstraction explicitly requires them.

---

# GORM Usage

Use the GORM style already established by the current backend.

Custom queries may use:

```go
gorm.G[Entity](r.Conn)
```

when that is the repository convention.

Example:

```go
result, err := gorm.G[Entity](r.Conn).
	Where(
		"document = ?",
		document,
	).
	First(ctx)
```

Do not replace the inherited base Repository simply to use a different GORM syntax.

---

# Filters

Add custom persistence filters only when required by the task.

Example:

```go
query := gorm.G[Entity](r.Conn)

if status != "" {
	query = query.Where(
		"status = ?",
		status,
	)
}
```

Before writing generic filtering infrastructure, inspect whether the base Repository or another existing project abstraction already covers it.

---

# Ordering

Add explicit ordering only when required by the operation or existing module behavior.

Example:

```go
Order("created_at DESC")
```

Use actual persistence columns.

Do not introduce arbitrary ordering without a requirement.

---

# Aggregates

Custom Repository methods may implement persistence-level aggregate operations such as:

```text
COUNT
SUM
AVG
GROUP BY
```

when required by the caller.

Keep such methods narrowly focused on retrieving persistence information.

---

# Relationships and Joins

Use relationships, joins and related-table conditions only when required by the persistence operation.

Inspect:

```text
entity associations
foreign keys
table relationships
existing Repository patterns
```

before constructing the query.

Do not turn the Repository into a generic persistence facade for unrelated modules.

---

# Transactions

Use explicit transactions only when the persistence operation requires them and follow the transaction approach already established by the current backend.

Do not introduce a new transaction abstraction inside the module Repository.

---

# Creating a New Repository

Start from:

```go
package module

import "project/internal/infra/base"

type Repository struct {
	base.RepositoryImpl[Entity]
}
```

Adapt paths and package names to the current project.

Then add only the custom persistence behavior required by the module.

The base inheritance must remain present even if the Repository contains multiple custom methods.

---

# Modifying an Existing Repository

When `repository.go` already exists:

1. preserve the embedded `base.RepositoryImpl[Entity]`;
2. inspect inherited behavior before adding new methods;
3. preserve existing custom persistence methods;
4. add only the persistence behavior required by the task;
5. avoid duplicating base Repository functionality;
6. preserve existing method signatures unless the task requires changing them;
7. preserve existing interface composition when compatible.

Do not replace base inheritance with manual CRUD methods.

---

# Missing Information

When information required for a custom persistence operation is unavailable, do not invent it.

Examples:

* required columns cannot be determined;
* relationship ownership is unclear;
* ordering materially affects behavior but is unspecified;
* required lookup semantics are ambiguous;
* specification and schema describe incompatible persistence behavior.

State which persistence information is missing or conflicting.

---

## Review Evidence (For Reviewer Agents Only)

When reporting a Repository issue, identify:

```text
requirement
-> repository file
-> affected method/query/inheritance
-> observed problem
-> persistence consequence
-> expected correction
```

Example:

```text
Requirement:

The repository must reuse the generic persistence implementation.

Repository:

internal/domain/checklist/repository.go

Observed:

The repository manually implements Save, FindById and Delete instead of embedding base.RepositoryImpl[Checklist].

Impact:

Generic persistence behavior is duplicated and may diverge from the shared Repository implementation.

Expected:

Embed base.RepositoryImpl[Checklist] and keep only checklist-specific persistence methods.
```

Do not report a finding merely because another valid GORM or SQL formulation could have been used.

Findings must be based on:

* the specification;
* backend standards;
* existing Repository conventions;
* actual base Repository behavior;
* actual schema relationships;
* concrete persistence consequences.

---

## Repository Inheritance Review (For Reviewer Agents Only)

Confirm that the concrete Repository embeds:

```go
base.RepositoryImpl[Entity]
```

Check that generic operations supplied by the base implementation were not reimplemented unnecessarily.

Pay particular attention to duplicated implementations of operations already exposed by the current base Repository.

Examples may include:

```text
Save
SaveContext

FindWithPagination
FindWithPaginationContext

FindById
FindByIdContext

FindOne
FindOneContext

Delete
DeleteContext
```

The exact list must come from the current project's base implementation.

If equivalent behavior already exists in the base Repository, a module-specific implementation should have a concrete persistence reason.

Also confirm that custom queries use the connection inherited from `base.RepositoryImpl[Entity]` rather than introducing a duplicate database dependency.

---

## Repository Interface Review (For Reviewer Agents Only)

When a Repository interface exists, inspect whether inherited behavior is represented through:

```go
base.Repository[Entity]
```

when appropriate.

Prefer:

```go
type RepositoryInterface interface {
	base.Repository[Entity]

	FindByDocument(...)
}
```

over manually reproducing the entire generic Repository contract.

Check that custom methods represent actual module-specific persistence requirements.

---

## Query Review (For Reviewer Agents Only)

For each custom query, inspect:

```text
input parameters
-> query predicates
-> table/columns involved
-> expected result cardinality
-> returned value
```

Pay particular attention to:

```text
missing predicates
wrong columns
incorrect joins
unexpectedly broad queries
incorrect ordering
incorrect limit behavior
unnecessary preloads
duplicated base Repository functionality
```

Describe the concrete persistence consequence of the issue.

---

## Verification (For Reviewer Agents Only)

When repository commands are available, use the backend verification commands defined by the repository instructions.

Typical verification may include:

```bash
go test ./...
```

When relevant package-level tests exist, run those as well.

Use failures as evidence only when they are related to the Repository implementation.

Successful compilation does not by itself prove that a custom persistence query has correct semantics.

---

# Output

When creating a Repository, produce the complete resulting:

```text
repository.go
```

When modifying an existing Repository, return the complete resulting file unless the caller explicitly requests a diff or isolated change.

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
Persistence schema
        +
base.Repository
        +
base.RepositoryImpl
        +
Existing Repository patterns
        ↓
base.RepositoryImpl[Entity]
        +
Custom persistence methods
        ↓
repository.go
```

For reviewer agents:

```text
Task specification
        +
Sources of truth
        +
base Repository behavior
        +
Persistence schema
        +
Repository implementation
        ↓
Review Evidence
        +
Repository Inheritance Review
        +
Repository Interface Review
        +
Query Review
        +
Verification
```

Always reuse inherited base Repository behavior before introducing module-specific persistence code.

---

# Domain Errors

Repositories do not define error types and do not keep a domain `errors.go` file.

Never declare sentinel errors (`Err*`) in the domain package, and never keep a `normalizeRepositoryError`-style switch translating them.

When a persistence constraint violation is detected, return the matching `api_errors` typed error at the detection site:

```go
if isMaintenancePlanNameConstraintError(err) {
    return nil, api_errors.NewEntityAlreadyExistsError("MaintenancePlan", "name", strings.TrimSpace(plan.Name))
}
```

Use the typed error that matches the failure (`NewEntityAlreadyExistsError`, `NewNotFoundEntityError`, `NewValidationError`, `NewForbiddenError`). Reserve `NewDatabaseError` for failures that carry no domain meaning — never wrap a typed error in it.
