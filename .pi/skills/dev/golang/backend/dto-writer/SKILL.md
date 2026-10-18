---

name: dto-writer
description: Create or modify Go DTOs using the task specification, HTTP contract, target module, existing DTO conventions, and integrated backend source-of-truth context.
---

# Backend DTO Writer

## Purpose

Create or modify backend DTOs.

DTOs typically live inside the DTO package associated with the module.

Example:

```text
internal/dtos/<module>/
```

Typical files include:

```text
save_entity_dto.go
update_entity_dto.go
entity_response_dto.go
entity_filter_dto.go
```

Adapt file names and locations to the actual project structure.

DTOs represent transport and application-boundary data.

Do not repeat or reinterpret rules already defined by the backend sources of truth.

---

## Sources of Truth

Before creating or reviewing a DTO, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/golang/backend-standard.md`;
3. `docs/engineering/golang/backend-style.md`;
4. `docs/engineering/golang/backend-example.md`;
5. the specification or task contract describing the required request or response contract, if needed.

---

## Scope

This skill handles DTO definition.

Typical work includes:

* creating request DTOs;
* creating response DTOs;
* creating update DTOs;
* creating filter/query DTOs when the project uses them;
* modifying existing DTOs;
* defining Go field types;
* defining JSON field names;
* defining binding tags;
* representing optional request fields;
* representing nested request or response structures;
* reusing existing DTO types when appropriate.

Do not expand the task into Entity, Mapper, Service, Repository, Component, Controller, or migration changes unless explicitly requested.

---

# Workflow

## 1. Locate the DTO Package

Identify:

```text
module
DTO package
existing DTO files
request contract
response contract
```

If a relevant DTO already exists, use it as the starting point.

---

## 2. Inspect the API Contract

Before creating a DTO, determine:

```text
request fields
response fields
JSON names
required fields
optional fields
nested structures
collection fields
field types
```

Use the task specification and existing API contract as the primary reference.

Do not derive the HTTP contract solely from the Entity.

---

## 3. Inspect Existing DTO Conventions

Inspect nearby DTOs from the same module and similar modules.

Determine:

```text
package naming
file naming
type naming
JSON naming convention
binding tag style
pointer usage
nested DTO style
response identifier representation
```

Follow the existing project convention.

Do not introduce a different DTO style merely because another representation is also valid Go.

---

# Request DTOs

Request DTOs represent data accepted from the caller.

Example:

```go
type SaveEntityDto struct {
	Name     string `json:"name" binding:"required"`
	Document string `json:"document" binding:"required"`
}
```

Use the actual fields and types defined by the API contract.

Do not add fields merely because they exist in the persistence Entity.

---

# Response DTOs

Response DTOs represent the data returned by the API.

Example:

```go
type EntityResponseDto struct {
	ID       string `json:"id"`
	Name     string `json:"name"`
	Document string `json:"document"`
}
```

Response DTOs should represent the public response contract rather than mirror the Entity automatically.

Only expose fields required by the API.

---

# DTO Naming

Use the naming convention established by the project.

Common examples include:

```text
SaveEntityDto
UpdateEntityDto
EntityResponseDto
EntityFilterDto
EntityListResponseDto
```

Do not create alternative naming patterns when the project already defines one.

For a concrete domain:

```go
type SaveChecklistDto struct {
	// ...
}
```

or whatever naming convention is already used by nearby DTOs.

---

# Package Naming

Use the package naming convention already established by the DTO folder.

Example:

```go
package checklistDto
```

or:

```go
package checklist
```

depending on the project.

Do not infer package naming solely from general Go conventions.

Inspect existing DTO packages first.

---

# JSON Tags

Define the JSON field names required by the API contract.

Example:

```go
Name string `json:"name"`
```

For snake_case APIs:

```go
CreatedAt string `json:"created_at"`
```

Use the naming convention already established by the API.

Do not expose Go field names implicitly when explicit JSON tags are the project convention.

---

# Binding Tags

Use binding tags for transport-level requirements defined by the request contract.

Example:

```go
Name string `json:"name" binding:"required"`
```

Multiple requirements may follow the project's existing style:

```go
Email string `json:"email" binding:"required,email"`
```

Only add binding constraints supported by:

* the specification;
* existing API conventions;
* established DTO patterns.

Do not invent additional request restrictions.

---

# Optional Fields

Represent optional fields according to the project's established DTO conventions.

For example, an update DTO may use pointers:

```go
type UpdateEntityDto struct {
	Name *string `json:"name"`
}
```

when the application needs to distinguish:

```text
field omitted
```

from:

```text
field explicitly provided with zero value
```

Do not introduce pointers automatically.

Inspect how optional fields are represented elsewhere in the project.

---

# Save DTOs

A creation DTO should contain only the data that the API caller is expected to provide.

Example:

```go
type SaveEntityDto struct {
	Name string `json:"name" binding:"required"`
}
```

Do not automatically copy every Entity field into a Save DTO.

Fields controlled by the application should not be introduced into request DTOs merely because they are persisted.

---

# Update DTOs

Update DTOs should represent the actual update semantics of the endpoint.

Example:

```go
type UpdateEntityDto struct {
	Name *string `json:"name"`
}
```

If the endpoint uses full replacement semantics instead of partial update semantics, follow that contract instead.

Do not assume that every update DTO must use pointers.

---

# Response Identifiers

Use the identifier representation established by the API.

Example:

```go
ID string `json:"id"`
```

even when the underlying Entity uses another internal representation.

Do not expose persistence-specific identifier types automatically.

The Mapper is responsible for converting between domain and response representations.

---

# Time Fields

When response DTOs expose dates or timestamps, inspect existing DTO conventions.

Possible representations may include:

```go
CreatedAt time.Time `json:"created_at"`
```

or:

```go
CreatedAt string `json:"created_at"`
```

Use the representation established by the API.

Do not change timestamp representation based solely on the Entity field type.

---

# Nested DTOs

Use nested DTOs when the API contract contains nested structures.

Example:

```go
type TruckResponseDto struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}

type ChecklistResponseDto struct {
	ID    string           `json:"id"`
	Name  string           `json:"name"`
	Truck TruckResponseDto `json:"truck"`
}
```

Reuse an existing response DTO when the same representation is already defined and appropriate.

Do not reuse an unrelated DTO merely because its fields happen to match.

---

# Collections

Represent collection fields according to the API contract.

Example:

```go
Items []ItemResponseDto `json:"items"`
```

Use pointer slices only when the existing project convention or semantics require them.

Do not introduce unusual collection representations without a concrete requirement.

---

# Request and Response Separation

Do not use the same DTO for request and response merely because some fields overlap.

Example:

```text
SaveEntityDto
EntityResponseDto
```

may represent different contracts even when both contain `Name`.

Keep request and response contracts separate when they have distinct responsibilities.

---

# DTO Reuse

Reuse an existing DTO when it represents exactly the same API concept.

Do not duplicate:

```text
AddressDto
UserSummaryDto
FileResponseDto
```

if an existing type already represents the required structure.

However, do not reuse a DTO belonging to a different semantic contract solely to avoid creating a small type.

Representation compatibility is not always semantic compatibility.

---

# Pagination DTOs

When pagination DTOs already exist in shared infrastructure, reuse them.

Do not create module-specific pagination metadata types if the backend already defines a shared representation.

Example:

```go
dtos.PaginationDetailsDto
```

or the equivalent type defined by the current project.

---

# Query and Filter DTOs

If the project represents query parameters through DTOs, follow that pattern.

Example:

```go
type EntityFilterDto struct {
	Status string `form:"status"`
	Search string `form:"search"`
}
```

Only use tags such as:

```text
form
query
```

when they are already part of the project's transport conventions.

Do not introduce a filter DTO when existing Controllers read simple query parameters directly.

---

# File Upload DTOs

When the endpoint accepts files or multipart data, inspect existing DTO and bindin
