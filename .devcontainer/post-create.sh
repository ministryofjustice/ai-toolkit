#!/usr/bin/env bash

set -euo pipefail

# Install pre-commit hooks
uvx pre-commit install

# Update APM dependencies to the latest matching Git references
apm update --yes
