---
description: Working practices for safe, focused changes in LAA Java repositories.
source: https://github.com/ministryofjustice/ai-toolkit/blob/main/toolkits/legal-aid-agency/software-development/java/.apm/instructions/copilot-working.instructions.md
applyTo: "**"
---

# Copilot Working Instructions

## Before Making Changes

- Read the repository README, local instructions, relevant Gradle configuration, source files, tests and CI before editing.
- Identify affected modules, API contracts, dependencies and established patterns. Check which optional technologies are actually used before applying their guidance.
- Use the repository's declared Java toolchain, Spring Boot compatibility line and plugin versions; do not assume it follows the latest template.
- Apply mandatory security controls throughout. Use the technology defaults in this package for new services; preserve established choices in existing applications unless changing them is part of the task.
- If an explicit requirement conflicts with repository conventions or these instructions, explain the conflict and seek clarification before making a potentially breaking change.
- Prefer existing LAA libraries, convention plugins and approved dependencies over introducing alternatives.

## When Making Changes

- Make the smallest coherent change that fully satisfies the requirement. Keep unrelated refactoring, formatting, dependency upgrades and architectural migrations out of scope.
- Preserve backwards compatibility unless a breaking change is explicitly required and approved.
- Add frameworks, dependencies, layers or interfaces only for a demonstrated need.
- Update source specifications or generator configuration and regenerate rather than editing generated sources.
- Preserve authentication, authorisation, validation, logging and error-handling behaviour unless an intentional change is required.
- Maintain security settings and quality gates. Never disable tests, lower coverage requirements, broaden exclusions or suppress checks to make a change pass.
- Keep secrets, credentials, personal data and sensitive case information out of source code, fixtures and logs; use synthetic test data.
- Obtain explicit authorisation before destructive operations on shared or deployed resources, including migrations and changes that weaken deployment security.

## Testing and Verification

- Add or update tests for changed behaviour, including negative paths, validation and denied access where relevant.
- Use the checked-in Gradle wrapper and repository-defined verification tasks. Inspect task wiring and source sets before deciding where tests belong and which commands run them.
- Run the relevant tests and quality checks when execution is available. Investigate failures rather than changing tests to accommodate incorrect behaviour.
- Report checks as passed only after successful execution; distinguish new failures from known pre-existing failures using evidence.

## Reporting Changes

- Summarise what changed and why, identifying the affected modules and files.
- State which tests and quality checks ran and their results, and identify checks that failed, were skipped or could not run.
- Highlight material assumptions, compatibility concerns, security implications and remaining work.
- Treat compilation as one check, not proof that an implementation is production-ready.
