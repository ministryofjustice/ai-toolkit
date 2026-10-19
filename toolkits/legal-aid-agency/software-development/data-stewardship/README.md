# Legal Aid Agency Data Stewardship

**Status: shared working baseline for review.** These principles describe our
current thinking, primarily informed by the Access Data Stewardship prototype.
They are not the target data-stewardship architecture, an approved standard or
a claim that we know the right answers. Last reconciled: 2026-10-19.

We are making our principles explicit so that we can recognise what we currently
believe, agree or challenge it, and change it deliberately. The record should
show both what changed and the position we changed from, together with the
reasoning and evidence.

Other data-stewardship teams are invited to work with these principles and test
them against their own domains. The aim is to evolve a shared strategic
definition of data stewardship through that experience, rather than generalise
one prototype into a prescribed destination.

## Scope

This opt-in toolkit supports teams building data-owning services. It separates
stewardship invariants from consumer assessment and allocation policies, with
additional guidance for services that have chosen event sourcing.

It sits alongside the proposed `software-development/java` toolkit in
[ministryofjustice/ai-toolkit#42](https://github.com/ministryofjustice/ai-toolkit/pull/42).
The packages are complementary: this one does not prescribe Java conventions or
require a Java toolkit dependency.

## Guidance for Review

| Guidance                                                               | Contents                                                                                                                                                              |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Data stewardship](.apm/instructions/data-stewardship.instructions.md) | S1-S11: ownership, contracts, consumer-policy boundaries, access and attribution, store classification, privacy, retention, transactions, delivery and framework risk |
| [Event sourcing](.apm/instructions/event-sourcing.instructions.md)     | E1-E7: sourced state, stream concurrency, retention facts, atomic coordination, replay, persisted-event compatibility and evidence                                    |

All items remain open to challenge. Applicability, confidence and concrete
mechanisms should be tested against each service's domain and evidence.
Imperative wording expresses the current proposed position, not proof that the
prototype already follows it. Named maintainers and review approvals have not
yet been assigned.

Engineering should maintain the technical guidance; domain/product owners should
confirm business invariants and observable behaviour; information governance and
security should confirm classification, retention and access policy. These are
proposed responsibilities, not recorded approvals.

## How These Principles Evolve

- Use the stable principle identifiers to record where a domain supports,
  qualifies or contradicts the current position.
- Distinguish a local exception from evidence that the shared principle needs
  to change; record either without silently imposing it on another team.
- When changing a principle, record the previous position, replacement, reasons,
  domain evidence and remaining uncertainty in the pull request or a linked
  decision record.
- Preserve links to the previous wording and rationale through Git history and
  decision records so that the evolution remains traceable.
- Bring experience from other teams back into this toolkit. Agreement and
  evidence should shape the shared definition, not conformance to the prototype.

## The Ownership Boundary

The consumer owns the selection policy; the stewardship service owns the accepted
assignment and its consequences.

| Example                                         | Responsibility                  |
| ----------------------------------------------- | ------------------------------- |
| Owning office controls access                   | Authoritative resource state    |
| Only the assigned caseworker may decide         | Stewardship invariant           |
| Availability determines the next assignment     | Allocation policy               |
| Leave and teams used only to balance work       | Workforce information           |
| Team membership grants access                   | Authoritative entitlement input |
| Financial thresholds and household calculations | Consumer policy                 |

Resource ownership and assignment do not replace the identity system's authority
over caller identity and entitlements. Information outside an aggregate can still
need persistent storage in its owning service.

## Conditional Patterns, Not Mandates

- Use draft/submit lifecycles where provisional work and committed facts have
  distinct requirements; do not require them for every resource.
- The owning service controls identifier acceptance and integrity. Server-minted
  and client-generated identifiers can both be valid; neither replaces access
  checks.
- Select Axon versions, persistence, processor modes and commercial capabilities
  deliberately. Do not inherit another team's technology decision as a mandate.
- Keep LAA aggregate layouts, role meanings, office-transfer rules, error codes
  and retention schedules in the relevant service's decisions.

## Provenance and Evidence Limits

These are a curated reconciliation of the
[earlier principles](https://github.com/ministryofjustice/laa-dstew-workbench/tree/main/api-principles)
and [API workbench](https://github.com/ministryofjustice/laa-data-access-api-workbench),
including the subsequent retention, accountability, transactional-consistency and
consumer-policy refinements. Earlier wording is not authoritative where it
conflicts with these proposals.

The concrete API evidence baseline is
[`11f63f90`](https://github.com/ministryofjustice/laa-data-access-api/tree/11f63f90b2f846dd957ef25e460c73b1d5d55094/data-access-service-axon).
Useful reference material at that baseline:

- [Thin events and authoritative payloads][payloads]: ADR 0002 is accepted for
  the proof of concept, not general production privacy approval.
- [Persisted-event compatibility][compatibility] and [test boundaries][tests].
- [Publication guarantees][publication]: the current producer is best-effort,
  despite at-least-once delivery after successful publication.
- [Processor coordination][processors] and [raw replay][replay]: concrete
  mechanisms and bounded evidence, not proof of every proposed invariant.

The API and workbench contain implementation gaps and differing coordination
paths. Verify current code before adopting an example. A recorded proposal,
test's existence or working implementation is not a substitute for approval of
the relevant policy or guarantee.

[payloads]: https://github.com/ministryofjustice/laa-data-access-api/blob/11f63f90b2f846dd957ef25e460c73b1d5d55094/data-access-service-axon/docs/adr/0002-separate-sensitive-data-from-domain-events.md
[compatibility]: https://github.com/ministryofjustice/laa-data-access-api/blob/11f63f90b2f846dd957ef25e460c73b1d5d55094/data-access-service-axon/docs/event-evolution.md
[tests]: https://github.com/ministryofjustice/laa-data-access-api/blob/11f63f90b2f846dd957ef25e460c73b1d5d55094/data-access-service-axon/docs/testing-axon-code.md
[publication]: https://github.com/ministryofjustice/laa-data-access-api/blob/11f63f90b2f846dd957ef25e460c73b1d5d55094/data-access-service-axon/docs/application-submitted-integration-event.md
[processors]: https://github.com/ministryofjustice/laa-data-access-api/blob/11f63f90b2f846dd957ef25e460c73b1d5d55094/data-access-service-axon/src/main/java/uk/gov/justice/laa/dstew/access/config/AxonEventProcessingConfig.java
[replay]: https://github.com/ministryofjustice/laa-data-access-api/blob/11f63f90b2f846dd957ef25e460c73b1d5d55094/data-access-service-axon/src/integrationTest/java/uk/gov/justice/laa/dstew/access/RawReplayContractTest.java
