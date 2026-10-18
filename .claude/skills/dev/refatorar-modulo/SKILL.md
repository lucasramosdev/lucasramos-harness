---
name: refatorar-modulo
description: Audit every file in an application module against applicable skills and repository standards, produce a complete correction proposal for user approval, then implement only the approved refactoring.
---

# Module Refactor

Use this skill when an existing module must be brought into compliance with
the repository's skills, architecture, conventions, and contracts. The skill
has a mandatory proposal gate: never modify files before the user adjusts or
confirms the proposed correction.

## Authoritative flow

```text
user request
  -> exhaustive module inventory
  -> read every relevant module file
  -> load all applicable instructions and skills
  -> identify every violation
  -> produce complete correction proposal
  -> user adjusts or confirms proposal
       feedback -> revise same proposal -> user validates again
       confirmation -> test_writer when applicable
                   -> implementer applies approved refactor
                   -> independent reviewer
                   -> correction loop
                   -> validation_runner
```

Do not skip the user gate. If the user does not confirm the proposal, do not
modify the module.

## Exhaustive audit

First establish the exact module boundary. Recursively inventory every file
under that boundary, including source files, tests, fixtures, migrations,
configuration, generated or embedded assets, documentation, and nested
directories. Read every relevant file in full; do not review only the git
diff, entrypoint, or files that appear to contain the primary feature.

Inspect imports and references that cross the module boundary, plus the
closest comparable modules. Read repository instructions from the workspace
and any nested directories that govern the files under review. Load every
skill applicable to the module's stack and layers, but do not load unrelated
skills.

The audit must account for all discovered files and explicitly state when a
file was inspected and found compliant. Do not silently omit a file because it
looks generated, trivial, duplicated, or unrelated; determine its ownership
and relevance before excluding it.

For each issue, identify the exact file and line or symbol, the governing
requirement, the current violation, its impact, and the smallest compliant
correction. Group related findings only when they have the same cause and
correction. Preserve independent findings separately.

## Standards and architecture

Compare the complete module against:

- the user's requested behavior and existing module contract;
- applicable `AGENTS.md` instructions;
- all skills applicable to the module discovered in the repository or runtime;
- canonical engineering standards;
- neighboring modules and established repository patterns;
- file naming and placement conventions;
- layer ownership, dependency direction, and boundary contracts;
- authentication, authorization, tenant handling, and error behavior;
- test, formatting, lint, build, and migration expectations;
- file-name rules: no domain `errors.go` sentinels, `subentities.go`,
  `component_<feature>.go`, or `gorm_repository.go`;
- error handling: repositories return typed `api_errors` errors and services
  propagate them unwrapped;
- dependency direction: leaf services receive caller-computed data, and
  cross-domain orchestration lives in the owning domain while callers
  delegate concretely (ready data, existing interfaces, or bound methods).

First identify the module's language, framework, runtime, architecture, and
boundaries. Discover and read the repository instructions, all skills
applicable to that language and task, stack standards, and closest comparable
modules before proposing changes. Verify every referenced path before
following it. Report missing required sources as configuration problems rather
than inventing replacements.

For nested boundaries, verify that persistence, domain rules, representation
conversion, orchestration, and transport responsibilities remain in the layers
defined by the repository's architecture.

## Proposal phase

The proposal phase is read-only. Do not edit source, tests, fixtures,
generated output, migrations, or documentation. Do not run formatters, tests,
linters, builds, or validation commands during this phase.

Return a complete correction proposal containing:

1. the module boundary and exhaustive file inventory;
2. every violation found, with file/line or symbol and governing rule;
3. the intended compliant design and dependency/layer changes;
4. exact file-level changes for each correction;
5. behavior-preservation risks or behavior changes, explicitly identified;
6. required test, fixture, migration, or documentation updates;
7. files inspected with no changes required;
8. unresolved decisions, if any.

The proposal must not hide unrelated violations discovered during the audit.
If the module has no violations, report that no refactoring is proposed and
stop without modifying anything.

After returning the proposal, stop and request user adjustment or
confirmation. If the user requests changes, revise the same proposal and stop
at the same gate again. Do not begin implementation until explicit approval.

## Approved implementation

After confirmation, implement only the approved corrections. If the user
changes the scope materially, update the proposal and obtain confirmation
again before editing.

Before implementation, create or adjust the minimum applicable tests. Tests
must cover preserved behavior and every approved behavior change. Test-only
changes must remain separate from production changes in the handoff.

Follow the applicable layer skills and existing patterns. Do not introduce
unspecified features, normalize data beyond the contract, weaken tests, or
silently resolve an unresolved product or architecture decision.

## Review and validation after approval

Delegate an independent static reviewer after implementation. The reviewer
must inspect the original approved proposal, all changed files, the complete
module context, applicable skills, repository instructions, and relevant
patterns. It must not modify files or run tests, linters, formatters, builds,
architecture scripts, or other validation commands.

The reviewer returns `PASS` when no blocking violation remains, or `FAIL` with
each finding's requirement, file/location, reason, and expected correction.

The first review failure gets one implementer correction followed by exactly
one fresh second review. If review #2 passes, validate. If review #2 fails,
perform exactly one final implementer correction and validate without a third
review.

Delegate validation only after review #1 passes or after the mandated review #2
failure correction. Identify the repository's exact test, formatting, lint,
type-check, and build commands for the affected stack. Give the runner only
the affected stack, exact changed files when needed, and those commands. It
must not inspect or review code, load unrelated instructions, edit files, or
propose fixes.

Report completion only when the approved refactor is implemented, the review
path passes (or the mandated final correction path is complete), and
validation returns `PASS`. Never claim reviewer or validation success on
another agent's behalf.
