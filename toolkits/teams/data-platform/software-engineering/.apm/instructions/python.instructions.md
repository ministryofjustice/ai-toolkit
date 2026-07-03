---
description: Baseline conventions for Python code quality, structure, testing, and security.
applyTo: "**/*.py"
---

# Python Instructions

## Scope and Principles

- Treat this file as the default guidance for day-to-day Python development across this repository.
- Write clear, consistent code; prefer simple, readable solutions over clever abstractions.
- Avoid overengineering: solve the problem in front of you, not speculative future ones.
- Keep designs open to change: favour clear module boundaries and dependency seams so behaviour can be extended without large rewrites, but do not add abstraction until a concrete need exists.
- Remove duplication once a pattern is clear, but avoid premature abstraction; a third occurrence is a reasonable trigger.
- Apply SOLID and similar design principles where they improve clarity and testability, not as mandatory ceremony.
- Prefer composition over inheritance, and keep modules loosely coupled and highly cohesive.
- Isolate side effects; keep core logic as pure, easily testable functions.
- Prefer the standard library over third-party packages when it meets requirements.
- Use strict rules for security and test correctness; use pragmatic defaults for design choices.
- Target organisation-supported Python versions (preferably LTS) and avoid adopting language features outside the repository's declared version range.
- Follow [PEP 8](https://peps.python.org/pep-0008/), deferring to project tooling config (for example line length) where it differs from the letter of the spec.
- Adopt any pre-existing style rules in the repository over these defaults.

## Project Structure and Packaging

- Use uv for environment management, dependency resolution, and packaging.
- Manage dependencies and project metadata in `pyproject.toml`; commit the `uv.lock` file.
- Organise code into cohesive modules and packages with clear ownership boundaries.
- Avoid circular imports through clear module layering.

## Code Style and Formatting

- Format and lint with ruff; keep local and CI commands aligned.
- Follow PEP 8 naming: `snake_case` for functions and variables, `CapWords` for classes, `UPPER_SNAKE` for constants.
- Keep functions small and single-purpose; prefer early returns over deep nesting.
- Keep comments minimal; prefer self-explanatory names and structure. Comment only non-obvious intent.
- Keep style, naming, and module boundaries consistent with existing project conventions.

## Type Hints

- Annotate public interfaces (function signatures, class attributes) with type hints.
- Use static type checking as a quality gate.
- Prefer precise types; avoid `Any` except at genuinely untyped boundaries.

## Docstrings

- Write docstrings for public modules, classes, and functions where intent is not obvious from the signature.
- Update relevant docstrings in the same change when behaviour, signatures, or side effects change.

## Error Handling

- Do not catch broad `Exception` except at explicit process or entry-point boundaries.
- Catch specific exception types and handle only the cases you can recover from.
- Raise clear, intention-revealing exceptions with actionable messages.
- Introduce custom exception classes for domain-specific failures and reuse them consistently.
- Preserve root-cause context when re-raising exceptions (use `raise ... from ...`).

## Logging

- Use structured logs with consistent fields.
- Treat logs as event streams written to stdout; do not manage log files in the application.
- Never log secrets or sensitive payloads.

## Security

- Validate and sanitise external input at system boundaries.
- Never pass untrusted input to `eval`, `exec`, `pickle`, or `subprocess` with `shell=True`.
- Use the `secrets` module (not `random`) for tokens, keys, and other security-sensitive values.
- Load secrets from the environment or a secrets manager; never hardcode or commit them.
- Keep dependencies patched and act on known-vulnerability alerts promptly.

## Testing

- Use pytest for all tests.
- Practise test-driven development for non-trivial logic; tests and code should land together in the same change.
- Never alter tests to hide real regressions.
- Organise tests under `tests/`, mirroring source layout.
- Test behaviour and contracts, not implementation details.
- Keep tests deterministic and avoid unnecessary mocking; mock only external boundaries (network, third-party services, clocks).
- Prefer real collaborators for in-process logic.
- Prefer clear, behaviour-focused test names and assertions.
- Use lightweight test classes as grouping namespaces, not unittest inheritance with setup/teardown lifecycles.
- Add fixtures only when they provide clear reuse value.
- Maintain meaningful coverage for new and changed behaviour; treat coverage as a guardrail, not a target.
- Document one test entry point per repository (`make test`, or `pytest`) and keep local and CI runs equivalent.

## Dependencies

- Pin dependencies with `==` in `pyproject.toml`; let Dependabot manage updates.
- Keep dependencies minimal; prefer fewer, well-maintained packages.
- Enforce quality gates automatically (pre-commit and CI), including a deployment-safety check.

## Exceptions

- If you must deviate from these defaults, document the reason in the PR or code comments near the deviation.
- Choose the simplest deviation that solves the requirement without weakening security or test reliability.
