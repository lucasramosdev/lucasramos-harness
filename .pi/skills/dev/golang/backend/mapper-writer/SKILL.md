---
name: mapper-writer
description: Create or modify Go mappers responsible for converting between DTOs, domain entities, response DTOs, and other representation boundaries defined by the backend architecture.
---

# Backend Mapper Writer

## Purpose

Create or modify a backend Mapper.

The target is typically a `mapper.go` inside the corresponding domain package.

Examples:

```text
internal/domain/<module>/mapper.go
```

or:

```text
internal/domain/<module>/<subentity>/mapper.go
```

Adapt the location to the actual project structure.

A Mapper converts data between architectural representations.

Typical flows include:

```text
Request DTO
-> Domain Entity
```

and:

```text
Domain Entity
-> Response DTO
```

Do not repeat or reinterpret rules already defined by the backend sources of truth.

---

## Sources of Truth

Before creating or reviewing a mapper, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/golang/backend-standard.md`;
3. `docs/engineering/golang/backend-style.md`;
4. `docs/engineering/golang/backend-example.md`;
5. the specification or task contract describing the required representation behavior, if needed.

---

## Scope

This skill handles Mapper implementation.

Typical work includes:

- creating `mapper.go`;
- modifying an existing Mapper;
- mapping request DTOs to domain entities;
- mapping domain entities to response DTOs;
- mapping collections when required;
- mapping nested representations;
- converting identifiers between domain and transport representations;
- converting timestamps or other representation-specific values;
- reusing existing Mapper methods;
- composing deterministic representation transformations.

Do not expand the task into DTO, Entity, Repository, Service, Component, Controller, or migration changes unless explicitly requested.

---

## Workflow

### 1. Locate the Mapper

Identify:

```text
module
package
mapper.go
input DTOs
domain entities
response DTOs
existing Mapper methods
```

If `mapper.go` already exists, use it as the starting point.

### 2. Inspect Both Sides of the Mapping

Before creating a mapping method, inspect the complete source and target types.

For request-to-domain mapping, inspect:

```text
request DTO
domain Entity
```

For domain-to-response mapping, inspect:

```text
domain Entity
response DTO
```

Determine:

```text
source field
target field
source type
target type
conversion required
nested representation
optional representation
```

Do not infer mappings from field names alone.

### 3. Inspect Existing Mapper Conventions

Inspect:

1. the existing Mapper in the target module;
2. nearby Mapper implementations;
3. DTO naming conventions;
4. Entity conventions;
5. response representation conventions;
6. helper methods already used for common conversions.

Preserve the local Mapper style.

Do not introduce a mapping framework when explicit Go methods are already the project convention.

---

## Mapper Structure

A Mapper is typically stateless.

Example:

```go
type Mapper struct{}
```

Mapping methods may use value receivers:

```go
func (Mapper) EntityFromDto(
	input moduleDto.SaveEntityDto,
) Entity {
	// ...
}
```

and:

```go
func (Mapper) EntityToResponse(
	entity Entity,
) moduleDto.EntityResponseDto {
	// ...
}
```

Use the receiver style already established by the current project.

Do not add state to the Mapper without a concrete architectural requirement.

---

## DTO to Entity Mapping

Use a Mapper method to convert transport input into the corresponding domain representation.

Example:

```go
func (Mapper) EntityFromDto(
	input moduleDto.SaveEntityDto,
) Entity {
	return Entity{
		Name:     input.Name,
		Document: input.Document,
	}
}
```

Map only fields represented by the source DTO.

Do not populate domain fields from values that are not present in the DTO unless another explicit input to the Mapper provides them.

Do not invent defaults.

---

## Entity to Response Mapping

Use a Mapper method to convert a domain Entity into the corresponding response DTO.

Example:

```go
func (Mapper) EntityToResponse(
	entity Entity,
) moduleDto.EntityResponseDto {
	return moduleDto.EntityResponseDto{
		ID:   entity.GetIDAsString(),
		Name: entity.Name,
	}
}
```

Use the response representation defined by the DTO.

Do not expose Entity fields merely because they exist.

Only map fields required by the response contract.

---

## Mapper Method Naming

Follow existing project naming.

Common patterns may include:

```text
EntityFromDto
EntityToResponse
EntitiesToResponse
FromDto
ToResponse
ToDto
```

Do not introduce another naming pattern when the module already establishes one.

For concrete domains, method names may remain generic when the Mapper belongs exclusively to that domain.

Follow local convention.

---

## Field Mapping

Map fields explicitly.

Prefer:

```go
return Entity{
	Name:        input.Name,
	Description: input.Description,
}
```

over reflection-based or automatic mapping.

Explicit mapping makes representation changes visible and predictable.

Do not introduce reflection or external mapping libraries unless already established by the project.

---

## Different Field Names

The source and target fields do not need to have identical names.

Example:

```go
type SaveEntityDto struct {
	DisplayName string `json:"name"`
}
```

may map to:

```go
Entity{
	Name: input.DisplayName,
}
```

Use the semantic relationship defined by the API/domain contract.

Do not rename domain fields solely to make mapping syntactically symmetrical.

---

## Type Conversion

When source and target representations differ, perform the smallest deterministic conversion required.

Example:

```go
ID: entity.GetIDAsString(),
```

Inspect existing project helpers before implementing conversions manually.

Do not introduce conversions that are not required by the source and target types.

---

## Identifier Mapping

Identifiers may have different representations across boundaries.

Example:

```text
Entity ID
-> response string
```

Use existing Entity helpers when available.

Example:

```go
ID: entity.GetIDAsString(),
```

Prefer existing conversion methods over duplicating identifier formatting logic inside the Mapper.

---

## Optional Fields

When DTO and Entity optionality differ, follow the semantics defined by the operation.

Example:

```go
type UpdateEntityDto struct {
	Name *string `json:"name"`
}
```

The Mapper may need to preserve the distinction between:

```text
field omitted
field provided
```

Do not collapse optional input prematurely when the downstream operation requires that distinction.

---

## Update Mapping

Do not automatically reuse creation mapping for updates.

An update DTO may represent different semantics.

Example:

```go
func (Mapper) ApplyUpdate(
	entity Entity,
	input moduleDto.UpdateEntityDto,
) Entity {
	if input.Name != nil {
		entity.Name = *input.Name
	}

	return entity
}
```

Only use this style when update transformation genuinely belongs in the Mapper and matches project convention.

If update rules involve business decisions, keep those decisions outside the Mapper.

---

## Nested Response Mapping

When a response contains nested objects, map each representation explicitly.

Example:

```go
func (m Mapper) EntityToResponse(
	entity Entity,
) moduleDto.EntityResponseDto {
	return moduleDto.EntityResponseDto{
		ID:   entity.GetIDAsString(),
		Name: entity.Name,
		Category: moduleDto.CategoryResponseDto{
			ID:   entity.Category.GetIDAsString(),
			Name: entity.Category.Name,
		},
	}
}
```

When an existing Mapper already handles the nested domain type, reuse it when appropriate.

Do not duplicate complex nested mappings unnecessarily.

---

## Collection Mapping

When a response requires a collection transformation, add a dedicated method when it improves reuse or readability.

Example:

```go
func (m Mapper) EntitiesToResponse(
	entities []Entity,
) []moduleDto.EntityResponseDto {
	response := make(
		[]moduleDto.EntityResponseDto,
		0,
		len(entities),
	)

	for _, entity := range entities {
		response = append(
			response,
			m.EntityToResponse(entity),
		)
	}

	return response
}
```

Reuse the single-entity mapping method instead of duplicating field assignments.

---

## Pagination Mapping

When the application response combines mapped entities with pagination metadata, inspect the project convention before deciding whether that assembly belongs in the Mapper or Component.

The Mapper may map:

```text
[]Entity
-> []EntityResponseDto
```

while the Component assembles:

```text
items
+
pagination metadata
```

Do not create a new response assembly convention solely for one endpoint.

---

## Existing Domain Types

Preserve domain types when crossing only internal application boundaries.

Convert them only when the DTO representation requires it.

Example:

```go
Status: string(entity.Status),
```

may be appropriate when the API representation is a string and the domain uses:

```go
type Status string
```

Do not remove domain typing from the Entity merely to simplify mapping.

---

## Time Mapping

Map timestamps according to the DTO representation.

If the response DTO uses:

```go
CreatedAt time.Time `json:"created_at"`
```

the mapping may be direct.

If the response DTO uses a formatted string, inspect existing formatting helpers and API conventions first.

Do not introduce date formatting conventions inside an individual Mapper without project support.

---

## Enum and Status Mapping

When domain values and transport values differ, map them explicitly.

Example:

```go
Status: string(entity.Status),
```

when the API representation is a string.

For non-trivial status translation, inspect existing mappings and the specification.

Do not invent aliases or user-facing values.

---

## Mapper Composition

A Mapper may call another deterministic Mapper when nested representation belongs to another type.

Example:

```go
Category: categoryMapper.EntityToResponse(
	entity.Category,
),
```

Use this only when the external Mapper is already an established public representation helper.

Do not introduce Service or Repository dependencies merely to obtain mapping data.

---

## Mapper Must Remain Deterministic

Given the same inputs, a Mapper should produce the same output.

Do not make Mapper methods depend on:

```text
database state
network state
current request
current authenticated user
current time
randomness
global mutable state
```

unless the project's architecture explicitly defines otherwise.

A Mapper should normally require only the data passed to the mapping method.

---

## No Persistence Access

Do not access:

```text
Repository
gorm.DB
database connection
raw SQL
```

from a Mapper.

If additional domain data is required before mapping, obtain that data before invoking the Mapper.

---

## No Service Calls

Do not call Services from a Mapper.

The Mapper should transform already available data.

---

## No Business Decisions

Do not implement business rules inside mapping code.

Mapping may translate a representation.

It must not change domain behavior.

---

## No HTTP Behavior

Do not introduce:

```text
Gin context
HTTP status codes
HTTP headers
response writing
request parsing
```

inside Mapper methods.

---

## Constructors

A stateless Mapper normally does not require a constructor.

Prefer:

```go
Mapper{}
```

when that is the existing project convention.

Do not create `NewMapper()` unless Mapper construction already exists in the repository or the Mapper genuinely requires dependencies.

---

## Creating a New Mapper

A simple Mapper may look like:

```go
package module

import moduleDto "project/internal/dtos/module"

type Mapper struct{}

func (Mapper) EntityFromDto(
	input moduleDto.SaveEntityDto,
) Entity {
	return Entity{
		Name:     input.Name,
		Document: input.Document,
	}
}

func (Mapper) EntityToResponse(
	entity Entity,
) moduleDto.EntityResponseDto {
	return moduleDto.EntityResponseDto{
		ID:       entity.GetIDAsString(),
		Name:     entity.Name,
		Document: entity.Document,
	}
}
```

This is only a structural example.

Adapt:

```text
package
imports
DTO names
Entity type
field mappings
type conversions
method names
```

to the current repository.

---

## Modifying an Existing Mapper

When `mapper.go` already exists:

1. preserve unrelated mappings;
2. preserve existing method naming;
3. preserve established conversion helpers;
4. add only transformations required by the task;
5. reuse existing mapping methods when appropriate;
6. avoid modifying DTOs or Entities solely to simplify mapping;
7. avoid unrelated refactoring.

Do not rewrite the Mapper around a generic abstraction.

---

## Missing Information

When the required representation cannot be determined, do not invent it.

Examples:

- source DTO field has no clear target;
- response field source cannot be determined;
- identifier conversion is undefined;
- nested response representation is unclear;
- optional update semantics are unspecified;
- source and target types conflict without an established conversion;
- specification and current API representation disagree.

State which mapping information is missing or conflicting.

---

## Review Evidence (For Reviewer Agents Only)

When reporting a Mapper issue, identify:

```text
requirement
-> mapper file
-> affected method/field mapping
-> observed problem
-> representation consequence
-> expected correction
```

Example:

```text
Requirement:

EntityResponseDto.id must contain the public string representation
of the Entity identifier.

Mapper:

internal/domain/entity/mapper.go

Method:

EntityToResponse

Observed:

The Mapper converts the numeric ID manually instead of using the
existing entity identifier representation helper.

Impact:

The response may not follow the identifier format used by the API.

Expected:

Use the established Entity identifier conversion.
```

Do not report a finding merely because another valid Go formulation could have been used.

Findings must be based on:

- the specification;
- backend standards;
- existing Mapper conventions;
- actual DTO contracts;
- actual Entity representation;
- concrete representation consequences.

---

## Field Mapping Review (For Reviewer Agents Only)

For each Mapper method, map:

```text
source field
-> conversion
-> target field
```

Confirm that:

- required target fields are populated;
- unsupported source fields are not introduced;
- source and target semantics match;
- type conversions are intentional;
- identifiers use the expected representation;
- optional fields preserve required semantics;
- nested fields use the expected representation.

Do not require mappings for fields that are not part of the target contract.

---

## DTO to Entity Review (For Reviewer Agents Only)

For request-to-domain mapping, inspect:

```text
DTO
-> Mapper
-> Entity
```

Confirm that:

- DTO fields map to the intended Entity fields;
- fields absent from the DTO are not invented by the Mapper;
- application-controlled Entity fields are not populated from unrelated request data;
- representation conversion does not introduce business behavior.

A Mapper may leave Entity fields unset when those values are supplied later by another application layer.

---

## Entity to Response Review (For Reviewer Agents Only)

For domain-to-response mapping, inspect:

```text
Entity
-> Mapper
-> Response DTO
```

Confirm that:

- response fields come from the correct domain source;
- internal-only Entity fields are not accidentally exposed;
- nested response objects are mapped correctly;
- API identifier and time representations are preserved;
- collection mapping reuses the canonical single-item mapping when appropriate.

---

## Determinism Review (For Reviewer Agents Only)

Check that Mapper behavior depends only on its explicit inputs.

Look for:

```text
Repository calls
Service calls
database access
network calls
current request access
global mutable state
current time
randomness
```

Report these when they make representation conversion depend on external behavior.

---

## Boundary Review (For Reviewer Agents Only)

Confirm that the Mapper contains transformation behavior rather than responsibilities owned by another layer.

Look for:

```text
business rules
persistence queries
Service orchestration
authorization decisions
HTTP response writing
request binding
```

A representation conversion should not perform application workflows.

---

## Mapper Reuse Review (For Reviewer Agents Only)

Inspect repeated transformations.

If several methods manually repeat the same Entity-to-response mapping, determine whether an existing Mapper method should be reused.

Example:

```go
for _, entity := range entities {
	response = append(
		response,
		m.EntityToResponse(entity),
	)
}
```

Do not require abstraction when the mappings are intentionally different.

---

## Verification (For Reviewer Agents Only)

When repository commands are available, use the backend verification commands defined by the project instructions.

Typical verification may include:

```bash
go test ./...
```

When Mapper specifications exist, run the affected package or suite.

For Ginkgo/Gomega projects, relevant verification may also use:

```bash
ginkgo ./...
```

when that command is established by the repository.

Compilation can detect incompatible DTO/Entity types but does not prove semantic mapping correctness.

Source inspection remains necessary.

---

## Testing Guidance

Mapper tests should use the project's Ginkgo v2 + Gomega BDD convention when direct Mapper coverage is appropriate.

Typical structure:

```go
Describe("Given a save DTO", func() {
	var input moduleDto.SaveEntityDto

	BeforeEach(func() {
		input = moduleDto.SaveEntityDto{
			Name: "Example",
		}
	})

	When("mapping the DTO to an entity", func() {
		var result Entity

		BeforeEach(func() {
			result = Mapper{}.EntityFromDto(input)
		})

		It("should map the name", func() {
			Expect(result.Name).To(Equal(input.Name))
		})
	})
})
```

For response mapping:

```go
Describe("Given an entity", func() {
	var entity Entity

	BeforeEach(func() {
		entity = Entity{
			Name: "Example",
		}
	})

	When("mapping the entity to the response DTO", func() {
		var result moduleDto.EntityResponseDto

		BeforeEach(func() {
			result = Mapper{}.EntityToResponse(entity)
		})

		It("should map the name", func() {
			Expect(result.Name).To(Equal(entity.Name))
		})
	})
})
```

Do not add Mapper tests merely to assert trivial field assignments in every module unless direct Mapper coverage is required by the task or project convention.

---

## Mapper Test Review (For Reviewer Agents Only)

When Mapper tests exist, confirm that they use the project's Ginkgo/Gomega BDD structure.

Prefer:

```text
Describe("Given ...")
-> When("...")
   -> It("should ...")
```

Confirm that tests cover transformations significant to the API/domain contract, such as:

- identifier conversion;
- optional-field semantics;
- nested representation;
- custom type conversion;
- collection mapping;
- response field selection.

Do not require tests for every trivial assignment when the project does not require direct Mapper coverage.

---

## Output

When creating a Mapper, produce the complete resulting:

```text
mapper.go
```

When modifying an existing Mapper, return the complete resulting file unless the caller explicitly requests a diff or isolated change.

Do not include unrelated backend files.

---

## Execution Summary

For writer agents:

```text
Task specification
        +
Sources of truth
        +
Input DTOs
        +
Domain entities
        +
Response DTOs
        +
Existing Mapper patterns
        ↓
Representation mapping
        ↓
mapper.go
```

For reviewer agents:

```text
Task specification
        +
Sources of truth
        +
DTO contracts
        +
Entity representation
        +
Mapper implementation
        ↓
Review Evidence
        +
Field Mapping Review
        +
DTO to Entity Review
        +
Entity to Response Review
        +
Determinism Review
        +
Boundary Review
        +
Mapper Reuse Review
        +
Mapper Test Review
        +
Verification
```

Keep Mapper behavior explicit, deterministic, and limited to representation transformation.
