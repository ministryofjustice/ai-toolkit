# Confluence Scanner

A user-level skill for building a Markdown index of a Confluence space and
answering questions from that index, with the most relevant evidence first.
It can run directly or as a subagent called by another skill/agent. Bundled
[Python tooling](./scripts/scan_state.py) makes page queues and batch progress
durable; see the [batch workflow and JSON examples](./references/python-batches.md).
The helper is standard-library-only (Python 3.9+, macOS/Linux), has no network
access or credentials, and does not replace authenticated page-body retrieval
or agent-written substantive summaries.

The skill is a general-purpose tool for any accessible Confluence space.
Its directory contains only reusable instructions, templates and agent resources.
Generated indices, summaries, answers and scan history belong in a caller-selected
knowledge base, never in the skill directory.

## Use

The [Confluence Scanner skill](./SKILL.md) can be installed as a user-level
skill or plugin (for example from a plugin marketplace), so any workspace can
find it. Optionally set a shared knowledge root (the `KNOWLEDGE_HUB_ROOT`
environment variable, or `{"knowledge_root": "/path"}` in
`${XDG_CONFIG_HOME:-~/.config}/knowledge-hubs/config.json`) so the space registry
is found without passing `registry_path`.
Invoke `/confluence-scanner` or use a request such as:

- "Scan a Confluence space and save an index and page summaries as Markdown."
- "Refresh the index for this Confluence space: <space URL>."
- "Explain how another skill should call the Confluence Scanner."
- "Using the index for <space>, explain how authentication works. Prioritise the
  most relevant pages and save the answer as Markdown."

The scanner uses explicit inputs first, then unambiguous caller context and its
persistent space registry. It asks only when information is missing or ambiguous;
a delegated invocation returns `needs-input` to its caller instead.
There is no hardcoded default Confluence site, space or output knowledge base.

## Calling from another skill or agent

Use the [Confluence Scanner subagent](./.github/agents/confluence-scanner.agent.md)
when the host supports it. Its
[caller contract](./references/caller-contract.md)
defines inputs, resolution rules, return fields, and examples.

```text
Use the confluence-scanner subagent.
action: refresh
space_url: https://dsdmoj.atlassian.net/wiki/spaces/DPR
output_dir: ./research/confluence/DPR
caller_workspace: /absolute/path/to/my-project
context_key: my-project/design-review
triggered_by: design-review skill
requested_by: unknown
request_id: review-001
reason: Refresh the evidence for an integration design review.
```

`output_dir` is the exact space-specific destination; the scanner does not append
another site/space suffix. Relative destinations require `caller_workspace`.
Without a destination it reuses an unambiguous registered mapping. Alternatively,
supply `knowledge_base` to store a new space under
`<knowledge_base>/confluence-index/<site-host>/<space-id>/`.
If neither a knowledge base nor a mapping is available, a destination is required;
the scanner never defaults to its own source directory. It never picks between
multiple destinations by recency.

Actions are `scan`, `refresh`, `reindex`, `answer`, and `help`. `reindex` forces
body/link rereads while preserving old output until replacements succeed.
`help` explains invocation without scanning or changing files.

A skill alone does not register a subagent. The custom subagent definition
remains workspace-scoped; callers in other workspaces can load the user skill
inside an available agent or expose the custom agent separately through their
host's supported configuration. Reload the Visual Studio Code window or start a
new session if the user skill is not yet listed.

## Install

The skill is a folder containing `SKILL.md`, `references/`, `assets/`,
`scripts/` and `tests/`. Install the whole folder.

With [Agent Package Manager (APM)](https://microsoft.github.io/apm/), for
Copilot, Claude Code and Codex at user scope, once this toolkit is merged:

```bash
apm install -g ministryofjustice/ai-toolkit/toolkits/architecture/confluence-scanner#main --target copilot,claude,codex
```

Or copy the folder into your assistant's user skill folder:
`~/.copilot/skills/` or `~/.agents/skills/` (GitHub Copilot),
`~/.claude/skills/` (Claude Code) or `~/.agents/skills/` (Codex).

## Dependencies

| Dependency           | Required?                  | Why                                                                                                                                                                                                                        | Install                                                                                                                                        | Check                                                 |
| -------------------- | -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| Python 3.9 or later  | Required                   | Runs the batch helper (standard library only)                                                                                                                                                                              | [python.org/downloads](https://www.python.org/downloads/)                                                                                      | `python3 --version`                                   |
| Atlassian MCP server | Required for live scanning | Rovo is declared in APM; another approved Atlassian MCP server with Confluence read tools can be used instead. Setup guides: [macOS](./references/install-rovo-macos.md), [Windows](./references/install-rovo-windows.md). | [Atlassian Rovo MCP setup](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/getting-started-with-the-atlassian-remote-mcp-server/) | Verify an authenticated, read-only Confluence request |
| knowcat              | Optional                   | Stores scans inside a knowledge hub and uses them for explanations                                                                                                                                                         | Install separately when available                                                                                                              | Check your assistant's available skills               |

APM declares the MCP dependency, but installation does not prove authenticated
access. Check your assistant's configuration and sign in yourself. The scanner
does not handle API tokens. Browser-only scanning is not supported.

## Supported assistants

Targets GitHub Copilot CLI, Copilot in Visual Studio Code (agent mode),
Claude Code and Codex. Verify local script access and authenticated MCP tools
in your host; complete workflows have not been tested in every assistant.

Scanning needs an authenticated Atlassian MCP server. An existing index can
support offline answers, explicitly labelled as
based on stored summaries rather than current verified source pages. This skill
does not install a connector or manage credentials.

## Saved Markdown

### Resumable execution

The scanner persists listing batches, processes bounded body batches (10 pages
by default), and checkpoints each result before selecting more pages. Private
`.scanner/checkpoint.json` and a command lock sit under the approved output,
alongside a Markdown progress inventory. Raw source bodies are processed in
memory only. The helper checks cursor continuity, queues only verified
depth-one targets with base provenance, redacts sensitive URL query values,
protects existing summaries with hashes, and reports exact outstanding work.
It never calls a page listing a complete scan. See
[Python batches](./references/python-batches.md) for all commands, constraints
and explicit resume instructions.

Run synthetic offline tests with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s confluence-scanner/tests -v
```

Run that command from the parent `skills` directory. No live Confluence reads,
package installation or knowledge-base writes are performed by the tests.

The persistent space registry (`<knowledge root>/confluence-spaces.md`) records known
spaces, caller contexts, destinations, and last request/scan pointers. Each
destination has its own manifest and history; the registry can retain multiple
destinations for one space. It always lives outside the skill directory;
callers may supply `registry_path` for another external registry.

Output layout when a caller supplies `knowledge_base` without an exact destination:

```text
<knowledge-base>/
  confluence-index/
    <site-host>/
      <space-id>/
        index.md
        <space>-scanned.md
        external-urls.md
        pages/
          <page-id>.md
        linked-pages/
          <source-site-host>/
            <linked-page-id>.md
        answers/
          <UTC-timestamp>-<short-topic>.md
```

The index contains page links, short summaries, topics, source metadata, scan
coverage, and failures. Each page has a more detailed summary. Saved answers
include citations, relevance-ranked findings, and freshness/uncertainty notes.
Each scan also writes `external-urls.md`: a deduplicated list of all explicit
non-Confluence HTTP(S) URLs in base-space page content, with every referring
page, labels/types, host, safe fragment variants, and extraction time. This
includes plain-text links and authored embeds, not just selected related links.
External destinations are listed, **not visited or crawled**. URLs found only
on one-hop pages are outside this space-specific list. Sensitive URL components
are redacted; incomplete extraction and unresolved candidates are reported.
The `<space>-scanned.md` manifest records the initiator, calling skill/agent,
request and scan IDs, trigger/reason, timing, directory-resolution basis, counts,
outcome, and errors. It keeps the newest **20 scan invocation events**, including
failed and partial attempts. Progress/resume updates the same event. Answer/help
requests do not create scan events; pruning history never deletes page content.
Output may contain internal information: keep it in approved storage on your machine and
do not commit or share it without appropriate permission.

By default, scans cover all accessible current pages, including nested pages.
They also index current Confluence pages directly linked from any base-space
page, including other spaces/sites where authenticated access is available.
This is **one hop only**: linked pages' outgoing links and children are not
crawled. Shared targets are indexed once with all referring base pages recorded.
Archived pages, historical versions, comments, attachment contents, and external
non-Confluence site contents are excluded (their URLs are still inventoried).
A complete scan requires substantive summaries, complete base-link and external-
URL extraction, and no known retrieval gaps in the base or one-hop
sets. Restricted targets and unresolved links are reported rather than hidden.

## Extend later

Edit the [skill instructions](./SKILL.md) to
change the workflow and the
[Markdown templates](./assets/markdown-templates.md)
to change the output structure.
