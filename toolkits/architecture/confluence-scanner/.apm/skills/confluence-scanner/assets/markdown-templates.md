# Markdown output templates

Replace placeholders with observed values. Escape table pipes and newlines in
titles/summaries. Use relative links for local files and canonical URLs for
Confluence citations. Do not create example pages as if they were scanned data.

## Space/destination registry: `<external-registry-path>`

Keep the registry and all generated output outside the skill source. Use the
caller contract to resolve the registry and caller-selected knowledge base.

```markdown
# Confluence Scanner space registry

One row per verified site/space, destination, and caller context. Multiple
destinations are allowed; never choose between them by recency.

| Site | Space key | Space ID | Context key | Output directory (absolute) | Manifest | Last request ID | Last scan ID | Last outcome | Updated (UTC) |
|---|---|---|---|---|---|---|---|---|---|
| <canonical site> | <key> | <id or key fallback> | <caller context or unspecified> | <absolute path> | [Scan metadata](<relative path or absolute local path>) | <request ID> | <scan ID> | <state> | <UTC> |
```

Preserve unrelated rows. Links to destinations outside the registry directory may
use relative paths or absolute local filesystem paths; they are not web URLs.
The history inside each manifest is the source of truth for retained request IDs.

## Scan metadata: `<space>-scanned.md`

```markdown
# <Space key> - scan metadata

- Site: <canonical site>
- Space key: <key>
- Space ID: <id or explicitly labelled key fallback>
- Space title: <verified title>
- Output directory: <absolute directory>
- Index: [Page index](./index.md)
- External URLs: [External URL inventory](./external-urls.md)
- Registry: [Space registry](<relative or absolute local path>)
- Latest scan ID: <unique ID>
- Latest request ID: <caller correlation ID>
- Latest state: <in-progress | complete | partial | failed | interrupted>
- Last attempt started (UTC): <ISO 8601>
- Last attempt finished (UTC): <ISO 8601 or not finished or unknown>
- Last complete scan (UTC): <time or none>
- Scope policy: All accessible current base pages plus directly linked current Confluence pages; maximum link depth 1
- History limit: 20 invocation events, newest first

## Scan history

### <scan ID>

- Request ID: <caller correlation ID>
- Action: <scan | refresh | reindex>
- Requested by: <known initiating user/service or unknown>
- Triggered by: <calling skill, agent, workflow, or direct user request>
- Context key: <caller-supplied context or unspecified>
- Caller workspace: <supplied absolute path or unknown>
- Reason: <brief trigger/request description, without secrets>
- Started (UTC): <ISO 8601>
- Finished (UTC): <ISO 8601 or not finished or unknown>
- Duration (seconds): <measured/calculated value or unknown>
- Outcome: <in-progress | complete | partial | failed | interrupted>
- Output directory: <resolved absolute directory for this event>
- Resolution basis: <explicit | parent context | registry context/request | sole mapping | default | legacy import>
- Scope actually attempted: <base space/subtree and link depth, not merely current default>
- Base discovery exhausted: <yes | no | cannot establish>
- Base pages: discovered <N>; successful <N>; failed/incomplete <N>; pending <N>
- Linked-page discovery complete: <yes | no | not performed | unknown>
- Linked pages: discovered <N>; successful <N>; failed/incomplete <N>; pending <N>
- Unresolved link targets: <N or unknown>
- External URL inventory: <complete | partial | not performed>; unique safe URLs <N or unknown>; redacted observations <N or unknown>; unresolved candidates <N or unknown>
- Summary quality: <substantive | mixed | outline-only | unknown>
- Limitations/errors: <specific coverage gaps, failures, or none observed>
- Provenance: <observed invocation | legacy import, citing observed source metadata>
```

Repeat the `### <scan ID>` event block at most 20 times, newest first. Update the
same event on progress/completion/resume. Preserve the last successful complete
scan time across failed attempts. Resume does not reset the original start time.
Do not prune summaries when pruning events. A legacy import is not a new scan:
use unknown for unrecorded caller/timing/linked counts and state the old scope.
If an attempt fails before discovery, its unmeasured counts are unknown, not zero.

## Space index: `index.md`

```markdown
# <Space title> - Confluence index

- Site: <https://site-host>
- Space key: <key>
- Space ID: <id or explicitly labelled key fallback>
- Space URL: <canonical URL>
- Scan ID: <current scan event ID>
- Scan metadata: [Scan history](./<space>-scanned.md)
- External URLs: [External URL inventory](./external-urls.md)
- External URL coverage: <complete | partial | not performed>; unique safe URLs <N or unknown>
- Output resolution: <absolute directory and resolution basis>
- Scope: All accessible current pages, including nested pages, plus directly linked Confluence pages at depth one
- Exclusions: Archived pages, historical versions, comments, attachment contents,
  and non-Confluence external site contents (URLs are listed, not fetched), unless explicitly requested
- Scan state: <in-progress | complete | partial>
- Started (UTC): <ISO 8601>
- Finished (UTC): <ISO 8601 or not finished>
- Last complete scan (UTC): <ISO 8601 or none>
- Discovery exhausted: <yes | no | cannot establish>
- Source-reported total: <number or unavailable>
- Base pages: discovered <N>; successful <N>; failed/incomplete <N>; pending <N>
- Linked pages: discovered <N>; successful <N>; failed/incomplete <N>; pending <N>
- Base link discovery complete: <yes | no | cannot establish>
- Unresolved link targets: <number or unknown>
- Previously indexed but not observed this scan: <number, outside discovered count>

## Coverage and limitations

<Discovery method, failures, inaccessible content, missing sections, and caveats.
For each of the base and linked sets, discovered = successful + failed/incomplete
+ pending. Known body gaps and outline-only summaries count as incomplete even
when a partial summary exists. Unresolved target identities are separate from
page counts; aliases resolving to the same site/page ID count once.>

## Base pages (depth zero)

| Page ID | Title / source | Parent ID | Summary | Topics / search terms | Version | Source modified (UTC) | Retrieved (UTC) | Status | Local summary |
|---|---|---|---|---|---|---|---|---|---|
| <id> | [<title>](<Confluence URL>) | <id or unknown> | <1-3 sentences> | <terms> | <version or unknown> | <time or unknown> | <time or never> | <summarised / unchanged / pending / incomplete / failed / stale / not observed> | [Summary](./pages/<id>.md) |

## Linked pages (depth one only)

| Site | Page ID | Source space | Title / source | Referring base IDs | Summary / topics | Version | Source modified (UTC) | Retrieved (UTC) | Status | Local summary |
|---|---|---|---|---|---|---|---|---|---|---|
| <site> | <id> | <key / ID> | [<title>](<canonical URL>) | <base IDs> | <summary / topics> | <version or unknown> | <time or unknown> | <time or never> | <status> | [Summary](./linked-pages/<site-host>/<id>.md) |

## Base-page link inventory

Complete eligible link sets, not just selected related links. Include links that
resolve to other base pages (depth zero); they are not extra linked-page counts.

| Referring base ID | Safe source link | Resolved site / page ID | Target depth | Disposition / reason |
|---|---|---|---|---|
| <base ID> | [<label>](<URL without secrets>) | <site / ID or unresolved> | <0 / 1 / unknown / excluded> | <indexed / pending / restricted / unresolved / excluded with reason> |

## Errors and outstanding work

| Page ID or discovery step | Problem | Last attempt (UTC) | Next action |
|---|---|---|---|
| <id or step> | <specific reason, no secrets> | <time> | <retry / authenticate / clarify> |
```

For pages never successfully read, use plain text `Not available` rather than a
broken local summary link. Explain whether a stale record failed in this scan or
was not observed, so coverage totals stay unambiguous.

## External URL inventory: `external-urls.md`

```markdown
# <Space key> - external URLs

- Site / space: <canonical site, key, stable ID>
- Scan ID: <event ID>
- Index: [Page index](./index.md)
- Scope: Explicit HTTP(S) URLs in base-space page content only; depth-one pages excluded
- Extracted (UTC): <ISO 8601 or not performed>
- Coverage: <complete | partial | not performed>
- Base pages: total <N>; extraction complete <N>; incomplete/failed <N>; pending <N>
- Unique safe current URLs: <N or unknown>
- Redacted observations: <N or unknown, counted separately from confirmed unique URLs>
- Unresolved candidates: <N or unknown>
- Destination checks: Not performed; URLs were not fetched

## Current external URLs

| URL | Host | Referring base pages | Labels / occurrence types | Observed fragment variants (safe) | Extracted (UTC) |
|---|---|---|---|---|---|
| [<safe URL>](<safe URL>) | <host> | [<page title / ID>](<Confluence source URL>), ... | <labels; hyperlink / plain text / embed> | <fragments or none> | <UTC> |

## Per-base-page extraction sets

| Base page / source | Version | Extracted (UTC) | Extraction status | Complete safe URL set | Gaps |
|---|---|---|---|---|---|
| [<title / ID>](<source URL>) | <version or unknown> | <UTC or never> | <complete / incomplete / failed / pending> | <all safe URL keys, or none observed> | <reason or none observed> |

## Redacted, unresolved, or stale observations

| Safe candidate (plain text if redacted/unresolved) | Referring base pages | Status | Reason |
|---|---|---|---|
| <sanitised candidate, never raw credentials or signatures> | <source IDs/links> | <redacted / unresolved / stale> | <specific reason> |

## Coverage limitations

<Missing bodies, unreadable diagram/macro URLs, classification uncertainty, or
other gaps. No external targets have been visited.>
```

Use one current row per safely deduplicated URL and retain every referring base
page. Preserve query IDs and path case; remove fragments only for deduplication
and keep safe variants as provenance. Do not merge redacted collisions as known
duplicates. A complete extraction finding no URLs reports zero and says so;
unperformed extraction reports unknown. Do not cap rows or per-page URL sets.
Persist source versions and complete per-page sets to support safe refresh reuse.

## Page summary: `pages/<page-id>.md` or `linked-pages/<site-host>/<page-id>.md`

```markdown
# <Page title>

- Page ID: <id>
- Source: [<title>](<canonical Confluence URL>)
- Source site: <canonical site>
- Source space key: <key or unknown>
- Space ID: <id>
- Link depth: <0 for base, 1 for directly linked page>
- Referring base page IDs: <all referring base IDs, or not applicable>
- Parent ID: <id or unknown>
- Version: <version or unknown>
- Source modified (UTC): <time or unknown>
- Successfully retrieved (UTC): <time>
- Status: <summarised | incomplete | stale | not observed>
- Summary quality: <substantive | outline-only>
- Document status: <draft / accepted / superseded / not stated, with evidence>
- Search terms: <topics, acronyms, systems, concepts>

## Summary

<A concise paragraph or two, proportional to the content read.>

## Topics and headings

- <Heading or subject and what it covers>

## Key facts, decisions, and constraints

- <Source-supported fact, with section link when available>

## Related pages

- [<Title>](<Confluence URL>) - <relationship, if stated>

## Base-page link discovery

- Discovery complete: <yes | no | not applicable for depth-one page>
- Source version checked: <version or unknown>
- Full eligible outgoing links: <complete safe canonical list for base pages,
  or link to their complete rows in index.md; never truncate silently>

## Gaps and freshness

<Unreadable sections, missing diagrams, refresh failures, or "No known body gaps
in the retrieved content." Do not imply that excluded attachment contents were read.>
```

Omit unsupported facts and unnecessary empty sections. Record meaningful gaps
explicitly rather than filling them with guessed content.
Depth-one outgoing links may be shown for context but are not crawl candidates.
For older records without complete base link sets, reread links on refresh.

## Saved answer: `answers/<UTC-timestamp>-<short-topic>.md`

```markdown
# <Question or short topic>

- Question: <user question>
- Space: <site, key, and ID>
- Answered (UTC): <ISO 8601>
- Verification: <source pages checked now | stored summaries only | mixed>
- Index coverage: <scan state, last scan time, relevant limitations>

## Answer

<Direct answer with citations next to material claims. State when no supported
answer can be found.>

## Supporting findings, ranked by relevance

1. **<Most relevant finding>** - <evidence and why it answers the question>.
   Source: [<Page title>](<Confluence URL>).
   Version: <value or unknown>; retrieved: <UTC>; checked this invocation: <yes/no>.
2. **<Next relevant finding>** - <evidence>.
   Source: [<Page title>](<Confluence URL>).
   Version: <value or unknown>; retrieved: <UTC>; checked this invocation: <yes/no>.

## Uncertainty or conflicting guidance

<Gaps, conflicting sources, explicitly labelled inference, and freshness caveats,
or a concise statement that none were identified in the checked evidence.>
```

Do not force a second finding if only one relevant source exists. Relevance is
an evidence-based ordering, not a fabricated numeric confidence score.
