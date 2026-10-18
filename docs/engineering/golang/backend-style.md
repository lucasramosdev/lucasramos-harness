# Backend Style Guide and Conventions

> **Status:** Source of Truth

> **Scope:** Backend implementation, code generation, refactoring, reviews, tests, migrations, repositories, services, components, and HTTP routes.

> **Purpose:** This document defines the conventions that backend-related skills and agents must follow when working in this repository.

---

## 1. General Principles

All backend changes must prioritize:

1. **Consistency with the existing codebase**

2. **Explicit dependency wiring**

3. **Testability**

4. **Predictable error handling**

5. **Business-rule enforcement at the correct layer**

6. **Database integrity**

7. **Minimal invention of new architectural patterns**

When this guide conflicts with generic framework or language recommendations, **this guide takes precedence for this repository** unless the task specification explicitly requires otherwise.

Do not introduce new abstractions, architectural layers, naming conventions, persistence behavior, or framework patterns without first verifying that they already exist in the codebase or are explicitly required by the specification.

---

# 2. Instantiation and Dependency Injection

## 2.1 Production instantiation

Services and Components must use a singleton-style `GetInstance()` constructor when that pattern is already established for the module.

The production constructor must wire dependencies directly using:

- the concrete repository implementation;

- the global `database.Conn`;

- the expected base service configuration.

Example:

```go

type Service struct {

    base.Service[Entity]

    Repository

}

var moduleService *Service

func NewService() *Service {

    if moduleService == nil {

        repository := Repository{

            base.RepositoryImpl[Entity]{

                Conn: database.Conn,

            },

        }

        moduleService = &Service{

            Service: base.Service[Entity]{

                Repository: &repository,

                EntityName: "entity_name",

            },

            Repository: repository,

        }

    }

    return moduleService

}

```

```go

type Component struct {

    Service   Service

    DependencyService DependencyService

    Validator Validator

    Mapper    Mapper

}

var moduleComponent *Component

func NewComponent() *Component {

    if moduleComponent == nil {

        moduleComponent = &Component{

            Service:           *NewService(),

            DependencyService: *dependency.NewService(),

            Validator:         validator.GetInstance(),

            Mapper:            Mapper{},

        }

    }

    return moduleComponent

}

```



## 2.2 Dependency boundaries

Dependencies should be hidden behind **small interfaces** when tests need fakes.

Prefer interfaces that expose only the behavior actually required by the service or component.

Avoid unnecessarily broad repository interfaces.

Example:

```go

type EntityRepository interface {

    Save(ctx context.Context, entity Entity) (*Entity, error)

    FindByName(ctx context.Context, name string) (*Entity, error)

}

```

## 2.3 Testing

Tests should instantiate services directly whenever practical.

Do **not** rely on global singleton state in tests when a fake dependency can be injected directly.

Preferred:

```go

fakeRepo := &FakeRepository{}

svc := &Service{

    Service: base.Service[Entity]{

        Repository: fakeRepo,

        EntityName: "test_entity",

    },

    Repository: fakeRepo,

}

```

Avoid:

```go

svc := GetInstance()

```

when the test is intended to validate business logic independently from production wiring.

## 2.4 Rules

### Required

- Use `GetInstance()` for production service/component singleton construction when consistent with the module.

- Wire the concrete repository with `database.Conn`.

- Keep test dependencies replaceable.

- Prefer constructor-style direct instantiation in unit tests.

### Avoid

- Hidden mutable test dependencies.

- Tests coupled to global singleton state.

- Adding dependency injection frameworks.

- Creating factories or containers without an established project convention.

---

# 3. Layer Responsibilities

Business logic must be implemented at the correct layer.

## 3.1 Repository

Repositories are responsible for persistence operations.

Typical responsibilities:

- queries;

- inserts;

- updates;

- deletes;

- persistence-specific filtering;

- preload handling;

- database interaction.

Repositories should not contain business orchestration that belongs to services or components.

## 3.2 Service

Services are the preferred location for domain and business rules.

Examples:

- uniqueness validation;

- status transitions;

- permission-independent domain validation;

- entity-level invariants;

- creation/update rules;

- business decisions involving repository state.

## 3.3 Component

Components should be used for orchestration involving multiple services, repositories, or domain operations.

Examples:

- cross-service coordination;

- multi-step workflows;

- operations involving multiple entities;

- application-level orchestration.

Do not move simple service business rules into a Component unnecessarily.

## 3.4 Route

Routes are responsible for HTTP concerns.

Typical responsibilities:

- binding path/query/body parameters;

- validating transport-level input;

- invoking services/components;

- returning HTTP responses;

- delegating service errors to the common error treatment mechanism.

Routes should remain thin.

Do not duplicate service business rules in route handlers.

---

# 4. Error Handling

Error handling must remain consistent across the backend.

## 4.1 Database errors

Database failures must be converted using:

```go

api_errors.NewDatabaseError(...)

```

Do not expose raw database errors directly to API consumers.

## 4.2 Missing entities

When a required entity is not found, use:

```go

api_errors.NewNotFoundEntityError(...)

```

or:

```go

api_errors.NewNotFoundEntityErrorWithQuery(...)

```

Choose the variant that best matches the lookup context.

## 4.3 Route error handling

Service and component errors returned to route handlers must be processed using:

```go

api_errors.DefaultErrorTreatment(ginContext, err)

```

Example:

```go

result, err := service.Process(ginContext.Request.Context(), input)

if err != nil {

    api_errors.DefaultErrorTreatment(ginContext, err)

    return

}

```

Do not manually duplicate status mapping already handled by `DefaultErrorTreatment`.

## 4.4 Invalid JSON or binding errors

For request binding failures caused by invalid client payloads, return HTTP `400 Bad Request`.

The response body must contain:

```json

{

  "error": "...",

  "message": "..."

}

```

The exact values should follow the existing API convention.

## 4.5 User-facing messages

User-facing error messages should follow the project's primary language convention.

Unless a specification explicitly requires another language, prefer **Portuguese** for messages exposed to API consumers.

Internal identifiers, variable names, type names, and code symbols remain in English when consistent with the codebase.

## 4.6 Rules

### Required

- Convert database failures with `NewDatabaseError`.

- Convert missing records with the appropriate not-found API error.

- Use `DefaultErrorTreatment` in routes.

- Return HTTP 400 for malformed request payloads.

- Preserve the API response keys `error` and `message`.

### Avoid

- Returning raw GORM/database errors.

- Reimplementing centralized route error mapping.

- Mixing languages in user-facing errors without a reason.

- Returning generic `500` errors for known domain or validation failures.

---

# 5. Database and Migrations

The backend separates migrations into two streams:

```text

projects/backend/database/migrations/common

projects/backend/database/migrations/dev

```

## 5.1 `common` migrations

Use `common` for all real schema changes and production-relevant persistence changes.

Examples:

- tables;

- columns;

- constraints;

- indexes;

- foreign keys;

- defaults;

- schema-level invariants;

- production-required data transformations.

A business rule that must remain true regardless of application code should be enforced at the database level when practical.

Examples:

- uniqueness;

- required foreign-key relationships;

- non-null constraints;

- unique composite indexes.

## 5.2 `dev` migrations

Use `dev` only for local development or seed data.

Examples:

- development users;

- sample trucks;

- local checklist data;

- demo records;

- local fixtures.

`dev` migrations must not contain real schema changes.

## 5.3 Migration stream versioning

Before assuming that `common` and `dev` have independent version sequences, inspect how migrations are loaded by the application.

If they are loaded as independent migration sources, their version sequences may be independent.

If they are combined into one migration source, version numbers must not conflict.

Do not infer migration sequencing rules from folder names alone.

## 5.4 Data integrity

When a business rule requires persistence-level integrity, add the appropriate:

- unique constraint;

- index;

- foreign key;

- check constraint;

- non-null constraint;

when compatible with the repository's database conventions.

Application validation does not replace database integrity when concurrent requests could violate the rule.

## 5.5 Soft delete and archival behavior

Do not invent:

- soft delete;

- inactive flags;

- archival behavior;

- historical-state retention;

unless the backend already has an established convention for the entity or the specification explicitly requires it.

If deletion behavior is ambiguous, follow the existing project pattern.

## 5.6 Rules

### Required

- Schema changes belong in `common`.

- Development seed data belongs in `dev`.

- Add database constraints when required to enforce business integrity.

- Verify migration-loading behavior before choosing migration versions.

### Forbidden

- Real schema changes inside `dev`.

- Using a `dev` migration to compensate for a missing `common` migration.

- Inventing soft-delete behavior without project/spec support.

- Relying only on service validation for database invariants that require concurrency safety.

---

# 6. Testing Standards

## 6.1 Test framework

Backend tests must use Behavior-Driven Development with:

```go
. "github.com/onsi/ginkgo/v2"
. "github.com/onsi/gomega"
```

Go's standard `testing` package is used as the Ginkgo suite entry point.

Typical suite registration:

```go
func TestModule(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Module Suite")
}
```

Do not create new backend tests using plain `t.Run` scenarios when Ginkgo/Gomega are available in the project.

Do not introduce another assertion or BDD framework alongside Ginkgo/Gomega unless explicitly required by the specification.

## 6.2 BDD specification structure

Tests must describe behavior through Ginkgo specifications.

Prefer the hierarchy:

```text
Describe("Given ...")
  -> When("...")
      -> It("should ...")
```

Example:

```go
Describe("Given an entity", func() {
	When("saving the entity", func() {
		var (
			result *Entity
			err    error
		)

		BeforeEach(func() {
			result, err = repository.Save(
				context.Background(),
				Entity{},
			)
		})

		It("should return no error", func() {
			Expect(err).NotTo(HaveOccurred())
		})

		It("should return the persisted entity", func() {
			Expect(result).NotTo(BeNil())
		})
	})
})
```

Use:

- `Describe` to establish the subject or a relevant `Given` state;
- `When` to describe the operation or event;
- `It` to describe an observable expectation;
- `BeforeEach` for setup shared by specifications in the current context;
- `AfterEach` when explicit cleanup is required.

Do not use comments such as `Given`, `When`, and `Then` as a substitute for the Ginkgo specification structure.

## 6.3 Specification naming

Specification descriptions must communicate behavior.

Good:

```text
Describe("Given a duplicated document")
When("creating the customer")
It("should return an error")
It("should not persist the customer")
```

Avoid implementation-oriented descriptions such as:

```text
Describe("CreateCustomer method")
It("should test repository call")
It("should enter the if statement")
```

Descriptions should come from the business rule, persistence behavior, orchestration contract, or HTTP contract being tested.

## 6.4 Layer testing strategy

Use the test strategy appropriate to the layer under test.

```text
Repository
-> Ginkgo + Gomega + real isolated persistence when persistence behavior is under test

Service
-> Ginkgo + Gomega + fake Repository

Component
-> Ginkgo + Gomega + fake Services / Validators / collaborators

Controller / Route
-> Ginkgo + Gomega + HTTP test infrastructure + fake Component

Mapper
-> Ginkgo + Gomega when mapping behavior is significant enough to require direct coverage
```

Do not unnecessarily cross architectural boundaries in tests.

### Repository tests

Repository tests may use a real isolated database when the subject is persistence behavior.

Examples:

- custom queries;
- GORM mappings;
- pagination behavior;
- unique constraints;
- foreign-key behavior;
- transaction semantics;
- database-specific queries.

SQLite in-memory may be used when its behavior is compatible with the persistence semantics being tested.

Repository specifications should isolate database state between scenarios.

### Service tests

Service tests should use fake Repository dependencies when testing business behavior.

Instantiate the Service directly instead of obtaining production singleton state.

Example:

```go
repository := &FakeRepository{}

service := &Service{
	Service: base.Service[Entity]{
		Repository: repository,
		EntityName: "test_entity",
	},
	Repository: repository,
}
```

The fake may expose configurable results/errors and record calls or received arguments required by the specification.

### Component tests

Component tests should use fake Services, Validators, and other collaborators.

Instantiate the Component directly.

Example:

```go
component := &Component{
	Service:           fakeService,
	DependencyService: fakeDependencyService,
	Validator:         fakeValidator,
	Mapper:            Mapper{},
}
```

Focus on application orchestration rather than re-testing the internal business rules of the called Services.

### Controller / Route tests

Controller and route tests should use the project's HTTP test infrastructure and a fake Component.

For Gin-based projects, this normally includes:

```go
gin.New()
httptest.NewRequest(...)
httptest.NewRecorder()
```

Focus on:

- request binding;
- path/query parameter handling;
- HTTP status codes;
- response bodies;
- error mapping;
- invocation of the Component.

## 6.5 Setup and isolation

Use `BeforeEach` to establish the state required by each specification.

A specification must not depend on state left by another `It`.

Avoid dependencies on:

- execution order;
- production singleton state;
- mutable shared global state;
- uncontrolled database contents;
- external network access;
- uncontrolled time or randomness.

When setup depends on an operation succeeding, assert setup failures immediately.

Prefer:

```go
savedEntity, err = repository.Save(
	context.Background(),
	entity,
)
Expect(err).NotTo(HaveOccurred())
```

instead of silently returning from `BeforeEach` after an unexpected setup error.

## 6.6 Fakes

Fakes should be small, deterministic, and focused on the behavior required by the specifications.

A fake may expose:

- configured return values;
- configured errors;
- call counts;
- received arguments;
- persisted input;
- operation order when ordering is part of the contract.

Do not reproduce production business logic inside a fake.

Do not create a generic mocking framework when a small fake implementation is sufficient.

## 6.7 Assertions

Use Gomega matchers.

Prefer:

```go
Expect(err).NotTo(HaveOccurred())
Expect(result).NotTo(BeNil())
Expect(result.ID).NotTo(BeZero())
Expect(items).To(HaveLen(2))
Expect(value).To(Equal(expected))
Expect(flag).To(BeTrue())
Expect(err).To(MatchError(gorm.ErrRecordNotFound))
```

Each `It` should describe a clear observable expectation.

Multiple assertions may exist in the same `It` when together they represent one meaningful outcome.

Do not assert implementation details unless they are part of the contract being tested.

Depending on the scenario, meaningful assertions may include:

- returned value;
- returned error;
- error type;
- persisted input;
- dependency calls;
- received dependency arguments;
- status transition;
- orchestration outcome;
- HTTP status;
- response body.

## 6.8 Test placement and suite organization

Keep tests associated with the layer being tested.

Typical files:

```text
repository_test.go
service_test.go
component_test.go
controller_test.go
route_test.go
mapper_test.go
```

Follow the suite organization already established by the package.

A package may use a dedicated suite file such as:

```text
service_suite_test.go
service_test.go
```

or keep suite registration and specifications together when that is the established local convention.

Do not introduce multiple competing Ginkgo suite organizations inside the same package.

Do not create phase-oriented test files.

Avoid:

```text
recurrence_phase1_test.go
recurrence_phase2_test.go
feature_step3_test.go
```

Use layer-oriented test files instead.

## 6.9 Generic base behavior

Do not duplicate the complete test suite for inherited generic behavior inside every module.

When a module inherits behavior from shared abstractions such as:

```go
base.RepositoryImpl[Entity]
base.Service[Entity]
```

test the shared implementation where it is defined.

Module tests should focus on behavior added or specialized by that module unless the specification explicitly requires otherwise.

---

# 7. Repository Conventions

Repositories should remain persistence-focused and compatible with the generic base repository abstractions already present in the project.

When extending a repository:

- reuse `base.RepositoryImpl` when applicable;

- expose only the methods required by the module;

- pass `context.Context`;

- convert persistence failures according to the project's error-handling convention at the appropriate layer;

- avoid duplicating generic repository behavior unless the query is module-specific.

Example structure:

```go

type Repository struct {

    base.RepositoryImpl[Entity]

}

```

When the service needs a narrower abstraction for testing, define an interface representing only the required methods.

Example:

```go

type RepositoryContract interface {

    FindByDocument(ctx context.Context, document string) (*Entity, error)

    Save(ctx context.Context, entity Entity) (*Entity, error)

}

```

---

# 8. Route Conventions

Route handlers should remain small and predictable.

A route typically performs the following sequence:

1. bind input;

2. validate transport-level errors;

3. invoke service or component;

4. handle returned errors with `DefaultErrorTreatment`;

5. return the successful response.

Example:

```go

func Create(c *gin.Context) {

    var input CreateEntityDto

    if err := c.ShouldBindJSON(&input); err != nil {

        c.JSON(http.StatusBadRequest, gin.H{

            "error":   "invalid_request",

            "message": "Requisição inválida.",

        })

        return

    }

    result, err := GetInstance().Create(c.Request.Context(), input)

    if err != nil {

        api_errors.DefaultErrorTreatment(c, err)

        return

    }

    c.JSON(http.StatusCreated, result)

}

```

Business rules must not be duplicated in routes.

---

# 9. Business Rules and Data Integrity

Whenever implementing a business requirement, determine whether it belongs to:

- route validation;

- service validation;

- component orchestration;

- database integrity;

- or a combination of these.

Example:

> "An entity document must be unique."

Preferred enforcement:

1. service-level validation for a clear business error;

2. database unique constraint for concurrency safety.

Do not rely exclusively on:

```go

if existing == nil {

    repository.Save(...)

}

```

for uniqueness guarantees.

Concurrent requests may still violate the business rule unless the database also enforces it.

---

# 10. Naming and Language

Follow existing project naming before introducing new conventions.

General guidance:

- Go identifiers: English;

- domain type names: consistent with current codebase;

- database identifiers: follow existing schema naming;

- user-facing API messages: Portuguese by default;

- test scenario names: may follow the language used by the specification, but should remain consistent inside the module.

Do not rename existing concepts merely for stylistic preference.

---

# 11. Change Discipline

When implementing a task:

1. inspect the existing module first;

2. identify established patterns;

3. modify the smallest appropriate layer;

4. avoid unrelated refactors;

5. add or update tests for the business rule;

6. add migrations only when persistence structure changes;

7. preserve backward compatibility unless the specification explicitly changes the contract.

Do not perform broad cleanup unrelated to the requested change.

---

# 12. Anti-Patterns

Backend skills and agents must avoid the following unless explicitly required.

## Architecture

- introducing a new DI framework;

- replacing established repository/service/component patterns;

- creating new layers without a demonstrated need;

- moving business logic into routes;

- placing HTTP concerns inside repositories.

## Persistence

- schema changes in `dev`;

- seed data in `common` unless production data is explicitly required;

- missing database constraints for critical invariants;

- invented soft-delete columns;

- raw database errors exposed to callers.

## Testing

- plain `t.Run` scenario suites when the package uses Ginkgo/Gomega;
- mixing Ginkgo/Gomega with another assertion or BDD framework without a requirement;
- production singleton usage when dependencies can be injected directly;
- real database setup for ordinary Service or Component behavior;
- fake dependencies that reproduce production business logic;
- state leaking between `It` specifications;
- setup failures silently ignored inside `BeforeEach`;
- phase-named test files;
- specifications named after implementation details instead of behavior;
- duplicating the same behavior across multiple layers without a contract-level reason.


## Error handling

- manual error mapping in every route;

- raw GORM errors returned to clients;

- inconsistent error response structures;

- untranslated or inconsistent user-facing messages.

---

# 13. Decision Checklist for Skills

Before generating or modifying backend code, a skill should answer:

### Architecture

- Which layer owns this behavior?

- Does an existing Service, Component, Repository, or Route already implement a similar pattern?

- Is a new abstraction actually necessary?

### Dependency injection

- How is the production instance wired?

- Can tests inject a fake repository directly?

- Is the dependency interface minimal?

### Database

- Does this task require a schema change?

- If yes, is the migration in `common`?

- Is an index or constraint needed?

- Is the rule vulnerable to race conditions without database enforcement?

- How are migration versions loaded?

### Errors

- Can the repository/database fail?

- Should the failure become `NewDatabaseError`?

- Can the requested entity be missing?

- Should it become `NewNotFoundEntityError`?

- Is the route delegating to `DefaultErrorTreatment`?

### Tests

- Which behaviors are defined by the specification?
- Which architectural layer owns each behavior?
- How should the behavior be represented as `Describe("Given ...") -> When -> It`?
- Does the layer require real isolated persistence or fake dependencies?
- Are Service tests using fake Repositories where persistence itself is not under test?
- Are Component tests using fake Services and collaborators?
- Are Controller/Route tests using HTTP test infrastructure with a fake Component?
- Are Gomega matchers asserting observable outcomes rather than implementation details?
- Are specifications independent and isolated from production singleton state?


---

# 14. Rule Priority

When deciding how to implement a backend change, use this order of precedence:

1. **Explicit task specification**

2. **This Backend Style Guide**

3. **Existing module conventions**

4. **Existing repository-wide conventions**

5. **General Go/framework best practices**

If an explicit task requirement conflicts with this guide, follow the requirement but keep the deviation as narrow as possible.

If the task is silent, prefer the established project pattern rather than inventing a new one.

---

# 15. Source-of-Truth Directive for Skills

Backend-related skills must treat this document as the authoritative baseline for implementation decisions.

When a skill generates code, reviews code, plans a backend change, creates tests, or proposes a migration, it should:

- follow the rules in this document;

- inspect the target module for local conventions;

- avoid contradicting established project patterns;

- avoid inventing behavior not present in the specification;

- explicitly preserve testability;

- enforce business-critical persistence rules at the database level when appropriate.

If a requested implementation appears to conflict with this guide, the skill should first determine whether the specification intentionally overrides the convention or whether the implementation should be adapted to remain compliant.