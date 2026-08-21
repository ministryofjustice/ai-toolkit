# Ministry of Justice AI Toolkit

[![Ministry of Justice Repository Compliance Badge](https://github-community.service.justice.gov.uk/repository-standards/api/ai-toolkit/badge)](https://github-community.service.justice.gov.uk/repository-standards/ai-toolkit)

[![Open in Dev Container](https://raw.githubusercontent.com/ministryofjustice/.devcontainer/refs/heads/main/contrib/badge.svg)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/ministryofjustice/ai-toolkit)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ministryofjustice/ai-toolkit)

A central repository of toolkits for the Ministry of Justice. This repository
provides reusable toolkit packages that are distributed to consuming repositories via APM (Agent Package Manager),
ensuring consistent AI-assisted development practices across the organisation.

## Toolkits

Toolkits are organised by team.
Teams can define profession-specific instructions within their team directory,
alongside other toolkit assets (for example standards, prompts, skills,
plugins, and language conventions).

This section is generated from the `toolkits/` directory by `scripts/update-readme-toolkits.sh`.

<!-- BEGIN GENERATED TOOLKITS -->

| Team          | Toolkit                                                             | Contents                                         |
| ------------- | ------------------------------------------------------------------- | ------------------------------------------------ |
| Universal     | [universal](toolkits/universal)                                     | Universal instructions.                          |
| Data Platform | [platform-engineering](toolkits/data-platform/platform-engineering) | Data Platform platform engineering instructions. |
| Data Platform | [software-engineering](toolkits/data-platform/software-engineering) | Data Platform software engineering instructions. |

<!-- END GENERATED TOOLKITS -->

## Contributing toolkits

Teams are welcome to add their own families, teams, and toolkits to this repository.
If you want to contribute or evolve guidance for your area, open a pull request with
your proposed `apm.yml` and toolkit assets.

To scaffold a skeleton toolkit for a new team, run the helper script with the
team name (and an optional toolkit/profession name, which defaults to
`engineering`):

```bash
./scripts/new-team-toolkit.sh <team-name> [toolkit-name]
```

For example, `./scripts/new-team-toolkit.sh digital-services engineering`
creates `toolkits/digital-services/engineering/` with a starter `apm.yml` and an
empty `.apm/` folder, registers the toolkit in the root [apm.yml](apm.yml) and
[.claude-plugin/marketplace.json](.claude-plugin/marketplace.json), and refreshes
the generated toolkits table above. Add your team's instructions under `.apm/`,
then commit the changes and open a pull request.

## Setup Instructions

These toolkits are consumed with [APM (Agent Package Manager)](https://github.com/microsoft/apm).
You can install APM directly, or use a [development container](#using-a-development-container) to install it automatically.

### 1. Install APM

Follow the [APM installation guide](https://microsoft.github.io/apm/getting-started/installation/)
to install APM using your preferred method (Homebrew, Scoop, pip, and others).

Verify the installation:

```bash
apm --version
```

### 2. Declare the toolkits as dependencies

Create an `apm.yml` in the root of your repository (or run `apm init`) and add
the toolkits you want as dependencies.

Example:

```yaml
name: <name>
version: 1.0.0
description: APM project for <name>
author: <author>
targets:
  - copilot
dependencies:
  apm:
    - ministryofjustice/ai-toolkit/toolkits/universal#main
```

### 3. Install the dependencies

```bash
apm install
```

APM resolves the toolkits, pins them in `apm.lock.yaml`, and deploys their
assets into the detected harness (for example `.github/` for Copilot).

## Optional: discovering toolkits via the marketplace

This repository is also published as an APM marketplace - a curated index of the
toolkits above. The marketplace is a discovery and naming layer; it is not
required for the automated `apm install` flow described above, which resolves
dependencies directly from `apm.yml`.

It lets consumers register this repository once and then add toolkits by
friendly name rather than by repository path.

### 1. Register the marketplace

Register this repository as a marketplace:

```bash
apm marketplace add ministryofjustice/ai-toolkit
```

The marketplace is registered under its `name:` from [apm.yml](apm.yml) -
`ministryofjustice` - along with the toolkits it lists.

### 2. Install a toolkit by name

Install a toolkit using the `<plugin>@<marketplace>` format, where the plugin is
the toolkit's package name (for example `universal`):

```bash
apm install universal@ministryofjustice --target copilot
```

APM adds the toolkit to your `apm.yml`, resolves it, and integrates its
instructions into the harness (for Copilot, `.github/instructions/`).

### 3. Track the latest toolkit

Point the toolkit at `main` in `apm.yml` so installs track the latest version,
then reinstall:

```yaml
dependencies:
  apm:
    - ministryofjustice/ai-toolkit/toolkits/universal#main
```

```bash
apm install
```

How a toolkit is surfaced and installed can also vary by AI assistant. See
[Consume from any assistant](https://microsoft.github.io/apm/producer/publish-to-a-marketplace/#consume-from-any-assistant)
for the current, assistant-specific steps.

## Using a development container

If your repository uses [development containers](https://containers.dev/), you can
install APM automatically as part of your container setup instead of installing the
CLI by hand.

1. [Install](https://github.com/ministryofjustice/.devcontainer#adding-a-development-container-to-a-project) the Ministry of Justice [Development Container](https://github.com/ministryofjustice/.devcontainer) in your repository.
1. Add the APM feature to your `.devcontainer/devcontainer.json`:

   ```json
   {
     "features": {
       "ghcr.io/ministryofjustice/devcontainer-feature/apm:1": {}
     }
   }
   ```

1. Add `apm install` to your `.devcontainer/post-create.sh` script so dependencies are installed when the container is created:

   ```bash
   #!/usr/bin/env bash
   apm install
   ```

You still declare the required toolkit dependencies in `apm.yml` as shown above
for your chosen team.

## Maintaining the marketplace

The marketplace is defined by the `marketplace:` block in the root
[apm.yml](apm.yml) and compiled to
[.claude-plugin/marketplace.json](.claude-plugin/marketplace.json). To add or
update a toolkit:

1. Edit the `packages:` list in `apm.yml` (or use `apm marketplace package add ./toolkits/<path>`).
1. Regenerate and validate the artifact:

   ```bash
   apm pack --check-versions --check-clean
   ```

1. Commit both `apm.yml` and the generated `.claude-plugin/marketplace.json`.

Consumers track `main` directly (`#main`), so changes merged to `main` are
picked up on the next `apm install` without a separate release step.
