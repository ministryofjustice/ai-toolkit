#!/usr/bin/env python3
"""Verify the compiled marketplace is in sync with the toolkits on disk.

Checks that the set of toolkits (each toolkits/**/apm.yml), the marketplace
packages in the root apm.yml, and the plugins in
.claude-plugin/marketplace.json all agree on the same sources, and that the
name, description and version for each package match its plugin.

Kept dependency-free (standard library only, no PyYAML) so it runs anywhere.

Usage: scripts/check_marketplace_sync.py
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APM_MANIFEST = os.path.join(ROOT, "apm.yml")
MARKETPLACE_JSON = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
TOOLKITS_DIR = os.path.join(ROOT, "toolkits")

FIELDS = ("name", "description", "version")


def normalise(source):
    """Return a source path relative to the repo root as './toolkits/...'."""
    return "./" + os.path.relpath(source, ROOT).replace(os.sep, "/")


def clean(value):
    """Strip whitespace and surrounding quotes from a YAML scalar."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def add_field(entry, text):
    """Parse a 'key: value' fragment into entry, if it contains a colon."""
    if ":" in text:
        key, _, value = text.partition(":")
        entry[key.strip()] = clean(value)


def parse_packages(path):
    """Parse the marketplace.packages list from the root apm.yml.

    Relies on the two-space-indented block structure this repository uses.
    """
    packages = []
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
            elif in_marketplace and indent == 2:
                in_packages = stripped == "packages:"
            elif in_packages and indent == 4 and stripped.startswith("- "):
                packages.append({})
                add_field(packages[-1], stripped[2:].strip())
            elif in_packages and indent >= 6 and packages:
                add_field(packages[-1], stripped)

    return packages


def collect_disk_sources():
    """Return the set of toolkit sources found on disk."""
    sources = set()
    for current_dir, _dirs, files in os.walk(TOOLKITS_DIR):
        if "apm.yml" in files:
            sources.add(normalise(current_dir))
    return sources


def collect_packages():
    """Return marketplace packages from apm.yml keyed by source."""
    by_source = {}
    for package in parse_packages(APM_MANIFEST):
        source = package.get("source", "").rstrip("/")
        if source:
            by_source[source] = package
    return by_source


def collect_plugins():
    """Return marketplace.json plugins keyed by source."""
    with open(MARKETPLACE_JSON, encoding="utf-8") as handle:
        marketplace = json.load(handle)

    by_source = {}
    for plugin in marketplace.get("plugins") or []:
        source = plugin.get("source", "").rstrip("/")
        if source:
            by_source[source] = plugin
    return by_source


def field_mismatches(source, package, plugin):
    """Return field-level mismatches between a package and its plugin."""
    mismatches = []
    for field in FIELDS:
        expected = package.get(field)
        actual = plugin.get(field)
        if str(expected) != str(actual):
            mismatches.append(
                f"Mismatch for '{source}' field '{field}': "
                f"apm.yml='{expected}' but marketplace.json='{actual}'."
            )
    return mismatches


def find_errors(disk, packages, plugins):
    """Return sync errors across disk, apm.yml and marketplace.json."""
    package_sources = set(packages)
    plugin_sources = set(plugins)
    errors = []

    for source in sorted(disk - package_sources):
        errors.append(
            f"Toolkit '{source}' has no matching package in apm.yml "
            "(marketplace.packages)."
        )
    for source in sorted(package_sources - disk):
        errors.append(
            f"apm.yml lists package '{source}' but no toolkit exists " "at that path."
        )
    for source in sorted(package_sources - plugin_sources):
        errors.append(
            f"Package '{source}' in apm.yml is missing from "
            ".claude-plugin/marketplace.json."
        )
    for source in sorted(plugin_sources - package_sources):
        errors.append(
            f"marketplace.json lists plugin '{source}' with no matching "
            "package in apm.yml."
        )
    for source in sorted(package_sources & plugin_sources):
        errors.extend(field_mismatches(source, packages[source], plugins[source]))

    return errors


def main():
    """Run the sync check and return a process exit code."""
    errors = find_errors(
        collect_disk_sources(),
        collect_packages(),
        collect_plugins(),
    )

    if errors:
        print("Marketplace is out of sync:")
        for error in errors:
            print(f"  - {error}")
        print()
        print("Regenerate it with: apm pack --check-versions --check-clean")
        print(
            "or scaffold new toolkits with: "
            "scripts/scaffold-new-toolkit.sh <team> [toolkit]"
        )
        return 1

    print("Marketplace is in sync with the toolkits on disk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
