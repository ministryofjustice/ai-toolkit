---
description: Commit Style Instructions
---

# Commit Styling

- Use [Conventional Commits](https://www.conventionalcommits.org)
- Make sure commits are signed; this is a common requirement in our repositories

## Signing Commits via API

When creating commits through the GitHub API (e.g. in a cloud agent context with no local git checkout), always use the **GraphQL `createCommitOnBranch` mutation** instead of the REST `PUT /contents/{path}` endpoint. GitHub signs commits made via this mutation server-side, satisfying repository commit signature verification requirements

Never use the REST Contents API (`PUT /repos/{owner}/{repo}/contents/{path}`) to create commits, as these are unsigned
