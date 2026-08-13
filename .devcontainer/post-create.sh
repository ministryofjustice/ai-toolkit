#!/usr/bin/env bash

set -euo pipefail

# Install pre-commit hooks
uvx pre-commit install

# Install APM dependencies declared in apm.yml
apm install
