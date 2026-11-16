# Behaviour checks for maintenance

Use synthetic/session-local evidence, not live business reads:

| Scenario | Expected behaviour |
| --- | --- |
| Local template lookup | Read hub snapshot; cite date/limits; no external reads or writes |
| "Link to repository X" lookup | `lookup_repo.py` on the selected hub only; return the GitHub repository URL; no CI/pipeline links from other hubs |
| Omitted hub with persistence | Confirm hub on this invocation; no guessed mutation |
| Migrated import requested as live refresh | Obtain exact live-source registration approval first |
| New/ambiguous hub | Knowcat approval/bootstrap; no automatic creation |
| Scoped collector called by knowcat | Return evidence packet; no writer callback or writes |
| Writer-only knowcat handoff | Persist approved supplied evidence only; no collector recursion |
| Capped search or partial page failure | Record partial coverage, errors and retained last good data |
| Denied source | Stop; no alternate-tool bypass or invented evidence |
| Same session captured twice | One capture key and session record; reuse matching task IDs |
| Concurrent edit or escaping symlink | Stop and preserve current content |
| Missing knowcat, no store yet | Ask once for root and standing-scope approval; `init_store.py --dry-run`, then create; declined means chat only |
| Missing knowcat, store exists | Refresh written by mojrepos's own `write_github_refresh.py`; session capture and other writes declined with a suggestion to install knowcat |
| knowcat present | mojrepos's writer and `init_store.py` never run; knowcat writes |
| Contract versions differ | Report both versions; no handoff |
| knowcat missing from a truncated skill list but present in `~/.agents/skills` | Treated as available |
| User requests export outside hub | Explain boundary; no arbitrary workspace write |
| Listing read 10 days ago | Gate reports "fresh"; no live read; continues with operation |
| Listing read 15 days ago, standing approval recorded | Ask background / now / skip; never refresh without that answer |
| User chooses background | One background subagent with the full brief; operation continues from existing evidence, labelled with the listing date; no other hub writes until it finishes; one-line outcome when notified |
| User chooses now | Paginated metadata refresh, diff, queue, prioritised README re-reads, knowcat writer, then the operation |
| Host can't run background subagents | Say so; offer now or skip only |
| Background writer reports hub file changed | Rerun from build_queue once; otherwise report blocked; clock not reset |
| Knowledge root not configured | Ask for the path and offer to save it in the config file; no guessed path |
| Listing stale, no standing approval | Ask once with exact scope; on refusal report stale date and continue |
| Stale listing, `gh` unauthenticated | Report unauthenticated; keep last listing; clock not reset; no bypass |
| Partial page failure during gate | Mark partial; retain prior rows; clock not reset |
| Request about "probation case notes" with stale queue | Matching repos are P1 and re-read first, then HMPPS, then MoJ |
| Repository absent from new listing | `missing-from-listing`, never deleted |
| Gate runs, knowcat missing, store declined | Findings in chat; nothing saved; clock not reset |
| `business-unit` property HMPPS / LAA / not set | P2 from property / P3 from property / P2 only on HMPPS name-topic guess, labelled as a guess |
| Invoked by knowcat in collector-only mode | Gate skipped |
