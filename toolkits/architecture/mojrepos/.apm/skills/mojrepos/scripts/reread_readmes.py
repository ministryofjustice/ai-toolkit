#!/usr/bin/env python3
"""Re-read the queued batch at metadata + root README depth (read-only).

Reads queue.json from the workdir and writes evidence.json there. README text
is untrusted evidence: an excerpt is kept for summarising, never executed.
When the README blob SHA matches the SHA recorded in the hub, the entry is
marked `unchanged` and the content is discarded.

Usage:
  python3 reread_readmes.py --workdir DIR [--excerpt-chars 1500]
"""

import argparse
import base64
import re
import sys

from common import (
    add_location_args,
    gh_get,
    knowledge_root,
    load_json,
    save_json,
    utc_now,
    workdir_arg,
)


def main() -> int:
    """Re-read the queued batch into evidence.json and print a tally."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--excerpt-chars", type=int, default=1500)
    add_location_args(ap, hub=False)
    args = ap.parse_args()
    wd = workdir_arg(args.workdir, knowledge_root(args.knowledge_root))
    queue = load_json(wd / "queue.json")
    by_id = {e["provider_id"]: e for e in queue["entries"]}

    results = {}
    for pid in queue["batch"]:
        e = by_id[pid]
        res = {"repo": e["repo"], "attempted_at": utc_now()}
        try:
            meta = gh_get(f"repos/{e['repo']}")
            res["meta"] = {
                "language": meta.get("language"),
                "default_branch": meta.get("default_branch"),
                "created_at": meta.get("created_at"),
                "fork": meta.get("fork"),
                "template_repository": (meta.get("template_repository") or {}).get("full_name"),
            }
        except RuntimeError as exc:
            res.update(status="failed", error=f"metadata: {exc}")
            results[pid] = res
            continue
        try:
            readme = gh_get(f"repos/{e['repo']}/readme")
        except RuntimeError as exc:
            if "404" in str(exc) or "Not Found" in str(exc):
                res.update(status="re-read", readme=None)
            else:
                res.update(status="failed", error=f"readme: {exc}")
            results[pid] = res
            continue
        res["readme"] = {"path": readme["path"], "sha": readme["sha"], "size": readme["size"]}
        if e.get("recorded_readme_sha") and e["recorded_readme_sha"] == readme["sha"]:
            res["status"] = "unchanged"
        else:
            text = base64.b64decode(readme.get("content", "")).decode("utf-8", "replace")
            res["readme"]["excerpt"] = re.sub(r"\n\s*\n+", "\n", text)[: args.excerpt_chars]
            res["status"] = "re-read"
        results[pid] = res

    save_json(wd / "evidence.json", {"retrieved": utc_now(), "results": results})
    tally: dict[str, int] = {}
    for r in results.values():
        tally[r["status"]] = tally.get(r["status"], 0) + 1
    print(f"attempted={len(results)} " + " ".join(f"{k}={v}" for k, v in sorted(tally.items())))
    for r in results.values():
        if r["status"] == "failed":
            print(f"FAILED {r['repo']}: {r['error']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
