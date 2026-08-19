#!/usr/bin/env bash
set -euo pipefail

# Verifies that the compiled marketplace is in sync with the toolkits on disk.
#
# Checks that the set of toolkits (each toolkits/**/apm.yml), the marketplace
# packages in the root apm.yml, and the plugins in
# .claude-plugin/marketplace.json all agree on the same sources, and that the
# name, description and version for each package match its plugin.
#
# Usage: scripts/check-marketplace-sync.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ROOT_DIR="$ROOT_DIR" python3 <<'PY'
import json
import os
import sys

root = os.environ["ROOT_DIR"]
apm_manifest = os.path.join(root, "apm.yml")
marketplace_json = os.path.join(root, ".claude-plugin", "marketplace.json")
toolkits_dir = os.path.join(root, "toolkits")

errors = []


def normalise(source):
    return "./" + os.path.relpath(source, root).replace(os.sep, "/")


def clean(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def parse_packages(path):
    """Parse the marketplace.packages list from the root apm.yml.

    Kept dependency-free (no PyYAML) so it runs anywhere. Relies on the
    two-space-indented block structure this repository uses.
    """
    packages = []
    current = None
    in_marketplace = False
    in_packages = False

    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            if not line.strip():
                continue

            indent = len(line) - len(line.lstrip(" "))
            stripped = line.strip()

            if indent == 0:
                in_marketplace = stripped == "marketplace:"
                in_packages = False
                continue

            if in_marketplace and indent == 2:
                in_packages = stripped == "packages:"
                continue

            if not in_packages:
                continue

            if indent == 4 and stripped.startswith("- "):
                current = {}
                packages.append(current)
                rest = stripped[2:].strip()
                if ":" in rest:
                    key, _, value = rest.partition(":")
                    current[key.strip()] = clean(value)
            elif indent >= 6 and current is not None and ":" in stripped:
                key, _, value = stripped.partition(":")
                current[key.strip()] = clean(value)

    return packages


# 1. Toolkits on disk: every toolkits/**/apm.yml is a toolkit.
disk_sources = set()
for current_dir, _dirs, files in os.walk(toolkits_dir):
    if "apm.yml" in files:
        disk_sources.add(normalise(current_dir))

# 2. Marketplace packages declared in the root apm.yml.
package_by_source = {}
for package in parse_packages(apm_manifest):
    source = package.get("source", "").rstrip("/")
    if source:
        package_by_source[source] = package

# 3. Plugins in the compiled marketplace.json.
with open(marketplace_json, encoding="utf-8") as handle:
    marketplace = json.load(handle)

plugin_by_source = {}
for plugin in marketplace.get("plugins") or []:
    source = plugin.get("source", "").rstrip("/")
    if source:
        plugin_by_source[source] = plugin

package_sources = set(package_by_source)
plugin_sources = set(plugin_by_source)

for source in sorted(disk_sources - package_sources):
    errors.append(f"Toolkit '{source}' has no matching package in apm.yml (marketplace.packages).")

for source in sorted(package_sources - disk_sources):
    errors.append(f"apm.yml lists package '{source}' but no toolkit exists at that path.")

for source in sorted(package_sources - plugin_sources):
    errors.append(f"Package '{source}' in apm.yml is missing from .claude-plugin/marketplace.json.")

for source in sorted(plugin_sources - package_sources):
    errors.append(f"marketplace.json lists plugin '{source}' with no matching package in apm.yml.")

# 4. Fields must match for sources present in both.
for source in sorted(package_sources & plugin_sources):
    package = package_by_source[source]
    plugin = plugin_by_source[source]
    for field in ("name", "description", "version"):
        expected = package.get(field)
        actual = plugin.get(field)
        if str(expected) != str(actual):
            errors.append(
                f"Mismatch for '{source}' field '{field}': "
                f"apm.yml='{expected}' but marketplace.json='{actual}'."
            )

if errors:
    print("Marketplace is out of sync:")
    for error in errors:
        print(f"  - {error}")
    print()
    print("Regenerate it with: apm pack --check-versions --check-clean")
    print("or scaffold new toolkits with: scripts/new-team-toolkit.sh <team> [toolkit]")
    sys.exit(1)

print("Marketplace is in sync with the toolkits on disk.")
PY
