# Atlassian MCP access for the scanner

Read this before a scan or refresh when choosing how to reach Confluence. It
covers tool selection, connection checks and user setup. It does not change
the scope or safety rules in [SKILL.md](../SKILL.md).

## Choose an access route

Use the first route that works, and record it in the scan manifest:

1. **Atlassian Rovo MCP server:** Atlassian's official remote server at
   `mcp.atlassian.com`. Recognise it by a configured server URL on that host;
   check read-only with `copilot mcp list` or the Visual Studio Code MCP server list. You
   can also recognise its tools: `getAccessibleAtlassianResources`, then
   `getConfluenceSpaces`, `getPagesInConfluenceSpace` and `getConfluencePage`,
   all taking `cloudId`.
2. **Another approved Atlassian MCP server** with Confluence read tools. Find
   it by capability with tool search, and read its schemas first.

Confirm the chosen route with one read-only call, such as accessible resources
or user info, which also gives you the `cloudId`. If a server is missing, try
the next approved MCP server. On unauthenticated or denied access, stop and
report it; never bypass it through another route or account. Browser-only
scanning is not supported.

## First run without Rovo

"First run" means the user's config file has no recorded decision. That file
is `${XDG_CONFIG_HOME:-~/.config}/knowledge-hubs/config.json`, key
`confluence_scanner.rovo_setup`. When route 1 is unavailable on a first run,
ask once with a structured question:

- **Set it up now:** show the guide for the user's OS:
  [macOS](./install-rovo-macos.md) or [Windows](./install-rovo-windows.md).
  For Linux, use the macOS Copilot CLI steps. With explicit agreement you may
  run its `copilot mcp add` command; the user does the sign-in. New tools
  usually appear only in a new session, so offer to continue this run on route
  2, or to stop so they can restart and resume from the checkpoint.
- **Not now:** use route 2 if available; otherwise stop live scanning.

Record the answer as `{"confluence_scanner": {"rovo_setup": "accepted" |
"declined", "decided_at": "<UTC>"}}`, merged into the existing config without
removing other keys. Don't offer again unless the user asks. Never put credentials in
that file.

## Tool choice (verified in this host on 2026-11-16)

| Need                                      | Preferred tool                        | Notes                                                                              |
| ----------------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------- |
| Resolve space key → stable ID             | `getConfluenceSpaces` (`keys` filter) | Returns space ID used for page listing                                             |
| Enumerate every page                      | `getPagesInConfluenceSpace`           | `spaceId`, `status=current`, `limit` ≤ 250, follow `cursor` until none is returned |
| Read a page body and version              | `getConfluencePage`                   | `pageId` also accepts tiny-link IDs from `/wiki/x/` URLs                           |
| Resolve a link when only a title is known | `searchConfluenceUsingCql`            | A candidate only. Confirm the ID with `getConfluencePage`                          |
| Anything else                             | Generic `fetch`                       | Read-only GET only; prefer the specific tools above                                |

If the MCP server cannot enumerate or retrieve the approved pages, report the
limitation and preserve the checkpoint rather than switching to browser access.

## Errors

The bundled helper does not retry or back off. The agent must handle errors:

- 429 or other transient errors: wait, retry a bounded number of times, then
  record the page as failed and continue. Honour any retry-after guidance.
- 401 or expired session: stop and ask the user to sign in again. Don't
  repeat unauthenticated requests.
- 403 or restricted page: record it as restricted with the reason. Never try
  to get it another way.

## User setup

Setup is the user's, using the [macOS](./install-rovo-macos.md) or
[Windows](./install-rovo-windows.md) guide. Never ask for API tokens or
passwords in chat, or write them to the workspace, the knowledge base,
`.vscode/` or `.copilot/` files.
