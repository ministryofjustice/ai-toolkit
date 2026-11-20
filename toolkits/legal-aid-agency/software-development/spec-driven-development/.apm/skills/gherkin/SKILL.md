---
name: gherkin
description: Write or review Gherkin features and, when requested, step definitions using the project's behaviour and test conventions.
---

# Gherkin

Read [the Gherkin guidelines](references/gherkin-guidelines.md) before writing
or reviewing scenarios. Use the project's domain vocabulary, relevant
specifications and tickets, and `TECHNOLOGY.md` if present.

Write focused, independently executable behaviour examples. Link each feature
to its source specification or ticket when one exists, using the project's
existing convention; do not invent a reference. Keep links outside step text.

When step definitions are requested, inspect the existing test framework and
steps first. Reuse matching steps, follow established conventions and make
assertions observable. Do not assume a framework or install one without
agreement; explain missing infrastructure or other blockers.

Before finishing, check the feature against the guidelines, including syntax,
Given/When/Then order, independent scenarios and observable outcomes. Run the
project's existing Gherkin parser or test command where available and
appropriate; run the affected tests when step definitions are added. Report
what was checked, any failures and any validation that could not be run.
