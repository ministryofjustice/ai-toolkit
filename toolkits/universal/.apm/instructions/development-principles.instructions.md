---
description: MOJ development principles for writing maintainable, correct code.
---

# Development Principles

- Prioritise correctness, then clarity, then brevity — in that order.
- Include tests with every fix and new feature; correctness means proven by tests.
- Choose clarity over cleverness; avoid monkey-patching and meta-programming.
- Remove duplication only once a pattern is clear (Rule of Three); avoid premature abstraction.
- Design for change: keep clear module boundaries and prefer clarity over performance unless there is a measured bottleneck.
- Don't over-engineer; prefer the simplest solution that works and follow the principle of least surprise.
- Code defensively around external calls: set timeouts, handle errors, and fail fast.
- Write comments that explain why, not how.
- Don't pollute the global namespace, and design APIs for usability.
- Keep units small: apply the Single Responsibility Principle and keep functions and methods short.
- Prefer composition over inheritance ('has-a' over 'is-a').
