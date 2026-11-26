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
patterns based on the behaviour required, not just their names. Read the
pattern's trade-offs and adapt it to the specification,
project conventions and installed Forge version. In particular, consider
reachability and stale answers when changing branches, and whether editing an
earlier answer requires later answers to be revalidated.

The following lists reflect the guide checked on 26 November 2026. Check the
guide for additions and changes, and verify availability against the installed
Forge version.

## Patterns

- [Single question per page](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/single-question-per-page)
- [Branching based on an earlier answer](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/branching)
- [Reveal fields](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/reveal-fields)
- [Multi-part composite fields](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/composite-fields)
- [Resuming a partially-completed journey](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/resuming)
- [Adding, editing and deleting from collections](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/add-another)
- [Task list](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/task-list)
- [Load reference data on access](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/load-reference-data)
- [Pre-fill from an external system](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/pre-fill)
- [Repeating fieldsets](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/repeating-fieldsets)
- [Edit and return](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/edit-and-return)
- [Require authentication / role](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/auth-role)
- [Read-only mode](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/read-only-mode)
- [Search and select](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/search-and-select)
- [Pagination](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/pagination)
- [Shaping data inline](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/inline-functions)
- [CMS content](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/cms-content)
- [Validating collections with iterators](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/patterns/collection-validation)

## Components

The [GOV.UK components package](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/packages/govuk-components/overview)
documents:

- Form inputs: text input, password input, textarea, character count, radios,
  checkboxes, select and date input (full, year-month and month-day).
- Buttons: button and link button.
- Navigation: back link, breadcrumbs, pagination and exit this page.
- Content: heading, body, list, inset text, warning text, details, notification
  banner, panel, accordion and tabs.
- Data display: summary list, table, tag and task list.
- Layout: button group, grid row and section break.
- Utilities: `GovUKUtilityClasses` and `GovUKValidations`.

The [MOJ components package](https://forge-developer-guide-dev.hmpps.service.justice.gov.uk/forge-developer-guide/packages/moj-components/overview)
documents:

- Messages and status: alert, badge, banner, messages, progress bar,
  notification badge, ticket panel, interruption card and timeline.
- Navigation: side navigation and sub navigation.
- Actions and layout: button menu, card, card group, identity bar and page
  header actions.
- Forms and lists: date picker, filter, multi-select and sortable table.

For GOV.UK design guidance, also use the `gds` skill. Forge's components are
not necessarily the complete set of GOV.UK Design System components.

## Unavailable guidance

If the guide or demo is unavailable, say so and use verified local
documentation and project code where possible. Do not invent Forge APIs or
claim an example is compatible without evidence; flag any material gap before
relying on it.
