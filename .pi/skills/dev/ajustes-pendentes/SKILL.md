---
name: ajustes-pendentes
description: Execute a workflow for localized adjustments, bug fixes, and clear end-state changes to existing functionality, with focused tests, implementation, independent review, and final validation.
---

# Adjustment Workflow

Apply this workflow only when the requested change is localized to an existing
feature and its intended end state is clear. This skill does not handle new
features, new modules, new entities, new route families, or changes requiring
unresolved product, architecture, schema, authorization, tenant, or
cross-stack decisions.

## Authoritative flow

The primary agent owns this state machine:

```text
user message
  -> test_writer
  -> implementer
  -> reviewer #1
       FAIL -> implementer correction
            -> reviewer #2
                 PASS -> validation_runner
                 FAIL -> final implementer correction
                      -> validation_runner
       PASS -> validation_runner
```

If the implementer discovers that the adjustment is actually a new
implementation or requires an unresolved decision, stop this flow and restart
using the new-implementation workflow with task-contract planning.

## Test writing

Delegate `test_writer` in a fresh context before implementation. Provide the
original request, the explicit requested end state, relevant defect evidence,
and the affected area.

The test writer must:

- locate and adjust the existing test covering the behavior;
- create a new test only when no existing test can represent the requested
  behavior, and explain why in its handoff;
- modify only tests, fixtures, and test-only helpers;
- follow repository instructions and applicable skills;
- return the changed files and covered behaviors.

The test writer must not modify production code, weaken unrelated coverage,
run validation commands, review its own work, or issue a review verdict. Tests
may fail before the implementation is changed.

Only after the test writer returns completed test changes and a handoff may the
implementer be delegated.

## Implementation

Before modifying code, identify the language, framework, runtime, architecture,
and affected boundaries. Read the repository instructions, applicable skills,
stack guidance, and closest existing implementation and tests. Verify
referenced paths before following them. Keep each concern in the layer and
boundary required by the repository's own architecture. Implement only the
requested end state and do not weaken tests.

## Static review

After implementation, delegate an independent reviewer in a fresh context.
Provide the original request, the explicit requested end state, relevant
evidence, the implementation handoff, and the current diff.

The reviewer must inspect the request, diff, repository instructions,
applicable skills, and relevant existing patterns. It must not modify files or
run tests, linters, formatters, builds, architecture scripts, or other
analysis tools. Read-only inspection of files, paths, and git diff is allowed.

The reviewer returns `PASS` when no blocking violation is found, or `FAIL` with
every finding's requirement, file/location, why it is a violation, and what is
expected instead. It must actively check for missing requirements, regressions,
incorrect assumptions, missing error handling, unnecessary changes,
architectural violations, convention mismatches, and missing validation.

The first `FAIL` returns to the implementer with every blocking finding. After
that correction, run exactly one fresh second review. If review #2 passes,
continue to validation. If review #2 fails, perform exactly one final
implementer correction and then continue to validation without a third review.

## Validation

Delegate validation only after review #1 passes or after the mandated review #2
failure correction. Identify the repository's exact test, formatting, lint,
type-check, and build commands for the affected stack. Give the runner only
the affected stack, exact changed files when needed, and those commands. It
must not inspect code, review, edit, or propose fixes. The runner returns
`PASS` plus passed commands, or `FAIL` plus the failed command and a short
error excerpt. Do not claim completion after validation failure.

## Completion gate

Report completion only when the requested adjustment is implemented, the
review path has passed (or the mandated final correction path is complete),
and validation returns `PASS`. The implementer must never declare reviewer or
validation `PASS` on their behalf.
