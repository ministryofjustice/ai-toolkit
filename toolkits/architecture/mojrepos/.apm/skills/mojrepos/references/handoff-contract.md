# knowcat ↔ mojrepos handoff contract

Contract version: **1**

This file is shipped, byte for byte, in both `knowcat/references/` and
`mojrepos/references/`. Change both copies together and increase the version.
If the two skills report different versions, say so and stop the handoff.

Each skill works on its own. This contract applies only when both are
available in the same session.

## Detect the partner skill

Treat the other skill as available when any of these is true:

1. It appears in the host's list of available skills.
1. The host can load it by name (for example `knowcat` or `mojrepos`).
1. Its `SKILL.md` exists in a standard skill folder:
   - user scope: `~/.agents/skills/<name>/`, `~/.copilot/skills/<name>/`,
     `~/.claude/skills/<name>/`
   - project scope: `.agents/skills/<name>/`, `.github/skills/<name>/`,
     `.claude/skills/<name>/`

Some hosts shorten the skill list when many skills are installed, so a missing
list entry alone does not prove the skill is absent. Check the folders, and if
it is still unclear, ask the user.

Use the folder where you found the partner's `SKILL.md` as
`<partner-skill-dir>` when you need its bundled scripts. Before relying on the
partner, read its copy of this file and confirm the contract version matches.

## Roles

| Skill | Role |
| --- | --- |
| mojrepos | Collects, classifies and orchestrates GitHub repository evidence. Never writes to a knowledge hub while knowcat is available. |
| knowcat | The only writer to a knowledge hub. Resolves the hub, checks approval and containment, persists records and navigation. |

Both skills run as stages in the current assistant session. Do not start a
subagent only to switch skills, except for the background listing refresh
described in mojrepos.

## Collector-only request (knowcat → mojrepos)

knowcat establishes the hub and the exact approved scope first, then asks
mojrepos for evidence:

```text
contract_version: 1
mode: collector-only
caller: knowcat
hub_id: <resolved stable hub ID>
approved_scope: <exact owner/repositories or listing, depth (metadata, root README), exclusions>
approval: <the user's own words or a link to the session where they approved>
```

mojrepos returns a writer-only packet (below) and must not call knowcat back,
register sources or write anything. It skips its freshness gate in this mode.

## Writer-only packet (mojrepos → knowcat)

```text
contract_version: 1
mode: writer-only
caller: mojrepos
hub_id: <resolved stable hub ID>
hub_index: <resolved, contained index path>
operation: <session | refresh | learn, with the approved research objective>
approval: <direct user evidence and exact registered scope, or "approval needed">
capture_key: <host session ID + hub ID, for session operations>
registrations: <stable IDs; imports kept distinct from approved live sources>
evidence: <canonical owner/name, URL, provider ID if returned, metadata,
           categories with evidence, selected README summaries and citations>
provenance: <live read, import or user statement; retrieval times;
             source versions or timestamps, or "unknown"; snapshot dates>
coverage: <queries or API, pages, totals, new/duplicate/error counts, caps,
           visibility, archive policy, exclusions, unresolved conflicts>
proposed_outputs: <existing stable hub records to upsert; new contained paths>
tasks: <explicit commitments only, otherwise "none">
limitations: <failed or unavailable reads; never invent successful evidence>
```

For a listing refresh, the packet is the mojrepos working directory
(`listing.json`, `queue.json`, `evidence.json`, `summaries.json`). Name it in
`evidence` and `coverage`, and knowcat persists it with
`<knowcat-skill-dir>/scripts/write_github_refresh.py` instead of editing hub
files by hand.

knowcat consumes only the packet and approved local artefacts: no new live
reads, no call back to mojrepos or another collector. Missing evidence or
approval means ask, or record a blocked or partial result.

## When the partner is not available

| Situation | mojrepos | knowcat |
| --- | --- | --- |
| knowcat missing | Uses its own standalone store, as described in its `SKILL.md` | Not applicable |
| mojrepos missing | Not applicable | Reads only the exact approved repositories at metadata and root README depth with read-only GitHub tools, records them without mojrepos categories, and suggests installing mojrepos |
| Contract versions differ | Report both versions; do not hand off | Report both versions; do not accept the packet |
