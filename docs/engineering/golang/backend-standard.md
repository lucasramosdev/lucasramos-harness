# Backend Architecture Standard — Go + Gin

## 1. Purpose

This document is the **source of truth** for backend architecture in Go projects.

AI agents, reviewers, and developers **must consult this document before creating or modifying backend features**.

The goal is to ensure that generated and manually written code remains:

- consistent;
- testable;
- secure;
- maintainable;
- aligned with the project's architectural conventions.

Architecture compliance is mandatory even when the implementation compiles and all tests pass.

---

## 2. Canonical Project Layout

The backend directory structure must strictly follow this layout:

```text
projects/backend/
  cmd/
    api/

  internal/
    api_errors/

    dtos/
      <module>/

    domain/
      <module>/
      <module>/
        <subentity>/

    infra/
      base/

    web/
      middlewares/
      routes/

  database/
    migrations/
      common/
      dev/
```

### Canonical Paths

| Responsibility | Canonical Path |
|---|---|
| Backend module | `projects/backend` |
| API entry point | `projects/backend/cmd/api` |
| Domain packages | `projects/backend/internal/domain/<module>` |
| Subentity packages | `projects/backend/internal/domain/<module>/<subentity>` |
| DTO packages | `projects/backend/internal/dtos/<module>` |
| HTTP routes/controllers | `projects/backend/internal/web/routes` |
| Middlewares | `projects/backend/internal/web/middlewares` |
| Shared API errors | `projects/backend/internal/api_errors` |
| Base infrastructure helpers | `projects/backend/internal/infra/base` |
| Production/schema migrations | `projects/backend/database/migrations/common` |
| Development/local migrations | `projects/backend/database/migrations/dev` |

Do not create alternative directory structures without an explicit architectural decision.

---

## 3. Request Flow

The forward flow of a normal request must follow exactly this order:

```text
Controller -> Component -> Mapper -> Service -> Repository -> Database
```

The return flow must follow:

```text
Repository -> Service -> Mapper -> Component -> Controller
```

Layers must not be skipped when the skipped layer owns behavior required by the operation.

Examples of forbidden shortcuts:

```text
Controller -> Repository
Controller -> Service -> Database
Component -> Database
Service -> DTO
Repository -> API Error
```

---

## 4. Layer Ownership and Responsibilities

Each architectural layer has a strict ownership boundary.

### 4.1 Controller / Route

The Controller is the HTTP-facing layer.

#### Owns

- Gin request binding;
- route parameter extraction;
- query parameter extraction when part of the API contract;
- authenticated identity/claims extraction;
- HTTP response status;
- HTTP response serialization;
- calling the corresponding Component.

#### Must Not Own

- business rules;
- database queries;
- repository access;
- persistence;
- DTO-to-Entity mapping;
- Entity-to-Response mapping when a Mapper exists;
- cross-domain orchestration.

A Controller must never access a Repository or Database directly.

---

### 4.2 Component

The Component is the route-facing application facade.

#### Owns

- orchestration initiated by the Controller;
- Mapper invocation;
- coordination between Services;
- cross-domain service orchestration;
- relationship validation requiring multiple modules;
- assembling the final result returned to the Controller.

#### Must Not Own

- database queries;
- direct ORM access;
- Gin context manipulation;
- HTTP status codes;
- HTTP response writing.

The Component is the correct place to coordinate multiple Services.

---

### 4.3 Mapper

The Mapper is responsible exclusively for data transformation between architectural boundaries.

#### Owns

- DTO -> Domain conversion;
- Domain -> Response conversion;
- transformations required strictly for representation changes.

#### Must Not Own

- business rule validation;
- persistence;
- repository access;
- service orchestration;
- HTTP behavior;
- external calls.

Mapping logic must remain deterministic whenever possible.

---

### 4.4 Service

The Service owns business behavior for its domain.

#### Owns

- business rules;
- domain-specific validations;
- module behavior;
- calls to its own Repository;
- persistence decisions for its module.

#### Must Not Own

- Gin imports;
- HTTP package knowledge;
- HTTP status codes;
- route manipulation;
- direct DTO references;
- cross-domain Service orchestration;
- direct access to another module's Repository.

A Service must not orchestrate Services belonging to other modules.

Cross-domain orchestration belongs to the Component.

---

### 4.5 Repository

The Repository is the exclusive persistence boundary for its module's tables.

#### Owns

- ORM queries;
- SQL/persistence behavior;
- reads and writes for its module's tables;
- filtering and persistence-level query composition.

#### Must Not Own

- business rules;
- DTO imports;
- Gin context;
- HTTP behavior;
- shared/global `api_errors`;
- cross-domain orchestration;
- validation of external-domain relationships through direct table access.

Repositories must remain persistence-focused.

---

### 4.6 DTO

DTOs define API payload shapes only.

#### Owns

- request payload structure;
- response payload structure;
- validation tags related to payload shape when appropriate.

#### Must Not Own

- domain behavior;
- service logic;
- repositories;
- infrastructure injection;
- persistence;
- orchestration.

DTOs are transport contracts, not domain models.

---

## 5. Domain and Subentity Rules

A primary domain may contain subentities.

Example:

```text
internal/domain/order/
internal/domain/order/item/
```

A subentity package is treated as its own implementation boundary.

### Mandatory Rules

A subentity must have its own:

- Repository;
- Service.

It is strictly forbidden to reuse the parent entity's:

- Repository;
- Service;
- Component

to manage the subentity.

The only layer that may be shared between a parent entity and subentity is the Mapper, and only when the mapping behavior is genuinely identical.

### Relationship Validation

A subentity Repository must not query parent tables merely to validate relationships.

Forbidden example:

```text
ItemRepository -> query Order table to verify ownership
```

Correct orchestration:

```text
Component
  -> OrderService
  -> ItemService
```

The Component coordinates the validation between domains or boundaries.

---

## 6. Security, Authentication, and Identity

Authenticated identity is authoritative.

The actor's identity, tenant, role, permissions, or other security-sensitive context must come strictly from **verified authentication claims** produced by trusted middleware.

### Trusted Sources

Security-sensitive identity may come from:

- authenticated token claims;
- trusted middleware context populated after verification.

### Untrusted Sources

The application must never accept or override authenticated caller identity using:

- request payload fields;
- route parameters;
- query parameters;
- untrusted HTTP headers;
- client-provided tenant identifiers;
- client-provided role identifiers.

Example of forbidden behavior:

```json
{
  "author_id": 123,
  "tenant_id": 99
}
```

when those values are supposed to represent the authenticated caller.

If authorship or tenant context is derived from authentication, it must be populated from verified claims instead.

### Service Scoping

Services must scope queries and actions using the actor context extracted from authenticated claims.

Client-provided data must never override this context.

---

## 7. Architecture Rejection Conditions

Implementation must be immediately rejected when any of the following occurs.

### Controller Violations

Reject if:

- a Controller accesses a Repository directly;
- a Controller accesses the Database directly;
- a Controller implements business rules;
- a Controller manually maps DTOs and Domain objects when a Mapper/Component exists.

### Service Violations

Reject if:

- a Service imports Gin;
- a Service depends on HTTP status codes;
- a Service imports or directly references DTO packages;
- a Service orchestrates another module's Service;
- a Service accesses another module's Repository directly.

### Repository Violations

Reject if:

- a Repository imports DTO packages;
- a Repository imports global `api_errors`;
- a Repository owns business rules;
- a Repository manipulates HTTP/Gin context;
- a Repository performs cross-domain orchestration.

### Security Violations

Reject if:

- client-provided identity overrides authenticated claims;
- tenant information from the request overrides trusted tenant claims;
- role or access-control information is accepted from untrusted input;
- persistence operations are not correctly scoped to the authenticated actor when scoping is required.

### General Rule

Passing tests does **not** make an architectural violation acceptable.

If the architecture is violated, the implementation must be rejected even if:

```text
go test ./...
```

passes successfully.

---

## 8. Mandatory Stop Conditions

Stop implementation and request additional context when any of the following is true:

### Ambiguous Specification

Stop when:

- behavior is ambiguous;
- requirements conflict;
- expected domain behavior cannot be determined safely.

### Missing API Contract

Stop when there is no clear contract describing:

- request payload;
- response payload;
- route behavior;
- expected status/error behavior.

### Missing Authorization Rules

Stop when essential rules are undefined for:

- authorship;
- tenant ownership;
- roles;
- permissions;
- access control;
- resource visibility.

Do not invent authorization behavior.

### Undefined Soft Delete Convention

If soft delete is requested, stop when the project does not define:

- whether soft delete is globally adopted;
- the canonical deletion field;
- repository filtering behavior;
- uniqueness behavior for deleted records;
- restoration behavior, if any.

Do not introduce a new soft-delete convention implicitly.

---

## 9. Architectural Decision Checklist

Before implementing a backend feature, verify:

- [ ] The target code belongs under `projects/backend`.
- [ ] The correct domain/module has been identified.
- [ ] DTOs live under `internal/dtos/<module>`.
- [ ] Domain code lives under `internal/domain/<module>`.
- [ ] Controllers/routes live under `internal/web/routes`.
- [ ] The request follows `Controller -> Component -> Mapper -> Service -> Repository`.
- [ ] The Controller contains no business logic.
- [ ] The Component owns cross-service orchestration.
- [ ] The Mapper owns DTO/Domain transformations.
- [ ] The Service contains no Gin/HTTP/DTO dependencies.
- [ ] The Service only calls its own Repository.
- [ ] The Repository contains persistence logic only.
- [ ] Subentities have their own Repository and Service.
- [ ] Identity and tenant information come from verified claims.
- [ ] Client input cannot override authenticated identity.
- [ ] Authorization and tenancy rules are explicit.
- [ ] Schema migrations use the correct migration stream.

If any mandatory rule cannot be satisfied, stop and resolve the architectural ambiguity before implementation.

---

## 10. Source-of-Truth Rule

When generated code conflicts with this document, **this document wins**.

Agents must not preserve an existing architectural violation merely because similar code already exists elsewhere in the repository.

Existing code may be used as implementation reference only when it is compatible with the rules defined here.

When repository conventions and this document appear to conflict, stop and inspect the surrounding architecture before introducing new behavior.