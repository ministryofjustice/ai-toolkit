---
description: LAA Java conventions for toolchains, Gradle, dependencies and code quality.
source: https://github.com/ministryofjustice/ai-toolkit/blob/main/toolkits/legal-aid-agency/software-development/java/.apm/instructions/java.instructions.md
applyTo: "**/*.java,**/*.gradle,**/*.gradle.kts,**/gradle.properties,**/gradle-wrapper.properties"
---

# Java Instructions

## Scope and Principles

- Follow the Copilot working instructions in this package when changing Java applications or their builds.
- Write clear, consistent code; prefer simple, readable solutions over clever abstractions.
- Keep modules cohesive and loosely coupled. Prefer composition over inheritance and keep business logic separate from framework and infrastructure concerns.
- Use the Java version declared by the Gradle toolchain. Upgrade Java, Spring Boot major versions or related libraries only when the task requires it.
- For new projects, confirm and use the currently approved LAA Java baseline rather than assuming a fixed version.

## Build and Dependencies

- Inspect `settings.gradle`/`settings.gradle.kts`, module build files, version catalogues, wrapper configuration and CI before changing the build.
- Use the checked-in Gradle wrapper locally and in CI.
- For new LAA Java services, use Gradle's Groovy DSL (`build.gradle` and `settings.gradle`), following the LAA convention plugins and microservice template. In existing repositories, preserve the established DSL unless migration is explicitly requested.
- For new Java modules, apply `uk.gov.justice.service.laa.laa-java-gradle-plugin`. For Spring Boot modules, use `uk.gov.justice.service.laa.laa-spring-boot-gradle-plugin`, which also applies the Java plugin.
- Apply the appropriate plugin to each Java subproject; a root declaration with `apply false` alone is not sufficient.
- Preserve established build conventions in existing services; propose an adoption plan rather than silently replacing their build.
- Pin explicit compatible plugin releases and centralise multi-project version selection in `pluginManagement`.
- Resolve released convention plugins from Maven Central; use snapshot repositories only for deliberate snapshot dependencies.
- Where the Spring Boot convention plugin is used, let it import the LAA dependency BOM rather than independently versioning managed dependencies.
- Document temporary dependency overrides with their reason and removal condition; remove them once dependency management supplies the required version.
- Keep Gradle toolchains, CI JDKs and container runtimes compatible.
- Keep Spring Boot 3/Jackson 2 and Spring Boot 4/Jackson 3 compatibility lines separate, including common starters and generator configuration.
- Keep dependencies minimal, patched and covered by automated update checks.

## Code Style and Formatting

- Treat the repository's Checkstyle and formatter configuration as authoritative for indentation, line length, imports and naming.
- For new template-based services, retain the supplied Google-style Checkstyle configuration and zero-warning setting.
- Keep methods focused and names intention-revealing; prefer early returns over deeply nested conditions.
- Comment only non-obvious intent and update relevant documentation when behaviour changes.
- Verify formatter configuration and tasks before relying on them as quality gates.

## Error Handling and Resources

- Use specific, intention-revealing exceptions for domain failures and preserve root-cause context when wrapping exceptions.
- Handle only failures that can be recovered from, except at explicit application boundaries.
- Bound outbound timeouts, connection pools and executor queues; retry only safe or idempotent operations.
- Close owned resources with try-with-resources or framework lifecycle management.
- Preserve interruption when handling `InterruptedException`.
- Avoid untrusted native Java deserialisation.
