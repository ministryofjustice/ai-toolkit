# Ministry of Justice AI Toolkit

[![Ministry of Justice Repository Compliance Badge](https://github-community.service.justice.gov.uk/repository-standards/api/ai-toolkit/badge)](https://github-community.service.justice.gov.uk/repository-standards/ai-toolkit)

[![Open in Dev Container](https://raw.githubusercontent.com/ministryofjustice/.devcontainer/refs/heads/main/contrib/badge.svg)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/ministryofjustice/ai-toolkit)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ministryofjustice/ai-toolkit)

A central repository of GitHub Copilot instructions for the Ministry of Justice. It
provides reusable agent packages that are distributed to consuming repositories via APM (Agent Package Manager),
ensuring consistent AI-assisted development practices across the organisation.

## Toolkits

Toolkits are organised by family and profession/domain. Profession-level toolkits
contain technology-specific instruction files (for example, language conventions)
that apply only to matching file types.

This section is generated from the `toolkits/` directory by `scripts/update-readme-toolkits.sh`.

<!-- BEGIN GENERATED TOOLKITS -->
### Data Platform family

| Toolkit | Contents |
| ------- | -------- |
| [platform-engineering](toolkits/data-platform/platform-engineering) | Data Platform platform engineering instructions. |
| [software-engineering](toolkits/data-platform/software-engineering) | Data Platform software engineering instructions. |

### Universal toolkit

| Toolkit | Contents |
| ------- | -------- |
| [universal](toolkits/universal) | Universal instructions. |

<!-- END GENERATED TOOLKITS -->

Each toolkit is an APM package: an `apm.yml` manifest plus
`.apm/instructions/*.instructions.md` files. See each toolkit directory for the
full list of instructions and source-aligned guidance.

## Contributing toolkits

Teams are welcome to add their own families, teams, and toolkits to this repository.
If you want to contribute or evolve guidance for your area, open a pull request with
your proposed `apm.yml` and instruction files.

## Setup Instructions

These toolkits are consumed with [APM (Agent Package Manager)](https://github.com/danielmeppiel/apm).

### 1. Install APM

<!-- jscpd:ignore-start -->

**macOS / Linux:**

```bash
curl -sSL https://aka.ms/apm-unix | sh
```

**Windows (PowerShell):**

```powershell
irm https://aka.ms/apm-windows | iex
```

Verify the installation:

```bash
apm --version
```

For Homebrew, Scoop, pip, or other install methods, see the [APM installation guide](https://microsoft.github.io/apm/getting-started/installation/).

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
    - ministryofjustice/ai-toolkit/toolkits/universal#1.0.0
```

<!-- jscpd:ignore-end -->

### 3. Install the dependencies

```bash
apm install
```

APM resolves the toolkits, pins them in `apm.lock.yaml`, and deploys their
instructions into the detected harness (for example `.github/` for Copilot).

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
for your chosen family.
