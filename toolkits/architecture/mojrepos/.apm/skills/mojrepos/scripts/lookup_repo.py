#!/usr/bin/env python3
"""Look up repositories in the selected hub's listing only (no network).

Matches terms against repo name, description and topics in the hub's
visibility listing and prints the canonical GitHub URL with listing metadata.
It does not search other hubs; fall back to them only when this finds nothing.

Usage:
  python3 lookup_repo.py [--hub HUB | --hub-id ID] [--knowledge-root DIR] TERM [TERM ...]
  (all terms must match)
"""

import argparse
import re
import sys

from common import add_location_args, knowledge_root, read_table, resolve_hub


def main() -> int:
    """Print matching listing rows; exit 1 when nothing matches."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_location_args(ap)
    ap.add_argument("terms", nargs="+")
    args = ap.parse_args()
    hub = resolve_hub(knowledge_root(args.knowledge_root), args.hub, args.hub_id)
    listing = hub / "sources" / "github" / "moj-repos-visibility.md"
    text = listing.read_text()
    retrieved = re.search(r"^- Retrieved:\s*(.+)$", text, re.M)
    terms = [t.lower() for t in args.terms]
    hits = []
    for row in read_table(text, "Repository Index"):
        hay = " ".join(
            [row.get("repo", ""), row.get("description", ""), row.get("topics", "")]
        ).lower()
        if all(t in hay for t in terms):
            hits.append(row)
    print(f"listing: {listing} (retrieved {retrieved.group(1) if retrieved else 'unknown'})")
    if not hits:
        print("no matches in this hub's listing")
        return 1
    name_terms = [re.sub(r"\s+", "-", t) for t in terms]
    hits.sort(
        key=lambda r: (
            r.get("archived") == "yes",
            not all(t in r["repo"].lower() for t in name_terms),
            len(r["repo"]),
            r["repo"].lower(),
        )
    )
    for r in hits:
        print(
            " | ".join(
                [
                    r["url"],
                    r.get("visibility", ""),
                    "archived" if r.get("archived") == "yes" else "active",
                    r.get("description", ""),
                    r.get("topics", ""),
                    "pushed " + r.get("pushed_at", ""),
                ]
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
