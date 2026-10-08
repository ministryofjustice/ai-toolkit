"""Ensure toolkit instruction files declare description and source metadata."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLKITS_DIR = ROOT / "toolkits"
REQUIRED_FIELDS = ("description", "source")


def read_frontmatter_fields(path):
    """Return non-empty required fields found in a file's YAML frontmatter."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return set()

    fields = set()
    for line in lines[1:]:
        if line.strip() == "---":
            break

        key, separator, value = line.partition(":")
        if separator and key.strip() in REQUIRED_FIELDS:
            value = value.strip().strip("\"'").strip()
            if value:
                fields.add(key.strip())

    return fields


def main():
    """Check all toolkit instruction files and return a process exit code."""
    instruction_files = sorted(TOOLKITS_DIR.rglob("*.instructions.md"))
    errors = []

    for path in instruction_files:
        missing_fields = set(REQUIRED_FIELDS) - read_frontmatter_fields(path)
        if missing_fields:
            relative_path = path.relative_to(ROOT)
            fields = ", ".join(sorted(missing_fields))
            errors.append(f"{relative_path}: missing or empty frontmatter field(s): {fields}")

    if errors:
        print("Toolkit instruction metadata check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"Validated metadata for {len(instruction_files)} toolkit instruction files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())