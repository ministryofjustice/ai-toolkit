#!/usr/bin/env python3
"""Diff a fresh listing against the hub, then build and prioritise the re-read queue.

Read-only for the hub. Reads listing.json from the workdir plus the hub's
visibility listing, refresh queue and per-repository records. Writes queue.json
to the workdir for reread_readmes.py and the knowcat writer.

Usage:
  python3 build_queue.py --workdir DIR [--hub HUB | --hub-id ID] [--knowledge-root DIR]
                         [--terms "term" ...] [--p1-cap 25] [--extra 15]

--terms are the current request's topic words (P1 matching on name,
description and topics, case-insensitive). Omit them for a bare invocation.
--extra 0 re-reads only P1 entries this run.
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

from common import (
    NON_RECORD_FILES,
    add_location_args,
    knowledge_root,
    load_json,
    norm_text,
    read_table,
    resolve_hub,
    save_json,
    workdir_arg,
)

REASON_ORDER = {"new": 0, "metadata-changed": 1, "content-stale": 2}
DONE = {"re-read", "unchanged", "superseded"}


def ts(value: str) -> str:
    """Normalise '2026-11-10T15:03Z' style stamps so string comparison works."""
    m = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})(:\d{2})?", value or "")
    return (m.group(1) + (m.group(2) or ":00") + "Z") if m else ""


def sha(path: Path) -> str:
    """Return the SHA-256 of a file, or "" when it does not exist."""
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def previous_listing(path: Path) -> tuple[dict, dict]:
    """Index the hub's previous visibility listing rows by provider ID and lower-case name."""
    by_id: dict[str, dict] = {}
    by_name: dict[str, dict] = {}
    if not path.exists():
        return by_id, by_name
    for row in read_table(path.read_text(), "Repository Index"):
        rec = {
            "name": row.get("repo", ""),
            "id": row.get("provider_id", ""),
            "visibility": row.get("visibility", ""),
            "archived": row.get("archived", ""),
            "is_template": row.get("is_template", ""),
            "description": row.get("description", ""),
            "topics": row.get("topics", ""),
            # None when the previous listing predates the business_unit column.
            "business_unit": row.get("business_unit"),
        }
        by_name[rec["name"].lower()] = rec
        if rec["id"]:
            by_id[rec["id"]] = rec
    return by_id, by_name


def deep_records(gh_dir: Path, owner: str) -> dict:
    """Map repo name -> latest README-or-deeper record (retrieved time, path, README SHA)."""
    out: dict[str, dict] = {}
    link = re.compile(rf"https://github\.com/{re.escape(owner)}/([A-Za-z0-9._-]+)", re.I)
    for f in sorted(gh_dir.glob("*.md")):
        if f.name in NON_RECORD_FILES:
            continue
        text = f.read_text()
        m = re.search(r"^Retrieved at:\s*(\S+)", text, re.M)
        if not m:
            continue
        retrieved = ts(m.group(1))
        names = set()
        src = re.search(r"^Source URL:\s*(\S+)", text, re.M)
        if src and (hit := link.search(src.group(1))):
            names.add(hit.group(1))
        for line in text.splitlines():
            if line.startswith("| [") and (hit := link.search(line.split("|")[1])):
                names.add(hit.group(1))
        readme_sha = re.search(r"README blob SHA `([0-9a-f]{40})`", text)
        for n in names:
            key = n.lower()
            if key not in out or out[key]["retrieved"] < retrieved:
                out[key] = {
                    "retrieved": retrieved,
                    "record": f.name,
                    "readme_sha": readme_sha.group(1) if readme_sha and len(names) == 1 else "",
                }
    return out


def priority(repo: dict, terms: list) -> tuple[str, str]:
    """Return (priority, basis) for a listed repository."""
    text = " ".join(
        [repo["name"], repo.get("description") or "", ",".join(repo.get("topics") or [])]
    ).lower()
    hits = [t for t in terms if t in text]
    if hits:
        return "P1", "matched: " + ", ".join(hits)
    unit = repo.get("business_unit") or ""
    if unit == "HMPPS":
        return "P2", "business-unit property: HMPPS"
    if unit:
        return "P3", f"business-unit property: {unit}"
    if (
        "hmpps" in (repo.get("topics") or [])
        or repo["name"].lower().startswith("hmpps-")
        or "hmpps" in (repo.get("description") or "").lower()
    ):
        return (
            "P2",
            "HMPPS guess (topic/name/description; business-unit not set); not confirmed ownership",
        )
    return "P3", "rest of MoJ"


def metadata_changed(prev: dict, r: dict) -> bool:
    """Return True when listing metadata differs from the previous listing row."""
    now = {
        "visibility": r["visibility"],
        "archived": "yes" if r["archived"] else "no",
        "is_template": "yes" if r["is_template"] else "no",
        "topics": ",".join(r["topics"]),
    }
    changed = [k for k, v in now.items() if prev[k] != v]
    if prev["business_unit"] is not None and prev["business_unit"] != (
        r.get("business_unit") or ""
    ):
        changed.append("business_unit")
    if norm_text(prev["description"]) != norm_text(r["description"] or ""):
        changed.append("description")
    if prev["name"].lower() != r["name"].lower():
        changed.append("renamed")
    return bool(changed)


def detect_changes(current: dict, prev_by_id: dict, prev_by_name: dict, deep: dict) -> dict:
    """Map provider_id -> change reasons for repositories in the current listing."""
    detected = {}
    for pid, r in current.items():
        prev = prev_by_id.get(pid) or prev_by_name.get(r["name"].lower())
        reasons = []
        if prev is None:
            reasons.append("new")
        elif metadata_changed(prev, r):
            reasons.append("metadata-changed")
        d = deep.get(r["name"].lower())
        if d and ts(r["pushed_at"]) > d["retrieved"]:
            reasons.append("content-stale")
        if reasons:
            detected[pid] = reasons
    return detected


def existing_queue(queue_md: Path) -> dict:
    """Map provider_id -> row of the hub's current refresh queue."""
    existing = {}
    if queue_md.exists():
        for row in read_table(queue_md.read_text(), "Queue"):
            if row.get("provider_id"):
                existing[row["provider_id"]] = row
    return existing


def build_entry(pid: str, old: dict, reasons: list, ctx: dict) -> dict:
    """Build one queue entry from the previous queue row and this run's reasons."""
    listing, deep = ctx["listing"], ctx["deep"]
    repo = ctx["current"].get(pid)
    status = old.get("status", "pending")
    detected_at = old.get("detected_at") or listing["started"]
    if reasons and (status in DONE or not old):
        status, detected_at = "pending", listing["started"]
        all_reasons = reasons
    else:
        prior = [x.strip() for x in old.get("reason", "").split(",") if x.strip()]
        all_reasons = sorted(set(prior) | set(reasons), key=lambda x: REASON_ORDER.get(x, 9))
    if repo is None:
        # Queued earlier but absent now (or listing partial): keep, don't re-read.
        return {
            **{
                k: old.get(k, "")
                for k in (
                    "repo",
                    "url",
                    "priority",
                    "priority_basis",
                    "last_attempt",
                    "evidence",
                )
            },
            "provider_id": pid,
            "reason": all_reasons,
            "detected_at": detected_at,
            "status": status if status in DONE else "pending",
            "in_listing": False,
        }
    pr, basis = priority(repo, ctx["terms"])
    return {
        "repo": repo["full_name"],
        "url": repo["url"],
        "provider_id": pid,
        "name": repo["name"],
        "archived": bool(repo["archived"]),
        "pushed_at": repo["pushed_at"] or "",
        "reason": all_reasons,
        "priority": pr,
        "priority_basis": basis,
        "detected_at": detected_at,
        "status": status,
        "last_attempt": old.get("last_attempt", ""),
        "evidence": old.get("evidence", ""),
        "in_listing": True,
        "recorded_readme_sha": (deep.get(repo["name"].lower()) or {}).get("readme_sha", ""),
    }


def sort_key(e: dict) -> tuple:
    """Order entries by priority, reason, archived flag, then most recently pushed."""
    first = min((REASON_ORDER.get(x, 9) for x in e["reason"]), default=9)
    pushed = "".join(chr(255 - ord(c)) for c in e.get("pushed_at", ""))
    return (e["priority"] or "P9", first, e.get("archived", False), pushed)


def open_counts(entries: list) -> dict:
    """Count open entries by 'priority reason'."""
    counts: dict[str, int] = {}
    for e in entries:
        if e["status"] in ("pending", "failed"):
            for r in e["reason"]:
                counts[f"{e['priority']} {r}"] = counts.get(f"{e['priority']} {r}", 0) + 1
    return counts


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--workdir", required=True)
    add_location_args(ap)
    ap.add_argument("--terms", nargs="*", default=[])
    ap.add_argument("--p1-cap", type=int, default=25)
    ap.add_argument("--extra", type=int, default=15)
    return ap.parse_args()


def report(out: dict, entries: list, detected: dict, p1_batched: int) -> None:
    """Print the run summary."""
    open_entries = sum(1 for e in entries if e["status"] in ("pending", "failed"))
    print(
        f"detected this run={len(detected)} open={open_entries} batch={len(out['batch'])} "
        f"(P1 {p1_batched}) missing={len(out['missing'])}"
    )
    print(
        "open by priority/reason:",
        ", ".join(f"{k}: {v}" for k, v in sorted(open_counts(entries).items())) or "none",
    )
    if out["p1_remaining_after_batch"]:
        print(f"P1 entries beyond cap: {out['p1_remaining_after_batch']}")
    if not out["previous_had_provider_ids"]:
        print("note: previous listing had no provider IDs; renames not detectable this run")


def build_entries(existing: dict, detected: dict, ctx: dict) -> list:
    """Merge carried-forward queue entries with this run's detections, in priority order."""
    entries = [
        build_entry(pid, existing.get(pid, {}), detected.get(pid, []), ctx)
        for pid in sorted(set(existing) | set(detected))
    ]
    entries.sort(key=sort_key)
    return entries


def missing_names(listing: dict, prev_by_name: dict) -> list:
    """Previously listed names absent now; only meaningful when every page was read."""
    if listing["status"] != "complete":
        return []
    current_names = {r["name"].lower() for r in listing["repos"]}
    return sorted(n for n in prev_by_name if n not in current_names)


def select_batch(entries: list, p1_cap: int, extra: int) -> tuple[list, int, int]:
    """Pick this run's re-read batch: P1 up to p1_cap, then up to `extra` others."""
    eligible = [e for e in entries if e["in_listing"] and e["status"] in ("pending", "failed")]
    p1 = [e for e in eligible if e["priority"] == "P1"]
    rest = [e for e in eligible if e["priority"] != "P1"]
    batch = [e["provider_id"] for e in p1[:p1_cap] + rest[:extra]]
    return batch, len(p1[:p1_cap]), max(0, len(p1) - p1_cap)


def main() -> int:
    """Build queue.json in the workdir and print a summary."""
    args = parse_args()
    root = knowledge_root(args.knowledge_root)
    wd, hub = workdir_arg(args.workdir, root), resolve_hub(root, args.hub, args.hub_id)
    files = {
        "listing": hub / "sources" / "github" / "moj-repos-visibility.md",
        "queue": hub / "sources" / "github" / "refresh-queue.md",
        "index": hub / "index.md",
    }
    listing = load_json(wd / "listing.json")
    prev_by_id, prev_by_name = previous_listing(files["listing"])
    ctx = {
        "listing": listing,
        "terms": [t.lower() for t in args.terms if t.strip()],
        "deep": deep_records(files["listing"].parent, listing["org"]),
        "current": {str(r["id"]): r for r in listing["repos"]},
    }
    detected = detect_changes(ctx["current"], prev_by_id, prev_by_name, ctx["deep"])
    entries = build_entries(existing_queue(files["queue"]), detected, ctx)
    batch, p1_batched, p1_remaining = select_batch(entries, args.p1_cap, args.extra)
    out = {
        "listing_started": listing["started"],
        "listing_status": listing["status"],
        "terms": ctx["terms"],
        "entries": entries,
        "missing": missing_names(listing, prev_by_name),
        "batch": batch,
        "p1_remaining_after_batch": p1_remaining,
        "hub_fingerprints": {p.name: sha(p) for p in files.values()},
        "previous_had_provider_ids": bool(prev_by_id),
    }
    save_json(wd / "queue.json", out)
    report(out, entries, detected, p1_batched)
    return 0


if __name__ == "__main__":
    sys.exit(main())
