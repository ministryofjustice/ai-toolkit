---
description: MOJ development principles for writing maintainable, correct code.
---

# Development Principles

## Share the knowledge

If you have unique knowledge, share it. Use GitHub flow: small, short-lived branches. All non-throwaway code must be reviewed. Package reusable work (e.g. PyPI, rubygems) and share via MOJ Reusables where appropriate.

## Code should be correct, clear, concise – in that order

Correct means provably correct, with tests. All fixes and new features must include tests. Choose clarity over cleverness; avoid monkey-patching and meta-programming unless justified. DRY: apply the Rule of Three for duplication. Less code is better, but not at the expense of clarity.

## Optimize for change

Focus on making code easy to change. Don't prematurely optimize – choose clarity over performance unless there is a serious performance issue.

## Something simple which exists is better than a perfect solution which doesn't

Get it done, get it in front of users, learn early. Don't over-engineer. Follow Least Surprise. Don't roll your own crypto. Handle exceptions at the app level. Use process concurrency over threading unless there is good reason.

## Everything fails, all of the time

Code defensively when calling other services. Every HTTP call can error or hang – handle failures and fail fast. Don't let long-running external calls harm user experience.

## Other developers are users too

If you have to explain how your code works, it's not clear enough. Comments explain *why*, not *how*. Commit messages: follow GDS guidance (e.g. `type(scope): description`). APIs need designing for usability. Don't pollute the global namespace.

## Think smaller

Single Responsibility Principle. Keep views, controllers, models simple; keep methods short. Many small simple things are better than one big complex thing. Consider Null Object, Facade, Form Objects, and Sandi Metz's rules.

## Names have power – use them wisely

Don't be cute or jokey. Names convey meaning; well-named functions and variables can remove the need for comments. Avoid meaningless names (obj, result, foo). Use single-letter variables only for well-known maths (e.g. e = mc²) or when meaning is clear. Names should be self-descriptive. Avoid puns, uncommon acronyms, version numbers, or brand names in ways that obscure purpose.

## Composition over inheritance

Prefer 'has-a' over 'is-a' (e.g. Car has-a Motor, not Car is-a MotorVehicle). Inheritance trees often create tech debt.

> Source: [Development Principles](https://technical-guidance.service.justice.gov.uk/documentation/principles/development-principles.html)
