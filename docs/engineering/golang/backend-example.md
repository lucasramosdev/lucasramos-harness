# Backend Architecture Examples

> **Status:** Reference Examples
> **Companion to:** `backend-style.md`
> **Scope:** Backend modules, DTOs, repositories, services, components, routes, tests, and migrations.
> **Purpose:** Provide small, copyable examples that demonstrate the conventions defined by the backend source of truth.

---

## 1. How to Use This File

This document is **illustrative**, not the primary source of architectural rules.

Use it together with:

```text
backend-style.md
```

The style guide defines **what must be followed**.

This file demonstrates **how those rules usually look in code**.

When implementing a real task:

1. read the specification;
2. read `backend-style.md`;
3. inspect the target module;
4. use the closest existing module as the primary local reference;
5. use this file as a fallback example;
6. adapt names and dependencies to the real domain.

Do not copy examples mechanically when the target module already has a more specific established pattern.

---

# 2. Example Module Layout

A typical backend module may follow this structure:

```text
projects/backend/internal/domain/module/
  entity.go
  repository.go
  service.go
  component.go
  mapper.go
  module_suite_test.go
  repository_test.go
  service_test.go
  component_test.go
projects/backend/internal/dtos/module/
  save_entity_dto.go
  entity_response_dto.go
projects/backend/internal/web/routes/
  module.go
```

The expected dependency flow is:

```text
Route
  -> Component
    -> Mapper
    -> Service
      -> Repository
        -> Database
```

For cross-domain orchestration:

```text
Route
  -> Component
    -> Local Service
    -> External Domain Service
```

Avoid bypassing layers without an established reason.

---

# 3. Entity Example

```go
package module
import "project-backend/internal/infra/base"
type Entity struct {
    base.BaseEntity
    UniqueField string `gorm:"column:unique_field;not null"`
    Name        string `gorm:"column:name;not null"`
    TenantID    string `gorm:"column:tenant_id;not null"`
}
func (Entity) TableName() string {
    return "entities"
}
```

## What this example demonstrates

- The entity represents persistence/domain state.
- Shared entity fields come from `base.BaseEntity`.
- GORM configuration remains attached to the entity when that is the existing project convention.
- Transport-specific JSON bindings do not belong in the domain entity.
- Persistence identity such as `TenantID` may exist in the entity even when it must not be accepted directly from the HTTP payload.

---

# 4. DTO Examples

## 4.1 Input DTO

```go
package moduleDto
type SaveEntityDto struct {
    UniqueField string `json:"unique_field" binding:"required"`
    Name        string `json:"name" binding:"required"`
}
```

## 4.2 Response DTO

```go
package moduleDto
type EntityResponseDto struct {
    ID          string `json:"id"`
    UniqueField string `json:"unique_field"`
    Name        string `json:"name"`
}
```

## DTO rules demonstrated

DTOs are responsible for the HTTP/application boundary representation.

Use DTOs for:

- JSON field names;
- request binding;
- transport-level required fields;
- response shape.

Do not place trusted identity fields in request DTOs when those values must come from authenticated claims.

Examples:

```text
user_id
tenant_id
role
```

If those values are security-sensitive, obtain them from the authenticated request context instead of trusting client input.

---

# 5. Repository Example

```go
package module
import (
    "context"
    "gorm.io/gorm"
    "project-backend/internal/infra/base"
)
type RepositoryInterface interface {
    base.Repository[Entity]
    FindByUniqueField(
        ctx context.Context,
        tenantID string,
        uniqueField string,
    ) (*Entity, error)
}
type Repository struct {
    base.RepositoryImpl[Entity]
}
func (r *Repository) FindByUniqueField(
    ctx context.Context,
    tenantID string,
    uniqueField string,
) (*Entity, error) {
    result, err := gorm.G[Entity](r.Conn).
        Where(
            "tenant_id = ? AND unique_field = ?",
            tenantID,
            uniqueField,
        ).
        First(ctx)
    if err != nil {
        return nil, err
    }
    return &result, nil
}
```

## Repository rules demonstrated

The repository:

- owns GORM usage;
- owns persistence queries;
- receives `context.Context`;
- does not import HTTP DTOs;
- does not know Gin;
- does not return HTTP status codes;
- does not perform cross-domain orchestration;
- does not validate ownership by calling another domain's repository directly.

A repository may expose module-specific queries in addition to the generic base repository operations.

---

# 6. Service Example

```go
package module
import (
    "context"
    "project-backend/internal/api_errors"
    "project-backend/internal/infra/base"
    "project-backend/internal/infra/database"
)
type Service struct {
    base.Service[Entity]
    Repository RepositoryInterface
}
var entityService *Service
func GetInstance() *Service {
    if entityService == nil {
        repository := Repository{
            RepositoryImpl: base.RepositoryImpl[Entity]{
                Conn: database.Conn,
            },
        }
        entityService = &Service{
            Service: base.Service[Entity]{
                Repository: &repository,
                EntityName: "entity",
            },
            Repository: &repository,
        }
    }
    return entityService
}
func (s *Service) CreateEntity(
    ctx context.Context,
    actor ActorContext,
    entity Entity,
) (*Entity, error) {
    existing, err := s.Repository.FindByUniqueField(
        ctx,
        actor.TenantID,
        entity.UniqueField,
    )
    if err == nil && existing != nil {
        return nil, api_errors.NewDatabaseError(
            "Já existe uma entidade com esse identificador.",
        )
    }
    entity.TenantID = actor.TenantID
    created, err := s.Repository.Create(ctx, entity)
    if err != nil {
        return nil, api_errors.NewDatabaseError(
            "Erro ao criar entidade.",
        )
    }
    return created, nil
}
```

> Adapt the exact base repository method signatures to the repository implementation that exists in the codebase. Do not change generic base APIs merely to match this example.

## Service rules demonstrated

The service:

- owns business rules;
- owns domain-level decisions;
- may query repository state before persisting;
- translates persistence failures according to the project's API error convention;
- receives trusted application/domain context explicitly;
- does not know Gin;
- does not bind HTTP requests;
- does not return HTTP status codes;
- normally does not receive HTTP DTOs.

Production construction uses the established singleton-style instance getter and wires the concrete repository with `database.Conn`.

For tests, instantiate the service directly with fake dependencies instead of relying on the singleton.

---

# 7. Mapper Example

```go
package module
import moduleDto "project-backend/internal/dtos/module"
type Mapper struct{}
func (Mapper) EntityFromDto(
    input moduleDto.SaveEntityDto,
) Entity {
    return Entity{
        UniqueField: input.UniqueField,
        Name:        input.Name,
    }
}
func (Mapper) EntityToResponse(
    entity Entity,
) moduleDto.EntityResponseDto {
    return moduleDto.EntityResponseDto{
        ID:          entity.GetIDAsString(),
        UniqueField: entity.UniqueField,
        Name:        entity.Name,
    }
}
```

## Mapper rules demonstrated

The mapper owns representation conversion.

Typical responsibilities:

```text
DTO -> Domain Entity
Domain Entity -> Response DTO
```

The mapper must not:

- validate business rules;
- query repositories;
- call services;
- authorize actions;
- perform persistence;
- depend on Gin.

Keep mappers deterministic whenever possible.

---

# 8. Component Example

```go
package module
import (
    moduleDto "project-backend/internal/dtos/module"
)
type EntityService interface {
    CreateEntity(
        ctx context.Context,
        actor ActorContext,
        entity Entity,
    ) (*Entity, error)
}
type Component struct {
    Service EntityService
    Mapper  Mapper
}
var entityComponent *Component
func GetComponentInstance() *Component {
    if entityComponent == nil {
        entityComponent = &Component{
            Service: GetInstance(),
            Mapper:  Mapper{},
        }
    }
    return entityComponent
}
func (c *Component) Create(
    ctx context.Context,
    actor ActorContext,
    input moduleDto.SaveEntityDto,
) (*moduleDto.EntityResponseDto, error) {
    entity := c.Mapper.EntityFromDto(input)
    created, err := c.Service.CreateEntity(
        ctx,
        actor,
        entity,
    )
    if err != nil {
        return nil, err
    }
    response := c.Mapper.EntityToResponse(*created)
    return &response, nil
}
```

## Component rules demonstrated

The component is the route-facing application orchestration layer.

Typical responsibilities:

- DTO/domain conversion orchestration;
- coordinating one or more services;
- cross-domain service calls;
- assembling the final response DTO;
- keeping route handlers thin.

A Component may depend on small interfaces so it can be tested with fakes.

The Component should not own persistence queries directly.

---

# 9. Component With Multiple Dependencies

A more realistic Component may coordinate several services and helper abstractions.

```go
type Component struct {
    Service                 ChecklistService
    TruckService            trucks.TruckService
    ObligationService       obligations.ObligationService
    FileAttachmentValidator FileAttachmentValidator
    Mapper                  Mapper
}
var checklistComponent *Component
func GetComponentInstance() *Component {
    if checklistComponent == nil {
        checklistComponent = &Component{
            Service:                 GetInstance(),
            TruckService:            trucks.GetInstance(),
            ObligationService:       obligations.GetInstance(),
            FileAttachmentValidator: files.GetInstance(),
            Mapper:                  Mapper{},
        }
    }
    return checklistComponent
}
```

## Important

Production wiring should use the established constructor/instance getter exposed by each dependency.

Do not create an alternative construction path for another domain unless that domain's public API requires it.

Tests should instantiate the Component directly:

```go
component := &Component{
    Service:                 fakeChecklistService,
    TruckService:            fakeTruckService,
    ObligationService:       fakeObligationService,
    FileAttachmentValidator: fakeFileValidator,
    Mapper:                  Mapper{},
}
```

This prevents tests from depending on production singleton state.

---

# 10. Route Example

```go
package routes
import (
    "net/http"
    "github.com/gin-gonic/gin"
    "project-backend/internal/api_errors"
    "project-backend/internal/domain/module"
    moduleDto "project-backend/internal/dtos/module"
)
type ModuleController struct {
    entityComponent *module.Component
}
func registerModule(router *gin.RouterGroup) {
    group := router.Group("/entities")
    controller := &ModuleController{
        entityComponent: module.GetComponentInstance(),
    }
    group.POST("", controller.Create)
}
func (controller *ModuleController) Create(
    ginContext *gin.Context,
) {
    var input moduleDto.SaveEntityDto
    if err := ginContext.ShouldBindJSON(&input); err != nil {
        ginContext.JSON(http.StatusBadRequest, gin.H{
            "error":   "bad_request",
            "message": "Payload inválido.",
        })
        return
    }
    actor := module.ActorContext{
        UserID:   getUserIDFromClaims(ginContext),
        TenantID: getTenantIDFromClaims(ginContext),
        Role:     getRoleFromClaims(ginContext),
    }
    response, err := controller.entityComponent.Create(
        ginContext.Request.Context(),
        actor,
        input,
    )
    if err != nil {
        api_errors.DefaultErrorTreatment(
            ginContext,
            err,
        )
        return
    }
    ginContext.JSON(
        http.StatusCreated,
        response,
    )
}
```

## Route rules demonstrated

The route:

- binds HTTP DTOs;
- extracts trusted authenticated claims;
- builds the application/domain actor context;
- invokes the Component;
- delegates service/component errors to `DefaultErrorTreatment`;
- returns the HTTP response.

The route must not:

- map DTOs to entities manually when the module has a Mapper;
- call repositories;
- implement domain business rules;
- trust client-provided identity fields when claims are authoritative.

---

# 11. Trusted Actor Context Example

A useful application/domain context may look like:

```go
type ActorContext struct {
    UserID   string
    TenantID string
    Role     string
}
```

This object should contain trusted identity/context values derived from authentication or application infrastructure.

It is not an HTTP DTO.

Example flow:

```text
Authenticated claims
  -> Route
    -> ActorContext
      -> Component
        -> Service
```

Do not construct trusted identity from user-controlled request fields.

---

# 12. Cross-Domain Component Example

## Scenario

A sub-workflow belongs to a parent entity.

Before creating the subentity, the application must ensure that:

1. the parent exists;
2. the parent is accessible to the current actor;
3. the subentity is created using the validated parent.

The Component should orchestrate that interaction through the parent domain's Service.

## Correct dependency flow

```text
submodule.Controller
  -> submodule.Component
    -> parentmodule.Service.GetEntityByID(...)
    -> submodule.Mapper.EntityFromDto(...)
    -> submodule.Service.CreateSubEntity(...)
      -> submodule.Repository
```

## Example

```go
package submodule
import (
    "context"
    "project-backend/internal/domain/parentmodule"
    submoduleDto "project-backend/internal/dtos/submodule"
)
type SubEntityService interface {
    CreateSubEntity(
        ctx context.Context,
        actor ActorContext,
        parent parentmodule.Entity,
        subEntity SubEntity,
    ) (*SubEntity, error)
}
type ParentService interface {
    GetEntityByID(
        ctx context.Context,
        actor parentmodule.ActorContext,
        id string,
    ) (*parentmodule.Entity, error)
}
type Component struct {
    Service       SubEntityService
    ParentService ParentService
    Mapper        Mapper
}
func (c *Component) Create(
    ctx context.Context,
    actor ActorContext,
    parentID string,
    input submoduleDto.SaveSubEntityDto,
) (*submoduleDto.SubEntityResponseDto, error) {
    parentActor := parentmodule.ActorContext{
        UserID:   actor.UserID,
        TenantID: actor.TenantID,
        Role:     actor.Role,
    }
    parentEntity, err := c.ParentService.GetEntityByID(
        ctx,
        parentActor,
        parentID,
    )
    if err != nil {
        return nil, err
    }
    subEntity := c.Mapper.EntityFromDto(input)
    created, err := c.Service.CreateSubEntity(
        ctx,
        actor,
        *parentEntity,
        subEntity,
    )
    if err != nil {
        return nil, err
    }
    response := c.Mapper.EntityToResponse(*created)
    return &response, nil
}
```

## Why this is correct

The submodule Component coordinates application behavior across domain boundaries without bypassing the parent domain's business rules.

The parent domain remains responsible for how its entity is loaded and validated.

---

# 13. Incorrect Cross-Domain Repository Access

Avoid this:

```go
func (r *Repository) CreateSubEntityForParent(
    parentID string,
    subEntity SubEntity,
) (*SubEntity, error) {
    var parent parentmodule.Entity
    r.Conn.First(
        &parent,
        "id = ?",
        parentID,
    )
    // ...
}
```

The submodule repository should not directly query another domain's entity merely to perform application-level validation.

Prefer:

```text
submodule.Component
  -> parentmodule.Service
  -> submodule.Service
  -> submodule.Repository
```

---

# 14. Subentity Example

## Suggested structure

```text
internal/domain/parentmodule/
  component.go
  service.go
  repository.go
  mapper.go
internal/domain/parentmodule/submodule/
  component.go
  service.go
  repository.go
  mapper.go
```

## Normal subentity flow

```text
submodule.Controller
  -> submodule.Component
    -> submodule.Mapper
    -> submodule.Service
      -> submodule.Repository
```

## With parent validation

```text
submodule.Controller
  -> submodule.Component
    -> parentmodule.Service.GetEntityByID(...)
    -> submodule.Mapper
    -> submodule.Service
      -> submodule.Repository
```

## Avoid

```text
submodule.Controller -> parentmodule.Component
submodule.Service -> parentmodule.Repository
submodule.Repository -> parentmodule.Repository
parentmodule.Service -> submodule business rules
```

A domain should expose business behavior through its Service rather than allowing unrelated modules to reach directly into its Repository.

---

# 15. Testing Convention — Ginkgo v2 + Gomega

Backend tests use BDD with:

```go
. "github.com/onsi/ginkgo/v2"
. "github.com/onsi/gomega"
```

Use Go's standard `testing` package only to bootstrap the Ginkgo suite.

A package should normally register its suite once:

```go
func TestModule(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "Module Suite")
}
```

Specifications should express behavior through:

```text
Describe("Given ...")
  -> When("...")
      -> It("should ...")
```

Use `BeforeEach` to prepare the state shared by specifications inside the current context.

When several `It` blocks assert different outcomes of the same operation, execute that operation in the surrounding `BeforeEach`.

Prefer Gomega matchers:

```go
Expect(err).NotTo(HaveOccurred())
Expect(result).NotTo(BeNil())
Expect(result.ID).NotTo(BeZero())
Expect(items).To(HaveLen(2))
Expect(err).To(MatchError(expectedErr))
```

Do not create new tests using plain `t.Run` scenarios when Ginkgo/Gomega are the established project testing stack.

The default testing strategy by layer is:

```text
Repository
  -> Ginkgo + Gomega
  -> real isolated persistence when persistence behavior is under test
Service
  -> Ginkgo + Gomega
  -> fake Repository
Component
  -> Ginkgo + Gomega
  -> fake Services / Validators / collaborators
Controller / Route
  -> Ginkgo + Gomega
  -> httptest + fake Component
Mapper
  -> Ginkgo + Gomega when mapping behavior requires dedicated coverage
Entity / DTO
  -> normally no dedicated test unless they contain actual behavior
```

For Repository persistence tests, SQLite in-memory may be used when its behavior is compatible with what the specification needs to demonstrate.

Example:

```go
var _ = Describe("Given an entity", func() {
    var (
        db         *gorm.DB
        repository *Repository
        entity     Entity
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
        repository = &Repository{
            RepositoryImpl: base.RepositoryImpl[Entity]{
                Conn: db,
            },
        }
        entity = Entity{}
    })
    When("saving the entity", func() {
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
        It("should return the persisted entity", func() {
            Expect(saved).NotTo(BeNil())
            Expect(saved.ID).NotTo(BeZero())
        })
    })
})
```

Repository tests should focus on persistence behavior. Module repositories should not repeat every inherited base Repository scenario unless the inherited behavior itself is the subject of the task.

## Service Test Example With Fake Repository

Service tests should validate business behavior without depending on production singleton state or a real database.

```go
var _ = Describe("Given an entity with a duplicated unique field", func() {
    var (
        repository *fakeEntityRepository
        service    *Service
        actor      ActorContext
        input      Entity
    )
    BeforeEach(func() {
        repository = newFakeEntityRepository()
        repository.existingByField["tenant-1:VAL123"] = Entity{
            UniqueField: "VAL123",
            TenantID:    "tenant-1",
        }
        service = &Service{
            Repository: repository,
        }
        actor = ActorContext{
            UserID:   "user-1",
            TenantID: "tenant-1",
            Role:     "admin",
        }
        input = Entity{
            UniqueField: "VAL123",
            Name:        "Test Name",
        }
    })
    When("creating the entity", func() {
        var (
            created *Entity
            err     error
        )
        BeforeEach(func() {
            created, err = service.CreateEntity(
                context.Background(),
                actor,
                input,
            )
        })
        It("should return an error", func() {
            Expect(err).To(HaveOccurred())
        })
        It("should not return a created entity", func() {
            Expect(created).To(BeNil())
        })
        It("should not persist the entity", func() {
            Expect(repository.saveCalls).To(Equal(0))
        })
    })
})
```

## What this test demonstrates

The Service test verifies observable business behavior:

- duplicate input is rejected;
- no entity is returned;
- persistence is not attempted;
- the Repository is replaced by a fake;
- production singleton state is not required.

---

# 16. Component Test Example With Fake Services

Component tests should validate application orchestration between dependencies.

```go
var _ = Describe("Given an existing parent entity", func() {
    var (
        parentService    *fakeParentService
        subEntityService *fakeSubEntityService
        component        *Component
        actor            ActorContext
        input            submoduleDto.SaveSubEntityDto
    )
    BeforeEach(func() {
        parentService = &fakeParentService{
            entity: parentmodule.Entity{},
        }
        subEntityService = &fakeSubEntityService{}
        component = &Component{
            Service:       subEntityService,
            ParentService: parentService,
            Mapper:        Mapper{},
        }
        actor = ActorContext{
            UserID:   "user-1",
            TenantID: "tenant-1",
            Role:     "admin",
        }
        input = submoduleDto.SaveSubEntityDto{
            Name: "Check sub-item",
        }
    })
    When("creating the subentity", func() {
        var err error
        BeforeEach(func() {
            _, err = component.Create(
                context.Background(),
                actor,
                "parent-1",
                input,
            )
        })
        It("should return no error", func() {
            Expect(err).NotTo(HaveOccurred())
        })
        It("should resolve the parent through the parent Service", func() {
            Expect(parentService.receivedParentID).To(Equal("parent-1"))
        })
        It("should call the local Service once", func() {
            Expect(subEntityService.createCalls).To(Equal(1))
        })
    })
})
```

## What this test demonstrates

The Component test checks orchestration:

```text
Parent Service called
  -> parent resolved
    -> local Service called
```

The test uses fake Services and does not require a real database.

When operation order is itself part of the application contract, fakes may record a shared call sequence and the specification should assert that sequence.

---

# 17. Route / Controller Test Example With Fake Component

Controller and route tests should validate HTTP behavior using the real Gin handler boundary and a fake Component.

```go
var _ = Describe("Given the create entity endpoint", func() {
    var (
        component *fakeEntityComponent
        router    *gin.Engine
        response  *httptest.ResponseRecorder
    )
    BeforeEach(func() {
        gin.SetMode(gin.TestMode)
        component = &fakeEntityComponent{}
        controller := &ModuleController{
            entityComponent: component,
        }
        router = gin.New()
        router.Use(func(ctx *gin.Context) {
            ctx.Set("user_id", "claims-user")
            ctx.Set("tenant_id", "claims-tenant")
            ctx.Set("role", "admin")
            ctx.Next()
        })
        router.POST(
            "/entities",
            controller.Create,
        )
        response = httptest.NewRecorder()
    })
    When("sending a valid request with client supplied identity", func() {
        BeforeEach(func() {
            body := strings.NewReader(`{
                "user_id": "spoofed-user",
                "tenant_id": "spoofed-tenant",
                "unique_field": "VAL123",
                "name": "Test Name"
            }`)
            request := httptest.NewRequest(
                http.MethodPost,
                "/entities",
                body,
            )
            request.Header.Set(
                "Content-Type",
                "application/json",
            )
            router.ServeHTTP(
                response,
                request,
            )
        })
        It("should use the authenticated user identity", func() {
            Expect(component.receivedActor.UserID).To(Equal("claims-user"))
        })
        It("should use the authenticated tenant identity", func() {
            Expect(component.receivedActor.TenantID).To(Equal("claims-tenant"))
        })
        It("should call the Component once", func() {
            Expect(component.createCalls).To(Equal(1))
        })
    })
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
                response,
                request,
            )
        })
        It("should return bad request", func() {
            Expect(response.Code).To(Equal(http.StatusBadRequest))
        })
        It("should not call the Component", func() {
            Expect(component.createCalls).To(Equal(0))
        })
    })
})
```

The Controller test verifies the HTTP boundary independently from Service and Repository implementations.

The security property being tested by the first scenario is:

```text
authenticated context > client-supplied identity
```

Use the same pattern for other HTTP scenarios such as:

```text
invalid path parameter
query parameter binding
Component error mapping
successful response status/body
```

---

# 18. Bad Request Example

Malformed or invalid request binding should return HTTP `400`.

```go
if err := ginContext.ShouldBindJSON(&input); err != nil {
    ginContext.JSON(http.StatusBadRequest, gin.H{
        "error":   "bad_request",
        "message": "Payload inválido.",
    })
    return
}
```

Expected response shape:

```json
{
  "error": "bad_request",
  "message": "Payload inválido."
}
```

Preserve the project's standard `error` and `message` keys.

---

# 19. Error Treatment Example

Service and Component errors should be delegated to the centralized treatment mechanism.

```go
response, err := controller.entityComponent.Create(
    ginContext.Request.Context(),
    actor,
    input,
)
if err != nil {
    api_errors.DefaultErrorTreatment(
        ginContext,
        err,
    )
    return
}
ginContext.JSON(
    http.StatusCreated,
    response,
)
```

Avoid manually reproducing centralized error/status mapping in individual routes.

---

# 20. Migration Examples

## 20.1 Common migration

Schema and production-relevant persistence changes belong in:

```text
projects/backend/database/migrations/common
```

Example:

```text
projects/backend/database/migrations/common/20260704120000_create_entities_table.sql
```

```sql
CREATE TABLE entities (
    id VARCHAR(255) PRIMARY KEY,
    unique_field VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
CREATE UNIQUE INDEX idx_entities_tenant_unique_field
ON entities (tenant_id, unique_field);
```

The unique index protects the invariant:

```text
tenant_id + unique_field must be unique
```

This complements service-level validation and protects against concurrent writes.

## 20.2 Dev seed migration

Development-only seed data belongs in:

```text
projects/backend/database/migrations/dev
```

Example:

```text
projects/backend/database/migrations/dev/20260704121000_seed_entities.sql
```

```sql
INSERT INTO entities (
    id,
    unique_field,
    name,
    tenant_id,
    created_at,
    updated_at
)
VALUES (
    'entity-dev-1',
    'VAL123',
    'Test Entity',
    'tenant-dev-1',
    NOW(),
    NOW()
);
```

Do not create real schema in `dev` migrations.

---

# 21. End-to-End Example Flow

For a standard creation endpoint:

```text
POST /entities
  -> Route
     - bind SaveEntityDto
     - extract ActorContext from claims
  -> Component.Create
     - Mapper.EntityFromDto
  -> Service.CreateEntity
     - validate business rules
     - query Repository if needed
     - persist Entity
  -> Component
     - Mapper.EntityToResponse
  -> Route
     - HTTP 201
```

For a cross-domain subentity:

```text
POST /parents/:parentId/subentities
  -> Route
     - bind SaveSubEntityDto
     - extract ActorContext
  -> Submodule Component
     - Parent Service validates parent
     - Mapper converts DTO
     - Submodule Service executes local rule
     - Submodule Repository persists
     - Mapper converts response
  -> Route
     - HTTP response
```

---

# 22. Copying Checklist

Before copying an example from this file, verify:

### Structure

- Is this the same layer as the target code?
- Does the target module already have a better local example?
- Are package names and folders correct?

### Service

- Is production wiring using the established singleton getter?
- Is the concrete repository connected to `database.Conn`?
- Can tests inject a fake repository?

### Component

- Does it orchestrate instead of persisting directly?
- Does it depend on Services rather than foreign Repositories?
- Are its dependencies replaceable in tests?

### Route

- Is the route thin?
- Does it bind DTOs only?
- Does trusted identity come from claims?
- Does it call `DefaultErrorTreatment`?

### Repository

- Does it own only persistence behavior?
- Does it receive the request/application context?
- Does it avoid HTTP DTOs and Gin?

### Database

- Does schema work belong in `common`?
- Does local seed data belong in `dev`?
- Does the business invariant require an index or constraint?

### Tests

- Is the behavior being tested at the correct layer?
- Does the package use the established Ginkgo v2 + Gomega suite?
- Is the specification structured around `Describe("Given ...") -> When(...) -> It(...)` behavior?
- Does each `It` describe an observable expectation?
- Are Service tests using fake Repositories when persistence itself is not under test?
- Are Component tests using fake Services and collaborators?
- Are Controller/Route tests using `httptest` with a fake Component?
- Are Repository tests using isolated real persistence when persistence behavior is the subject?
- Is setup isolated through `BeforeEach` / cleanup when required?
- Are Gomega matchers used instead of manual `t.Fatal` / `t.Fatalf` assertions?

---

# 23. Example Priority

When an example in this document differs from the real codebase, use the following priority:

1. explicit task specification;
2. `backend-style.md`;
3. established pattern in the target module;
4. established repository-wide pattern;
5. this examples document.

This file must not be used to justify replacing a valid local convention with a generic example.

---

# 24. Directive for Backend Skills

Backend skills may use this document as a reusable implementation reference.

Before generating code from an example, the skill should adapt:

- entity names;
- repository contracts;
- service contracts;
- DTO names;
- actor context;
- package paths;
- error messages;
- persistence rules;
- cross-domain dependencies.

A skill must not blindly copy placeholder identifiers such as:

```text
Entity
Repository
Service
Component
module
entity_name
```

The generated code should reflect the real module and specification.

The objective of these examples is **consistency of architecture**, not textual duplication.