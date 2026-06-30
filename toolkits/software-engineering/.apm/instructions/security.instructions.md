---
description: Application security standards for engineering work.
---

# Security Standards

- Run regular vulnerability scans (e.g. OWASP, SonarQube) and keep dependencies updated.
- Use secure authentication (OAuth 2.0, JWT).
- Encrypt sensitive data at rest (AES 256) and in transit (TLS).
- Use parameterised queries to prevent SQL injection.
- Validate all relevant inputs, both server and client side.
- Don't implement your own cryptography; use established, well-reviewed libraries.
