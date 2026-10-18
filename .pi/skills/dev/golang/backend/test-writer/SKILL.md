---

name: test-writer
description: Create or modify Go backend tests using BDD with Ginkgo v2 and Gomega, adapting test strategy to the architectural layer under test.
---

# Backend Test Writer

## Purpose

Create or modify backend tests using Behavior-Driven Development with:

```go
github.com/onsi/ginkgo/v2
github.com/onsi/gomega
```

Tests must describe behavior using Ginkgo's specification hierarchy.

The expected structure is:

```text
Describe
  -> Given
      -> When
          -> It
```

Example:

```go
Describe("Given an entity", func() {
	When("save the entity", func() {
		It("should return no error", func() {
			// ...
		})

		It("should return the persisted entity", func() {
			// ...
		})
	})
})
```

Use Gomega for assertions.

Example:

```go
Expect(err).NotTo(HaveOccurred())
Expect(result).NotTo(BeNil())
Expect(result.ID).NotTo(BeZero())
```

Do not implement new tests using plain `t.Run` scenarios when Ginkgo/Gomega are available in the project.

---

## Sources of Truth

Before creating or reviewing tests, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/golang/backend-standard.md`;
3. `docs/engineering/golang/backend-style.md`;
4. `docs/engineering/golang/backend-example.md`;
5. the specification or task contract describing the expected behavior, if needed;
6. existing Ginkgo/Gomega tests from the same architectural layer.

---

# Testing Stack

Use:

```go
. "github.com/onsi/ginkgo/v2"
. "github.com/onsi/gomega"
```

with Go's standard `testing` package only as the Ginkgo suite entry point.

Typical suite entry:

```go
func TestModule(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Module Suite")
}
```

Follow the suite organization already established by the project.

Do not introduce another assertion or BDD framework alongside Ginkgo/Gomega.

---

# BDD Structure

Tests must express behavior hierarchically.

Use:

```text
Describe
```

for the subject or broad behavior being tested.

Use:

```text
Given
```

to describe the relevant initial state.

Use:

```text
When
```

to describe the operation or event.

Use:

```text
It
```

to describe one observable expectation.

Example:

```go
Describe("Given an existing customer", func() {
	When("updating the customer", func() {
		It("should return no error", func() {
			Expect(err).NotTo(HaveOccurred())
		})

		It("should preserve the entity id", func() {
			Expect(updated.ID).To(Equal(saved.ID))
		})
	})
})
```

Nested `When` blocks may be used when a scenario has meaningful variations.

---

# Shared Setup

Use:

```go
BeforeEach(...)
```

for state required by every specification inside the current context.

Example:

```go
Describe("Given an entity", func() {
	var entity Entity

	BeforeEach(func() {
		entity = Entity{}
	})

	// ...
})
```

Use nested `BeforeEach` blocks to prepare state specific to a `When` or nested context.

Do not repeat identical setup in every `It` when it belongs naturally in `BeforeEach`.

---

# Subject Execution

When multiple `It` specifications assert different outcomes of the same operation, execute the subject in the surrounding `BeforeEach`.

Preferred:

```go
When("save the entity", func() {
	var (
		result *Entity
		err    error
	)

	BeforeEach(func() {
		result, err = repository.Save(
			context.Background(),
			entity,
		)
	})

	It("should return no error", func() {
		Expect(err).NotTo(HaveOccurred())
	})

	It("should return an entity", func() {
		Expect(result).NotTo(BeNil())
	})

	It("should assign an id", func() {
		Expect(result.ID).NotTo(BeZero())
	})
})
```

This makes each `It` describe one expectation over the same behavior.

---

# Assertions

Use Gomega assertions.

Prefer:

```go
Expect(err).NotTo(HaveOccurred())
```

over:

```go
Expect(err).To(BeNil())
```

when asserting ordinary errors.

Examples:

```go
Expect(result).NotTo(BeNil())

Expect(result.ID).NotTo(BeZero())

Expect(items).To(HaveLen(2))

Expect(value).To(Equal(expected))

Expect(flag).To(BeTrue())

Expect(flag).To(BeFalse())

Expect(err).To(MatchError(gorm.ErrRecordNotFound))
```

Use the matcher that best communicates the behavior.

---

# Repository Tests

Repository tests verify persistence behavior.

Typical file:

```text
repository_test.go
```

When the behavior depends on actual GORM/database semantics, use a real isolated test database.

SQLite in-memory is appropriate when compatible with the persistence behavior being tested.

Example setup:

```go
var (
	db   *gorm.DB
	repo *Repository
)

BeforeEach(func() {
	var err error

	db, err = gorm.Open(
		sqlite.Open(":memory:"),
		&gorm.Config{},
	)
	Expect(err).NotTo(HaveOccurred())

	err = db.AutoMigrate(&Entity{})
	Expect(err).NotTo(HaveOccurred())

	repo = &Repository{
		RepositoryImpl: base.RepositoryImpl[Entity]{
			Conn: db,
		},
	}
})
```

If the project exposes a Repository constructor, use the established constructor instead.

---

# Repository BDD Structure

Repository tests should typically follow:

```text
Describe Repository
  -> Given persisted or persistable state
      -> When saving
          -> It ...
      -> When updating
          -> It ...
      -> When finding by id
          -> It ...
      -> When executing custom lookup
          -> It ...
      -> When paginating
          -> It ...
      -> When deleting
          -> It ...
```

Example:

```go
Describe("Given an entity", func() {
	var entity Entity

	BeforeEach(func() {
		entity = Entity{}
	})

	When("save the entity", func() {
		var (
			saved *Entity
			err   error
		)

		BeforeEach(func() {
			saved, err = repository.SaveContext(
				context.Background(),
				entity,
			)
		})

		It("should return no error", func() {
			Expect(err).NotTo(HaveOccurred())
		})

		It("should assign an id", func() {
			Expect(saved.ID).NotTo(BeZero())
		})
	})
})
```

---

# Repository Database Isolation

Each Repository scenario must start from predictable persistence state.

Use the mechanism appropriate to the project, such as:

```go
BeforeEach(func() {
	db.Exec("DELETE FROM entities")
})
```

or recreate the in-memory database between scenarios.

Tests must not depend on execution order.

When multiple tables are involved, reset all state required by the scenario.

---

# Base Repository Tests

When testing the shared generic Repository itself, verify the generic behavior directly.

Typical scenarios include:

```text
Given an entity
  When saving the entity
    It should persist the entity
    It should assign generated fields

  When updating the entity
    It should preserve identity
    It should persist changes

  When finding the entity by id
    It should return the entity
    It should return not found for missing entity

  When finding one entity by condition
    It should return the matching entity

  When finding entities with pagination
    It should respect page size
    It should fill pagination metadata

  When deleting the entity
    It should remove the entity
```

Module Repository tests should focus mainly on custom persistence behavior added by that module instead of repeating every generic base Repository scenario.

---

# Custom Repository Queries

For each custom Repository method, construct scenarios from its persistence behavior.

Example:

```go
Describe("Given stored customers", func() {
	When("finding a customer by document", func() {
		var (
			result *Customer
			err    error
		)

		BeforeEach(func() {
			// persist required state

			result, err = repository.FindByDocument(
				context.Background(),
				document,
			)
		})

		It("should return no error", func() {
			Expect(err).NotTo(HaveOccurred())
		})

		It("should return the matching customer", func() {
			Expect(result.Document).To(Equal(document))
		})
	})
})
```

Test the observable persistence behavior rather than GORM implementation details.

---

# Service Tests

Service tests verify business behavior.

Typical file:

```text
service_test.go
```

Use fake Repository dependencies rather than a database when persistence behavior itself is not under test.

Typical hierarchy:

```text
Describe Service
  -> Given some domain state
      -> When business operation occurs
          -> It should ...
          -> It should ...
```

Example:

```go
Describe("Given a customer document that already exists", func() {
	var (
		repository *fakeRepository
		service    *Service
		result     *Customer
		err        error
	)

	BeforeEach(func() {
		repository = &fakeRepository{
			existing: &Customer{
				Document: "123",
			},
		}

		service = &Service{
			Repository: repository,
		}
	})

	When("creating the customer", func() {
		BeforeEach(func() {
			result, err = service.CreateCustomer(
				context.Background(),
				Customer{
					Document: "123",
				},
			)
		})

		It("should return an error", func() {
			Expect(err).To(HaveOccurred())
		})

		It("should not return a customer", func() {
			Expect(result).To(BeNil())
		})

		It("should not persist the customer", func() {
			Expect(repository.saveCalls).To(Equal(0))
		})
	})
})
```

---

# Service Fakes

Create small fake Repository implementations that expose only what the scenarios require.

Example:

```go
type fakeRepository struct {
	existing  *Entity
	result    *Entity
	err       error
	saveCalls int
}

func (f *fakeRepository) FindByDocument(
	ctx context.Context,
	document string,
) (*Entity, error) {
	return f.existing, f.err
}

func (f *fakeRepository) SaveContext(
	ctx context.Context,
	entity Entity,
) (*Entity, error) {
	f.saveCalls++

	if f.err != nil {
		return nil, f.err
	}

	if f.result != nil {
		return f.result, nil
	}

	return &entity, nil
}
```

Do not reproduce production Repository behavior inside a fake.

---

# Service Scenario Organization

Organize scenarios around business state.

Prefer:

```go
Describe("Given a duplicated document", ...)
```

followed by:

```go
When("creating the customer", ...)
```

instead of:

```go
Describe("CreateCustomer method", ...)
```

The behavior and business context should be visible from the hierarchy.

---

# Component Tests

Component tests verify application orchestration.

Typical file:

```text
component_test.go
```

Use fake Services, Validators, and other Component dependencies.

Typical hierarchy:

```text
Describe Component
  -> Given application dependencies
      -> When executing workflow
          -> It should call required dependency
          -> It should pass expected data
          -> It should return mapped result
```

Example:

```go
Describe("Given an existing parent entity", func() {
	var (
		parentService *fakeParentService
		entityService *fakeEntityService
		component     *Component
		result        *EntityResponseDto
		err           error
	)

	BeforeEach(func() {
		parentService = &fakeParentService{
			result: &Parent{},
		}

		entityService = &fakeEntityService{}

		component = &Component{
			Service:       entityService,
			ParentService: parentService,
			Mapper:        Mapper{},
		}
	})

	When("creating the child entity", func() {
		BeforeEach(func() {
			result, err = component.Create(
				context.Background(),
				parentID,
				input,
			)
		})

		It("should return no error", func() {
			Expect(err).NotTo(HaveOccurred())
		})

		It("should resolve the parent", func() {
			Expect(parentService.calls).To(Equal(1))
		})

		It("should create the child entity", func() {
			Expect(entityService.createCalls).To(Equal(1))
		})
	})
})
```

---

# Component Dependency Order

When operation order matters, fakes may record a shared call sequence.

Example:

```go
calls := []string{}
```

Dependencies may append:

```go
calls = append(calls, "parent")
```

and:

```go
calls = append(calls, "child")
```

Then assert:

```go
Expect(calls).To(Equal([]string{
	"parent",
	"child",
}))
```

Only assert ordering when ordering itself belongs to the workflow contract.

---

# Controller Tests

Controller tests verify HTTP behavior.

Typical file:

```text
controller_test.go
```

or:

```text
route_test.go
```

according to project convention.

Use:

```go
gin.New()
httptest.NewRequest(...)
httptest.NewRecorder()
```

with a fake Component.

Typical hierarchy:

```text
Describe Controller
  -> Given an HTTP request
      -> When request is valid
          -> It should call the Component
          -> It should return expected status
          -> It should return expected body

      -> When request is malformed
          -> It should return bad request

      -> When Component returns an error
          -> It should return mapped error response
```

---

# Controller Setup

Example:

```go
Describe("Given the create entity endpoint", func() {
	var (
		router    *gin.Engine
		component *fakeComponent
		recorder  *httptest.ResponseRecorder
	)

	BeforeEach(func() {
		gin.SetMode(gin.TestMode)

		component = &fakeComponent{}

		controller := &ModuleController{
			component: component,
		}

		router = gin.New()
		router.POST(
			"/entities",
			controller.Create,
		)

		recorder = httptest.NewRecorder()
	})

	// ...
})
```

Use the actual route and Controller construction pattern from the project.

---

# Controller Valid Request Scenario

Example:

```go
When("sending a valid request", func() {
	BeforeEach(func() {
		request := httptest.NewRequest(
			http.MethodPost,
			"/entities",
			strings.NewReader(`{
				"name": "Example"
			}`),
		)

		request.Header.Set(
			"Content-Type",
			"application/json",
		)

		router.ServeHTTP(
			recorder,
			request,
		)
	})

	It("should return created", func() {
		Expect(recorder.Code).To(Equal(
			http.StatusCreated,
		))
	})

	It("should call the Component", func() {
		Expect(component.createCalls).To(Equal(1))
	})
})
```

---

# Controller Invalid Request Scenario

Example:

```go
When("sending malformed JSON", func() {
	BeforeEach(func() {
		request := httptest.NewRequest(
			http.MethodPost,
			"/entities",
			strings.NewReader(`{invalid`),
		)

		request.Header.Set(
			"Content-Type",
			"application/json",
		)

		router.ServeHTTP(
			recorder,
			request,
		)
	})

	It("should return bad request", func() {
		Expect(recorder.Code).To(Equal(
			http.StatusBadRequest,
		))
	})

	It("should not call the Component", func() {
		Expect(component.createCalls).To(Equal(0))
	})
})
```

---

# Mapper Tests

Create Mapper tests when mapping contains behavior worth protecting or when a specification explicitly defines the transformation.

Typical file:

```text
mapper_test.go
```

Mapper tests generally do not require fakes or infrastructure.

Typical hierarchy:

```text
Describe Mapper
  -> Given an input DTO
      -> When converting to entity
          -> It should map field X
          -> It should map field Y

  -> Given an entity
      -> When converting to response DTO
          -> It should map expected representation
```

Example:

```go
Describe("Given a save DTO", func() {
	var (
		input  SaveEntityDto
		result Entity
	)

	BeforeEach(func() {
		input = SaveEntityDto{
			Name: "Example",
		}
	})

	When("mapping to entity", func() {
		BeforeEach(func() {
			result = Mapper{}.EntityFromDto(input)
		})

		It("should map the name", func() {
			Expect(result.Name).To(Equal(input.Name))
		})
	})
})
```

Do not create Mapper tests solely to assert trivial assignments across every module unless required by the project.

---

# Entity Tests

Entities generally do not need standalone tests when they contain only fields and persistence metadata.

Create `entity_test.go` only when the Entity contains observable behavior such as:

```text
domain methods
state-transition helpers
computed behavior
custom conversion behavior
```

Do not write tests merely to assert that struct fields exist.

---

# DTO Tests

DTOs generally do not require standalone unit tests when they only define fields and transport tags.

DTO behavior is normally exercised through Controller binding tests.

Create direct DTO tests only when the DTO has actual custom behavior supported by the project.

---

# One Behavior Per It

Each `It` should express one expectation.

Prefer:

```go
It("should return no error", ...)
It("should return the entity", ...)
It("should assign an id", ...)
```

instead of:

```go
It("should work", func() {
	Expect(err).NotTo(HaveOccurred())
	Expect(result).NotTo(BeNil())
	Expect(result.ID).NotTo(BeZero())
	Expect(result.CreatedAt).NotTo(BeZero())
})
```

Multiple closely related assertions may remain in the same `It` when they together represent a single meaningful outcome.

Example:

```go
It("should return the persisted entity", func() {
	Expect(result).NotTo(BeNil())
	Expect(result.ID).NotTo(BeZero())
})
```

---

# Nested Scenarios

Use nested `When` blocks for meaningful variations of the current scenario.

Example:

```go
When("finding entities with pagination", func() {
	// first page

	When("requesting the second page", func() {
		// second page expectations
	})

	When("searching by document", func() {
		// search expectations
	})
})
```

Use nesting when it makes the behavior hierarchy easier to understand.

Avoid excessive nesting that makes the test difficult to follow.

---

# Failure Short-Circuiting

When setup inside `BeforeEach` depends on a previous operation, prefer immediate Gomega assertions when failure makes subsequent setup meaningless.

Example:

```go
saved, err = repository.SaveContext(
	context.Background(),
	entity,
)

Expect(err).NotTo(HaveOccurred())
```

This prevents later setup from continuing with invalid state.

Avoid patterns such as:

```go
if err != nil {
	return
}
```

when the error itself represents failed test setup.

---

# Test Data

Keep scenario data explicit and close to the behavior.

Example:

```go
entity = Entity{
	Name: "Example",
}
```

Use helper factories only when repeated setup becomes substantial.

Avoid hiding the Given state behind generic builders when a direct struct literal is clearer.

---

# Database Tests

Use a real database or in-memory database for tests whose subject is persistence behavior.

Examples:

```text
Repository queries
GORM mappings
constraints
foreign keys
transactions
pagination queries
custom joins
```

Prefer SQLite in-memory only when its behavior is compatible with what the scenario needs to demonstrate.

When database-specific behavior matters, use the appropriate test database strategy already established by the project.

---

# Fake-Based Tests

Use fake dependencies for:

```text
Service
Component
Controller
```

when the dependency's internal behavior is not the subject of the scenario.

Typical dependency strategy:

```text
Repository test
-> real persistence

Service test
-> fake Repository

Component test
-> fake Services / Validators

Controller test
-> fake Component
```

This is the default layer-isolation strategy.

---

# Test Isolation

Each scenario must be independent.

Avoid reliance on:

```text
spec execution order
shared mutable global state
production singleton state
external network
state left by another It
uncontrolled database contents
```

Use `BeforeEach` to establish the required state for every scenario.

Use `AfterEach` when cleanup is required.

---

# Production Singletons

Do not obtain production singleton instances in unit tests when dependencies can be constructed directly.

Avoid:

```go
service := GetInstance()
```

for isolated Service tests.

Prefer:

```go
service := &Service{
	Repository: fakeRepository,
}
```

Likewise, construct Components and Controllers directly using fake dependencies.

---

# Suite Organization

Follow the project's existing Ginkgo suite organization.

A project may use a dedicated suite file:

```text
service_suite_test.go
service_test.go
```

with:

```go
func TestService(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Service Suite")
}
```

and specifications declared separately:

```go
var _ = Describe("Service", func() {
	// ...
})
```

Alternatively, if the project already registers `Describe` blocks before `RunSpecs` in the same test entry file, preserve that convention.

Do not introduce multiple competing suite styles inside the same package.

---

# Existing Tests

When modifying a package that already uses Ginkgo/Gomega:

* preserve its suite organization;
* preserve existing `Describe`, `Given`, `When`, and `It` structure;
* add new scenarios into the closest appropriate context;
* reuse existing fakes and setup where appropriate;
* avoid rewriting unrelated specifications.

Do not convert existing valid Ginkgo tests into plain `testing` tests.

---

# Missing Information

When expected behavior cannot be determined, do not invent a scenario.

Examples:

* expected result is unclear;
* expected error behavior is undefined;
* business state transition is incomplete;
* required orchestration order cannot be determined;
* HTTP response contract is unavailable;
* persistence semantics are ambiguous.

State which expected behavior is missing or conflicting.

---

## Review Evidence (For Reviewer Agents Only)

When reporting a test issue, identify:

```text
requirement
-> test file
-> Describe/Given/When/It path
-> observed gap
-> behavior not demonstrated or incorrectly demonstrated
-> expected correction
```

Example:

```text
Requirement:

A duplicated document must prevent persistence.

Test:

service_test.go

Scenario:

Given a duplicated document
-> When creating the customer
-> It should return an error

Observed:

The suite asserts the returned error but never verifies whether persistence was attempted.

Impact:

The scenario does not demonstrate the requirement that persistence must stop after the business rule fails.

Expected:

Add a specification asserting that the fake Repository received no save call.
```

Findings must be tied to required behavior.

Do not report a finding merely because another Ginkgo organization or Gomega matcher could have been used.

---

## BDD Structure Review (For Reviewer Agents Only)

Confirm that tests use the project's Ginkgo/Gomega BDD structure.

Inspect whether behavior is expressed through:

```text
Describe
Given
When
It
```

or the equivalent hierarchy already established by the package.

Check that:

* `Given` describes state;
* `When` describes an operation or event;
* `It` describes an observable expectation;
* setup shared by specifications is placed appropriately;
* multiple outcomes of one operation are expressed clearly.

Do not require literal `Given` when an existing `Context` or equivalent Ginkgo construct communicates the same intent and follows project convention.

---

## Layer Strategy Review (For Reviewer Agents Only)

Confirm that test infrastructure matches the subject under test.

Expected default:

```text
Repository
-> real isolated persistence

Service
-> fake Repository

Component
-> fake Services / collaborators

Controller
-> Gin/HTTP test infrastructure + fake Component
```

Report unnecessary cross-layer integration when it obscures the behavior under test or introduces avoidable infrastructure dependencies.

---

## Scenario Coverage Review (For Reviewer Agents Only)

Map requirements to specifications.

Example:

```text
Requirement
-> Given ...
   -> When ...
      -> It ...
      -> It ...
```

Identify required behavior with no corresponding specification.

Do not require speculative scenarios that are not supported by the task or existing contract.

---

## Assertion Review (For Reviewer Agents Only)

Map each `It` description to its assertions.

Example:

```text
It should return no error
-> Expect(err).NotTo(HaveOccurred())

It should not persist the entity
-> Expect(repository.saveCalls).To(Equal(0))

It should return created
-> Expect(recorder.Code).To(Equal(http.StatusCreated)
```

Confirm that the matcher actually demonstrates the behavior named by the specification.

Do not require unrelated assertions.

---

## Setup Review (For Reviewer Agents Only)

Inspect `BeforeEach`, `JustBeforeEach`, and `AfterEach` usage.

Check for:

```text
state leaking between specifications
database records not reset
shared fake call counters not reset
setup errors silently ignored
test data mutated by previous It blocks
```

Each `It` must be independently executable.

---

## Fake Review (For Reviewer Agents Only)

Confirm that fakes:

* implement only the behavior required by the scenario;
* expose configurable return values and errors;
* record relevant calls and arguments;
* remain deterministic;
* do not replicate production business rules.

A fake should provide control and observation, not become another implementation of the production dependency.

---

## Repository Test Review (For Reviewer Agents Only)

When reviewing Repository specifications, inspect:

```text
database setup
schema creation
test data cleanup
query execution
returned entity/entities
persistence errors
```

Confirm that custom Repository behavior is exercised against actual persistence when required.

Avoid demanding duplicate tests for generic inherited Repository operations in every domain module.

---

## Service Test Review (For Reviewer Agents Only)

For Service specifications, map:

```text
Given domain state
-> fake Repository behavior
-> When Service operation executes
-> It business outcome
```

Confirm that business behavior is tested independently of a real database when persistence itself is not the subject.

---

## Component Test Review (For Reviewer Agents Only)

For Component specifications, map:

```text
Given dependencies
-> When application workflow executes
-> Service calls
-> Mapper/result
-> It orchestration outcome
```

Confirm that dependencies are faked and that the test focuses on orchestration.

---

## Controller Test Review (For Reviewer Agents Only)

For Controller specifications, map:

```text
Given HTTP request
-> When request is served
-> Controller binding/extraction
-> fake Component
-> HTTP response
```

Confirm that scenarios cover the HTTP behavior required by the contract.

---

## Verification (For Reviewer Agents Only)

Run the Ginkgo-compatible test commands established by the project.

Typical Go execution:

```bash
go test ./...
```

If the project uses the Ginkgo CLI, the repository may instead define commands such as:

```bash
ginkgo ./...
```

Use the command established by the repository instructions.

For focused verification, execute the affected package or suite.

Confirm that:

```text
new specifications pass
existing specifications still pass
specifications are isolated
repeated execution remains deterministic
```

Passing tests do not prove that all required behaviors have specifications.

Review scenario coverage separately.

---

# Output

When creating tests, produce the complete resulting test file or files required by the task.

Possible outputs include:

```text
repository_test.go
repository_suite_test.go

service_test.go
service_suite_test.go

component_test.go
component_suite_test.go

controller_test.go
controller_suite_test.go
```

Follow the suite/file organization already established by the project.

When the module consolidates component coverage into one file, keep the Ginkgo suite runner (`RunSpecs`) inside `component_test.go` rather than a separate `component_suite_test.go`.

Do not include unrelated production files unless explicitly requested.

---

# Execution Summary

For Repository tests:

```text
Persistence requirement
        ↓
Real isolated database
        ↓
Describe
  -> Given persisted state
      -> When Repository operation
          -> It persistence outcome
```

For Service tests:

```text
Business requirement
        ↓
Fake Repository
        ↓
Describe
  -> Given domain state
      -> When Service operation
          -> It business outcome
```

For Component tests:

```text
Application workflow
        ↓
Fake Services / collaborators
        ↓
Describe
  -> Given application state
      -> When Component operation
          -> It orchestration outcome
```

For Controller tests:

```text
HTTP contract
        ↓
Gin + httptest + fake Component
        ↓
Describe
  -> Given HTTP request
      -> When endpoint executes
          -> It HTTP outcome
```

Use Ginkgo to describe behavior and Gomega to express expectations.
