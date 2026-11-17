#!/usr/bin/env python3
"""Local, resumable Confluence batch bookkeeping. No network or credentials."""

import argparse
import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile
from contextlib import contextmanager
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit


class ScanError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ScanError(message)


def identifier(value: object) -> str:
    require(
        isinstance(value, str) and bool(re.fullmatch(r"[0-9]+", value)),
        "Page and space IDs must be numeric strings.",
    )
    return str(value)


def site_url(value: str) -> str:
    parsed = urlsplit(value)
    require(
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and bool(re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", parsed.hostname or "", re.I))
        and not parsed.username
        and not parsed.password
        and parsed.path in ("", "/")
        and not parsed.query
        and not parsed.fragment,
        "Site must be an HTTPS origin without credentials, path, or query.",
    )
    return value.rstrip("/").lower()


def safe_url(value: str, base: str) -> str:
    parsed = urlsplit(urljoin(base, value.strip()))
    require(
        parsed.scheme in ("https", "http") and bool(parsed.hostname), "Expected an HTTP(S) URL."
    )
    require(not parsed.username and not parsed.password, "URL credentials are forbidden.")
    query = []
    for key, val in parse_qsl(parsed.query, keep_blank_values=True):
        if re.search(
            r"token|secret|signature|credential|password|api.?key|ouid|jwt|^st$", key, re.I
        ):
            val = "REDACTED"
        query.append((key, val))
    return urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, urlencode(query), "")
    )


def page_key(site: str, page_id: str) -> str:
    return site + "|" + page_id


def digest(path: Path) -> Optional[str]:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def atomic_write(path: Path, text: str) -> None:
    require(not path.is_symlink(), "Refusing to overwrite a symlink.")
    fd, name = tempfile.mkstemp(prefix=".scanner-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def contained(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    require(resolved == root or root in resolved.parents, "Path escapes the output root.")
    return resolved


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.urls: List[str] = []
        self.text: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        for key, value in attrs:
            if value and key in ("href", "src", "ri:value"):
                self.urls.append(value)
        # Confluence storage links with ri:content-title need connector resolution.
        if tag == "ri:page":
            values = dict(attrs)
            if values.get("ri:content-title"):
                self.urls.append(
                    "unresolved-title:"
                    + str(values["ri:content-title"])
                    + "|space:"
                    + str(values.get("ri:space-key", "source"))
                )

    def handle_data(self, data: str) -> None:
        self.text.append(data)
        self.urls.extend(re.findall(r"https?://[^\s<>\"']+", data))


def extract(body: str, base: str) -> List[dict]:
    parser = Links()
    parser.feed(body)
    parser.close()
    results: Dict[str, dict] = {}
    for value in parser.urls:
        if value.startswith("unresolved-title:"):
            value += "|context:" + hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]
            results[value] = {"url": value, "kind": "unresolved", "target": None}
            continue
        if value.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
            continue
        try:
            url = safe_url(value, base)
        except (ScanError, ValueError):
            # Do not echo malformed source text, which might contain credentials.
            opaque = hashlib.sha256(value.encode("utf-8")).hexdigest()
            label = "unresolved-url:" + opaque
            results[label] = {"url": label, "kind": "unresolved", "target": None}
            continue
        parsed = urlsplit(url)
        query = dict(parse_qsl(parsed.query))
        match = re.search(r"/(?:wiki/)?spaces/[^/]+/pages/(\d+)(?:/|$)", parsed.path)
        page_id = match.group(1) if match else None
        if parsed.path.endswith("/viewpage.action") and query.get("pageId", "").isdigit():
            page_id = query["pageId"]
        origin = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
        if page_id:
            kind = "confluence"
        elif "/attachments/" in parsed.path or "/download/attachments/" in parsed.path:
            kind = "attachment"
        elif (
            origin == urlsplit(base).scheme + "://" + urlsplit(base).netloc
            or "/wiki/" in parsed.path
        ):
            kind = "unresolved"
        else:
            kind = "external"
        # Redacted URLs cannot establish target identity.
        target = page_key(origin, page_id) if page_id and "REDACTED" not in url else None
        results[url] = {"url": url, "kind": kind, "target": target}
    return list(results.values())


class Store:
    def __init__(self, output: Path, knowledge_base: Path) -> None:
        root = knowledge_base.resolve(strict=True)
        self.output = contained(output, root)
        require(self.output.is_dir(), "Output directory must already exist and be approved.")
        skill_root = Path(__file__).resolve().parent.parent
        require(
            self.output != skill_root and skill_root not in self.output.parents,
            "Output cannot be inside the skill.",
        )
        self.directory = contained(self.output / ".scanner", self.output)
        self.directory.mkdir(exist_ok=True, mode=0o700)
        self.path = contained(self.directory / "checkpoint.json", self.output)

    @contextmanager
    def locked(self) -> Iterator[None]:
        lock_path = self.directory / "lock"
        require(not lock_path.is_symlink(), "Lock path cannot be a symlink.")
        with lock_path.open("a", encoding="utf-8") as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ScanError("Another helper invocation owns the output lock.") from exc
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def load(self, scan_id: str) -> dict:
        require(self.path.is_file(), "No checkpoint: run init first.")
        state = json.loads(self.path.read_text(encoding="utf-8"))
        require(state["scan_id"] == scan_id, "Scan ID mismatch; do not resume another event.")
        return state

    def save(self, state: dict) -> None:
        atomic_write(self.path, json.dumps(state, indent=2, sort_keys=True) + "\n")

    def summary_path(self, page: dict) -> Path:
        site = urlsplit(page["site"]).hostname
        relative = (
            "pages/" + page["id"] + ".md"
            if page["depth"] == 0
            else "linked-pages/" + str(site) + "/" + page["id"] + ".md"
        )
        return contained(self.output / relative, self.output)


def new_state(
    scan_id: str, site: str, space_id: str, linked_sites: Optional[List[str]] = None
) -> dict:
    require(bool(re.fullmatch(r"[A-Za-z0-9_-]+", scan_id)), "Invalid scan ID.")
    return {
        "schema": 1,
        "scan_id": scan_id,
        "site": site_url(site),
        "space_id": identifier(space_id),
        "authorised_sites": sorted({site_url(site), *(site_url(s) for s in linked_sites or [])}),
        "discovery_complete": False,
        "cursor": None,
        "seen_cursors": [],
        "pages": {},
        "links": {},
    }


def page_metadata(data: dict) -> dict:
    site = site_url(data["site"])
    page_id = identifier(data["id"])
    require(
        isinstance(data.get("title"), str) and bool(data["title"].strip()),
        "A page title is required.",
    )
    require(
        isinstance(data.get("version"), int)
        and not isinstance(data["version"], bool)
        and data["version"] > 0,
        "A positive observed page version is required.",
    )
    require(data.get("status") == "current", "Only verified current pages can be queued.")
    return {
        "site": site,
        "id": page_id,
        "title": data["title"],
        "version": data["version"],
        "space_id": identifier(data["space_id"]),
        "url": site + "/wiki/pages/viewpage.action?pageId=" + page_id,
        "modified": data.get("modified", "unknown"),
        "status": "pending",
        "attempts": 0,
    }


def inventory(state: dict, data: dict) -> None:
    require(not state["discovery_complete"], "Discovery already complete.")
    require(data.get("cursor") == state["cursor"], "Unexpected inventory cursor.")
    require(isinstance(data.get("pages"), list), "pages must be a list.")
    require("next_cursor" in data, "Explicit next_cursor (null when exhausted) is required.")
    next_cursor = data["next_cursor"]
    require(
        next_cursor is None or isinstance(next_cursor, str) and bool(next_cursor),
        "next_cursor must be a nonempty string or null.",
    )
    require(
        next_cursor is None
        or next_cursor != state["cursor"]
        and next_cursor not in state["seen_cursors"],
        "Pagination cursor repeated.",
    )
    pages = [page_metadata(item) for item in data["pages"]]
    for page in pages:
        require(
            page["site"] == state["site"] and page["space_id"] == state["space_id"],
            "Inventory page is outside the approved base space.",
        )
        key = page_key(page["site"], page["id"])
        previous = state["pages"].get(key)
        if previous:
            require(
                previous["version"] == page["version"], "Page version changed during discovery."
            )
        page.update(depth=0)
        state["pages"][key] = page
    if state["cursor"] is not None:
        state["seen_cursors"].append(state["cursor"])
    state["cursor"] = next_cursor
    state["discovery_complete"] = next_cursor is None


def resolve_link(state: dict, data: dict) -> None:
    require(state["discovery_complete"], "Finish base discovery before resolving linked pages.")
    observed_url = (
        data["url"]
        if data["url"].startswith(("unresolved-title:", "unresolved-url:"))
        else safe_url(data["url"], state["site"])
    )
    require(observed_url in state["links"], "Link was not observed on a base page.")
    link = state["links"][observed_url]
    require(bool(link["referrers"]), "Linked page needs base-page provenance.")
    if data["disposition"] != "current":
        require(
            data["disposition"] in ("archived", "attachment", "external", "denied", "unresolved"),
            "Unknown link disposition.",
        )
        link.update(disposition=data["disposition"])
        if data["disposition"] == "external":
            link["kind"] = "external"
            for ref in link["referrers"]:
                for url in state["pages"][ref].get("urls", []):
                    if url["url"] == observed_url:
                        url["kind"] = "external"
        return
    page = page_metadata(data["page"])
    require(
        page["site"] in state["authorised_sites"],
        "Cross-site target has no explicitly authorised connector/site in this checkpoint.",
    )
    key = page_key(page["site"], page["id"])
    require(link["target"] in (None, key), "Resolved page conflicts with observed target ID.")
    if key not in state["pages"]:
        page.update(depth=1)
        state["pages"][key] = page
    link.update(target=key, disposition="resolved")


def record(store: Store, state: dict, data: dict) -> None:
    require(state["discovery_complete"], "Finish base discovery before processing bodies.")
    key = page_key(site_url(data["site"]), identifier(data["id"]))
    require(key in state["pages"], "Page is not queued.")
    page = state["pages"][key]
    require(
        data.get("source_status") == "current",
        "Body retrieval must confirm the page is still current.",
    )
    require(data["version"] == page["version"], "Body version differs from inventory version.")
    require(isinstance(data.get("body"), str), "Retrieved page body is required (never persisted).")
    require(
        isinstance(data.get("summary"), str) and bool(data["summary"].strip()),
        "A substantive agent-written summary or explicit empty-body finding is required.",
    )
    for flag in ("body_complete", "links_complete", "urls_complete"):
        require(type(data.get(flag)) is bool, "Explicit completeness flags are required.")
    require(
        isinstance(data.get("gaps"), list) and all(isinstance(g, str) for g in data["gaps"]),
        "gaps must be an explicit list of descriptions.",
    )
    require(
        isinstance(data.get("retrieved_at"), str)
        and bool(re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z", data["retrieved_at"])),
        "Observed UTC retrieval timestamp required.",
    )
    urls = extract(data["body"], page["url"]) if page["depth"] == 0 else []
    path = store.summary_path(page)
    require("expected_summary_sha256" in data, "Supply the summary hash returned by next.")
    require(
        digest(path) == data["expected_summary_sha256"],
        "Summary changed since selection; reread and reconcile it.",
    )
    complete = data["body_complete"] and not data["gaps"]
    if page["depth"] == 0:
        complete = complete and data["links_complete"] and data["urls_complete"]
    page.update(
        status="complete" if complete else "incomplete",
        attempts=page["attempts"] + 1,
        retrieved_at=data["retrieved_at"],
        gaps=data["gaps"],
        body_complete=data["body_complete"],
        links_complete=data["links_complete"],
        urls_complete=data["urls_complete"],
        urls=urls,
    )
    if page["depth"] == 0:
        # Replacing a base link set removes its previous provenance, not another page's.
        for link in state["links"].values():
            link["referrers"] = [ref for ref in link["referrers"] if ref != key]
        for url in urls:
            if url["kind"] not in ("confluence", "unresolved"):
                continue
            link = state["links"].setdefault(
                url["url"], {**url, "referrers": [], "disposition": "pending"}
            )
            if url["target"] in state["pages"]:
                link["disposition"] = "resolved"
            if key not in link["referrers"]:
                link["referrers"].append(key)
    # Incomplete reads must never replace a previously useful summary.
    if complete or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        summary = data["summary"].strip()
        require(
            "ouid=" not in summary.lower(), "Remove identifying URL query parameters from summary."
        )
        text = (
            "# "
            + page["title"].replace("\n", " ")
            + "\n\n"
            + "- Source: "
            + page["url"]
            + "\n"
            + "- Page ID: "
            + page["id"]
            + "\n"
            + "- Version: "
            + str(page["version"])
            + "\n"
            + "- Source modified (UTC): "
            + str(page["modified"])
            + "\n"
            + "- Link depth: "
            + str(page["depth"])
            + "\n"
            + "- Retrieved (UTC): "
            + data["retrieved_at"]
            + "\n"
            + "- Status: "
            + page["status"]
            + "\n\n## Summary\n\n"
            + summary
            + "\n"
            + "\n## Gaps\n\n"
            + (
                "\n".join("- " + gap for gap in data["gaps"])
                or "None reported by the connector/agent."
            )
            + "\n"
        )
        if page["depth"] == 0:
            text += "\n## Observed base-page URLs\n\n"
            text += "\n".join("- " + url["kind"] + ": " + url["url"] for url in urls) + "\n"
        else:
            referrers = sorted(
                {
                    ref
                    for link in state["links"].values()
                    if link["target"] == key
                    for ref in link["referrers"]
                }
            )
            text += (
                "\n## Referring base pages\n\n" + "\n".join("- " + ref for ref in referrers) + "\n"
            )
        atomic_write(path, text)
    state["pages"][key] = page


def counts(state: dict) -> dict:
    result: dict = {}
    for depth, name in ((0, "base"), (1, "linked")):
        pages = [p for p in state["pages"].values() if p["depth"] == depth]
        result[name] = {
            status: sum(p["status"] == status for p in pages)
            for status in ("pending", "complete", "incomplete", "failed")
        }
        result[name]["discovered"] = len(pages)
    active_links = [link for link in state["links"].values() if link["referrers"]]
    unresolved = [
        link
        for link in active_links
        if link["disposition"] not in ("resolved", "archived", "attachment", "external")
    ]
    result["unresolved_links"] = len(unresolved)
    result["discovery_complete"] = state["discovery_complete"]
    # Unreferenced old linked pages stay in the checkpoint, but cannot prove completeness.
    result["complete"] = (
        state["discovery_complete"]
        and not unresolved
        and all(p["status"] == "complete" for p in state["pages"].values())
    )
    result["cursor"] = state["cursor"]
    return result


def select(store: Store, state: dict, limit: int, retry: bool, max_attempts: int = 3) -> dict:
    require(1 <= limit <= 100, "Batch limit must be between 1 and 100.")
    require(1 <= max_attempts <= 10, "Maximum attempts must be between 1 and 10.")
    selected = []
    for key, page in sorted(state["pages"].items(), key=lambda item: (item[1]["depth"], item[0])):
        retryable = (
            page["status"] == "incomplete"
            or page["status"] == "failed"
            and page.get("retryable", False)
        )
        if page["status"] == "pending" or retry and retryable and page["attempts"] < max_attempts:
            selected.append({**page, "expected_summary_sha256": digest(store.summary_path(page))})
        if len(selected) == limit:
            break
    return {
        "pages": selected,
        "links": [
            link
            for link in state["links"].values()
            if link["referrers"] and link["disposition"] == "pending"
        ][:limit],
        "coverage": counts(state),
    }


def report(store: Store, state: dict) -> None:
    path = contained(store.directory / "progress.md", store.output)
    marker = "<!-- confluence-scanner batch checkpoint -->"
    require(
        not path.exists() or path.read_text(encoding="utf-8").startswith(marker),
        "Progress file is not helper-owned; refusing to overwrite it.",
    )
    coverage = counts(state)
    text = (
        marker
        + "\n# Batch progress\n\nScan ID: `"
        + state["scan_id"]
        + "`\n\n"
        + "Discovery exhausted: "
        + str(state["discovery_complete"])
        + "\n\n"
        + "Complete: "
        + str(coverage["complete"])
        + "\n\n"
        + "Unresolved link targets: "
        + str(coverage["unresolved_links"])
        + "\n\n"
        + "This is the current helper inventory, not the legacy scanner table. "
        + "Keep the scanner index and manifest reconciled with these counts.\n\n"
        + "| Site / page ID | Depth | Title | Version | Status | Summary |\n"
        + "|---|---|---|---|---|---|\n"
    )
    for key, page in sorted(state["pages"].items()):
        target = store.summary_path(page)
        link = (
            "[Summary](../" + str(target.relative_to(store.output)) + ")"
            if target.exists()
            else "Not available"
        )
        title = page["title"].replace("|", "\\|").replace("\n", " ")
        text += (
            "| "
            + key.replace("|", " / ")
            + " | "
            + str(page["depth"])
            + " | "
            + title
            + " | "
            + str(page["version"])
            + " | "
            + page["status"]
            + " | "
            + link
            + " |\n"
        )
    atomic_write(path, text)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--knowledge-base", type=Path, required=True)
    parser.add_argument("--scan-id", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--site", required=True)
    init.add_argument("--space-id", required=True)
    init.add_argument(
        "--previous-scan-id",
        help="Explicitly replace a prior finalized checkpoint for a new scan event.",
    )
    init.add_argument(
        "--linked-site",
        action="append",
        default=[],
        help="Additional HTTPS site with an already verified authorised read connector.",
    )
    for name in ("inventory", "record", "resolve", "fail", "status", "report"):
        commands.add_parser(name)
    pending = commands.add_parser("next")
    pending.add_argument("--limit", type=int, default=10)
    pending.add_argument("--retry", action="store_true")
    pending.add_argument("--max-attempts", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        store = Store(args.output, args.knowledge_base)
        with store.locked():
            if args.command == "init":
                state = new_state(args.scan_id, args.site, args.space_id, args.linked_site)
                if store.path.exists():
                    require(
                        args.previous_scan_id is not None,
                        "Checkpoint exists; resume it or supply --previous-scan-id for a new event.",
                    )
                    previous = store.load(args.previous_scan_id)
                    require(
                        previous["scan_id"] != args.scan_id, "New event must have a new scan ID."
                    )
                    require(
                        previous["site"] == state["site"]
                        and previous["space_id"] == state["space_id"],
                        "Cannot change checkpoint space identity.",
                    )
                    manifests = list(store.output.glob("*-scanned.md"))
                    for manifest in manifests:
                        text = manifest.read_text(encoding="utf-8")
                        require(
                            "- Latest state: in-progress" not in text
                            or "- Latest scan ID: " + args.scan_id + "\n" in text,
                            "Previous scan is active; explicitly resume it instead.",
                        )
                store.save(state)
                result = counts(state)
            else:
                state = store.load(args.scan_id)
                if args.command in ("inventory", "record", "resolve", "fail"):
                    data = json.load(sys.stdin)
                    require(isinstance(data, dict), "Command input must be a JSON object.")
                    if args.command == "inventory":
                        inventory(state, data)
                    elif args.command == "record":
                        rows = data.get("pages", [data])
                        require(
                            isinstance(rows, list) and 1 <= len(rows) <= 100,
                            "Record batch must contain 1 to 100 pages.",
                        )
                        for row in rows:
                            record(store, state, row)
                            store.save(state)
                    elif args.command == "resolve":
                        resolve_link(state, data)
                    else:
                        key = page_key(site_url(data["site"]), identifier(data["id"]))
                        require(key in state["pages"], "Page is not queued.")
                        require(
                            isinstance(data.get("error"), str) and bool(data["error"].strip()),
                            "A safe, non-sensitive failure reason is required.",
                        )
                        page = state["pages"][key]
                        require(
                            type(data.get("retryable")) is bool,
                            "Specify retryable=false for denials/authentication failures.",
                        )
                        page.update(
                            status="failed",
                            attempts=page["attempts"] + 1,
                            error=data["error"],
                            retryable=data["retryable"],
                        )
                    store.save(state)
                if args.command == "report":
                    report(store, state)
                result = (
                    select(store, state, args.limit, args.retry, args.max_attempts)
                    if args.command == "next"
                    else counts(state)
                )
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print("Scanner error: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
