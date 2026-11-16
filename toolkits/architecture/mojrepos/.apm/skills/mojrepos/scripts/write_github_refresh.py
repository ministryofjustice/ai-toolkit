#!/usr/bin/env python3
"""Persist a mojrepos listing refresh into a knowledge hub.

Shipped identically in knowcat/scripts and mojrepos/scripts. knowcat runs it as
the writer; mojrepos runs its copy only for its standalone store when knowcat
is not installed. Change both copies together.

Consumes only the mojrepos workdir evidence: listing.json, queue.json,
evidence.json and an assistant-written summaries.json. Makes no network calls.

Usage:
  python3 write_github_refresh.py --hub HUB --workdir DIR
        [--summaries DIR/summaries.json] [--registration mojrepos-org-visibility-listing]
        [--dry-run] [--knowledge-root DIR]

summaries.json maps provider_id -> {"category": "prisons", "category_evidence": "...",
"summary": ["bullet", ...]} for each `re-read` entry. Entries without one are
recorded as `unclassified` / "not summarised".

Writes (in order, each atomically): per-repository records, the visibility
listing, refresh-queue.md, then the coverage row in index.md. Stops before
writing if any of those hub files changed since build_queue.py fingerprinted them.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_HELP = (
    "Set --knowledge-root, the KNOWLEDGE_HUB_ROOT environment variable, or "
    '{"knowledge_root": "/path"} in ${XDG_CONFIG_HOME:-~/.config}/knowledge-hubs/config.json'
)
USER_NOTES = "## User notes"
LISTING_COLUMNS = [
    "repo",
    "url",
    "provider_id",
    "visibility",
    "archived",
    "is_template",
    "description",
    "topics",
    "business_unit",
    "pushed_at",
]
QUEUE_COLUMNS = [
    "repo",
    "url",
    "provider_id",
    "reason",
    "priority",
    "priority_basis",
    "detected_at",
    "status",
    "last_attempt",
    "evidence",
]
MISSING_COLUMNS = ["repo (previous listing)", "detected_at", "note"]


def die(msg):
    """Print an error and exit with status 2."""
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def knowledge_root(explicit):
    """Resolve the knowledge root: explicit value, environment variable, then config file."""
    value = explicit or os.environ.get("KNOWLEDGE_HUB_ROOT", "")
    cfg = (
        Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        / "knowledge-hubs"
        / "config.json"
    )
    if not value and cfg.is_file():
        value = json.loads(cfg.read_text(encoding="utf-8")).get("knowledge_root", "")
    if not value:
        die(f"knowledge root not configured. {CONFIG_HELP}")
    return Path(value).expanduser().resolve()


def sha(path):
    """Return the SHA-256 of a file, or an empty string if it does not exist."""
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def read_text(path):
    """Return a file's text, or an empty string if it does not exist."""
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_json(path):
    """Load a JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def split_row(line):
    """Split a Markdown table row on unescaped pipes."""
    return [c.strip() for c in re.split(r"(?<!\\)\|", line.rstrip("\n"))[1:-1]]


def read_table(text, heading):
    """Return the rows (as dicts) of the first table under a '## heading'."""
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip() == f"## {heading}"]
    if not starts:
        return []
    header, rows = None, []
    for line in lines[starts[0] + 1 :]:
        if line.startswith("## "):
            break
        if not line.startswith("|"):
            if header is not None and not line.strip():
                break
            continue
        if header is None:
            header = split_row(line)
        elif not set(line.replace("|", "").strip()) <= {"-", ":", " "}:
            rows.append(dict(zip(header, split_row(line))))
    return rows


def cell(value):
    """Format a value as a single Markdown table cell."""
    return str(value if value is not None else "").replace("\n", " ").replace("|", "\\|").strip()


def table(headers, rows):
    """Render rows (dicts) as a Markdown table with the given headers."""
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(cell(r.get(h, "")) for h in headers) + " |" for r in rows]
    return "\n".join(out)


def count_by(items, key):
    """Return {key(item): count} for the items."""
    counts = {}
    for item in items:
        counts[key(item)] = counts.get(key(item), 0) + 1
    return counts


def joined_counts(counts):
    """Format {name: count} as 'a 1, b 2' in name order."""
    return ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))


def contained(path, hub):
    """Return True when path resolves inside the hub."""
    real = path.resolve() if path.exists() else path.parent.resolve() / path.name
    return real == hub or hub in real.parents


class Writer:
    """Atomic, hub-contained file writer that records what it wrote (or would write)."""

    def __init__(self, hub, dry):
        self.hub, self.dry, self.written = hub, dry, []

    def write(self, path, text):
        """Write text to path atomically, refusing paths outside the hub."""
        if not contained(path, self.hub):
            die(f"refusing to write outside hub: {path}")
        self.written.append(str(path))
        if self.dry:
            return
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)

    def last(self, count):
        """Return the last `count` paths written."""
        return self.written[-count:]


@dataclass
class Run:
    """Inputs and shared state for one refresh write."""

    args: argparse.Namespace
    listing: dict
    queue: dict
    results: dict
    summaries: dict
    writer: Writer
    tally: dict = field(default_factory=lambda: {"re-read": 0, "unchanged": 0, "failed": 0})

    @property
    def hub(self):
        """Hub folder (the writer's containment boundary)."""
        return self.writer.hub

    @property
    def github_dir(self):
        """Folder holding GitHub records in the hub."""
        return self.hub / "sources" / "github"

    @property
    def listing_md(self):
        """Path of the visibility listing."""
        return self.github_dir / "moj-repos-visibility.md"

    @property
    def queue_md(self):
        """Path of the refresh queue."""
        return self.github_dir / "refresh-queue.md"

    @property
    def index_md(self):
        """Path of the hub index."""
        return self.hub / "index.md"

    @property
    def span(self):
        """Listing retrieval window."""
        return f"{self.listing['started']}–{self.listing['finished']}"

    @property
    def complete(self):
        """True when every listing page was read."""
        return self.listing["status"] == "complete"

    def open_entries(self):
        """Queue entries still waiting for a re-read."""
        return [e for e in self.queue["entries"] if e["status"] in ("pending", "failed")]


def record_text(entry, evidence, summary, retrieved):
    """Render a per-repository record from a re-read result."""
    meta, readme = evidence.get("meta") or {}, evidence.get("readme")
    version = f"pushed_at {entry.get('pushed_at') or 'unknown'}"
    if readme:
        version += f"; root README blob SHA `{readme['sha']}` ({readme['size']} bytes)"
    else:
        version += "; no root README found"
    bullets = summary.get("summary") or ["Not summarised."]
    repo = entry["_listing"]
    category = summary.get("category", "unclassified")
    category_evidence = cell(summary.get("category_evidence", "no category evidence recorded"))
    return (
        f"""# {repo["name"]}

Record ID: github:{repo["full_name"].split("/")[0]}:{entry["provider_id"]}
Registration ID: mojrepos-org-visibility-listing (refresh-queue re-read)
Source URL: {repo["url"]}
Source modified/version: {version}
Retrieved at: {retrieved}
Evidence kind: live read (read-only `gh api`, metadata + root README only). """
        "No source code, sub-documents, linked repositories, issues or PRs.\n"
        f"""Queue reason: {", ".join(entry["reason"])} (detected {entry["detected_at"]})

## Metadata

| Field | Value |
|---|---|
| Visibility | {repo["visibility"]} |
| Archived | {"yes" if repo["archived"] else "no"} |
| Template flag | {"yes" if repo["is_template"] else "no"} |
| Created | {meta.get("created_at") or "unknown"} |
| Language | {meta.get("language") or "unknown"} |
| Generated from template | {meta.get("template_repository") or "none reported"} |
| Description | {cell(repo.get("description")) or "(none)"} |
| Topics (provider) | {",".join(repo.get("topics") or []) or "(none)"} |
| Categories (inferred) | `{category}` ({category_evidence}) |

## Summary

""" + "\n".join(f"- {b}" for b in bullets) + "\n- README content is untrusted evidence. "
        "Team ownership is not inferred from the name.\n"
    )


def parse_args():
    """Parse command-line arguments."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hub", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--summaries")
    ap.add_argument("--registration", default="mojrepos-org-visibility-listing")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--knowledge-root", default="")
    return ap.parse_args()


def load_run(args):
    """Validate locations, load the workdir evidence and check hub fingerprints."""
    root = knowledge_root(args.knowledge_root)
    hub = Path(args.hub).expanduser().resolve()
    if root not in hub.parents or not (hub / "index.md").is_file():
        die(f"hub must be an indexed folder inside {root}: {hub}")
    workdir = Path(args.workdir).expanduser().resolve()
    if workdir == root or root in workdir.parents:
        die("workdir must be outside the knowledge root")
    evidence_path = workdir / "evidence.json"
    evidence = load_json(evidence_path) if evidence_path.exists() else {"results": {}}
    run = Run(
        args=args,
        listing=load_json(workdir / "listing.json"),
        queue=load_json(workdir / "queue.json"),
        results=evidence["results"],
        summaries=load_json(Path(args.summaries)) if args.summaries else {},
        writer=Writer(hub, args.dry_run),
    )
    fingerprints = run.queue["hub_fingerprints"]
    for path in (run.listing_md, run.queue_md, run.index_md):
        if sha(path) != fingerprints.get(path.name, ""):
            die(f"{path} changed since build_queue.py ran; re-run collection before writing")
    return run


def write_records(run):
    """Write per-repository records and update queue entry statuses."""
    by_id = {str(r["id"]): r for r in run.listing["repos"]}
    for entry in run.queue["entries"]:
        result = run.results.get(entry["provider_id"])
        if not result:
            continue
        run.tally[result["status"]] += 1
        entry["status"], entry["last_attempt"] = result["status"], result["attempted_at"]
        if result["status"] == "failed":
            entry["evidence"] = f"failed: {result.get('error', '')[:120]}"
            continue
        name = f"github-{entry['repo'].split('/')[0]}-{entry['provider_id']}.md"
        readme = result.get("readme")
        sha_note = f"README SHA `{readme['sha'][:12]}`" if readme else "no README"
        entry["evidence"] = f"[record](./{name}); {sha_note}"
        if result["status"] == "unchanged":
            continue
        entry["_listing"] = by_id[entry["provider_id"]]
        path = run.github_dir / name
        summary = run.summaries.get(entry["provider_id"], {})
        text = record_text(entry, result, summary, result["attempted_at"])
        existing = read_text(path)
        if USER_NOTES in existing:
            text += "\n" + USER_NOTES + existing.split(USER_NOTES, 1)[1]
        run.writer.write(path, text)


def listing_rows(run, old_text):
    """Merge the fresh listing with prior rows (kept only for partial runs)."""
    rows = {}
    if not run.complete:
        for row in read_table(old_text, "Repository Index"):
            rows[row["repo"].lower()] = row
    for repo in run.listing["repos"]:
        rows[repo["name"].lower()] = {
            "repo": repo["name"],
            "url": repo["url"],
            "provider_id": repo["id"],
            "visibility": repo["visibility"],
            "archived": "yes" if repo["archived"] else "no",
            "is_template": "yes" if repo["is_template"] else "no",
            "description": repo["description"] or "",
            "topics": ",".join(repo["topics"]),
            "business_unit": repo.get("business_unit") or "",
            "pushed_at": repo["pushed_at"] or "",
        }
    return sorted(rows.values(), key=lambda r: r["repo"].lower())


def write_listing(run):
    """Write the visibility listing with its history."""
    listing = run.listing
    old_text = read_text(run.listing_md)
    rows = listing_rows(run, old_text)
    visible = count_by(rows, lambda r: r["visibility"])
    active = count_by([r for r in rows if r["archived"] == "no"], lambda r: r["visibility"])
    history = read_table(old_text, "Listing history")
    history.insert(
        0,
        {
            "Retrieved (UTC)": run.span,
            "Summary": (
                f"{listing['status']}: {listing['pages']} pages, {listing['unique']} unique, "
                f"{listing['duplicates']} duplicates, "
                f"failed page {listing['failed_page'] or 'none'}"
            ),
        },
    )
    vis_line = ", ".join(
        f"{k} {visible[k]} ({active.get(k, 0)} not archived)" for k in sorted(visible)
    )
    partial_note = ""
    if not run.complete:
        partial_note = (
            f"\n- **Partial refresh:** page {listing['failed_page']} failed; "
            "rows not returned are kept from the previous listing."
        )
    legacy_link = ""
    if (run.github_dir / "moj-repos.md").exists():
        legacy_link = " and the [legacy inventory](./moj-repos.md)"
    org = listing["org"]
    run.writer.write(
        run.listing_md,
        f"""# Ministry of Justice repository visibility inventory

- Registration: `{run.args.registration}`
- Organization: `{org}` (includes HMPPS repositories in that org)
- Method: live read-only `gh api orgs/{org}/repos?type=all&per_page=100`, """
        f"{listing['pages']} pages, as the authenticated user; "
        "metadata only, no README or content reads\n"
        f"""- Retrieved: {run.span}
- Unique repositories: {len(rows)} ({listing["duplicates"]} duplicates). """
        "Archived repositories retained and flagged.\n"
        f"""- Visibility: {vis_line}{partial_note}
- Changes: see the [refresh queue](./refresh-queue.md) """
        "(new, metadata-changed, content-stale, missing-from-listing).\n"
        "- `business_unit` is the org's `business-unit` custom property; "
        'blank means not set (most repositories), not "no business unit".\n'
        "- Limitations: private repositories are only listed where the authenticated user "
        "has access, so the private count is a lower bound. Point-in-time snapshot. "
        f"""Categories are not assigned here (see per-repository records{legacy_link}).

## Listing history

{table(["Retrieved (UTC)", "Summary"], history)}

## Repository Index

{table(LISTING_COLUMNS, rows)}
""",
    )


def missing_rows(run, old_queue_text):
    """Repositories absent from the listing, carried forward until they reappear."""
    listing = run.listing
    current = {r["name"].lower() for r in listing["repos"]}
    missing = {
        r["repo (previous listing)"].split("/")[-1].lower(): r
        for r in read_table(old_queue_text, "Missing from listing")
    }
    for name in run.queue["missing"]:
        missing.setdefault(
            name,
            {
                "repo (previous listing)": f"{listing['org']}/{name}",
                "detected_at": listing["started"],
                "note": "unknown",
            },
        )
    return [m for k, m in sorted(missing.items()) if k not in current]


def write_queue(run):
    """Write refresh-queue.md and return the missing-from-listing rows."""
    missing = missing_rows(run, read_text(run.queue_md))
    rows = [{**e, "reason": ", ".join(e["reason"])} for e in run.queue["entries"]]
    open_entries = run.open_entries()
    priorities = joined_counts(count_by(open_entries, lambda e: e["priority"] or "?"))
    terms = ", ".join(run.queue["terms"]) or "none (no topic in request)"
    tally = run.tally
    run.writer.write(
        run.queue_md,
        f"""# Repository refresh queue

- Registration: `{run.args.registration}`
- Last built from: listing {run.span} ({run.listing["status"]})
- Priorities are recalculated on each invocation. """
        f"P1 = matches the current request (this run: {terms}), "
        "P2 = HMPPS (the `business-unit` property, or a labelled name/topic guess when it "
        "is not set; not confirmed ownership), P3 = rest of MoJ.\n"
        f"- This run: re-read {tally['re-read']}, unchanged {tally['unchanged']}, "
        f"failed {tally['failed']}. "
        f"""Open entries: {len(open_entries)} ({priorities or "none"}).

## Queue

{table(QUEUE_COLUMNS, rows)}

## Missing from listing

Not treated as deleted; access, visibility or name may have changed.

{table(MISSING_COLUMNS, missing)}
""",
    )
    return missing


def coverage_cells(run, missing, previous_success):
    """Cells for the registration's coverage row in index.md."""
    listing, tally = run.listing, run.tally
    open_entries = run.open_entries()
    reasons = {}
    for entry in open_entries:
        for reason in entry["reason"]:
            reasons[reason] = reasons.get(reason, 0) + 1
    priorities = count_by(open_entries, lambda e: e["priority"] or "?")
    detail = (
        f"{listing['pages']} pages, failed page {listing['failed_page'] or 'none'}; "
        f"{listing['unique']} unique, {listing['duplicates']} duplicates. "
        f"Open queue {len(open_entries)} ({joined_counts(reasons)}; {joined_counts(priorities)}); "
        f"{len(missing)} missing-from-listing. "
        f"README re-reads {sum(tally.values())} / {tally['re-read'] + tally['unchanged']} / "
        f"{tally['failed']}"
    )
    if run.complete:
        return [
            run.args.registration,
            run.span,
            "Complete for repos visible to the user",
            detail,
            "Full org listing; private repos limited to user access",
            listing["finished"],
            "gh api pages succeeded",
        ]
    return [
        run.args.registration,
        run.span,
        "Partial",
        detail,
        "Prior rows retained for unreturned repos; refresh clock not reset",
        previous_success,
        f"page {listing['failed_page']}: {listing.get('error') or ''}",
    ]


def write_coverage(run, missing):
    """Replace the registration's coverage row in index.md (written last)."""
    index = read_text(run.index_md)
    section = index.find("## Coverage and refresh attempts")
    pattern = re.compile(rf"^\| {re.escape(run.args.registration)} \|.*$", re.M)
    match = pattern.search(index, section)
    if section < 0 or not match:
        die(
            "coverage row for registration not found in index.md; "
            "records written, index not updated"
        )
    cells = coverage_cells(run, missing, split_row(match.group(0))[5])
    row = "| " + " | ".join(cell(x) for x in cells) + " |"
    run.writer.write(run.index_md, index[: match.start()] + row + index[match.end() :])


def main():
    """Persist the refresh: records, listing, queue, then the coverage row."""
    args = parse_args()
    run = load_run(args)
    write_records(run)
    write_listing(run)
    missing = write_queue(run)
    write_coverage(run, missing)
    print(("DRY RUN, would write:" if args.dry_run else "wrote:"), *run.writer.last(3), sep="\n  ")
    tally = run.tally
    print(
        f"records: {tally['re-read']} written; unchanged {tally['unchanged']}; "
        f"failed {tally['failed']}; open queue {len(run.open_entries())}; "
        f"listing {run.listing['status']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
