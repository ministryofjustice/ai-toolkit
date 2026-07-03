---
description: Conventions for building secure, maintainable Django applications.
applyTo: "**/*.py,**/templates/**/*.html"
---

# Django Instructions

## Scope and Principles

- Treat this file as the default guidance for day-to-day Django development across this repository.
- These instructions build on the general Python guidance; apply both, and prefer the more specific rule where they overlap.
- Default to Django LTS releases for production projects; if using non-LTS, document the reason and planned upgrade path.
- Prefer Django built-ins over third-party packages when they meet requirements.

## Project Structure and Routing

- Organise code by app/module with clear ownership boundaries.
- Keep app URL patterns in app-level `urls.py` files and include them from the project URLconf.
- Use URL names and namespaces consistently.
- Use `reverse()` and `reverse_lazy()` for URL references; do not hardcode URL paths.

## Settings and Configuration

- Use split, environment-specific settings layered over a shared base (for example `common`, `local`, `test`, `production`).
- Keep production settings minimal and security-focused; keep environment differences explicit.
- Load secrets from environment variables; never commit them.
- Keep environments at parity; treat backing services (database, cache, queues) as attached resources configured per environment.
- Keep processes stateless and disposable: no local session/file state, fast startup, graceful shutdown.

## Models and Database

- Use a custom user model from the start of a new project.
- Keep model `__str__` methods simple and human-readable.
- Add custom managers/querysets only when encapsulating repeated business logic.
- Enforce data invariants (valid ordering, required relationships, uniqueness, valid status transitions) at the model layer.
- Be deliberate about query counts; avoid N+1 queries in list and detail views.
- Cache expensive or repeated queries/computations deliberately, with a clear invalidation strategy.
- Prefer the ORM; if raw SQL is unavoidable, use parameterised queries and never interpolate user input into query strings.
- Wrap multi-step writes in a transaction, and use row locking (for example `select_for_update`) where concurrent updates could race.

## Views, Permissions, and Context

- Prefer class-based generic views for common CRUD patterns.
- Use function-based views only when they are clearly simpler or better suited to custom flow.
- Keep permission checks explicit and close to entry points.
- Return appropriate HTTP responses for expected failure modes (for example 400, 403, 404).
- Keep context processors pure: no side effects and no expensive per-request queries.
- Offload slow or blocking work (email, reports, external calls, heavy processing) to a background task queue instead of the request/response cycle.

## Authentication and Access Defaults

- Default to requiring authenticated users for the vast majority of views.
- Apply auth-by-default centrally where possible (for example a login-required middleware or equivalent request gate) and maintain an explicit allowlist for public endpoints.
- For class-based views, use `LoginRequiredMixin` unless the endpoint is intentionally public.
- For function-based views, use `@login_required` unless the endpoint is intentionally public.
- Document public-view exceptions clearly (for example marketing/product pages, health checks, and auth entry points).

## Forms and Validation

- Use `ModelForm` for model-backed forms unless a plain `Form` is a better fit.
- Keep validation deterministic and centralised.
- Use field-level validation for single-field rules and form/model-level validation for cross-field rules.

## Admin

- Register models with `ModelAdmin` classes and keep admin pages usable for the data they manage.
- Treat the admin as a high-value target: restrict access tightly and harden it in production rather than relying on defaults.

## API Guidance (When Applicable)

- Keep request/response contracts explicit; serialize data without leaking internal model details.
- Implement pagination/filtering for collection endpoints.
- Document APIs with OpenAPI, kept in sync with behaviour in the same change.
- Cover authentication, error shapes, pagination, and versioning in API docs.

## HTMX Guidance (Optional)

- Use HTMX when it meaningfully simplifies interactions without introducing a full client-side SPA.
- Prefer server-rendered HTML partials for HTMX responses and keep fragment templates small and reusable.
- Keep business logic in views/services, not in HTMX attributes.
- Preserve progressive enhancement where practical: core flows should still work with standard full-page requests.
- Test HTMX endpoints for both fragment and fallback behaviour when both are supported.

## Templates

- Use template inheritance (`extends`/`block`) for page structure, and `{% include %}` for repeated or shared components.
- Keep partials small and focused; name them clearly (for example a leading-underscore convention) and keep them in a predictable location.
- Pass explicit context to includes with `{% include ... with ... only %}` rather than relying on the full parent context.
- Keep logic out of templates; compute values in views or services and pass them in.

## Testing Strategy

- Follow the general Python testing guidance; the points below are Django-specific.
- Use pytest-django and prefer its built-in fixtures over custom wrappers.
- Use the database only when a test needs it; keep non-DB tests pure and fast.
- Focus on business logic, permissions, context behaviour, and integration boundaries.
- Test project behaviour and contracts, not Django/framework internals.
- Do not mock Django internals or the ORM in ways that hide integration regressions.
- Keep unit-style and integration-style tests in the same module when it improves local discoverability.

## Code Quality and Dependencies

- Follow the general Python guidance for style, linting, type hints, docstrings, dependency pinning, and packaging (uv).
- Run `make lint` (ruff) before committing. Provide canonical lint/format/test commands via a `Makefile` or the readme, and keep CI aligned with them.
- When behaviour, signatures, settings, or side effects change, update relevant docstrings in the same change.
- Follow current documented Django best practices unless there is a clear, local reason not to.

## Frontend and Static Assets (When the App Has a Frontend)

- Build UIs with GovUK Frontend [components](https://design-system.service.gov.uk/components/), [MOJ Components](https://design-patterns.service.justice.gov.uk/components/) and [X gov prototype components](https://govuk-prototype-components.x-govuk.org/).
- Build CSS from SCSS via a canonical command and commit compiled assets to the project's static path.

## Security Defaults

- Keep CSRF protection enabled for all state-changing requests.
- In production: secure cookies (Secure, HttpOnly, appropriate SameSite), HSTS, and restricted allowed hosts.
- Keep `DEBUG=False` outside local development.
- Keep health check endpoints lightweight and public only when infrastructure requires it.

## Observability Defaults

- Follow the general Python logging guidance; the points below are Django/service-specific.
- Include a request/correlation ID in logs and return it in responses where practical.
- Expose separate liveness and readiness checks (readiness should verify critical dependencies).
- Use Sentry for error capture; rely on its automatic unhandled-exception capture and avoid manual double-capture.
- For handled exceptions, either log with context or send to Sentry, not both.

## Error Handling Defaults

- Follow the general Python error-handling guidance, including the use of custom exception classes for domain failures.
- Translate domain exceptions into appropriate HTTP/API responses without leaking internal implementation details.

## Schema Change Workflow (When Applicable)

- Applies to projects running migrations against shared or production data.
- Use expand/contract: ship additive changes first, then remove old schema in a later release.
- Keep migrations small, focused, and reversible where possible.
- Test high-risk or long-running migrations on staging, and document a fallback plan in the PR.

## Exceptions

- If you must deviate from these defaults, document the reason in the PR or code comments near the deviation.
- Choose the simplest deviation that solves the requirement without weakening security or test reliability.
