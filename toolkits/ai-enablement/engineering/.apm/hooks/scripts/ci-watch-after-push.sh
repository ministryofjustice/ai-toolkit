#!/usr/bin/env bash
# postToolUse hook: after a successful `git push`, tell the agent to monitor CI.
set -euo pipefail

input=$(cat)

tool=$(jq -r '.toolName // empty' <<<"$input")
[[ "$tool" == "bash" ]] || exit 0

# toolArgs may be an object or a JSON-encoded string
cmd=$(jq -r '(.toolArgs | if type == "string" then (try fromjson catch {}) else . end) | .command // empty' <<<"$input")
[[ "$cmd" =~ (^|[[:space:];\&|])git[[:space:]]+push([[:space:]]|$) ]] || exit 0

branch=$(git branch --show-current 2>/dev/null || true)
[[ -n "$branch" ]] || exit 0

jq -n --arg branch "$branch" '{
  additionalContext: "A git push of branch \($branch) just succeeded. Monitor CI for it: find the PR with `gh pr view \($branch) --json number,url` (if none exists, say so and stop), then run `gh pr checks <number> --watch --interval 20` and report the final result, including failing check names, run URLs and the relevant failure logs."
}'
