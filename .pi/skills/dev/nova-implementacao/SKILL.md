---
name: nova-implementacao
description: Execute a repository workflow for new implementations, including user-approved planning gates, tests, implementation, independent review, correction loops, and final validation.
---

# New Implementation Workflow

Apply this workflow to every new implementation that modifies source code in
the current repository. This skill does not classify requests or handle
localized direct implementations.

## Authoritative flow

The primary agent owns this state machine and must not skip a user gate:

```text
user message
  -> task_contract_planner
  -> user validates contract
  -> bdd_test_planner (when the selected stack has applicable behavior)
  -> user validates BDD plan
  -> test_writer (when applicable)
  -> implementer
  -> reviewer #1
       FAIL -> implementer correction
            -> reviewer #2
                 PASS -> validation_runner
                 FAIL -> final implementer correction
                      -> validation_runner
       PASS -> validation_runner
```

## User validation gates

After contract planning, return the exact contract path and stop for explicit
user validation. On requested corrections, update the same artifact and stop
at the same gate. Do not start BDD planning before approval.

After BDD planning, return the exact plan path and stop for explicit user
validation. On requested corrections, update the same plan and stop at the
same gate. Do not start test writing before approval.

Contracts belong at `.ai/task-contract/back/<task_name>.md` and/or
`.ai/task-contract/front/<task_name>.md`. BDD plans belong at
`.ai/bdd-plan/back/<task_name>.md` and/or `.ai/bdd-plan/front/<task_name>.md`.
Each planner may edit only its own artifact directory.

## Planning and tests

Task-contract planning is required. For runtime behavior, BDD planning is
required and must produce traceable Given/When/Then scenarios. If no automated
test is applicable, the BDD handoff must justify that decision; do not invent
behavior or weaken coverage.

The test writer works in a fresh context and may modify only tests, fixtures,
and test-only helpers. It must not modify production code, weaken unrelated
coverage, run validation, or issue a review verdict.

Add the minimum tests covering every approved scenario. Only after the test
writer returns changed files and covered behaviors may the implementer be
delegated.

## Implementation and architecture

Before modifying code, identify the language, framework, runtime, architecture,
and affected boundaries. Read the repository instructions, applicable skills,
stack guidance, and closest comparable implementation. Verify referenced paths
before following them and report missing required sources as configuration
problems. Do not invent generic replacements. Keep persistence, domain rules,
representation conversion, orchestration, and transport concerns in the
boundaries established by the repository's own architecture. Do not expand
approved behavior with unspecified features or weaken tests.

## Static review

Delegate review in a fresh context after implementation. The reviewer must
inspect the request, current diff, repository instructions, applicable skills,
and relevant patterns, but must not edit files or run tests, linters,
formatters, builds, architecture scripts, or other analysis tools. Read-only
inspection of files, paths, and git diff is allowed.

The reviewer returns exactly `PASS` when no blocking violation is found, or
`FAIL` with each finding's requirement, file/location, violation, and expected
correction. Check missing requirements, architecture, assumptions, error
handling, regressions, unnecessary changes, conventions, and validation gaps.

The first `FAIL` gets one implementer correction followed by exactly one fresh
review. If review #2 passes, validate. If review #2 fails, perform exactly one
final implementer correction and validate without a third review.

## Validation

Delegate validation only after review #1 passes or after the mandated review #2
failure correction. Identify the repository's exact test, formatting, lint,
type-check, and build commands for the affected stack. Give the runner only
the affected stack, exact changed files when needed, and those commands. It
must not inspect code, review, edit, or propose fixes. The runner returns
`PASS` plus passed commands, or `FAIL` plus the failed command and a short
error excerpt. Do not claim completion after validation failure.

## Completion gate

Report completion only when requested behavior is implemented, applicable
skills were followed, the review path has passed (or the mandated final
correction path is complete), and validation returns `PASS`. The implementer
must never declare reviewer or validation `PASS` on their behalf.
