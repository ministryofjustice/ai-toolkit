---
name: setup-sdd
description: Set up minimal project guidance and technology context for spec-driven development using the grill-with-docs workflow.
disable-model-invocation: true
---

# Set up spec-driven development

Check the consuming project for evidence that `/setup-matt-pocock-skills` has
already been run. If it has not, invoke that skill and complete its workflow
before continuing. If the evidence is inconclusive, ask the user whether setup
has already been run. If setup is needed but the skill is unavailable, explain
the blocker and stop rather than substituting a different setup.

Invoke the installed `/grill-with-docs` skill and use its workflow to establish
the project's context with the user. Do not copy or replace that skill. If it is
unavailable, explain that it is required and stop.

Inspect the consuming project and its existing root `AGENTS.md` and
`TECHNOLOGY.md`, if present. Discuss only the decisions needed to capture the
project's actual technology stack, test tools and relevant constraints. Verify
claims against the repository where possible; distinguish confirmed facts from
unknowns and ask about material discrepancies. Do not invent details.

Create a minimal root `TECHNOLOGY.md` with the confirmed technologies, test
tools, constraints and any explicitly identified unknowns. Ask whether there is
a hold-out verification project; if so, record its location and any known test
commands and authoritative API contract or page model references. Identify its
repository clearly enough to route its tickets to that repository's
`docs/tickets`. Do not invent or assume access to it. Create a minimal
root `AGENTS.md` pointing to `TECHNOLOGY.md` and the existing domain glossary
and ADRs if present. Keep the domain glossary separate from technology
details.

If either file already exists, preserve its content and make only the necessary
additions, avoiding duplicates. Show the proposed changes and obtain approval
before modifying an existing file. Follow `/grill-with-docs` for any domain
modelling or ADR decisions; do not create speculative ADRs.
