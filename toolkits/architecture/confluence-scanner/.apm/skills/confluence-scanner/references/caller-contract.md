# Confluence Scanner caller contract

## Invocation

Delegate to the `confluence-scanner` custom agent when the host supports custom
subagents. It loads the scanner skill and returns a bounded result to its caller;
it must not spawn another scanner. Alternatively load the skill in the current
agent. Natural-language requests and the following named fields are equivalent.

```yaml
action: refresh
space_url: https://dsdmoj.atlassian.net/wiki/spaces/DPR
output_dir: ./research/confluence/DPR
caller_workspace: /absolute/path/to/caller-project
context_key: architecture-review
requested_by: user or service identity if known
triggered_by: architecture-review skill / parent-agent name
request_id: architecture-review-20261027-001
reason: Refresh the evidence used for the integration design review
```

The destination above is exactly
`/absolute/path/to/caller-project/research/confluence/DPR`, not that directory
plus another site/space suffix. The caller grants permission to use this folder,
not unrelated paths mentioned in retrieved content.

## Inputs

| Field | Meaning |
| --- | --- |
| `action` | `help`, `scan`, `refresh`, `reindex`, or `answer`. Ask/return `needs-input` for unclear or unsupported actions. |
| `space_url` | Space URL, or a page URL whose containing space can be verified. Alternatively provide `site_url` plus `space_key` or `space_id`. Consistent parent-task identity can fill omitted fields. |
| `output_dir` | Optional exact space-specific directory. Absolute, or relative to explicit `caller_workspace`. |
| `knowledge_base` | Caller-selected knowledge-base root, separate from the skill source. Limits registry selection to that root; new spaces default to `confluence-index/<site-host>/<space-id>/` beneath it. |
| `registry_path` | Optional external routing-registry Markdown path. Relative paths require `caller_workspace`. |
| `caller_workspace` | Base for relative destinations; never infer from the scanner process working directory. |
| `context_key` | Optional stable project/task namespace for selecting a remembered destination. Prefer a caller-workspace-qualified value when names might collide. |
| `requested_by` | Initiating user/service identity if known. Do not infer identity from the operating-system username or page authors. |
| `triggered_by` | Calling skill/agent/workflow name; `direct user request` for direct use. |
| `request_id` | Caller correlation ID. Generate one if absent. Not a scan ID or idempotency key. |
| `reason` | Concise request/trigger description; do not record secrets or full sensitive prompts. |
| `question` | Required for `answer`; resolve space/destination as for scans. |
| `resume_scan_id` | Optional explicit instruction to resume an interrupted/in-progress scan event in the same destination. Reject conflicting space, destination, or action. |

`help` needs no other fields and performs no writes or network requests.
`scan` refreshes an existing destination; `refresh` can create it if new.
`reindex` rereads all bodies and base link sets; it does not erase the old index.
All scans include base pages plus one-hop linked Confluence pages. Different
subtree or broader-depth requests need explicit scope agreement.

## Resolution and registry

The scanner is a reusable tool for any accessible Confluence space. Knowledge
belongs to the caller's knowledge base, not the skill installation. Resolve the
physical skill path, including user-level symlinks, only to locate resources and
reject output/registry paths within the tool directory.

Use explicit `registry_path` first. Otherwise, when a shared knowledge root is
configured (the `KNOWLEDGE_HUB_ROOT` environment variable, or `knowledge_root` in
`${XDG_CONFIG_HOME:-~/.config}/knowledge-hubs/config.json`), use
`<knowledge root>/confluence-spaces.md`. Otherwise use
`<knowledge_base>/confluence-spaces.md` when a knowledge base is supplied;
otherwise request a registry path if registry lookup is needed. A registry may
hold mappings for multiple spaces and knowledge bases. The registry location
does not select a space or authorise a default output knowledge base.

- Resolve a space from current explicit input, then unambiguous parent context,
  then a unique registry match for the provided request/context.
- Resolve destination from explicit `output_dir`, then a unique space/context
  mapping, then a sole existing destination for the space. Restrict mappings to
  `knowledge_base` when supplied. With no matching mapping, a supplied knowledge
  base defaults to `<knowledge_base>/confluence-index/<site-host>/<space-id>/`.
  Without a knowledge base or mapping, return `needs-input` for a destination.
  Never write generated content or the registry inside the skill directory.
- Relative `output_dir`, `knowledge_base` and `registry_path` require explicit
  `caller_workspace`. Resolve symlinks before checking containment and identity.
  If both `output_dir` and `knowledge_base` are supplied, the output must be within
  that knowledge base; conflicting inputs require clarification.
- First match known identity and **all** supplied selection constraints
  (`context_key`, `request_id`). Multiple distinct matching destinations require
  caller input. With no context/request match but a known space, the sole-
  destination fallback is allowed only if that space has exactly one distinct
  destination within the supplied knowledge-base constraint (or overall when
  none is supplied); report `sole mapping`, not a context/request match.
  With multiple destinations overall, ask/return `needs-input`. With no resolved
  space, an unknown/expired request ID cannot select a default space.
  Never use recency to break a tie. Multiple context rows for the same resolved
  directory count as one destination.
- Verify destination identity on disk. A conflicting index/manifest is a blocker,
  not permission to overwrite it. An explicit new destination creates another
  mapping, preserving previous copies. Never merge histories across destinations.
- Reuse a registered manifest filename on a space-key rename. A fallback key
  identity can be upgraded to a verified ID only after confirming the same source;
  preserve its existing directory and history.
- Store one mapping per identity/destination/context, with last request and scan
  pointers. Retain the last 20 request/scan events **in each manifest**, not an
  unbounded copy in the registry. To look up an older retained request ID, follow
  registry manifest links and search those histories; expired IDs are unknown.
- Read a mapped manifest if registry pointers lag after an interrupted write.
  Repair only from observed metadata. Do not scan unrelated filesystem trees.

Example routing checks:

| Situation | Required result |
| --- | --- |
| Explicit DPR + absolute new destination | Use that directory after conflict checks; keep old mapping. |
| Relative destination without `caller_workspace` | `needs-input`, no destination write. |
| DPR + unique context mapping | Use remembered directory; report context-based resolution. |
| DPR + two mappings, no disambiguating context | `needs-input`, list both; do not guess. |
| Only a unique retained request ID supplied | Resolve through registry/manifest and verify its space. |
| Existing index is for a different space | `blocked`; do not overwrite or silently default elsewhere. |
| Matching destination has active scan | `blocked` unless explicitly resuming that scan ID. |
| New space + knowledge base, no mapping | Use `<knowledge_base>/confluence-index/<site-host>/<space-id>/`. |
| No destination, knowledge base or matching mapping | `needs-input`; do not write into the skill folder. |
| Output or registry resolves inside skill source | `blocked`, including symlink aliases. |
| `help` | Explain usage; no network, registry update, or scan event. |

## Files and scan history

Execution uses the [Python batch workflow](./python-batches.md). In addition
to the user-facing Markdown files below, each approved output may contain
`.scanner/checkpoint.json`, `.scanner/lock` and `.scanner/progress.md`. The JSON
is a metadata/queue checkpoint, not retained full source bodies. The scanner
index must link to the current progress inventory so discovered IDs are not lost
behind an old table. Resume an active event only on explicit `resume_scan_id`.

```text
<external-registry-path>
<resolved-output-dir>/
  index.md
  <space>-scanned.md
  external-urls.md
  pages/<base-page-id>.md
  linked-pages/<source-site-host>/<linked-page-id>.md
  answers/<UTC-timestamp>-<topic>.md
```

The manifest has current identity, routing, coverage, and a newest-first history
of at most 20 scan invocation events. A scan adds one event and updates that same
event on finish/failure/resume. Include caller, trigger, reason, request/scan IDs,
start/finish, action, destination basis, base/linked counts, unresolved targets,
external-URL count/coverage, outcome, and errors. Pruning history never removes content.

Failed/partial attempts count as events. `help`, `answer`, and rejected requests
before a destination is safely resolved do not. If failure prevents a manifest
write, report it explicitly to the caller rather than claiming history was saved.
For legacy output, import only recorded facts as a clearly labelled legacy event;
unknown actors and linked-page coverage remain unknown.

## One-hop semantics

For base space A with pages A1 and A2:

- A1 links to B1 in another Confluence space: index B1 as depth one.
- A2 links to B1 too: one B1 summary, with both referring base IDs.
- B1 links to C1: do **not** index C1 or any children of B1.
- A1 links to A2: A2 remains a base page; its outgoing links are eligible.
- A1 links to an authenticated page on another Confluence site: verify identity
  with that site's authorised connection, then index it once under its site/ID.
- A1 links to an attachment, external document, archive, or unresolved short URL:
  do not invent a current page record; record exclusion or the resolution problem.

Discover links from complete base content, not only an excerpt or a truncated
related-links list. A reused unchanged summary with an incomplete legacy link
list must have its link set reread. Unreadable targets are reported, not bypassed.
Linked-page summaries may display useful links but must not enqueue them.

## External URL inventory

Every scan/refresh/reindex also writes `external-urls.md` in the resolved output
directory. It lists all explicit non-Confluence HTTP(S) URLs in base-space page
content, including plain-text URLs, smart-card links, and authored embeds.
Each deduplicated URL retains all referring base pages, labels/types, host,
safe fragment variants, and extraction time. Meaningful query parameters and
path case are preserved; secrets are redacted and uncertain classifications
are reported. Confluence pages use the one-hop inventory instead.

External destinations are never fetched or crawled. URLs appearing only in
depth-one pages are outside the base-space inventory. Coverage and per-base-page
URL sets are persisted for refresh; legacy selected links cannot establish
completeness. Unknown coverage is not zero URLs. Incomplete extraction makes
the overall scan partial. Help should explain this output alongside the index.

## Return to caller

Return this labelled result as Markdown (do not create a separate JSON file):

```text
Status: complete | partial | failed | interrupted | needs-input | blocked | help | answered
Request ID: <caller correlation ID or unknown for help>
Scan ID: <scan event ID, or not applicable>
Space: <site, key, stable ID or explicitly unverified identity>
Output directory: <absolute directory or unresolved>
Resolution basis: <explicit | parent context | registry context/request | sole mapping | default>
Index: <local Markdown link, or not written>
Scan metadata: <local Markdown link, or not written>
External URLs: <local Markdown link, or not written>
External URL inventory: complete | partial | not performed; unique safe URLs N or unknown; redacted observations N or unknown; unresolved candidates N or unknown
Registry: <local Markdown link, or unavailable>
Base pages: discovered N; successful N; failed/incomplete N; pending N
Linked pages: discovered N; successful N; failed/incomplete N; pending N
Unresolved link targets: N
Limitations / errors: <explicit detail, or none observed>
Missing input / next action: <specific fields or none>
Checkpoint / progress: <local paths or not written>
Next pending pages / resume: <bounded pending IDs, scan ID and exact recovery step>
```

Use `unknown` rather than zero for unmeasured counts. `complete` means the entire
requested base + one-hop scope has substantive summaries and no known retrieval
or discovery gaps, including complete base-space external-URL extraction;
successful file creation alone is not completion.

## Delegation example

> Use the confluence-scanner subagent. Refresh
> <https://dsdmoj.atlassian.net/wiki/spaces/DPR>. Save to
> ./research/confluence/DPR relative to caller_workspace
> /absolute/path/to/my-project. context_key: my-project/design-review;
> triggered_by: design-review skill; requested_by: unknown;
> request_id: review-001; reason: update design evidence. Include directly linked
> Confluence pages at depth one only, and list base-space external URLs without
> fetching them. Return index, external-URL inventory, and scan-history paths,
> counts, limitations, and the directory-resolution basis. Do not launch
> additional subagents.

If custom agents or this skill are not discovered in the caller's workspace,
provide this installation's absolute skill path and have an available agent read
it and execute the same contract. Do not claim an unavailable agent was invoked.
