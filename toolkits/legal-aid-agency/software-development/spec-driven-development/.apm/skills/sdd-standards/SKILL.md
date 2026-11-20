---
name: sdd-standards
description: Apply the spec-driven development formats and project technology context when writing specifications, tickets or architecture decision records.
---

# Spec-driven development standards

Use this skill alongside the existing workflow, not instead of it. Read the
relevant reference before writing an artefact:

- Specification: [specification format](references/specification.md).
- Ticket: [ticket format](references/ticket.md).
- Architecture decision record: [ADR format](references/adr.md).

For specifications and tickets, read `TECHNOLOGY.md` at the consuming project
root if it exists. Use it to inform relevant decisions without inventing
technologies. Check it against the repository and raise material conflicts or
unknowns with the user. If it is missing, inspect the repository and explain
any uncertainty; suggest `/setup-sdd` when appropriate.

For `/to-spec`, use the `gherkin` skill to include acceptance criteria as
Gherkin scenarios in the specification. Trace each scenario to the relevant
requirement or user story. Do not create step definitions unless requested.

For `/to-tickets`, read the consuming project's root `TECHNOLOGY.md` before
proposing ticket destinations. Put implementation tickets under `docs/tickets`
in the consuming repository. If `TECHNOLOGY.md` identifies a separate hold-out
verification repository, put its verification tickets under `docs/tickets` in
that repository, not in the implementation repository. If the file is missing,
the destination is ambiguous, or the target repository is inaccessible, ask the
user to clarify or provide access; do not silently choose another destination.
Confirm the destinations in the existing ticket approval step before writing.

For hold-out verification tickets, use the `gherkin` skill and base tickets on
the specification's acceptance scenarios. Link back to the source using a
reference usable from the verification repository. Identify the hold-out project
and include the relevant API contract or page model where applicable, plus the
test approach and any known command for running verification. Reference existing
authoritative contracts or models where possible; flag missing details rather
than inventing them. Give each ticket only its genuine blockers, including
cross-repository implementation blockers, and identify their repository. Do not
change the verification project beyond writing the approved tickets.

Continue to use the project's domain glossary and relevant ADRs. Link artefacts
to their source when available: tickets to their specification, and Gherkin
features to their specification or ticket. Do not invent references.

Follow the invoked workflow's existing locations, status handling and approval
steps. Where a format conflicts with an existing project requirement or another
skill's essential workflow, surface the conflict and ask the user to resolve it.
