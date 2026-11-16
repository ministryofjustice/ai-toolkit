"""Shared helpers for mojrepos collection scripts (read-only; no hub writes)."""

__all__ = [
    "DEFAULT_HUB_ID",
    "NON_RECORD_FILES",
    "add_location_args",
    "config_path",
    "die",
    "gh_get",
    "hub_arg",
    "knowledge_root",
    "load_json",
    "md_cell",
    "norm_text",
    "read_table",
    "resolve_hub",
    "save_json",
    "split_row",
    "utc_now",
    "workdir_arg",
]

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn
from urllib.parse import unquote

# Shared with the writer (shipped identically in knowcat) so table parsing stays in one place.
from write_github_refresh import read_table, split_row

CONFIG_HELP = (
    "Set the knowledge root with --knowledge-root, the KNOWLEDGE_HUB_ROOT environment "
    'variable, or {"knowledge_root": "/path"} in '
    "${XDG_CONFIG_HOME:-~/.config}/knowledge-hubs/config.json"
)
DEFAULT_HUB_ID = "mojrepos-kb"


def config_path() -> Path:
    """Return the shared knowledge-hubs config file path."""
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "knowledge-hubs" / "config.json"


def knowledge_root(explicit: str = "") -> Path:
    """Resolve the knowledge root: explicit value, env var, then config file."""
    value = explicit or os.environ.get("KNOWLEDGE_HUB_ROOT", "")
    if not value and config_path().is_file():
        value = json.loads(config_path().read_text()).get("knowledge_root", "")
    if not value:
        die(f"knowledge root not configured. {CONFIG_HELP}")
    root = Path(value).expanduser().resolve()
    if not (root / "hubs.md").is_file():
        die(f"no hubs.md in knowledge root {root}. {CONFIG_HELP}")
    return root


def resolve_hub(root: Path, hub: str = "", hub_id: str = DEFAULT_HUB_ID) -> Path:
    """Return a hub directory: an explicit path, or the hubs.md row for hub_id."""
    if hub:
        return hub_arg(hub, root)
    for line in (root / "hubs.md").read_text().splitlines():
        if line.startswith("|") and split_row(line)[:1] == [hub_id]:
            m = re.search(r"\]\(([^)]+)\)", line)
            if m:
                return hub_arg(str((root / unquote(m.group(1))).parent), root)
    die(f"hub ID {hub_id!r} not found in {root / 'hubs.md'}; pass --hub or --hub-id")


# Hub files that are inventories or queues rather than per-repository research records.
NON_RECORD_FILES = {
    "moj-repos-visibility.md",
    "moj-repos.md",
    "project-templates.md",
    "refresh-queue.md",
}


def utc_now() -> str:
    """Return the current UTC time as an ISO 8601 second-precision stamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def die(msg: str, code: int = 2) -> NoReturn:
    """Print an error to stderr and exit."""
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def add_location_args(ap: argparse.ArgumentParser, hub: bool = True) -> None:
    """Add the shared --knowledge-root (and optionally --hub/--hub-id) arguments."""
    ap.add_argument(
        "--knowledge-root", default="", help="defaults to KNOWLEDGE_HUB_ROOT or the config file"
    )
    if hub:
        ap.add_argument("--hub", default="", help="hub directory (overrides --hub-id)")
        ap.add_argument("--hub-id", default=DEFAULT_HUB_ID, help="hub ID registered in hubs.md")


def workdir_arg(path: str, root: Path) -> Path:
    """Resolve a working directory and refuse anything inside the knowledge root."""
    wd = Path(path).expanduser().resolve()
    if wd == root or root in wd.parents:
        die(f"workdir must be outside the knowledge root: {wd}")
    wd.mkdir(parents=True, exist_ok=True)
    return wd


def hub_arg(path: str, root: Path) -> Path:
    """Resolve a hub directory and require it to be an indexed folder inside the root."""
    hub = Path(path).expanduser().resolve()
    if root not in hub.parents:
        die(f"hub must be inside the knowledge root: {hub}")
    if not (hub / "index.md").is_file():
        die(f"hub has no index.md: {hub}")
    return hub


def gh_get(endpoint: str) -> Any:
    """Read-only GitHub API GET via the gh CLI. Raises RuntimeError on failure."""
    proc = subprocess.run(
        ["gh", "api", "--method", "GET", endpoint],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[:500] or f"gh exit {proc.returncode}")
    return json.loads(proc.stdout)


def md_cell(value: str) -> str:
    """Escape a value for use in a single Markdown table cell."""
    return (value or "").replace("\n", " ").replace("|", "\\|").strip()


def norm_text(value: str) -> str:
    """Normalise for comparison so Markdown escaping differences are not changes."""
    return re.sub(r"[\\|\s]", "", value or "")


def load_json(path: Path) -> Any:
    """Read and parse a JSON file."""
    return json.loads(path.read_text())


def save_json(path: Path, data: Any) -> None:
    """Write JSON atomically via a temporary sibling file."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, default=str))
    os.replace(tmp, path)
