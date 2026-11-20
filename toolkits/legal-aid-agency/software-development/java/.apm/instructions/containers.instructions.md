---
description: Mandatory LAA base container images and Dockerfile conventions for Java services.
source: https://github.com/ministryofjustice/ai-toolkit/blob/main/toolkits/legal-aid-agency/software-development/java/.apm/instructions/containers.instructions.md
applyTo: "**/Dockerfile,**/Dockerfile.*,**/*.Dockerfile,**/Containerfile,**/.dockerignore,**/docker-compose*.yml,**/docker-compose*.yaml,**/compose*.yml,**/compose*.yaml,**/*.gradle,**/*.gradle.kts,.github/workflows/*.yml,.github/workflows/*.yaml"
---

# Container Instructions

- LAA's Architecture Review Board (ARB) requires containerised Java services to use the [LAA base container images](https://github.com/ministryofjustice/laa-base-container-images). Follow its [Java catalogue](https://github.com/ministryofjustice/laa-base-container-images/blob/main/images/java/README.md) for tags and usage.
- Base the runtime stage on `ghcr.io/ministryofjustice/laa-base-container-images/java` with the implementation tag for the Gradle toolchain's Java version, for example `25-corretto-alpine`. Do not use other runtime bases, such as `eclipse-temurin` or `amazoncorretto`.
- Build deployable images from the repository's Dockerfile, and have pipelines build, scan and deploy that image. Do not use `bootBuildImage`, Jib or other builders that choose their own base image.
- Where an existing service uses another base image or builder and migration is outside the task, flag it and propose migration rather than extending it or changing it silently.
- If no variant meets a demonstrated need, raise an issue on the base images repository rather than building a bespoke base image.
- The images are runtime-only and run as `appuser` (UID 1001) in `/app`: build in a separate stage, copy artefacts with `--chown=1001:1001`, do not create another user, and use `USER root` only briefly for package installation.
- Setting `JAVA_TOOL_OPTIONS` replaces the base image defaults; carry them over unless deliberately changing them.
