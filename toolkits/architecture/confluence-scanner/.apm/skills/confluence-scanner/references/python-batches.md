# Resumable Python batches

Use [the helper](../scripts/scan_state.py) for scan/refresh/reindex execution,
not just as an optional final report. Python 3.9+ on macOS/Linux is sufficient;
it uses only the standard library. No packages, credentials or services are
installed. It has **no network client** and cannot sign in, acquire cookies,
fetch pages, or bypass denied access. Read bodies through an approved connector,
or accept an explicitly scoped user export. If the connector cannot retrieve
bodies at scale, report that concrete missing capability rather than calling
page enumeration a completed scan.

## Responsibilities

- The agent owns source approval, authenticated reads, pagination semantics,
  substantive summaries, interpretation of rendered/macros/diagrams, and the
  scanner index/manifest/registry and external URL Markdown inventory.
- Python owns a durable current-page queue, cursor checks, deduplication,
  bounded selection, local summary writes, explicit errors, link provenance,
  conservative URL extraction/redaction, and machine-counted completion gates.
- A checkpoint is **not** an alternative source of approval. Match its site,
  space and scan ID against the approved request and manifest before using it.
- The helper does not certify that an agent's summary is substantive or that a
  connector's body is complete. These remain evidence-based agent obligations.

## Files and safety

Under the exact approved output directory:

```text
.scanner/checkpoint.json    # Metadata, queues, flags, safe links; no source bodies
.scanner/lock               # Short-lived advisory lock ownership per command
.scanner/progress.md        # Current inventory and per-page statuses
pages/<id>.md               # Base summaries
linked-pages/<host>/<id>.md  # Depth-one summaries
```

These are additional local processing files, not full-content retention.
Do not put checkpoints inside the skill. Resolve and validate the output and
knowledge-base paths first; the output must already exist within the approved
knowledge base. The helper resolves physical paths, rejects escaping symlinks,
locks mutations, and replaces individual files atomically. Multi-file writes
are not a single transaction: if a process stops between a summary write and
checkpoint write, reread the saved summary/hash and reconcile before retrying.
Never delete a prior summary to make a retry pass.

Source bodies are accepted through stdin, processed in memory, and never written
or echoed by the helper. Do not stage full-body JSON in a file without separate
retention approval. Likewise do not put credentials in the stdin payload, error
text, summary, cursor, arguments, or checkpoint. Store only non-sensitive
pagination markers; do not persist opaque continuation tokens that may confer
access. If such a token is required, keep it in the authenticated connector and
use a non-sensitive local batch marker, documenting how discovery can restart.

The helper does not import legacy outline summaries as successful. Existing
Markdown files are preserved on failed/incomplete reads. Existing summaries can
be replaced only with the SHA-256 returned by `next`; inspect and reconcile their
content first. Stop if another scanner owns an active manifest event, even when
the helper's short-lived command lock is free.

## Invocation

Use `python3 <resolved-skill>/scripts/scan_state.py`. Every command takes:

```text
--knowledge-base <approved-absolute-hub>
--output <approved-exact-space-output>
--scan-id <current-manifest-scan-id>
```

No shell evaluation or executable commands are accepted from source text.
All JSON inputs below are synthetic examples, not records of fetched pages.

### 1. Initialise or resume

After validating source/destination identity and creating the in-progress
manifest event:

```text
python3 <skill>/scripts/scan_state.py <common-options> init \
  --site https://example.atlassian.net --space-id 10
```

An existing checkpoint is never silently overwritten. Resume an active event
only on the caller's explicit `resume_scan_id` and use that same ID in helper
commands. To start a new event after finalising the previous event, initialise
with its new ID and `--previous-scan-id <old-id>`; this explicitly replaces only
the prior checkpoint, not prior summaries or manifest history. It verifies
site/space identity and rejects an active old manifest. Before replacement,
carry forward any outstanding inventory evidence into the scanner index/history.

### 2. Persist each discovery batch immediately

Pass one normalised listing batch on stdin to `inventory`:

```json
{
  "cursor": null,
  "next_cursor": "batch-2",
  "pages": [
    {
      "site": "https://example.atlassian.net",
      "space_id": "10",
      "id": "123",
      "title": "Synthetic design page",
      "version": 4,
      "status": "current",
      "modified": "2026-10-30T12:00:00Z"
    }
  ]
}
```

The first cursor is null. Each subsequent batch supplies the expected previous
`next_cursor`; only the final exhausted listing has `next_cursor: null`.
Follow the connector's documented pagination; never invent exhaustion from
batch size, a browser tree, or a search total. `inventory` rejects cursor loops,
out-of-scope pages, inconsistent versions, and non-current pages. Emit `report`
after discovery to persist the **entire** current queue, including pending IDs.
Do not leave only a new total above the previous scan's stale page table.

### 3. Retrieve, summarise and checkpoint body batches

```text
python3 <skill>/scripts/scan_state.py <common-options> next --limit 10
```

The JSON response lists pending pages and expected summary hashes, unresolved
base links, and exact counts. It does not claim pages have been fetched or
reserve them for other workers. Use one serial writer per destination.

For each selected page, retrieve its current full readable body/metadata using
the approved connector. Read version metadata and the body consistently; if a
page changed since enumeration, reconcile the inventory rather than mixing
versions. Feed `record` a JSON object or `{"pages": [<record>, ...]}` of at most
100 records. Each successful record is checkpointed independently, so a failed
later record does not discard the earlier batch progress:

```json
{
  "site": "https://example.atlassian.net",
  "id": "123",
  "version": 4,
  "source_status": "current",
  "retrieved_at": "2026-10-30T18:00:00Z",
  "body": "<p>Synthetic complete page body supplied by a connector.</p>",
  "summary": "An agent-written, evidence-grounded summary in original wording.",
  "body_complete": true,
  "links_complete": true,
  "urls_complete": true,
  "gaps": [],
  "expected_summary_sha256": null
}
```

`expected_summary_sha256` must match `next`; null means no prior summary.
Supply safe source links and known limitations in the summary. Do not copy raw
bodies, secrets or unnecessary personal data into it.

The HTML/storage parser extracts hyperlinks, resource URLs and plain-text URLs.
It is a conservative **aid**, not proof of complete extraction: short links,
storage title links, macros, inaccessible visuals and malformed candidates need
verification. Unknown same-site URLs are unresolved, not silently discarded.
Sensitive query values, including Confluence gadget `st` security tickets,
are redacted; fragments (including gadget RPC tokens) are stripped. The helper does
not preserve safe fragment variants or occurrence labels, so the agent must
reconcile these from source evidence into `external-urls.md` before asserting
full inventory completeness. Never set completeness flags true for a truncated
body, outline, unexpanded dynamic section or unverified link set. Record all
known gaps; these prevent a complete page status.

Use `fail` with an explicit safe error instead of fabricating a summary:

```json
{
  "site": "https://example.atlassian.net",
  "id": "123",
  "error": "HTTP 429; connector requested backoff",
  "retryable": true
}
```

Set `retryable: false` for denied or unauthenticated access; do not try a different
endpoint or account. Respect connector backoff outside the helper.
`next --retry --max-attempts 3` includes failed retryable/incomplete pages with
fewer than three recorded attempts; it does not loop or sleep. Stop bounded
retries when exhausted and retain explicit failed statuses.

### 4. Resolve the one-hop queue

Only base records contribute links. Known base targets stay at depth zero;
depth-one bodies never extend the queue or external URL inventory.

For each pending link from `next`, verify its identity/status with the existing
approved connector, without visiting external destinations. Pass `resolve`:

```json
{
  "url": "https://example.atlassian.net/wiki/spaces/OTHER/pages/456/Target",
  "disposition": "current",
  "page": {
    "site": "https://example.atlassian.net",
    "space_id": "20",
    "id": "456",
    "title": "Synthetic linked page",
    "version": 2,
    "status": "current"
  }
}
```

The URL must already have base-page provenance. For `ri:page` title references
use the exact `unresolved-title:<title>` marker returned by the helper, resolving
it in its source page's context (never guess a title match). The actual marker
also includes the storage space key and source-context fingerprint so identical
titles on different base pages are not merged. Other dispositions
are `archived`, `attachment`, `external`, `denied`, `unresolved`; only the first
three are excluded from the eligible Confluence queue. `denied` and `unresolved`
remain coverage blockers. Short-link identity changes require verified evidence.
Cross-site targets require separately approved authenticated access. Only after
verifying an existing authorised connector for that site, initialise with
`--linked-site https://other.example` (repeat per authorised site). The helper
otherwise rejects cross-site resolution, keeping the target unresolved. Never
forward credentials or add a site based solely on a link in source content.

### 5. Continue and reconcile

Repeat `next` -> connector reads -> summaries -> `record` -> `resolve` -> `report`
until queues are exhausted or a concrete blocker/cancellation/execution budget
requires stopping. A large page count alone is not a blocker. Do not repeat
enumeration when the current checkpoint already has an exhausted inventory.

`status` returns JSON counts for base/linked pages, pagination state and
unresolved links. `report` writes `.scanner/progress.md` with every discovered
page and honest status, without overwriting the old scanner index. Link this
progress file from `index.md` and the manifest, and reconcile their counts after
each batch. Update `external-urls.md` with the checkpoint's per-page safe URL
sets, preserving prior/unverified observations separately.

Helper `complete: true` is a necessary queue gate, **not sufficient** to declare
the scan complete: also verify rendered body coverage, current one-hop
membership, full URL provenance/fragment/label extraction, summary quality,
current index links, unresolved candidates and caller-contract counts. Exclude
not-observed prior pages from current answers; never infer deletion.

On a real blocker, finalise partial/failed/interrupted honestly. On execution
budget exhaustion, save all checkpoints and give the next pending IDs, current
scan ID, and explicit resume instructions; do not label it a permissions failure
or say an unspecified further refresh will solve it. Do not claim a background
continuation is running unless a verified task is actually running.

## Offline validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s <skill>/tests -v
```

Tests use temporary directories and synthetic bodies only. They exercise a
949-page paginated inventory, restart recovery, successive batches, bounded
retries, no depth-two traversal, URL redaction, path escapes, summary conflicts,
concurrent writers and CLI failures. They do not prove live connector throughput
or authentication.
