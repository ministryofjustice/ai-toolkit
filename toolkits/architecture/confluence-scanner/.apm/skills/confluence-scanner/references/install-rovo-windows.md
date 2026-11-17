# Install the Atlassian Rovo MCP server on Windows

Use this guide when the user agrees to set up Atlassian's official remote MCP
server (the "Atlassian Rovo MCP server") on Windows. The user signs in; never
handle their credentials.

Sources (checked 2026-11-16): Atlassian
[getting started](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/getting-started-with-the-atlassian-remote-mcp-server/),
[v1 to v2 upgrade](https://support.atlassian.com/atlassian-ai-gateway/docs/how-to-upgrade-from-atlassian-mcp-v1-to-atlassian-mcp-v2/),
[troubleshooting](https://support.atlassian.com/atlassian-ai-gateway/docs/troubleshoot-and-verify-your-setup/);
GitHub [Copilot CLI MCP servers](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers);
Visual Studio Code [MCP servers](https://code.visualstudio.com/docs/agent-customization/mcp-servers).

## Before you start

- An Atlassian Cloud site with Confluence, and an account that can read the
  spaces to scan.
- A browser for the OAuth 2.1 sign-in. Use the browser where you're already
  signed in to Atlassian, ideally set as your default browser.
- Your organisation may restrict the MCP server or require API-token sign-in.
  If sign-in is refused, ask your Atlassian admin.
- Managed Windows devices often route traffic through a proxy or firewall.
  `mcp.atlassian.com` must be reachable over HTTPS.
- Calls through this server use **Rovo credits** from your organisation's
  shared pool. A full space scan makes at least one call per page.

Server URL: `https://mcp.atlassian.com/v2/mcp`

## Option A: GitHub Copilot CLI

1. In PowerShell or Windows Terminal:

   ```powershell
   copilot mcp add --transport http atlassian https://mcp.atlassian.com/v2/mcp
   copilot mcp get atlassian
   ```

   This adds the server to your user Copilot configuration
   (`%USERPROFILE%\.copilot\mcp-config.json`).

2. Start a new `copilot` session. When the Atlassian server first connects, a
   browser window opens for Atlassian sign-in. Approve the requested access.
   If no window opens, run `/mcp` in the session to check the server's status
   and start sign-in.

The agent may run step 1 for the user, but only after they explicitly agree.
Sign-in is always the user's.

## Option B: Visual Studio Code with GitHub Copilot

1. Press Ctrl+Shift+P and run **Chat: Open Customizations**, then select
   **MCP Servers**.
2. In the **User** group select **Add Server** (**+**), choose
   **HTTP (HTTP or Server-Sent Events)** and enter
   `https://mcp.atlassian.com/v2/mcp`.
3. Enter the server ID `atlassian`. Select **Global**, then **Copilot Global**
   so Copilot CLI on the same PC can use it too.
4. Accept the server trust prompt, then complete the Atlassian sign-in in the
   browser.

## Check it works

Start a **new** chat or session, because tools added mid-session usually don't
appear until then. Ask: "List the Confluence spaces I can access." A list of
your spaces means the scanner can use it.

## If it doesn't work

| Symptom                                      | Fix                                                                                                                                                                                        |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| No Atlassian tools in the session            | Start a new session; check `copilot mcp get atlassian` or the Visual Studio Code MCP server list                                                                                           |
| Connection or TLS errors                     | Your proxy or firewall is blocking `mcp.atlassian.com`; ask IT to allow it                                                                                                                 |
| Access denied                                | Confirm you can open the space in Confluence; ask your site admin                                                                                                                          |
| Empty or partial results, or silent failures | The sign-in expired. Sign in again (`/mcp` in Copilot CLI) and check the scopes you approve                                                                                                |
| Sign-in opens the wrong browser, or loops    | Set your default browser to the one signed in to Atlassian and allow pop-ups. If your setup uses the `mcp-remote` proxy, allow `http://localhost:3334` in the browser and Windows Firewall |

Never paste API tokens into chat, or put them in workspace, `.vscode/` or
knowledge-base files.
