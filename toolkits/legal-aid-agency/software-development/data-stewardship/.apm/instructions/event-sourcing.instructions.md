---
description: Working event-sourcing principles from the Access Data Stewardship prototype, for testing and evolution across domains.
source: https://github.com/ministryofjustice/ai-toolkit/blob/main/toolkits/legal-aid-agency/software-development/data-stewardship/.apm/instructions/event-sourcing.instructions.md
---

# Event-Sourced Stewardship Principles

## Scope and Review Status

- This records the current working position informed primarily by the Access
  Data Stewardship prototype, not a target architecture or proven shared design.
- Test the principles against other stewardship domains and record challenges,
  evidence and changes with the previous position and reasoning preserved.
- These proposed rules supplement the data-stewardship instructions only where a
  service already uses, or has explicitly chosen, event sourcing.
- Axon-specific mechanisms apply only to Axon services and must match the
  selected framework version and event store.
- Do not mandate Axon, PostgreSQL, a particular aggregate layout or commercial
  feature restrictions for another service.
- Preserve accepted service decisions and persisted compatibility; raise
  conflicts for review rather than silently changing existing behaviour.

## E1. Source Stewardship State from Domain Events

- Event streams are authoritative for recorded transitions and aggregate control
  state, including resource-specific ownership and assignment where they govern
  authority.
- Keep each aggregate's state to the facts needed to enforce its stewardship
  invariants.
- Do not query asynchronous projections to decide aggregate command validity;
  E8 applies this to the whole command path.
- Command handlers may load authoritative referenced payloads for validation or
  to construct the next payload; event-sourcing handlers must not perform that
  I/O.
- Detailed payloads may be authoritative outside the stream. Do not claim that
  thin events can reconstruct content which they never contained.
- Draw consistency boundaries around invariants and independent concurrent
  activity, not merely lifecycle or ownership.
- A rule spanning aggregates needs an explicit modelling or coordination
  decision, not an automatic prohibition on transactions.

## E2. Make the Owning Stream the Concurrency Authority

- Every accepted mutation governed by an aggregate must participate in that
  aggregate stream's concurrency check, even if the detailed write is in a
  separate payload table.
- A draft-body mutation must append an event associated with the owning stream;
  a thin event is sufficient when the content belongs outside the log.
- Commit or roll back the payload mutation and event together. Submission must
  consistently seal content and close or remove its draft.
- A stale writer must conflict or undergo a deliberate, bounded and safe retry;
  it must not silently overwrite accepted work.
- Do not substitute a projection timestamp or payload version for stream
  concurrency.
- Distinguish stream position, public optimistic-lock versions and
  payload-version pointers; they need not advance together.
- Stream concurrency protects one consistency boundary. Multi-aggregate
  invariants may additionally require transactional locks and coordinated
  appends across streams.

## E3. Event Every Retention-Relevant Change

- Retention-driving state must be reconstructible from events without reading
  mutable or erased payloads.
- Include application type or a sufficient retention classification when it
  determines the schedule, and record subsequent changes.
- Record accepted draft mutations and their authoritative occurrence times when
  they reset the retention clock; do not infer activity from an incidental
  database update.
- Record linking, unlinking, closure, submission, holds and releases wherever
  they affect a retention trigger or dependency.
- Facts may live on different owning streams, such as application and group
  streams. Define how the retention view combines them and establishes
  sufficient consistency before deletion.
- Persist the minimum sufficient facts, not sensitive inputs merely because they
  influence classification. Review those facts under the data-minimisation
  policy.
- If a required retention fact was never recorded historically, define an
  explicit migration or unknown-state treatment; do not invent history during
  replay.

## E4. Keep Atomic Writes and Coordination Honest

- Prove that payload writes and referencing events share the intended
  transaction, including rollback after either write fails.
- For atomic linked-group operations, resolve authoritative membership and
  protect it through commit across all competing paths.
- Do not use lagging query projections as the authoritative membership or
  assignment source for such a transaction.
- External document storage and message brokers do not automatically participate
  in the database transaction; define cleanup, recovery or publication
  guarantees separately.
- In Axon, choose subscribing or streaming processors according to the required
  transaction, failure, replay and scaling semantics.
- Subscribing processing is not proof of multi-aggregate atomicity. Streaming
  processing is not a substitute for an all-or-nothing invariant.
- A read-side precondition is acceptable only where its staleness and
  monotonicity assumptions are justified and recorded as E8 requires.
  Human-speed actors do not eliminate races.

## E5. Separate Replay from Live Side Effects

- Aggregate replay must derive state only from recorded facts: no repositories,
  network calls, current security context, clocks or random generators.
- Projection rebuilds must use declared, reproducible inputs, including pinned
  payload versions where needed.
- Keep irreversible publication and other external actions outside replay paths;
  a reset must not resend historical business notifications.
- Make projection handling tolerant of retries and ensure reset handlers clear
  only their own derived state.
- Test transient recovery and permanent failures without silently skipping
  events.
- Use supported Axon processor lifecycle and reset APIs; do not edit live token
  rows manually.

## E6. Treat Persisted Events as Long-Lived Contracts

- Stored type names, serialised fields, revisions and business meanings are
  compatibility obligations.
- Renaming or moving an event, removing a field, making an absent value
  mandatory, or changing serialiser behaviour is not a mechanical refactor.
- Preserve historical interpretation through compatible handling, new event
  types or deliberate, deterministic upcasting.
- Do not query mutable databases or external services from an upcaster to invent
  missing historical facts.
- Use historical serialised payloads to prove deserialisation, restored state
  and subsequent command behaviour.
- Cover projection replay and real event-store serialisation where affected;
  compilation and tests constructing only new events are insufficient.
- Changing future event writes does not remove sensitive fields already
  persisted. Historical remediation needs a separate decision.

## E7. Demonstrate Boundaries with Focused Evidence

- Use pure decision/state-transition tests for domain rules and aggregate
  fixtures for sourced state and command outcomes.
- Use real persistence integration tests for transaction rollback, concurrency,
  event tagging, serialisation and database controls.
- Exercise edit/upload/submit races and all-or-nothing group changes when those
  guarantees are affected.
- Assert that prohibited sensitive values are absent from stored event payloads
  and metadata.
- Reconstruct representative state from raw stored events outside framework
  replay machinery to demonstrate bounded portability.
- Record which aggregates and event histories that proof covers; a raw-replay
  test does not establish a complete, inexpensive framework exit.
- Do not infer runtime, production or privacy acceptance from a passing unit or
  fixture suite.

## E8. Keep Command-Side Decisions Off the Read Model

- Apply this to the whole command path: controllers, application services,
  command handlers, aggregates, process managers, sagas and helpers they call,
  not only aggregate command validity. S12 states the general stewardship rule.
- Base decisions that enforce invariants on authoritative state, including the
  owning stream, authoritative payloads classified under S6 and facts owned by
  authoritative external services. Do not treat query projections, read-model
  repositories or projection entities as authority for command acceptance,
  authorisation or required routing.
- Do not silently promote projected values into authoritative facts in new
  events or payloads. A deliberate record of a historical observation must
  identify its source, observation time and freshness limits, and must not be
  treated as proof of current authoritative state.
- Do not use projections for uniqueness, existence or duplicate checks that
  must hold. Protect the check through commit with stream concurrency, atomic
  create-if-absent, a unique constraint on owned transactional state or another
  mechanism that enforces the invariant. A deterministic identifier alone is
  not atomic enforcement.
- Process managers and sagas may use handled events, their persisted process
  state and authoritative service or payload reads where required. Do not use
  another processor's projection as invariant authority. Protect local process
  transitions against concurrent handling, and require receiving command
  handlers to enforce their own invariants against authoritative state.
- A command response must not present projection state as the committed
  result. Return what the command established, such as identifiers and stream
  versions, and let callers read the model under its stated freshness.
- Where a read-side check is genuinely acceptable, record its purpose, tolerated
  staleness, the outcome if a race occurs and how that outcome is detected or
  corrected in a service decision record. Treat it as advisory, never as the
  invariant's only protection. A stale advisory result may still reject valid
  work; document that observable behaviour too.
- Make the boundary mechanically checkable where practical, for example with an
  architecture test preventing command-side packages from depending on query
  repositories or projection entities.
