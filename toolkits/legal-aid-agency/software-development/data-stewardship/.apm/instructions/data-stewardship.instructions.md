---
description: Working LAA stewardship principles for cross-team review, informed primarily by the Access Data Stewardship prototype.
source: https://github.com/ministryofjustice/ai-toolkit/blob/main/toolkits/legal-aid-agency/software-development/data-stewardship/.apm/instructions/data-stewardship.instructions.md
---

# Data Stewardship Principles

## Scope and Review Status

- These describe current proposed principles, primarily informed by the Access
  Data Stewardship prototype, not a target architecture or approved standard.
- Treat them as an explicit working position to test and challenge, not as
  proven answers or a claim that the prototype implements every rule.
- Invite other stewardship teams to test applicability against their domains
  and contribute evidence towards a shared strategic definition.
- When revising a principle, retain its identifier and record the previous
  position, replacement, reasons, domain evidence and uncertainty in a pull
  request or linked decision record. Preserve access to the earlier rationale.
- Distinguish local exceptions from changes to the shared position; do not
  silently impose one domain's choices on another.
- Apply them to stewardship responsibilities; do not introduce event sourcing or
  move consumer policy into a data-owning service merely to follow this
  guidance.
- Read the consuming repository's architecture decisions, contracts and
  implementation before proposing changes.
- Distinguish implemented behaviour, accepted decisions, proposals and
  unverified claims. The reference API is evidence, not proof of conformance.
- Identify conflicts with accepted service decisions and seek agreement before
  changing behaviour or persisted contracts.
- For event-sourced services, also apply the event-sourcing instructions in this
  toolkit.

## S1. Give Each Business Fact an Authoritative Owner

- Own a bounded set of facts and provide supported ways to read and change them.
- Copies, caches, projections and analytical datasets are legitimate, but must
  have explicit provenance, freshness expectations and recovery behaviour.
- Do not let a derived copy become a competing authority for the same fact.
- Information outside an aggregate may still require durable storage in its
  owning service.

## S2. Publish Deliberate Contracts

- Consumers integrate through published API and integration-event contracts, not
  database tables, internal messages or persistence entities.
- Define structure, permitted values, completeness, operations, compatibility
  and observable failure guarantees.
- Validate agreed structural and completeness requirements without embedding
  consumers' eligibility or assessment calculations in the API or aggregate.
- Lifecycle rejection, authorisation, conflict handling and atomic completion
  remain part of the public contract.

## S3. Separate Stewardship Invariants from Consumer Policy

- The data-owning service enforces identity, ownership, lifecycle integrity,
  authorised attribution, retention, concurrency and transactional completeness.
- Consumer or specialist services own assessment, eligibility and allocation
  policies unless responsibility is explicitly assigned otherwise.
- Financial thresholds that trigger a means assessment and household-composition
  calculations are consumer/domain-policy concerns, not application-aggregate
  responsibilities.
- Recording an accepted assessment outcome does not transfer ownership of its
  calculation to the stewardship service.
- A consumer recommendation must not bypass the stewardship service's
  invariants.

## S4. Own Resource-Specific Access and Accountability Facts

- Durably record resource-specific facts that determine access, authority,
  accountability or retention.
- For event-sourced resources, reconstruct those facts from domain events and
  enforce them against authoritative sourced state.
- Distinguish the resource's owning office and current assignment from the
  caller's identity and entitlements.
- Identity and entitlement services remain authoritative for caller-side facts;
  do not copy the entire identity or workforce model into aggregates.
- Deciding who should receive work today is allocation policy. Once assignment
  determines who may decide, the accepted assignment is stewardship state.
- Leave dates, working patterns and team membership used only for allocation
  belong outside the application aggregate.
- If team membership or another workforce fact changes access or privileges,
  treat it as an authorisation input and revisit the boundary.

## S5. Enforce Access and Attribution at the Data-Owning Service

- Capture validated, minimum-necessary caller context explicitly before
  asynchronous dispatch. Do not rely on request-thread security context in
  handlers.
- Authorise writes against authoritative resource ownership, not a potentially
  stale query projection or a consumer's assurance.
- Where decisions require assignment, compare the authenticated actor with the
  current authoritative assignee and protect that check through commit.
- Derive attribution from authenticated context, not a caller-selected actor
  field. Record approved evidence of who acted, on what authority and against
  which resource state.
- An event log supports accountability; it does not by itself establish legal or
  cryptographic non-repudiation.
- Enforce read visibility before selecting, counting, sorting and paging data.
  Cover detail, list, history, documents and related-resource endpoints
  consistently.
- Fail closed for missing or unsupported access context. Choose
  inaccessible-resource responses deliberately.
- Keep credentials out of durable domain state. Review any persisted actor
  identifier separately under the retention policy.

## S6. Classify Stores by Authority and Recovery Behaviour

- Identify authoritative records, derived views and operational processing state
  explicitly.
- Document which information can be rebuilt, its required inputs and what
  becomes unavailable after deletion.
- Authoritative payload stores are not disposable projections, even when events
  reference them.
- Projection resets must clear only owned derived data, never authoritative
  payloads or event streams.
- A derived history view is not the sole authoritative audit record.

## S7. Minimise and Classify Data in Every Durable Surface

- Keep detailed sensitive content and unrestricted free text out of immutable
  events by default; use controlled payload storage where appropriate.
- Review identifiers, metadata, actor attribution, indices, logs, documents and
  backups. Thin identifiers are not necessarily anonymous or non-personal.
- Any retained personal data requires an explicit purpose, retention basis and
  approved treatment.
- Do not claim that payload isolation guarantees a single sensitive store,
  anonymous events or one-delete erasure.
- Authorised responses may intentionally hydrate sensitive content; preventing
  durable leakage is not a prohibition on legitimate access.

## S8. Design end-to-end Retention and Erasure

- Identify the facts that classify retention, start or reset a retention clock,
  establish dependencies, or place and release a hold.
- For event-sourced services, record those facts and changes in domain events;
  do not rely on mutable payloads or incidental database timestamps.
- Separate retention policy from the facts to which it applies. Record the
  policy version or retention decision where historical application must be
  evidenced.
- Define deletion behaviour across versions, drafts, projections, indices,
  documents, backups, reads, future commands and recovery.
- Distinguish deliberate deletion from unexplained missing data. Do not silently
  turn corruption into a legitimate retention outcome.
- Prevent replay, restoration and ordinary commands from unintentionally
  recreating erased information; define and verify the relevant controls.
- Retained identifiers and thin history still require classification and policy
  approval.

## S9. Enforce Required Transactional Completeness

- State which invariants require an all-or-nothing change and which permit
  intermediate states.
- The stewardship service owns the full transaction for required atomic changes:
  authoritative membership resolution, locking, validation, writes and rollback.
- Consumers must not assemble an atomic guarantee through separate API calls.
- If linked-case assignment must be atomic, assign every required member or
  none, and protect against concurrent membership and assignment changes.
- All competing mutation paths must participate in compatible coordination;
  locking only one endpoint does not establish the invariant.
- Use eventual consistency only where intermediate states are acceptable. Define
  pending states, retries, ordering, duplicate handling, failure visibility and
  reconciliation.
- Use a process manager or saga when persistent process state, timeouts or
  compensation justify it.
- Where external stores cannot share a transaction, define an explicit
  recoverable workflow rather than claiming atomicity.

## S10. Specify Retry, Completion and Delivery Semantics

- Define behaviour after repeated requests, concurrent changes and ambiguous
  network failures.
- Design and demonstrate idempotency where promised; do not assume every command
  is inherently idempotent.
- Distinguish acceptance, durable commit, query visibility and downstream
  delivery.
- A projection timeout does not undo a committed write; command completion does
  not make every read model current.
- Best-effort publication is not guaranteed delivery. At-least-once broker
  delivery does not guarantee that publication to the broker occurred.
- Define recovery, deduplication and operational ownership for each promised
  delivery guarantee.

## S11. Contain Framework Coupling and Dependency Risk

- Keep business decisions, state transitions and public contracts separable from
  framework and persistence adapters where practical.
- Record support, upgrade, operational, licensing and replacement implications.
- Treat free-tier constraints and paid capabilities as explicit local decisions,
  not universal architectural rules.
- Verify version-specific capability and licensing claims before depending on
  them.
- Turn important mechanically detectable boundaries into architecture checks,
  and use transaction, concurrency and recovery evidence appropriate to the
  risk.
