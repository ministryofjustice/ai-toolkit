---
description: Conventions for LAA Java tests, coverage verification and CI quality gates.
source: https://github.com/ministryofjustice/ai-toolkit/blob/main/toolkits/legal-aid-agency/software-development/java/.apm/instructions/testing.instructions.md
applyTo: "**/*.java,**/*.gradle,**/*.gradle.kts,**/config/checkstyle/**,.github/workflows/*.yml,.github/workflows/*.yaml,**/.pre-commit-config.yaml"
---

# Testing Instructions

## Test Structure and Behaviour

- Use JUnit Jupiter/JUnit Platform and Spring Boot test support for new services; follow established compatible test conventions in existing repositories.
- Use Mockito and MockMvc/controller slices where appropriate. Test behaviour and contracts rather than framework internals.
- Keep tests deterministic and prefer real collaborators for in-process logic; mock external boundaries where needed.
- Inspect the consumed convention plugin's configuration, Gradle source sets, task wiring and existing tests before choosing test directories. Resolve differences between documentation and implementation against the build actually used.
- For conventional builds, unit/slice tests use `src/test/java`. Use `src/integrationTest/java` only when the configured integration source set discovers it; do not assume either that path or `src/main/integrationTest` universally.
- Confirm that added tests are discovered and executed by the chosen tasks, including any test filters.
- For PostgreSQL-backed services, use Testcontainers for database integration tests, run migrations and match the deployed database major version.
- Import the template's `TestcontainersConfig` where it is present and appropriate.
- Cover changed behaviour, mapping edge cases, database constraints, transaction rollback, migrations and downstream failures as relevant.

## Coverage and Quality Gates

- Maintain or improve configured JaCoCo requirements. Identify the actual counter, threshold and exclusions before changing coverage configuration.
- Never reduce coverage requirements or exclude new business logic to make verification pass.
- Keep Checkstyle enabled and generated-code exclusions limited to generated sources.
- Keep local and CI commands aligned and document canonical build, lint and test entry points.
- Run the repository's build, coverage and integration checks explicitly. Where those tasks exist, template-based builds use `./gradlew build jacocoTestCoverageVerification integrationTest`.
- Verify task dependencies rather than assuming `build` or `check` includes integration tests and coverage verification.
- A declared formatter or Pact plugin is not evidence of an effective formatting gate or contract-test suite; inspect configuration and tasks.

## CI and Repository Controls

- Preserve dependency updates, Snyk application/container checks and report publication, with enforceable required checks.
- Follow the supplied MOJ DevSecOps pre-commit approach and pin external GitHub Actions to full commit SHAs.
- Configure repository permissions, branch protection, required reviews and security integrations; workflow files alone do not configure repository settings.
- Retain deployment security controls when editing CI and document any proposed exceptions for human review.
