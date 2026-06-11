---
description: MOJ Ruby-specific conventions.
applyTo: "**/*.rb"
---

# Ruby Standards

## Exceptions at application level

- Handle exceptions at the application level, not in libraries. Exceptions are for the unexpected or unhandleable, not flow control.
- Always put specific exception types in `rescue` statements unless there is good reason not to.

## Meta-programming with caution

- Use meta-programming with extreme caution; it makes code harder to read and debug, and can cause performance issues (e.g. method cache purging).
