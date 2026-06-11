---
description: Application security standards for engineering work.
---

# Security Standards

- Run regular vulnerability scans (e.g. OWASP, SonarQube) and keep dependencies updated.
- Use secure authentication (OAuth 2.0, JWT).
- Encrypt sensitive data at rest (AES 256) and in transit (TLS).
- Use parameterised queries to prevent SQL injection.
- Validate all relevant inputs, both server and client side.

> Source: [Justice Digital software engineering standards](https://technical-guidance.service.justice.gov.uk/documentation/standards/justice-digital-software-engineering-standards.html)
