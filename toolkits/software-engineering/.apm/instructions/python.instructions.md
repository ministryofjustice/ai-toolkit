---
description: MOJ Python-specific conventions.
applyTo: "**/*.py"
---

# Python Standards

## Exceptions at application level

- Don't swallow unexpected or base-type exceptions in libraries; let them propagate to the application.
- Always specify the exception type in `try`/`except` unless there is good reason not to.

## PEP 8 and the Zen of Python

- Follow [PEP 8](https://peps.python.org/pep-0008/).
- Consider the Zen of Python: readability, explicit over implicit, simple over complex.

## Concurrency

- Prefer process-based concurrency over threading unless there is a measured reason to use threads.
