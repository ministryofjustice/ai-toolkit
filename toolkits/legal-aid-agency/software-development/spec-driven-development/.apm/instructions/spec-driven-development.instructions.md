---
description: Apply spec-driven development formats alongside existing skills
applyTo: "**"
---

Agents must never create or amend Git commits, including through other tools or
delegated agents. The developer performs all commits.

When using `/to-spec`, `/to-tickets`, or creating an architecture decision record,
load the `sdd-standards` skill and apply its relevant format and project context
guidance. Continue to follow the invoked skill's workflow; do not replace it.

When using `/to-spec`, also load the `gherkin` skill to express acceptance
criteria as scenarios. When using `/to-tickets`, read the consuming project's
root `TECHNOLOGY.md` and follow the repository routing guidance in
`sdd-standards`. Load the `gherkin` skill for hold-out verification tickets
if that file identifies a hold-out verification project.
