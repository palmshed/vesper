# Vesper Review GitHub App Permissions (Webhook Mode)

<br>

Use the smallest set of GitHub App permissions needed for Vesper to review PRs and (optionally) merge them.

<br>

# Recommended (Vesper can merge PRs)

<br>

| Permission area (GitHub App) | Set to (mark) | Can be unmarked? |
|---|---:|---:|
| Repository metadata | Read-only | No (GitHub requires) |
| Pull requests | Read & write | No |
| Issues | Read & write | No |
| Contents | Read & write | No (needed for merge/authoring flows) |
| Everything else (Actions, Checks, Deployments, Environments, Workflows, Administration, Hooks, Secrets, Security events, Dependabot, Codespaces, Projects, Discussions, Packages, Pages, etc.) | No access | Yes (should be unmarked) |

<br>

# If you **do not** merge or author changes

<br>

- Keep `Pull requests: Read & write` and `Issues: Read & write`.
- Set `Contents` to `Read-only` (or `No access` if your deployment never reads file contents).

<br>

# Webhook events to subscribe

<br>

- `Pull request`
- `Issue comment`
