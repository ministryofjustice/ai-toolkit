---
description: Conventions for LAA Spring Boot application structure, security and observability.
source: https://github.com/ministryofjustice/ai-toolkit/blob/main/toolkits/legal-aid-agency/software-development/java/.apm/instructions/spring-boot.instructions.md
applyTo: "**/*.java,**/application*.yml,**/application*.yaml,**/application*.properties,**/logback-spring.xml,**/Dockerfile"
---

# Spring Boot Instructions

## Scope and Application Structure

- Apply this guidance only to modules using Spring Boot. Follow established architecture in existing services rather than introducing template layers automatically.
- Start new Java APIs from `ministryofjustice/laa-spring-boot-microservice-template` and use its initialisation tooling.
- In template-based services, keep API contracts and generated models in the API module and the executable application in the service module. Keep `bootJar` and `bootRun` disabled for the API module.
- Use valid Java packages beneath `uk.gov.justice.laa.<service>` for new services rather than copying kebab-case repository names into packages.
- Keep HTTP translation in controllers, use cases and business rules in services, persistence in repositories, and representation conversion in mappers.
- Use constructor injection and final dependencies; follow the repository's use of explicit constructors or Lombok `@RequiredArgsConstructor`.
- Replace template examples, placeholders, demo data and configuration before release. Complete the service readme, CODEOWNERS and deployment configuration.

## Object Mapping

- For new LAA Spring Boot services, use MapStruct for non-trivial object mapping, particularly API model/entity conversions.
- In existing services, follow the established mapping approach unless a migration is explicitly requested. Avoid introducing a mapping framework solely for trivial conversions.
- Where MapStruct is used, configure its annotation processor and use `@Mapper(componentModel = "spring")` with constructor injection.
- Keep mapping logic out of controllers and use-case logic. Make field names, null handling and writable fields explicit where they differ.
- Use controlled update mappings where appropriate; protect server-owned identifiers and audit fields.
- Prefer compile-time checks for unmapped target properties, with intentional omissions explicitly ignored.

## Errors and Security

- Centralise HTTP exception translation in the application's existing advice. For new API error contracts, use `@RestControllerAdvice` and Spring `ProblemDetail`/`ErrorResponse` rather than the deprecated common application-exception starter.
- Preserve existing error contracts unless changing them is explicitly required. Return safe failures rather than empty success results.
- Require authentication by default, with explicit public-endpoint exceptions. Apply least privilege and fail closed when identity or permission checks cannot be completed.
- Enforce authentication, endpoint authorisation and record-level access separately.
- Validate trusted issuers, signatures and accepted audiences. Use a single tenant unless cross-tenant access is explicitly required.
- Align endpoint permissions with Entra app registrations; use app roles for app-only calls and delegated scopes for user access as appropriate.
- Select security starters for actual requirements rather than adding every available starter.
- Load deployed secrets through approved platform mechanisms; keep local-development credentials and defaults out of deployed configuration.

## Logging and Deployment

- Preserve structured ECS JSON logs to stdout outside local development and Micrometer/Brave trace/span correlation where configured.
- Keep service name, version and environment accurate and preserve profile-based logging configuration.
- Keep secrets, personal data and entire request models out of logs, including sensitive generated `toString()` output.
- Configure Sentry for the actual service/environment and review sensitive-data handling.
- Use Actuator health checks and configure management access, ingress and probes explicitly; expose only required endpoints.
- Run containers as a non-root user and keep image, JAR and module names aligned.
