# Running the kit in a pipeline

- **Phase and date:** slice 0.6, 2026-11-22
- **Requirement IDs covered:** PIP-1 to PIP-7, NTF-1 to NTF-6, ADP-20
- **Assumptions:** the pipeline has Python 3.11 or later, PyYAML and git, and a full clone (not a shallow one)
- **Unverified:** none of the three shipped pipeline files has been run by its CI system

## The contract, for any CI/CD system

| Command | When | Exit code |
|---|---|---|
| `agentic.py selftest` | Every run. Proves each check fails on its broken fixture | 0 or 1 |
| `agentic.py connect run --base-ref <ref> [--branch <ref>] [--commit <sha>] [--summary <file>] [--json]` | On a proposed change and on the default branch | 0 pass, 1 a check failed, 2 a check could not run |
| `agentic.py connect notify --base-ref <ref> [--branch <ref>] --ledger <file> [--pr-url <url>]` | Only where secrets are safe (see below) | 0, or 1 if a delivery failed |
| `agentic.py connect mirror --change pull/<n> --commit <sha> --write` | Optional, after a review | 0 |
| `agentic.py connect fetch` | On a schedule | 0, or 2 if a source could not be read |

A command whose output is piped into a program that stops reading before the end, such as `head`, ends with 141 and gives no result. Under `set -o pipefail` that fails the step. Read the output to the end, or send it to a file.

`--base-ref` is the commit to compare with: the target branch for a proposed change, the previous commit on the default branch. Roles, settings, domain packs, agent specs, the tool allowlist and `connect.yml` are read from it.

On the default branch the gate check also asks each spec whose work is there for G5 and G6; on a proposed change it does not (`docs/design/checks.md`). The pipeline does not have to say which of the two it is. It makes a full clone of the project's repository, and git says: either the default branch is checked out, or the commit that is checked out is on it. The three shipped files rely on that and pass nothing for it.

`--branch` is for a pipeline whose checkout cannot say: a shallow or single-branch clone, an exported tree, a project kept in a folder of another repository. Pass the ref the pipeline built, as a full ref or a branch name: `refs/heads/main`, `refs/pull/7/merge`, `main`. On GitHub Actions that is `$GITHUB_REF` in a job started by a push or a pull request (in a `workflow_run` job it names the branch the workflow runs on, not the change), on Azure Pipelines `$(Build.SourceBranch)`, on GitLab CI `$CI_COMMIT_BRANCH` (empty in a merge request pipeline, which says nothing). What the caller says wins over what git says. Where neither can say, the gate check leaves a note that names what it did not ask for; it does not fail. The plain `check` command takes the same flag.

The ledger is a small text file that remembers what was announced. Keep it between runs (a cache or an artifact). Without it, chat and mail may repeat on a re-run; work-item notes never do.

## Where secrets may be used

A job that runs on a proposed change takes its pipeline file, and the kit's own code, from that change. Whoever opened it could alter either. So:

| Job | Runs on | Secrets |
|---|---|---|
| Checks | Every proposed change and the default branch | None |
| Notify, mirror | After the checks, from the default branch's copy of the pipeline and the kit. The proposed change is read as data and never executed | Tracker and notification secrets |
| Intake | A schedule, on the default branch | Tracker secrets |
| Any agent | Its own job | The agent's model key only. Never a tracker or notification secret |

`CK-PIPELINE-SECRETS` fails a pipeline that breaks these rules where it can see them: a stored secret in any pipeline file, and for GitHub Actions also a `pull_request` or `pull_request_target` workflow that names a tracker or notification secret, and an agent step with one in scope.

How each platform enforces the middle rows:

- **GitHub Actions** (`ci/github-actions.yml`): the connect workflow is triggered by `workflow_run`, which runs the default branch's copy. It checks the default branch out under `trusted/` and the change under `head/`, and runs `trusted/.../agentic.py --root head`.
- **Azure Pipelines** (`ci/azure-pipelines.yml`): secrets live in a variable group with a branch-control check that allows the default branch only.
- **GitLab CI** (`ci/gitlab-ci.yml`): secrets are protected variables, which GitLab gives only to jobs on protected branches.

## Approvals are still pull-request reviews

The kit reads approvals from GitHub pull-request reviews (ADP-3). Azure Pipelines and GitLab CI can run the checks and send notifications, but an approval made in Azure Repos or a GitLab merge request is not read yet (ADP-4).

Mirroring (`connect mirror`) saves a person from running the record command. It writes a decision record only when a review from a person carries the gate's line for the evidence as it stands and every required role is covered. It cannot approve anything: `CK-APPROVER` and `CK-GATE-MIRROR` read the review itself.

On GitHub the mirror job is off until the repository variable `AGENTIC_MIRROR` is `true`, and it needs a token that can push and that starts workflows (a GitHub App token). A push made with the built-in token does not start workflows, so the checks would not run on the commit that adds the record.

## Events

| Event | Raised when | Needs a base ref |
|---|---|---|
| `gate-ready` | Every check passes and the next gate a spec needs has evidence and no decision | No |
| `gate-approved`, `gate-rejected` | A decision record is new or different | Yes |
| `check-failed` | Any check failed or could not run | No |
| `released` | A spec has passed its last gate | Yes |
| `intake-new` | Intake records were added | Yes |
| `duplicate-candidate` | A new record resembles existing work | Yes |
| `source-changed` | A work item changed at its source after someone acted on it | No |
| `deadline` | A waiver expiry, an emergency retrospective or an outcome review is within `notify.deadline_days` (default 14) | No |

A notification says, for example, "Gate G3 of 004-export is ready for review by solutions-architect", with a link. It never includes requirement text. Projects may reword it under `notify.templates` using `{spec}`, `{gate}`, `{roles}`, `{count}`, `{ids}`, `{status}` and `{decision}` only.

## Not built

- A reminder cadence. Each event is announced once.
- Approvals from Azure Repos or GitLab.
- An MCP server that exposes the kit's state to agents. The protocol changed substantially in its 2026-07-28 revision; this should be built against a real client.
