---

name: controller-writer
description: Create or modify a Go HTTP controller using the task specification, route contract, component API, DTOs, authentication context, and integrated backend source-of-truth context.
---

# Backend Controller Writer

## Purpose

Create or modify a backend HTTP Controller.

The target is typically located in the project's HTTP or routes package.

Example:

```text
internal/web/routes/<module>.go
```

or another controller location established by the current repository.

Adapt the location and naming to the actual project structure.

The Controller is responsible for receiving the HTTP request, translating transport input into the values expected by the application layer, invoking the corresponding Component, and returning the HTTP response.

Do not repeat or reinterpret rules already defined by the backend sources of truth.

---

## Sources of Truth

Before creating or reviewing a controller, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/golang/backend-standard.md`;
3. `docs/engineering/golang/backend-style.md`;
4. `docs/engineering/golang/backend-example.md`;
5. the specification or task contract describing the required HTTP behavior, if needed.

---

## Scope

This skill handles Controller implementation.

Typical work includes:

* creating a Controller;
* modifying an existing Controller;
* wiring the corresponding Component;
* registering HTTP handlers when registration belongs to the same file;
* binding request bodies;
* reading path parameters;
* reading query parameters;
* extracting trusted request context when required;
* invoking Component methods;
* propagating request context;
* handling binding failures;
* delegating application errors to the existing error treatment mechanism;
* returning HTTP status codes and response bodies.

Do not expand the task into Component, Service, Repository, Mapper, Entity, DTO, middleware, or migration changes unless explicitly requested.

---

# Workflow

## 1. Locate the Controller

Identify:

```text
HTTP package
controller file
route group
Controller type
Component
DTOs
route parameters
query parameters
authentication context
response contract
```

If the Controller already exists, use it as the starting point.

---

## 2. Inspect the HTTP Contract

Before implementing a handler, determine:

```text
HTTP method
route path
path parameters
query parameters
request body
response body
success status
expected error behavior
```

Use the specification and nearby routes as the primary concrete reference.

Do not infer a new API contract from the Entity or Service implementation.

---

## 3. Inspect the Component

Inspect the corresponding Component before creating the handler.

Determine:

```text
Component constructor / instance getter
method name
method parameters
input DTO
additional arguments
return type
error behavior
```

The Controller should adapt the HTTP request to the existing Component API.

Do not bypass the Component to make handler implementation shorter.

---

# Controller Structure

A Controller typically holds the corresponding Component.

Example:

```go
type ModuleController struct {
	component *module.Component
}
```

Use the naming and pointer/value convention established by the current repository.

If the project exposes a narrower Component interface for Controllers, preserve that pattern.

Do not add unrelated dependencies to the Controller.

---

# Controller Construction

When route registration constructs the Controller, use the established Component constructor or instance getter.

Example:

```go
controller := &ModuleController{
	component: module.GetComponentInstance(),
}
```

or:

```go
controller := &ModuleController{
	component: module.NewComponent(),
}
```

Use the constructor actually provided by the project.

Do not manually reconstruct the Component's Services, Mapper, Validators, or other internal dependencies inside the Controller.

---

# Route Registration

When route registration belongs to the Controller file, follow the project's established registration pattern.

Example:

```go
func registerModule(router *gin.RouterGroup) {
	group := router.Group("/entities")

	controller := &ModuleController{
		component: module.GetComponentInstance(),
	}

	group.POST("", controller.Create)
}
```

Use the actual:

```text
route prefix
HTTP methods
middleware placement
handler names
```

from the task and existing routes.

Do not introduce a new route organization style when the repository already has one.

---

# Request Body Binding

For body-based endpoints, bind into the corresponding request DTO.

Example:

```go
var input moduleDto.SaveEntityDto

if err := ginContext.ShouldBindJSON(&input); err != nil {
	ginContext.JSON(
		http.StatusBadRequest,
		gin.H{
			"error":   "bad_request",
			"message": "Payload inválido.",
		},
	)
	return
}
```

Use:

* the project's existing binding method;
* the existing error response structure;
* the established language and message convention.

Do not bind directly into the domain Entity when a request DTO exists.

---

# Path Parameters

Extract route parameters according to the current project's conventions.

Example:

```go
id := ginContext.Param("id")
```

If conversion is required:

```go
id, err := strconv.ParseUint(
	ginContext.Param("id"),
	10,
	64,
)
```

Handle conversion failures using the established request-error convention.

Do not move parameter parsing into the Component when it is strictly an HTTP representation concern.

---

# Query Parameters

Read query parameters in the Controller when they are part of the HTTP contract.

Example:

```go
search := ginContext.Query("search")
```

or:

```go
pageValue := ginContext.DefaultQuery(
	"page",
	"1",
)
```

Convert transport representations into the types expected by the Component.

Do not implement persistence filtering logic inside the Controller.

The Controller extracts values; downstream layers decide application and persistence behavior.

---

# Authenticated Request Context

When the operation requires identity or other trusted authentication information, extract it using the middleware/context mechanism already established by the current project.

Example flow:

```text
verified middleware context
-> Controller
-> application/domain context
-> Component
```

Use the existing helpers or context keys.

Do not create a second authentication extraction mechanism inside an individual Controller.

Do not use request payload fields as replacements for trusted authenticated context when the application expects verified context.

---

# Application Context Objects

When the Component expects an application/domain context object, construct it in the Controller from the trusted request context.

Example:

```go
actor := module.ActorContext{
	UserID: getUserIDFromClaims(ginContext),
	Role:   getRoleFromClaims(ginContext),
}
```

Use the actual context type and fields defined by the module.

Do not define a new actor/context type inside the Controller.

---

# Request Context Propagation

Pass the request context to the Component.

Example:

```go
response, err := controller.component.Create(
	ginContext.Request.Context(),
	input,
)
```

When additional arguments are needed:

```go
response, err := controller.component.Create(
	ginContext.Request.Context(),
	resourceID,
	input,
)
```

Do not replace the request context with:

```go
context.Background()
```

inside an HTTP handler.

---

# Component Invocation

The handler should invoke the Component corresponding to the application operation.

Typical flow:

```text
HTTP request
-> bind/extract transport input
-> obtain trusted request context if needed
-> Component
-> HTTP response
```

Example:

```go
response, err := controller.component.Create(
	ginContext.Request.Context(),
	input,
)
```

Do not call the Service directly when the module exposes a Component for the operation.

Do not call a Repository from the Controller.

---

# Error Handling

When the Component returns an application error, use the common error treatment mechanism already established by the project.

Example:

```go
response, err := controller.component.Create(
	ginContext.Request.Context(),
	input,
)

if err != nil {
	api_errors.DefaultErrorTreatment(
		ginContext,
		err,
	)
	return
}
```

Do not manually reproduce centralized application-error-to-HTTP mapping in individual handlers.

Binding or parameter parsing failures may be handled directly when they are HTTP request errors.

---

# Successful Responses

Return the status code and response body defined by the API contract.

Example creation response:

```go
ginContext.JSON(
	http.StatusCreated,
	response,
)
```

Example retrieval response:

```go
ginContext.JSON(
	http.StatusOK,
	response,
)
```

For operations without a response body:

```go
ginContext.Status(
	http.StatusNoContent,
)
```

Use the actual contract instead of choosing status codes based solely on generic REST conventions.

---

# Create Handler

A typical creation handler may look like:

```go
func (controller *ModuleController) Create(
	ginContext *gin.Context,
) {
	var input moduleDto.SaveEntityDto

	if err := ginContext.ShouldBindJSON(&input); err != nil {
		ginContext.JSON(
			http.StatusBadRequest,
			gin.H{
				"error":   "bad_request",
				"message": "Payload inválido.",
			},
		)
		return
	}

	response, err := controller.component.Create(
		ginContext.Request.Context(),
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

This is only a structural example.

Use the actual DTO, Component method, response and error conventions from the current project.

---

# Handler With Path Parameter

Example:

```go
func (controller *ModuleController) GetByID(
	ginContext *gin.Context,
) {
	id, err := strconv.ParseUint(
		ginContext.Param("id"),
		10,
		64,
	)
	if err != nil {
		ginContext.JSON(
			http.StatusBadRequest,
			gin.H{
				"error":   "bad_request",
				"message": "Identificador inválido.",
			},
		)
		return
	}

	response, err := controller.component.GetByID(
		ginContext.Request.Context(),
		id,
	)
	if err != nil {
		api_errors.DefaultErrorTreatment(
			ginContext,
			err,
		)
		return
	}

	ginContext.JSON(
		http.StatusOK,
		response,
	)
}
```

Adapt the identifier type and request-error convention to the actual API.

---

# Handler With Query Parameters

A handler may extract pagination or filtering values before calling the Component.

Example flow:

```text
query parameters
-> parse transport representation
-> Component
-> response
```

Keep the Controller limited to HTTP-level extraction and conversion.

Do not construct GORM queries, SQL conditions, or persistence filters in the handler.

---

# Controller Must Not Perform Mapping Owned by Mapper

When the module has a Mapper and Component, do not manually transform DTOs into Entities inside the Controller.

Avoid:

```go
entity := module.Entity{
	Name: input.Name,
}
```

when the existing application flow expects:

```text
Controller
-> Component
-> Mapper
```

Likewise, do not manually construct response DTOs in the Controller when the Component returns the final response representation.

---

# Controller Must Not Implement Business Rules

Do not add domain decisions to HTTP handlers.

Avoid logic such as:

```go
if input.Status == "approved" {
	// domain decision
}
```

when that decision belongs to the Service or Component.

The Controller may reject malformed transport input.

It should not decide domain behavior.

---

# Component Dependency Only

When the module exposes a Component, the Controller should normally depend on that Component rather than separately injecting:

```text
Service
Repository
Mapper
Validator
```

Those dependencies belong behind the Component boundary.

Typical:

```go
type ModuleController struct {
	component *module.Component
}
```

Avoid:

```go
type ModuleController struct {
	service    *module.Service
	repository *module.Repository
	mapper     module.Mapper
}
```

unless the project's architecture explicitly defines otherwise.

---

# Creating a New Controller

A basic Controller may begin with:

```go
package routes

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"project/internal/api_errors"
	"project/internal/domain/module"
	moduleDto "project/internal/dtos/module"
)

type ModuleController struct {
	component *module.Component
}

func registerModule(
	router *gin.RouterGroup,
) {
	group := router.Group("/entities")

	controller := &ModuleController{
		component: module.GetComponentInstance(),
	}

	group.POST(
		"",
		controller.Create,
	)
}

func (controller *ModuleController) Create(
	ginContext *gin.Context,
) {
	var input moduleDto.SaveEntityDto

	if err := ginContext.ShouldBindJSON(&input); err != nil {
		ginContext.JSON(
			http.StatusBadRequest,
			gin.H{
				"error":   "bad_request",
				"message": "Payload inválido.",
			},
		)
		return
	}

	response, err := controller.component.Create(
		ginContext.Request.Context(),
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

This is only a structural example.

Adapt:

```text
package
imports
Controller name
Component constructor
route group
HTTP method
DTO
Component method
status code
response contract
```

to the current project.

---

# Modifying an Existing Controller

When the Controller already exists:

1. preserve the established Controller structure;
2. preserve route organization;
3. preserve Component construction;
4. preserve existing request parsing conventions;
5. preserve common error treatment;
6. add only the handler behavior required by the task;
7. avoid modifying unrelated endpoints;
8. avoid changing HTTP contracts unless the task requires it.

Do not rewrite the Controller around a generic template.

---

# Missing Information

When information required to implement the HTTP endpoint is unavailable, do not invent it.

Examples:

* HTTP method is unknown;
* route path is unclear;
* request DTO cannot be determined;
* expected response shape is undefined;
* success status is unspecified and cannot be inferred from existing API conventions;
* Component method required by the endpoint does not exist;
* required path/query parameters are unclear;
* authentication context requirements cannot be determined;
* specification conflicts with the existing API contract.

State which HTTP contract information is missing or conflicting.

---

## Review Evidence (For Reviewer Agents Only)

When reporting a Controller issue, identify:

```text
requirement
-> controller file
-> route/handler
-> observed problem
-> HTTP/application consequence
-> expected correction
```

Example:

```text
Requirement:

POST /entities must use SaveEntityDto and delegate creation to the Entity Component.

Controller:

internal/web/routes/entity.go

Handler:

Create

Observed:

The handler binds the request directly into Entity and calls Service.Create.

Impact:

The HTTP layer bypasses both the DTO boundary and the Component orchestration.

Expected:

Bind SaveEntityDto and invoke the corresponding Component method.
```

Do not report a finding merely because another valid Gin or Go formulation could have been used.

Findings must be based on:

* the specification;
* backend standards;
* existing Controller conventions;
* actual Component contracts;
* concrete HTTP or application consequences.

---

## HTTP Contract Review (For Reviewer Agents Only)

For every new or modified endpoint, map:

```text
HTTP method
-> route
-> path parameters
-> query parameters
-> request body
-> Component call
-> success status
-> response body
```

Confirm that the implementation matches the required API contract.

Pay particular attention to:

```text
wrong HTTP method
wrong route
missing path parameter
incorrect parameter type conversion
missing request binding
wrong DTO
incorrect success status
incorrect response body
unexpected request fields
```

Do not substitute generic REST preferences for an explicit project contract.

---

## Controller Boundary Review (For Reviewer Agents Only)

Confirm that the Controller communicates with the application through the intended Component.

Look for:

```text
direct Service calls
direct Repository calls
direct GORM/database access
manual DTO -> Entity mapping
manual Entity -> response mapping
business rules inside handlers
cross-domain orchestration inside handlers
```

When a Component exists for the operation, these behaviors should not bypass it.

---

## Component Invocation Review (For Reviewer Agents Only)

Inspect each handler invocation:

```text
transport input
-> converted arguments
-> request context
-> Component method
-> returned result/error
```

Confirm that:

* the correct Component method is called;
* parameters are passed in the correct order;
* request context is propagated;
* required application context is supplied;
* returned errors are handled before writing a success response;
* the returned value is used according to the HTTP contract.

---

## Request Binding Review (For Reviewer Agents Only)

Inspect body, path and query extraction.

For body-based endpoints, confirm that the expected DTO is used.

For path/query parameters, confirm that transport conversion matches the Component parameter type.

Pay attention to:

```text
binding directly into Entity
ignored binding errors
ignored numeric conversion errors
wrong parameter names
default values that change the API contract
manual validation duplicating downstream business rules
```

Only HTTP representation concerns should remain in the Controller.

---

## Authentication Context Review (For Reviewer Agents Only)

When an operation requires trusted authentication context, inspect:

```text
middleware context
-> Controller extraction
-> application/domain context
-> Component
```

Confirm that the Controller uses the project's established trusted context mechanism.

Do not report authentication-related findings for endpoints that do not require such context.

---

## Error Handling Review (For Reviewer Agents Only)

Separate:

```text
transport/binding failure
Component/application failure
successful response
```

Confirm that malformed HTTP input is handled according to the project's request-error convention.

Confirm that Component errors are delegated to the existing centralized error treatment mechanism when that mechanism applies.

Look for:

```text
ignored Component errors
success responses written after an error
manual duplication of centralized application error mapping
incorrect status for malformed request input
multiple responses written from the same execution path
```

---

## Response Review (For Reviewer Agents Only)

Confirm that each successful execution path returns:

```text
expected status
expected body
expected serialization shape
```

Check that the Controller does not reconstruct a response already returned by the Component unless explicitly required by the HTTP contract.

---

## Verification (For Reviewer Agents Only)

When repository commands are available, use the backend verification commands defined by the project instructions.

Typical verification may include:

```bash
go test ./...
```

Run relevant route/controller package tests when available.

When practical, verify endpoint behavior for scenarios such as:

```text
valid request
malformed body
invalid path parameter
Component error
successful response
```

Use failures as evidence only when they relate to the Controller change.

Successful compilation alone does not prove that the HTTP contract is correct.

---

# Output

When creating a Controller, produce the complete resulting Controller or route file.

When modifying an existing Controller, return the complete resulting file unless the caller explicitly requests a diff or isolated change.

Do not include unrelated backend files.

---

# Execution Summary

For writer agents:

```text
Task specification
        +
Sources of truth
        +
HTTP contract
        +
DTOs
        +
Component API
        +
Existing Controller patterns
        ↓
Request extraction
        +
Component invocation
        +
Error handling
        +
HTTP response
        ↓
Controller
```

For reviewer agents:

```text
Task specification
        +
Sources of truth
        +
HTTP contract
        +
Component API
        +
Controller implementation
        ↓
Review Evidence
        +
HTTP Contract Review
        +
Controller Boundary Review
        +
Component Invocation Review
        +
Request Binding Review
        +
Authentication Context Review
        +
Error Handling Review
        +
Response Review
        +
Verification
```

Keep the Controller focused on the HTTP boundary and delegate application behavior to the Component.
