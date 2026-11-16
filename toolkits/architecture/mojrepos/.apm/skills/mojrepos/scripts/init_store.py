#!/usr/bin/env python3
"""Create the mojrepos standalone store: a minimal knowledge hub mojrepos can write to.

Use only when knowcat is not installed and the user has approved the location
and the standing listing scope. The layout matches a knowcat hub (root
hubs.md row, <hub>/index.md with registration and coverage tables,
<hub>/sources/github/), so knowcat can adopt the store later without migration.

Usage:
  python3 init_store.py --knowledge-root DIR --approval "user's words" [--save-config]
        [--hub-id mojrepos-kb] [--name "mojrepos kb"] [--org ministryofjustice] [--dry-run]

Creates the knowledge root and hubs.md if missing, then the hub folder. Does
nothing if the hub ID is already registered. Refuses to use an existing
non-empty folder that is not registered. --save-config records the root in
${XDG_CONFIG_HOME:-~/.config}/knowledge-hubs/config.json if that file has no
knowledge_root yet. Exit 0 on success or no-op, 2 on refusal.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote

from common import config_path, die, split_row, utc_now

REGISTRATION = "mojrepos-org-visibility-listing"
HUBS_HEADER = """# Knowledge hubs

| Hub ID | Name | Aliases | Scope | Relative index path |
|---|---|---|---|---|
"""
START_HERE = (
    "- Repository listing and refresh queue are written to `sources/github/` "
    "after the first refresh."
)
REGISTERED_HEADER = (
    "| Registration ID | Type | Identity and approved scope | Approval evidence | Exclusions "
    "| Connector prerequisite/status | Output |"
)
COVERAGE_HEADER = (
    "| Registration ID | Attempted at (UTC) | Status | Attempted / succeeded / failed "
    "| Coverage and limits | Last successful read (UTC) | Error or evidence |"
)


def cell(value: str) -> str:
    """Escape a value for use in a single Markdown table cell."""
    return value.replace("\n", " ").replace("|", "\\|").strip()


def write(path: Path, text: str, dry_run: bool, written: list) -> None:
    """Record a path and, unless dry-running, write it atomically."""
    written.append(str(path))
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def index_text(hub_id: str, name: str, org: str, approval: str, created: str) -> str:
    """Return the new hub's index.md."""
    scope = (
        f"`{org}` org repository listing via `gh api orgs/{org}/repos?type=all`, metadata only. "
        "**Standing approval:** (a) recurring metadata-only listing when mojrepos is invoked and "
        "the last successful read is older than 14 days; (b) re-reading queued repositories at "
        "metadata + root README depth only (no source code, sub-documents, linked repositories, "
        "issues or PRs)."
    )
    not_run_row = (
        "| "
        + " | ".join(
            [REGISTRATION, "not yet run", "Not yet run", "0 / 0 / 0", "None yet", "none"]
            + [f"Store created {created}"]
        )
        + " |"
    )
    return f"""# {name}

Hub ID: `{hub_id}`
Aliases: none
Scope: MoJ GitHub repository discovery, categorisation and inventory, created by
mojrepos as a standalone store on {created}. knowcat can adopt this hub as it is.

## Start here

{START_HERE}

## Registered sources

{REGISTERED_HEADER}
|---|---|---|---|---|---|---|
| {REGISTRATION} | Live GitHub org listing | {cell(scope)} | {cell(approval)} ({created}) \
| None; archived retained and flagged | `gh` CLI, read-only use \
| `sources/github/moj-repos-visibility.md` |

## Coverage and refresh attempts

{COVERAGE_HEADER}
|---|---|---|---|---|---|---|
{not_run_row}
"""


def main() -> int:
    """Create the store (or report no change) and print the files written."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--knowledge-root", required=True)
    ap.add_argument(
        "--approval",
        required=True,
        help="the user's own words approving the location and standing scope",
    )
    ap.add_argument("--hub-id", default="mojrepos-kb")
    ap.add_argument("--name", default="mojrepos kb")
    ap.add_argument("--org", default="ministryofjustice")
    ap.add_argument("--save-config", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a.hub_id):
        die(f"hub ID must be a lowercase slug: {a.hub_id!r}")
    if not a.name.strip() or "/" in a.name or a.name.strip() in (".", ".."):
        die(f"hub name must be a single folder name: {a.name!r}")
    if not a.approval.strip():
        die("--approval must quote the user's approval")

    root = Path(a.knowledge_root).expanduser().resolve()
    hub = (root / a.name.strip()).resolve()
    if hub.parent != root:
        die(f"hub folder must be directly inside the knowledge root: {hub}")
    hubs_md = root / "hubs.md"
    written: list = []

    if hubs_md.is_file():
        for line in hubs_md.read_text(encoding="utf-8").splitlines():
            if line.startswith("|") and split_row(line)[:1] == [a.hub_id]:
                print(f"no change: hub ID {a.hub_id!r} is already registered in {hubs_md}")
                return 0
    if hub.exists() and any(hub.iterdir()):
        die(
            f"{hub} exists, is not empty and is not registered as {a.hub_id!r}; choose another name"
        )

    created = utc_now()
    write(
        hub / "index.md",
        index_text(a.hub_id, a.name.strip(), a.org, a.approval.strip(), created),
        a.dry_run,
        written,
    )
    if not a.dry_run:
        (hub / "sources" / "github").mkdir(parents=True, exist_ok=True)

    registry = hubs_md.read_text(encoding="utf-8") if hubs_md.is_file() else HUBS_HEADER
    row = (
        "| "
        + " | ".join(
            [
                a.hub_id,
                cell(a.name.strip()),
                "none",
                "MoJ GitHub repository listing, queue and research records "
                "(mojrepos standalone store)",
                f"[{cell(a.name.strip())}/index.md](./{quote(a.name.strip())}/index.md)",
            ]
        )
        + " |"
    )
    write(hubs_md, registry.rstrip("\n") + "\n" + row + "\n", a.dry_run, written)

    if a.save_config:
        cfg = config_path()
        data = json.loads(cfg.read_text()) if cfg.is_file() else {}
        if data.get("knowledge_root"):
            print(f"config not changed: {cfg} already sets knowledge_root")
        else:
            data["knowledge_root"] = str(root)
            write(cfg, json.dumps(data, indent=2) + "\n", a.dry_run, written)

    print(("DRY RUN, would write:" if a.dry_run else "wrote:"), *written, sep="\n  ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
