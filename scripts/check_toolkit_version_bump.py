"""Require a version change when existing toolkit contents change."""

import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def git_output(*arguments):
    """Run Git in the repository and return stdout."""
    result = subprocess.run(
        ["git", *arguments],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def read_git_file(revision, path):
    """Read a file from a Git revision, returning None if it does not exist."""
    result = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        return None
    return result.stdout


def read_version(manifest):
    """Return the top-level version scalar from an APM manifest."""
    for line in manifest.splitlines():
        key, separator, value = line.partition(":")
        if separator and not key.startswith(" ") and key.strip() == "version":
            return value.strip().strip("\"'").strip()
    return ""


def toolkit_manifest(path, revision, manifest_cache):
    """Find the closest toolkit apm.yml containing a changed file."""
    parts = PurePosixPath(path).parts
    for end in range(len(parts) - 1, 1, -1):
        directory = PurePosixPath(*parts[:end])
        manifest_path = directory / "apm.yml"
        manifest_key = str(manifest_path)
        if manifest_key not in manifest_cache:
            manifest_cache[manifest_key] = read_git_file(revision, manifest_key)
        if manifest_cache[manifest_key] is not None:
            return manifest_key
    return None


def check_versions(base_revision, head_revision):
    """Return errors for changed existing toolkits with unchanged versions."""
    changed_paths = git_output(
        "diff",
        "--name-only",
        "--no-renames",
        f"{base_revision}...{head_revision}",
        "--",
        "toolkits/",
    ).splitlines()
    manifest_cache = {}
    changed_manifests = set()

    for path in changed_paths:
        manifest_path = toolkit_manifest(path, head_revision, manifest_cache)
        if manifest_path is not None:
            changed_manifests.add(manifest_path)

    errors = []
    for manifest_path in sorted(changed_manifests):
        base_manifest = read_git_file(base_revision, manifest_path)
        head_manifest = manifest_cache[manifest_path]
        if base_manifest is None:
            continue

        base_version = read_version(base_manifest)
        head_version = read_version(head_manifest)
        if base_version == head_version:
            errors.append(
                f"Version remains '{head_version or '(empty)'}' despite toolkit changes. "
                f"Update {manifest_path}."
            )

    return errors, len(changed_manifests)


def main():
    """Check toolkit versions between two Git revisions."""
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <base-revision> <head-revision>", file=sys.stderr)
        return 2

    errors, checked_count = check_versions(sys.argv[1], sys.argv[2])
    if errors:
        print("Toolkit version check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"Checked versions for {checked_count} changed existing toolkit(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
