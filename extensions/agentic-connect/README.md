# agentic-connect

Connections for agentic-spec-kit (slice 0.6). Needs `agentic` and `agentic-product`.

| Direction | What | Where |
|---|---|---|
| In | Requirements become intake records. For an item of Jira, Azure DevOps or GitHub the record also gets a count and a hash of the item's comments, and none of their text | Azure DevOps, Jira, ClickUp, GitHub Issues and Projects, documents (Markdown, text, HTML, CSV, JSON) |
| Run | Checks, events and review mirroring, with no prompt | GitHub Actions, Azure Pipelines, GitLab CI; any system that can run one command |
| Out | People are told | Slack, Teams, email, a note on the originating work item |

## Three rules the extension enforces

1. **A notification is not an approval.** Gates are passed by pull-request reviews. Nothing sent or received here changes a gate.
2. **A notification carries identifiers, a status and a link.** Templates may use `{spec}`, `{gate}`, `{roles}`, `{count}`, `{ids}`, `{status}`, `{decision}` and nothing else (CK-NOTIFY-CONTENT). Requirement text does not leave the repository this way.
3. **Secrets are named, never stored, and never visible to an agent.** `connect.yml` holds variable names. CK-CONNECT-CONFIG and CK-PIPELINE-SECRETS fail a stored secret, a pipeline that exposes secrets to pull-request code, and an agent step that can read a tracker or notification credential.

`connect.yml` is read from the base branch when the pipeline runs, so a change cannot redirect a token to a new address.

## Commands

```
agentic.py connect init --write          # write connect.yml with every option commented out
agentic.py connect check                 # CK-CONNECT-CONFIG, CK-NOTIFY-CONTENT, CK-PIPELINE-SECRETS
agentic.py connect fetch [--source id]   # pipeline: fetch requirements into .specify/agentic/intake/, with a digest of each item's comments
agentic.py connect run --base-ref <ref>  # pipeline: every check, a summary, the check result as exit code
agentic.py connect notify --base-ref <ref> --ledger <file>   # pipeline: tell people what changed
agentic.py connect mirror --change pull/<n> --commit <sha> [--write]   # pipeline: reviews to decision records
agentic.py connect events                # what would be announced now
```

## Not verified

The adapters for Jira, Azure DevOps and ClickUp and the notification channels have not been run against the live service. Each is tested against recorded responses that follow the vendor's published API. `docs/adapters/trackers.md` lists every endpoint and when it was read. The files for Azure Pipelines and GitLab CI have not been run by their CI systems.

The GitHub adapter and the file for GitHub Actions ran for the first time on 2026-11-27, on the reference repository: `connect fetch` read one issue, one Project and the issue's comments, the intake job opened a pull request with the record, and the notify job wrote its summary. The mirror job has not run, and no note has been posted on a live issue. `docs/adapters/trackers.md` says which token reads what on GitHub.

Gate approvals are read from GitHub pull-request reviews only. The kit runs in Azure Pipelines and GitLab CI, but approvals made in Azure Repos or GitLab merge requests are not read yet.

## Seen on GitHub, 2026-11-27

What GitHub did with the workflow on the reference repository, which the kit cannot change:

- **No run for a pull request that the bot opened.** GitHub starts no `workflow_run` after a run of `agentic-checks` whose actor is the workflow's own bot, whether a person approved that run or not. Two of two such runs started none; each of the eleven runs that the owner caused started one within five seconds. So notify and mirror do not see a pull request that `agentic-open-pull-request` opened. GitHub's page on triggering a workflow says that events the workflow's own token causes start no new run, and names the exceptions; `workflow_run` is not among them.
- **The cache write is refused after a run on a pull request.** In the notify job GitHub answered "token has no writable scopes" when the job tried to keep its ledger after a run on a pull request, and kept it after a run on a push. So the ledger of what was sent is kept from runs on a push.
- **Approve the held run before the pull request is merged.** GitHub holds the checks of a pull request that a bot opened until a person clicks "Approve workflows to run". Merged first, the held run ends as "failure", with no jobs.
- **The pipeline's own token is not told who may bypass a ruleset**, so `CK-ENFORCE-SETUP` notes that it cannot check whether administrators are exempt.
- **The mirror job and a repository that dismisses stale approvals.** The job pushes its records onto the pull request's branch. Where the default branch dismisses an approval when a commit is pushed, that push dismisses the review the records cite, and `CK-APPROVER` fails them. In such a repository leave `AGENTIC_MIRROR` unset and record after the merge, on a branch of its own, with `agentic.py record --change pull/<n>`. `docs/design/first-gate-on-github.md` has what was seen.
