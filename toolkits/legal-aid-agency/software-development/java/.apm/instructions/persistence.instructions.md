---
description: Conventions for LAA Java relational persistence, transactions and safe schema changes.
source: https://github.com/ministryofjustice/ai-toolkit/blob/main/toolkits/legal-aid-agency/software-development/java/.apm/instructions/persistence.instructions.md
applyTo: "**/*.java,**/db/migration/**,**/application*.yml,**/application*.yaml,**/application*.properties,**/*.gradle,**/*.gradle.kts"
---

# Persistence Instructions

## Scope and Defaults

- Apply this guidance only to modules using relational persistence; stateless services do not need a database.
- For new LAA relational services, use PostgreSQL, JPA/Spring Data JPA and Flyway. Keep H2 demonstration storage out of production.
- In existing services, preserve the established persistence and migration technologies unless a migration is explicitly required.
- Apply JPA- and Flyway-specific instructions only where those technologies are adopted.

## Queries and Transactions

- Keep persistence entities separate from external API models and map entities rather than serialising persistence graphs.
- Use bound parameters or parameterised queries; never concatenate external values into SQL. Allowlist dynamic identifiers that cannot be bound.
- Treat SQL scanning as supplementary detection, not a substitute for parameterisation or validation.
- Put Spring `@Transactional` boundaries around coherent service operations, including multi-step writes. Check proxy invocation and rollback semantics so the intended transaction actually applies.
- Avoid holding database transactions across slow external calls; define consistency and recovery behaviour where a use case spans a database and another system.
- Review query counts and fetch behaviour to avoid N+1 queries.

## Schema Changes

- Use Flyway as schema owner where adopted; platform infrastructure provisions database instances and credentials.
- Follow the repository's configured migration locations and naming. New template-based services use `src/main/resources/db/migration` and names such as `V1__create_items_table.sql`.
- Never modify a migration that may have been applied to a shared environment; create a new versioned migration.
- Keep Hibernate schema creation and updates disabled in deployed environments; use `ddl-auto: none` or explicitly agreed schema validation.
- Keep demonstration seed data out of deployed migrations unless it is deliberately required reference data.
- Assess backwards compatibility, locking, constraints, indexes, data preservation and rollback implications. Prefer expand/contract changes.
- Test clean schema creation and relevant upgrade paths using the adopted migration tooling.
- Document recovery or forward-fix for destructive changes; application rollback alone cannot restore lost data.
- Do not execute destructive migrations against shared or deployed databases without explicit authorisation and human review of the migration and recovery plan.
