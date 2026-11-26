---
name: forge-development
description: Use Forge developer guidance when designing, implementing or testing Forge UI journeys, steps and patterns, including alongside workflows such as tdd.
---

# Forge development

Use this skill alongside the active development workflow, not instead of it.
For `/tdd`, continue to agree test seams with the user and follow its
red-green cycle. Do not prescribe tests at unconfirmed seams.

## Establish project context

Read the consuming project's `TECHNOLOGY.md`, domain glossary, relevant ADRs,
specification and ticket when available. Inspect its dependencies, lockfile
and existing journeys and tests to establish whether it uses Forge, which
version is installed and which conventions apply. Do not assume a project
uses Forge solely because this skill is installed.

If Forge use or version is unclear, explain the uncertainty and check with the
user when it affects the implementation. Check guide examples against the
installed version and existing project code before adopting them; do not
assume the development guide matches every released version.

## Find the relevant guidance

Start with the [building journeys overview](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/building-journeys/overview)
for journey definitions, steps, blocks, fields, routing, navigation, hooks and
validation. Follow the links to the specific topics needed for the current
change. For custom server-side logic, follow the guide's building functions and
components section.

Consult the [patterns overview](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/overview)
and read the relevant pattern's overview and linked demo when useful. Select
patterns based on the behaviour required, not just their names. Examples
include:

- [Single question per page](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/single-question-per-page),
  [branching](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/branching)
  and [reveal fields](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/reveal-fields).
- [Composite fields](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/composite-fields),
  [add another](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/add-another)
  and [repeating fieldsets](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/repeating-fieldsets).
- [Resuming](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/resuming),
  [task list](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/task-list)
  and [edit and return](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/edit-and-return).
- [Loading reference data](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/load-reference-data),
  [pre-fill](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/pre-fill)
  and [authentication and roles](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/auth-role).

The overview lists further patterns; check it rather than treating this list as
exhaustive. Read the pattern's trade-offs and adapt it to the specification,
project conventions and installed Forge version. In particular, consider
reachability and stale answers when changing branches, and whether editing an
earlier answer requires later answers to be revalidated.

If the guide or demo is unavailable, say so and use verified local
documentation and project code where possible. Do not invent Forge APIs or
claim an example is compatible without evidence; flag any material gap before
relying on it.
