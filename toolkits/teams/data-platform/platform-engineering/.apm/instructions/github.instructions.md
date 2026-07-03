---
description: This file provides instructions for using GitHub to report bugs and create pull requests in the `ministryofjustice/data-platform` repository.
---

# GitHub Instructions

- If a user asks you to raise a bug or issue on GitHub, do so in the `ministryofjustice/data-platform` repository, unless they specify otherwise.
- When raising an issue include the label `platform-engineering` to ensure it is visible to the right team.
- Ask the user which squad the issue should be assigned to, and assign it to the appropriate label for that squad (e.g. `squad-one` or `squad-two`).

## Bug Reporting

When reporting a bug, use the current session context first (recent prompts, commands, errors, and changed files) to draft the issue description.
Only ask follow-up questions when required information is missing.

Include the following information in the issue description:

- A clear and concise description of the bug
- Steps to reproduce the bug (derived from session context where possible)
- Expected behaviour
- Actual behaviour (include exact error messages when available)
- Any relevant screenshots or error messages

## Pull Requests

When creating pull requests:

- Write the PR title in Conventional Commits format: `<type>(<scope>): <description>`.
- The PR title must describe the overall outcome of the PR, not a single commit.
- If the first commit subject already reflects the full PR scope, you may reuse it as the PR title.
- Reference: [Conventional Commits](https://www.conventionalcommits.org/)
- Do not include emojis in the title.
- Add labels based on the files and systems changed.
- If the PR changes Terraform code (`*.tf`, `*.tfvars`, or `terraform/` paths), add the `terraform` label.
- The PR description must include:
  - Summary
  - Reason for Change
  - Changes Made
  - Testing (facts only; if not run, state that clearly)
  - Release Notes / Upgrade Notes (include links when applicable)
- In the PR description, use inline links to the relevant files or sections in the PR diff.
- Use one link style consistently across all sections of the PR description.

When creating a pull request, report testing results as facts only.
If this repository has no relevant tests, state "Testing not applicable" and explain briefly.
If tests were not run, state "Testing not run" and explain why.
If the result is unknown, state "Testing unknown".

## Labels

Do not invent labels. Use existing repository labels only. If none match, ask the user to choose from existing labels.
