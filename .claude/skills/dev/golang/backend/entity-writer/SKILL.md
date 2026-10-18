---

name: entity-writer
description: Create or modify a Go domain entity using the task specification, repository schema, target module, and integrated backend source-of-truth context.
---

# Backend Entity Writer

## Purpose

Create or modify a backend domain entity.

The expected target is usually:

```text
projects/backend/internal/domain/<module>/entity.go
```

For a subentity:

```text
projects/backend/internal/domain/<module>/<subentity>/entity.go
```

Use the backend source-of-truth documents already available in the prompt as the authoritative reference.

Do not repeat or reinterpret those documents.

---

## Sources of Truth

Before creating or reviewing a entity, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/golang/backend-standard.md`;
3. `docs/engineering/golang/backend-style.md`;
4. `docs/engineering/golang/backend-example.md`;
5. the specification or task contract describing the required persistence behavior (if needed).

---

## Scope

This skill handles only the entity definition.

Typical work includes:

* creating `entity.go`;
* modifying an existing entity;
* adding or removing fields required by the task;
* selecting the appropriate Go field types;
* mapping fields to database columns;
* adding GORM tags when needed;
* embedding existing base entity types;
* representing foreign keys;
* representing existing associations;
* implementing `TableName()` when appropriate.

Do not expand the task into other backend layers unless explicitly requested.

---

# Workflow

## 1. Locate the Entity

Identify:

```text
module
package
entity name
entity.go
database table
```

If `entity.go` already exists, use it as the starting point.

---

## 2. Inspect the Local Model

Before writing the entity, inspect the files directly relevant to its representation.

Prefer, in this order:

1. existing `entity.go`;
2. migration that creates or changes the corresponding table;
3. nearby entities from the same module;
4. entities representing similar fields or relationships;
5. integrated backend examples when no closer reference exists.

Also inspect shared embedded types when used by the module, such as:

```go
base.BaseEntity
```

The goal is to discover the concrete representation already used by the repository.

---

## 3. Determine the Fields

For each field required by the task, determine:

```text
Go field name
Go type
database column
GORM metadata, when necessary
```

Base these decisions on the actual repository.

Example:

```sql
truck_id VARCHAR(255) NOT NULL
```

may correspond to:

```go
TruckID string `gorm:"column:truck_id;not null"`
```

Follow existing naming and type conventions instead of introducing new ones.

---

## 4. Preserve Shared Fields

When the entity embeds a shared type such as:

```go
base.BaseEntity
```

inspect that type before declaring fields that may already be provided by it.

Do not duplicate shared fields in the entity.

Example structure:

```go
type Checklist struct {
	base.BaseEntity

	Name    string `gorm:"column:name;not null"`
	TruckID string `gorm:"column:truck_id;not null"`
}
```

---

## 5. Map the Persistence Model

Use the actual database structure to define the entity.

Consider:

```text
column names
column types
nullability
foreign-key columns
defaults
existing relationships
```

Do not derive the entity only from an API payload or DTO.

The persistence model and domain representation are the primary references.

---

## 6. Relationships

When the entity has a relationship, first inspect how that relationship is represented elsewhere in the repository.

A foreign-key column may require only:

```go
TruckID string `gorm:"column:truck_id;not null"`
```

or the existing model may also expose an association:

```go
TruckID string       `gorm:"column:truck_id;not null"`
Truck   trucks.Truck `gorm:"foreignKey:TruckID;references:ID"`
```

Use the form established by the repository.

Do not add an association solely because a foreign key exists.

---

## 7. Table Name

Determine the table name from the existing persistence model.

When the module explicitly maps table names, use:

```go
func (Checklist) TableName() string {
	return "checklists"
}
```

Use the real table name rather than inferring it from the Go type.

---

# Creating a New Entity

A typical new entity may look like:

```go
package checklist

import "project-backend/internal/infra/base"

type Checklist struct {
	base.BaseEntity

	Name    string `gorm:"column:name;not null"`
	TruckID string `gorm:"column:truck_id;not null"`
}

func (Checklist) TableName() string {
	return "checklists"
}
```

This is only a structural example.

Names, types, tags, imports and table mapping must come from the target module and task.

---

# Modifying an Existing Entity

When `entity.go` already exists:

1. start from the current implementation;
2. modify only what the task requires;
3. preserve unrelated fields;
4. preserve existing naming;
5. preserve existing field types unless the task changes them;
6. preserve existing relationship representation;
7. preserve the module's import and formatting style.

Do not rewrite the file around a preferred generic template.

---

# GORM Metadata

Add GORM metadata only when it is part of the repository's representation.

Examples may include:

```go
gorm:"column:name"
gorm:"column:name;not null"
gorm:"foreignKey:TruckID;references:ID"
```

Determine the exact form from the existing schema and module conventions.

Do not add optional GORM features simply because GORM supports them.

---

# Existing Domain Types

Reuse domain types already defined by the project.

For example, if the module already contains:

```go
type Status string
```

and the entity uses that concept, prefer:

```go
Status Status `gorm:"column:status;not null"`
```

instead of creating a second representation for the same concept.

Inspect the module before creating new types or constants.

---

# Imports

Include only imports required by the resulting entity.

Common reasons include:

```text
base entity embedding
time.Time
related domain entities
existing custom domain types from another package
```

Do not add imports for layers unrelated to the entity.

---

# Missing Information

When information required to model the entity is unavailable, do not invent it.

Examples:

* database type is unknown;
* nullable representation is unclear;
* table name cannot be determined;
* relationship ownership is unclear;
* referenced entity cannot be identified;
* specification and existing schema describe different structures.

State exactly which piece of information is missing or conflicting.

---

# Review Evidence (For Reviewer Agents Only)

When reporting an entity issue, identify:

```text
requirement
-> entity file
-> affected field/tag/relationship
-> observed problem
-> domain or persistence consequence
-> expected correction
```

Example:

```text
Requirement:

A checklist must reference its truck through the existing truck_id foreign key.

Entity:

internal/domain/checklist/entity.go

Observed:

The entity declares Truck but does not declare TruckID, while the persistence schema stores truck_id.

Impact:

The entity does not represent the persistence model used by the table and existing relationship.

Expected:

Represent the foreign-key field according to the schema and the established entity pattern.
```

Do not report a finding merely because another valid Go or GORM representation could have been used.

Findings must be based on:

* the specification;
* backend standards;
* existing entity conventions;
* actual persistence schema;
* concrete domain or persistence consequences.

---

# Entity Review (For Reviewer Agents Only)

Review the resulting entity against the task, persistence model and local module conventions.

Check that:

* every requested field is represented;
* no unsupported field was introduced;
* field names follow the repository convention;
* Go types match the persistence representation;
* database column names are correct;
* nullability is represented consistently;
* embedded base fields are not duplicated;
* foreign-key fields match the corresponding relationship;
* associations follow existing repository patterns;
* `TableName()` references the correct table;
* GORM tags match the intended persistence model;
* imports are necessary and correctly scoped;
* unrelated changes were not introduced.

When reviewing a modification, compare the resulting entity with the original file and identify unintended changes to unrelated fields or relationships.

Do not classify stylistic preference as a defect when the implementation is compatible with the specification and repository conventions.

---

# Verification (For Reviewer Agents Only)

When repository commands are available, use them to detect concrete problems introduced by the entity change.

Prefer the backend commands defined by the repository instructions.

Typical verification may include:

```bash
go test ./...
```

or another project-defined compilation/test command.

Use command failures as evidence only when they are related to the entity under review.

When a failure is unrelated to the entity change, do not report it as an entity finding.

When a failure originates from another layer because that layer has not yet been updated for an intentional entity change, distinguish that dependency from an incorrect entity implementation.

Verification should complement source inspection, not replace it.

---

# Output

When creating an entity, produce the complete resulting `entity.go`.

Example output shape:

```go
package module

import "project-backend/internal/infra/base"

type Entity struct {
	base.BaseEntity

	// fields
}

func (Entity) TableName() string {
	return "table_name"
}
```

When modifying an existing entity, return the complete resulting file unless the caller explicitly requests a diff or isolated change.

Do not include unrelated backend files.

---

# Execution Summary

For writer agents:

```text
Task specification
        +
Integrated backend source of truth
        +
Existing entity
        +
Database migration/schema
        +
Nearby domain patterns
        ↓
     entity.go
```

For reviewer agents:

```text
Task specification
        +
Integrated backend source of truth
        +
Persistence model
        +
Generated/existing entity
        ↓
Review Evidence
        +
Entity Review
        +
Verification
```

Prefer the closest concrete repository implementation over generic examples.

---

# Submodule Re-exports

When a module has submodules (e.g. `items/`, `links/`), their entity types and constants may be re-exported so the module keeps a single import surface — but declared inline in `entity.go`, never in a dedicated `subentities.go` file:

```go
type (
    MaintenancePlanItem      = items.MaintenancePlanItem
    TruckMaintenancePlanLink = links.TruckMaintenancePlanLink
)
```
