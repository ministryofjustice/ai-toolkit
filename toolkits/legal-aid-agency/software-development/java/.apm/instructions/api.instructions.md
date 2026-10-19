---
description: Conventions for LAA Java API contracts, generated code and request validation.
source: https://github.com/ministryofjustice/ai-toolkit/blob/main/toolkits/legal-aid-agency/software-development/java/.apm/instructions/api.instructions.md
applyTo: "**/*.java,**/*openapi*.yml,**/*openapi*.yaml,**/*openapi*.json,**/open-api-specification.yml,**/open-api-specification.yaml,**/*.gradle,**/*.gradle.kts"
---

# API Instructions

## Scope and Contracts

- Apply this guidance to Java API modules; apply generation-specific rules only where generated OpenAPI contracts are used.
- Use contract-first OpenAPI development for new template-based APIs. In existing services, identify the current contract workflow before changing it.
- Define endpoints, schemas, constraints and responses in the source contract before implementing generated-contract changes.
- Preserve backwards compatibility unless a breaking contract change is explicitly required and approved.
- For template-based services, generate Spring API interfaces and models with OpenAPI Generator before compilation and implement those interfaces in service-module controllers.
- Treat generated models as contract output rather than maintaining parallel handwritten versions. Update the specification or generator configuration and regenerate.

## Validation and Responses

- Validate external request models at entry points using Jakarta Bean Validation and contract-defined constraints.
- Keep cross-field and business-rule validation in the service/domain layer.
- Return contract-defined status codes, headers, response models and errors without exposing internal implementation details.
- Bound growing collection reads with contract-defined pagination.
- Cover changed contracts with tests, including malformed requests, validation failures, negative authorisation scenarios and status/header/error behaviour where relevant.
