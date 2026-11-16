#!/usr/bin/env python3
"""Fetch every page of an organization's repository listing (metadata only).

Read-only: uses `gh api --method GET`. Writes only to the working directory.

Usage:
  python3 fetch_listing.py --workdir DIR [--org ministryofjustice]

Outputs in DIR:
  listing.json  {org, started, finished, pages, page_counts, failed_page,
                 status: complete|partial, unique, duplicates, repos: [...]}
                Each repo includes business_unit from the org's `business-unit`
                custom property (empty when not set).
Exit code 0 when complete, 1 when partial (a page failed), 2 on usage errors.
"""

import argparse
import sys

from common import (
    add_location_args,
    gh_get,
    knowledge_root,
    save_json,
    utc_now,
    workdir_arg,
)

FIELDS = tuple("visibility archived is_template description topics pushed_at updated_at".split())


def repo_record(r: dict) -> dict:
    """Reduce one GitHub API repository object to the listing fields."""
    rec = {
        "name": r["name"],
        "full_name": r["full_name"],
        "id": r["id"],
        "url": r["html_url"],
    }
    for f in FIELDS:
        rec[f] = r.get(f)
    rec["topics"] = rec["topics"] or []
    # Org custom property; empty when the org has not set it for this repo.
    rec["business_unit"] = (r.get("custom_properties") or {}).get("business-unit") or ""
    return rec


def fetch_pages(org: str, per_page: int) -> dict:
    """Read listing pages until a short page or a failure."""
    state: dict = {
        "repos": [],
        "page_counts": [],
        "duplicates": 0,
        "failed_page": None,
        "error": None,
    }
    seen = {}
    page = 1
    while True:
        endpoint = f"orgs/{org}/repos?type=all&per_page={per_page}&page={page}"
        try:
            batch = gh_get(endpoint)
        except RuntimeError as exc:
            state["failed_page"], state["error"] = page, str(exc)
            break
        state["page_counts"].append({"page": page, "returned": len(batch)})
        for r in batch:
            key = r["full_name"].lower()
            if key in seen:
                state["duplicates"] += 1
                continue
            seen[key] = True
            state["repos"].append(repo_record(r))
        if len(batch) < per_page:
            break
        page += 1
    return state


def main() -> int:
    """Fetch the listing into listing.json and print a summary."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--org", default="ministryofjustice")
    ap.add_argument("--per-page", type=int, default=100)
    add_location_args(ap, hub=False)
    args = ap.parse_args()
    wd = workdir_arg(args.workdir, knowledge_root(args.knowledge_root))

    started = utc_now()
    state = fetch_pages(args.org, args.per_page)
    repos, page_counts = state["repos"], state["page_counts"]
    duplicates, failed_page, error = state["duplicates"], state["failed_page"], state["error"]

    out = {
        "org": args.org,
        "started": started,
        "finished": utc_now(),
        "pages": len(page_counts),
        "page_counts": page_counts,
        "failed_page": failed_page,
        "error": error,
        "status": "partial" if failed_page else "complete",
        "unique": len(repos),
        "duplicates": duplicates,
        "repos": repos,
    }
    save_json(wd / "listing.json", out)
    print(
        f"{out['status']}: pages={out['pages']} unique={out['unique']} "
        f"duplicates={duplicates} failed_page={failed_page or '-'} "
        f"{started}..{out['finished']}"
    )
    if error:
        print(f"page {failed_page} error: {error}", file=sys.stderr)
    return 1 if failed_page else 0


if __name__ == "__main__":
    sys.exit(main())
