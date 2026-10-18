---
name: code-review
description: Review an application module against repository instructions, applicable skills, architecture, conventions, and requirements, returning only concrete violations found without modifying or validating the code.
---

# Module Validator

Use this skill only as a static code review for an existing module. Its sole
output is the list of concrete problems found in the module. It must not
implement fixes, edit files, create tests, run validation, or continue into a
development workflow.

## Scope

Inspect the module named by the user and determine whether it complies with:

- the user's stated requirements and expected behavior;
- repository instructions and applicable `AGENTS.md` rules;
- applicable skills discovered for the module's language and stack;
- canonical engineering standards discovered in the repository;
- existing patterns in the closest comparable modules;
- architecture and layer ownership;
- file names and locations;
- error handling and boundary contracts;
- test expectations and validation requirements.

First identify the module's language, framework, runtime, architecture, and
boundaries. Then discover and read the repository instructions, applicable
skills, stack standards, and closest comparable modules. Verify referenced
paths before following them. If a required source is missing, report the
configuration problem rather than inventing a replacement. Do not load
unrelated skills.

## Review constraints

Work in a fresh read-only review context. Inspect only the relevant repository
files, module dependencies, applicable instructions, existing patterns, and
the current diff when one is provided.

Do not:

- modify source, tests, fixtures, generated files, or documentation;
- run tests, linters, formatters, builds, architecture scripts, or validation
  commands;
- invoke an implementer or another correction workflow;
- invent requirements not supported by the user request, repository rules,
  applicable skills, or established patterns;
- report style preferences as violations unless a rule or project convention
  requires them.

## What to check

Actively search for:

- requirements that are missing or only partially implemented;
- behavior inconsistent with the module contract;
- violations of applicable skill instructions;
- incorrect layer ownership or boundary leakage;
- invalid file names or locations;
- domain `errors.go` sentinels or `Err*` values instead of typed `api_errors`
  errors returned by repositories;
- split component files (`component_<feature>.go`), `subentities.go`, or
  `gorm_repository.go` instead of `component.go`/`entity.go`/`repository.go`;
- orchestration of another domain's concept implemented locally instead of
  delegated to the owning domain's component or service;
- submodule services injected with parent components or evaluators instead of
  receiving caller-computed data;
- persistence queries outside the owning repository boundary;
- incorrect DTO, mapper, service, component, controller, or entity roles;
- missing authentication, authorization, tenant, or error handling required by
  the contract or existing pattern;
- regressions and unsafe assumptions;
- missing or inadequate tests when the applicable rules require them;
- unnecessary changes and inconsistencies with neighboring modules.

Verify that each nested boundary with its own persistence or business behavior
owns the corresponding responsibilities according to the repository's
architecture. Reject persistence, business rules, mapping, orchestration, or
transport logic placed in the wrong layer when the applicable standards
prohibit it.

## Output contract

Return only the review result. Do not include a plan, implementation steps,
validation commands, or general commentary.

When violations exist, return one finding per violation using this format:

```text
FAIL

1. [file:line or symbol] Requirement/rule: <specific rule>
   Problem: <what is wrong and why it violates the rule>
   Expected: <the compliant state>
```

Include every blocking finding. Keep findings concrete, traceable, and
independent. Do not combine unrelated violations.

When no violation is found, return exactly:

```text
PASS — no violations found.
```

Do not claim that tests, builds, or validation passed because this skill is
strictly static and must not execute those commands.
