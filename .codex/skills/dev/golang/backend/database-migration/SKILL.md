---
name: database-migration
description: Create or review golang backend database migrations using the repository's golang-migrate conventions, schema history, persistence requirements, and forward-only migration policy.
---

# Database Migration

Use this skill whenever a backend change requires creating or reviewing a database migration.

This skill is shared by implementation and review agents.

It defines how migrations must be designed, named, placed, and evaluated. The invoking agent decides whether files may be modified and how findings are reported.

## Sources of Truth

Before creating or reviewing a migration, inspect:

1. applicable `AGENTS.md`;
2. `docs/engineering/golang/backend-standard.md`;
3. migrations already present under `projects/backend/database/migrations`;
4. the affected entities and repositories;
5. the specification or task contract describing the required persistence behavior (if needed).

Use the existing migration history to determine concrete repository conventions.

Do not introduce a new migration convention when the repository already has one.

---

## Migration System

The backend uses `golang-migrate/migrate`.

Migration filenames follow this structure:

```text
<version>_<description>.up.sql
```

Example:

```text
000081_create_tire_pending_movements.up.sql
```

The numeric prefix is the migration version.

The description exists for human readability.

The migration version determines execution order.

Helu uses only forward migrations.

Do not create `.down.sql` files.

---

## Local Naming Convention

Helu uses sequential numeric migration versions padded to six digits.

Follow the existing format exactly:

```text
000001_description.up.sql
000002_description.up.sql
000003_description.up.sql
```

Use:

```text
NNNNNN_<short_snake_case_description>.up.sql
```

Examples:

```text
000082_add_status_to_service_orders.up.sql
000083_create_service_order_events.up.sql
000084_add_supplier_to_tire_movements.up.sql
```

Do not switch to another numbering or naming style unless the repository convention is intentionally changed.

Avoid names based on tickets or implementation phases.

Prefer:

```text
000082_add_status_to_service_orders.up.sql
```

over:

```text
000082_att_1234.up.sql
000082_service_order_fix.up.sql
000082_phase_2.up.sql
```

The description should communicate the database change.

---

## Version Selection

Before assigning a version, inspect the existing migrations in the relevant migration source.

Determine the highest existing version and use the next valid sequential version according to the repository convention.

Example:

```text
000079_link_maintenance_plans_to_categories.up.sql
000080_create_maintenance_items.up.sql
000081_create_tire_pending_movements.up.sql
```

The next migration should normally be:

```text
000082_<description>.up.sql
```

Never reuse an existing migration version.

Two migrations must not share the same version inside the same migration source, even if their descriptions differ.

Invalid:

```text
000081_create_tire_pending_movements.up.sql
000081_add_status_to_tires.up.sql
```

---

## Common and Dev Migration Streams

Helu separates migrations into:

```text
projects/backend/database/migrations/common
projects/backend/database/migrations/dev
```

The directories have different responsibilities, but they share the same
migration version sequence.

Use `common` for application schema and production-relevant persistence changes.

Examples:

- tables;
- columns;
- constraints;
- indexes;
- foreign keys;
- defaults;
- schema-level invariants.

Use `dev` only for development or local seed data.

Examples:

- development users;
- sample trucks;
- local checklist data;
- demo records.

Never place a real schema change in `dev`.

Never use a `dev` migration to compensate for a missing `common` migration.

Do not guess.

---

## Shared Version Sequence

Migration versions are global across both common and dev.

Treat both directories as a single ordered migration history for version
selection.

For example, this is valid:
```text

common/
  000001_create_users.up.sql

dev/
  000002_insert_dev_user.up.sql

common/
  000003_create_trucks.up.sql

dev/
  000004_insert_dev_truck.up.sql
```

This is invalid:
```text

common/
  000003_create_trucks.up.sql

dev/
  000003_insert_dev_truck.up.sql
```

A migration version must not exist in both directories.

Before creating a migration:

inspect both database/migrations/common and database/migrations/dev;
determine the highest migration version across both directories;
use the next sequential version.

Example:

```text

common/
  000081_create_tire_pending_movements.up.sql

dev/
  000082_insert_tire_pending_movement.up.sql

```

The next migration must be:

```text
000083_<description>.up.sql
```
regardless of whether it belongs in common or dev.

Valid:
```text
common/
  000083_add_status_to_tire_pending_movements.up.sql
```
or:

```text
dev/
  000083_insert_tire_pending_movement_demo.up.sql
```

but never both.

The migration directory determines the migration's purpose.

The numeric version determines its position in the shared migration history.

Therefore:
```text
common vs dev = responsibility
version number = global ordering
```
Never assign a migration version by inspecting only the destination directory.
Always inspect both migration directories before selecting the next version.

---

## Forward-Only Migration Policy

Helu uses forward-only migrations.

Every migration must move the database from its current schema version to the next required schema state.

Do not create:

```text
<version>_<description>.down.sql
```

The absence of rollback files is intentional.

When a previously applied migration must be corrected, create a new migration.

Example:

```text
000081_create_tire_pending_movements.up.sql
000082_fix_tire_pending_movement_status.up.sql
```

Do not:

- edit an already applied migration;
- rename an already applied migration;
- renumber an already applied migration;
- delete an already applied migration;
- create a `.down.sql` file to undo it.

Think in terms of:

```text
V80 -> V81 -> V82 -> V83
```

not:

```text
V81 -> rollback -> rewritten V81
```

---

## Existing Migrations Are Append-Only History

Treat committed migrations as append-only schema history once they may have been applied outside an isolated local environment.

If the current schema is wrong, correct it with another forward migration.

Incorrect:

```text
edit 000041_create_service_orders.up.sql
```

to add a column required by a new feature.

Correct:

```text
000082_add_new_field_to_service_orders.up.sql
```

Changing historical migration contents can make a fresh database and an existing database reach different schema states.

---

## Determine Whether a Migration Is Required

Create a migration when the requested final state changes persisted database structure or required persistent data.

Typical reasons include:

- creating a table;
- adding a column;
- removing a column;
- renaming a column;
- changing a column type;
- changing nullability;
- adding or removing a default;
- adding a foreign key;
- adding a unique constraint;
- adding an index;
- changing a database-enforced invariant.

Do not create migrations for changes that exist only in application behavior.

For example, changing a service calculation without changing persisted schema does not require a migration.

---

## Inspect Schema History Before Writing SQL

Do not determine the database schema from Go entities alone.

Before writing a migration, inspect migrations related to:

- the affected table;
- referenced tables;
- existing constraints;
- existing indexes;
- previous column changes;
- previous table renames;
- related domain entities.

Reconstruct the relevant current schema from migration history.

The entity describes what application code expects now.

The migration history describes how persisted environments reached that state.

Both must be considered.

---

## Migration Ordering

Migrations are applied according to their numeric version.

Dependencies must already exist when a migration runs.

Incorrect ordering:

```text
000082_add_fk_to_service_order_events.up.sql
000083_create_service_order_events.up.sql
```

when `000082` depends on the table created by `000083`.

Correct ordering:

```text
000082_create_service_order_events.up.sql
000083_add_fk_to_service_order_events.up.sql
```

Do not rely on description text or alphabetical wording to express dependency order.

---

## One Migration, One Coherent Change

A migration should represent one coherent persistence change.

Good:

```text
000082_create_service_order_events.up.sql
```

containing the table plus directly related constraints and indexes.

Also reasonable:

```text
000083_add_supplier_to_maintenances.up.sql
```

containing the column and directly related constraint required by that field.

Avoid mixing unrelated schema changes into the same migration.

Do not opportunistically refactor neighboring schema.

---

## SQL Must Describe the Required Final State

Start from the persistence requirement, not from the easiest SQL statement.

For each schema change determine:

- table;
- column;
- SQL type;
- nullability;
- default;
- uniqueness;
- foreign-key relationship;
- index requirements;
- database-level invariant.

Example business rule:

```text
A tenant cannot have two trucks with the same license plate.
```

If persistence correctness requires database enforcement, the migration may need a tenant-scoped uniqueness constraint such as:

```text
UNIQUE (tenant_id, license_plate)
```

Do not rely only on an application-level existence check when the invariant must remain correct under concurrent writes.

Use database constraints when required by the specification or established backend architecture.

---

## Existing Data Must Be Considered

Never assume the target table is empty.

Before adding:

```sql
NOT NULL
```

determine what happens to existing rows.

Before adding:

```sql
UNIQUE
```

determine whether existing duplicate rows can exist.

Before creating a foreign key, determine whether existing records can violate the relationship.

Before changing a type, determine whether all persisted values can be converted safely.

Before removing a column, determine whether the current application still reads or writes it.

A migration that works only on an empty development database is not sufficient.

---

## Adding Columns

When adding a column, explicitly reason about:

```text
type
nullability
default
existing rows
application expectations
```

Do not add `NOT NULL` merely because the Go field is non-pointer.

Determine whether existing rows can satisfy the new constraint.

Do not add arbitrary defaults merely to make the migration execute successfully.

A default changes persisted application behavior and must be intentional.

---

## Removing or Renaming Columns

Treat destructive changes carefully.

Before dropping a column verify that:

- current application code no longer depends on it;
- no repository query references it;
- no constraint depends on it;
- no index depends on it;
- no required data preservation behavior is being violated.

Do not model a rename as drop-and-create when that would unnecessarily destroy existing data.

Follow existing repository conventions for renames.

---

## Foreign Keys

Before adding a foreign key determine:

- owning table;
- referenced table;
- referenced key;
- cardinality;
- nullability;
- required deletion behavior.

Do not invent:

```text
ON DELETE CASCADE
ON DELETE SET NULL
ON UPDATE CASCADE
```

without an explicit requirement or established repository convention.

Deletion behavior is part of domain semantics.

---

## Unique Constraints

Determine the actual uniqueness scope.

These are different invariants:

```text
license plate is globally unique
```

and:

```text
license plate is unique inside a tenant
```

The second may require:

```text
UNIQUE (tenant_id, license_plate)
```

rather than:

```text
UNIQUE (license_plate)
```

Review tenant-scoped uniqueness carefully.

---

## Indexes

Create indexes when justified by:

- an explicit specification;
- uniqueness enforcement;
- established repository query patterns;
- known persistence requirements.

Do not add speculative indexes merely because a field exists.

For compound indexes, column order must reflect the intended constraint or access pattern.

Follow existing index naming conventions from nearby migrations.

---

## SQL Dialect and Repository Conventions

`golang-migrate` manages migration sequencing and execution, but migration files still contain SQL for the configured database.

Use SQL compatible with the database used by Helu.

Inspect nearby migrations before choosing syntax for:

- IDs;
- timestamps;
- booleans;
- enum-like values;
- `ALTER TABLE`;
- indexes;
- constraints;
- defaults;
- comments;
- transaction blocks.

Do not introduce syntax copied from another database without confirming compatibility with the backend's actual database.

---

## Transactions and Partial Failure

Do not assume that every migration is automatically wrapped in one transaction.

Follow existing repository conventions and database-driver behavior.

For a multi-statement migration, reason about what happens if an intermediate statement fails.

Avoid designing migrations that depend on accidental partial execution.

A failed migration may leave the migration version in a dirty state that requires explicit recovery.

Keep multi-statement migrations coherent and safe.

---

## Do Not Hide Schema Drift With Idempotency

Do not automatically add:

```sql
IF EXISTS
IF NOT EXISTS
```

to every migration.

These clauses can hide unexpected schema state or migration-history drift.

Use them only when:

- existing repository conventions use them for the same situation;
- the migration semantics genuinely require them;
- their effect is understood.

A migration should normally fail when the database state contradicts the schema history it expects.

---

## Dev Data Migrations

Development migrations contain development-only data.

They should:

- depend only on schema already available from common migrations;
- satisfy current foreign-key constraints;
- remain compatible with current schema rules;
- provide deterministic local development data when practical.

They must not:

- create production schema;
- alter production constraints;
- repair missing common migrations;
- contain data required for production correctness.

---

## Consistency With Go Code

After creating or reviewing a migration, compare it with:

- entity fields and GORM tags;
- repository queries;
- service persistence behavior;
- DTO validation when persistence-related;
- task requirements.

Look for contradictions such as:

```text
Entity expects column
-> migration never creates it
```

```text
Repository filters by column
-> column does not exist
```

```text
Service assumes uniqueness
-> database allows duplicates even though persistence enforcement is required
```

```text
Migration adds NOT NULL
-> existing application creates records without that value
```

The resulting database schema and the application must describe compatible final states.

---

## Migration Review Checklist  (For Reviewer Agents Only)

When reviewing a migration, verify:

1. A migration is actually necessary.
2. It is in the correct `common` or `dev` directory.
3. Its numeric version follows the current repository sequence.
4. Its version does not conflict with another migration in the same migration source.
5. Its filename follows the six-digit Helu convention.
6. Its description clearly represents the schema change.
7. It uses `.up.sql`.
8. No `.down.sql` migration was introduced.
9. Historical migrations were not modified, renamed, renumbered, or deleted.
10. Migration ordering satisfies all dependencies.
11. SQL matches the configured database dialect and repository conventions.
12. Existing data has been considered.
13. Nullability is intentional.
14. Defaults are intentional.
15. Foreign keys reflect actual ownership.
16. Delete/update behavior was not invented.
17. Unique constraints use the correct scope.
18. Indexes are justified.
19. The migration does not contain unrelated schema changes.
20. `dev` migrations contain only development data.
21. Go entities and repositories are consistent with the resulting schema.
22. The resulting database state satisfies the requested persistence invariant.

---

## Review Evidence (For Reviewer Agents Only)

When reporting a migration issue, identify:

```text
requirement
-> migration file
-> affected statement/table/column
-> observed problem
-> persistence consequence
-> expected correction
```

Example:

```text
Requirement:
A maintenance category name must be unique within the tenant.

Migration:
000082_create_categories.up.sql

Observed:
The migration creates global uniqueness on `name`.

Impact:
Two different tenants cannot use the same category name.

Expected:
Use the tenant-scoped uniqueness required by the specification and the existing multi-tenant persistence model.
```

Do not report a finding merely because another valid SQL formulation could have been used.

Findings must be based on:

- the specification;
- backend standards;
- existing migration conventions;
- actual schema dependencies;
- concrete persistence risks.

---

## Verification (For Reviewer Agents Only)

Run the verification commands required by:

- applicable `AGENTS.md`;
- `backend-standard.md`;
- the invoking agent's task instructions.

Never invent command results.

A successful migration implementation or review requires both:

```text
SQL/schema correctness
```

and:

```text
consistency with the backend behavior that depends on it
```
