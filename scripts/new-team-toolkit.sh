#!/usr/bin/env bash
set -euo pipefail

# Scaffolds a skeleton toolkit for a new team under toolkits/<team>/<toolkit>/,
# and registers it in the root apm.yml and the compiled marketplace.json.
#
# Usage: scripts/new-team-toolkit.sh <team-name> [toolkit-name]
#   <team-name>     Required. Slug for the team (for example "digital-services").
#   [toolkit-name]  Optional. Slug for the profession/toolkit. Defaults to "engineering".

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLKITS_DIR="$ROOT_DIR/toolkits"
APM_MANIFEST="$ROOT_DIR/apm.yml"
MARKETPLACE_JSON="$ROOT_DIR/.claude-plugin/marketplace.json"

usage() {
  echo "Usage: scripts/new-team-toolkit.sh <team-name> [toolkit-name]" >&2
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 1
fi

TEAM_NAME="$1"
TOOLKIT_NAME="${2:-engineering}"

validate_slug() {
  local label="$1"
  local value="$2"

  if [[ ! "$value" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
    echo "Invalid $label '$value': use lowercase letters, numbers and hyphens (for example 'digital-services')." >&2
    exit 1
  fi
}

validate_slug "team name" "$TEAM_NAME"
validate_slug "toolkit name" "$TOOLKIT_NAME"

title_case() {
  local words=() word
  for word in ${1//-/ }; do
    words+=("${word^}")
  done
  echo "${words[*]}"
}

PACKAGE_NAME="${TEAM_NAME}-${TOOLKIT_NAME}"
TOOLKIT_DIR="$TOOLKITS_DIR/$TEAM_NAME/$TOOLKIT_NAME"
REL_TOOLKIT_DIR="toolkits/$TEAM_NAME/$TOOLKIT_NAME"
TEAM_DISPLAY="$(title_case "$TEAM_NAME")"
TOOLKIT_DISPLAY="$(title_case "$TOOLKIT_NAME")"
DESCRIPTION="$TEAM_DISPLAY $TOOLKIT_DISPLAY Copilot instructions"

if [[ -d "$TOOLKIT_DIR" ]]; then
  echo "Toolkit already exists at $REL_TOOLKIT_DIR" >&2
  exit 1
fi

if grep -q "^      source: ./$REL_TOOLKIT_DIR$" "$APM_MANIFEST"; then
  echo "A package for $REL_TOOLKIT_DIR is already registered in apm.yml" >&2
  exit 1
fi

# 1. Create the skeleton toolkit files.
mkdir -p "$TOOLKIT_DIR/.apm"

cat >"$TOOLKIT_DIR/apm.yml" <<EOF
---
name: $PACKAGE_NAME
version: 1.0.0
description: $TOOLKIT_DISPLAY Toolkit
author: $TEAM_DISPLAY
targets:
  - copilot
dependencies:
  apm: []
  mcp: []
includes: auto
scripts: {}
EOF

# 2. Register the package in the root apm.yml marketplace block (appended at EOF,
#    where the packages: list lives).
[[ -n "$(tail -c1 "$APM_MANIFEST")" ]] && echo >>"$APM_MANIFEST"
cat >>"$APM_MANIFEST" <<EOF

    - name: $PACKAGE_NAME
      description: $DESCRIPTION
      source: ./$REL_TOOLKIT_DIR
      version: 1.0.0
EOF

# 3. Add the matching plugin entry to the compiled marketplace.json.
PACKAGE_NAME="$PACKAGE_NAME" DESCRIPTION="$DESCRIPTION" REL_TOOLKIT_DIR="$REL_TOOLKIT_DIR" \
  python3 - "$MARKETPLACE_JSON" <<'PY'
import json
import os
import sys

path = sys.argv[1]

with open(path, encoding="utf-8") as handle:
    data = json.load(handle)

plugins = data.setdefault("plugins", [])
plugins.append(
    {
        "name": os.environ["PACKAGE_NAME"],
        "description": os.environ["DESCRIPTION"],
        "version": "1.0.0",
        "source": "./" + os.environ["REL_TOOLKIT_DIR"],
    }
)

with open(path, "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2)
    handle.write("\n")
PY

# 4. Refresh the generated toolkits table in the README.
if [[ -x "$ROOT_DIR/scripts/update-readme-toolkits.sh" ]]; then
  "$ROOT_DIR/scripts/update-readme-toolkits.sh"
fi

echo "Created toolkit '$PACKAGE_NAME' at $REL_TOOLKIT_DIR"
echo "Next steps:"
echo "  - Add your team's instructions under $REL_TOOLKIT_DIR/.apm/"
echo "  - Review the changes to apm.yml, .claude-plugin/marketplace.json and README.md"
echo "  - Commit and open a pull request"
