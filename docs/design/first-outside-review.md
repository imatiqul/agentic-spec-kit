# What the first review from outside found, and what changes

- **Phase and date:** Phase 12, the live test on HealthQCopilot, after its stage 3; 2026-11-27 (UTC)
- **Upstream and reference:** github/spec-kit `v1.4.3`; `imatiqul/azure-ai-cloud-healthcare`, pull request 83 at `ffb59d6`; `actions/checkout` at `3d3c42e` (release 7.0.1), read from its source
- **Requirement IDs covered:** REV-1 to REV-12, new with this document. They close two ways a credential could leave, make three checks and one command do what their requirements already say, and correct five files that people copy or agents read. No gate rule changes
- **Assumptions:**
  1. The owner said on 2026-11-26 that each failure of the live test is reported as it is and fixed on a local branch of the kit, which he pushes.
  2. A review by a program is a reader's findings and nothing more. Each finding was checked against the kit's code before anything changed. One of the thirteen was not taken, and the reason is given.
  3. On GitHub, whoever may push a branch may run a workflow on it and read the repository's secrets there. A secret held by an environment is read only by a job that names the environment, and an environment can be limited to chosen branches. GitHub's documents say both (sources 2 and 5).
- **Unverified:** nothing here has run on GitHub. That the pinned `actions/checkout` refuses a fork's commit in a `workflow_run` job was read in its source and not tried. The files for GitLab CI and Azure Pipelines are changed and have still not been run by those systems

## What happened

On 2026-11-26 the kit was installed into HealthQCopilot by pull request 83: seven extensions and three workflows, 126 files. That repository's rules ask for a review by GitHub Copilot on every pull request. The review arrived on 2026-11-27 at 00:09 UTC, six minutes after the pull request was merged, and it is the first review of the kit's code that this project neither asked for nor ran itself. It lists 13 findings and marks six of them as high.

Each was checked against the code at `ed70e93`. Twelve hold. The table gives each in this document's words, with what was found when it was checked.

| # | Finding | Checked | Requirement |
|---|---|---|---|
| 1 | A person can start the intake job from any branch, and it then runs that branch's copy of the kit with the tracker secrets and a token that can write | Holds. The template's opening comment says that a run started by hand is on the default branch. GitHub lets the person choose the branch | REV-3 |
| 2 | Where the base branch has no `connect.yml`, the notify job reads the one the pull request brings, and could send a secret to an address nobody reviewed | Holds. `config()` falls back to the change's copy. The job holds every secret the workflow names | REV-2 |
| 3 | The transport follows a redirect to any address and sends the `Authorization` header there | Holds. Tried on 2026-11-27 with two servers on one machine: the second received the header | REV-1 |
| 4 | `CK-POST-RELEASE` accepts a production check dated in the future, or before the release | Holds. Only whether the date can be read is checked | REV-7 |
| 5 | Where the base branch has no allowlist, a pull request can add an MCP server and the entry that approves it together | Holds, and against AGT-20, which says that a change cannot add a server and approve it itself | REV-5 |
| 6 | `server@1`, `server@1.2` and `server@1.x` count as exact versions | Holds. For npm these are ranges: `@1` is whatever 1.x is newest tomorrow | REV-6 |
| 7 | The pinned checkout refuses a fork's commit in a `workflow_run` job, so the notify and mirror jobs fail for a pull request from a fork | Holds for release 7.0.1, which the connect workflow pins. Its source refuses such a checkout unless `allow-unsafe-pr-checkout` is set | REV-4 |
| 8 | In the GitLab file a push to the default branch is compared with that same branch, so nothing has changed and the checks that compare see nothing | Holds. The Azure file does the same on a build of `main` | REV-12 |
| 9 | Mirroring asks for every role of a gate, also in Lite, where one role is enough | **Not taken.** PIP-6 says that a pipeline mirrors a review when every role the gate needs is covered, and the install scripts do not install the connect extension with the Lite profile | |
| 10 | A review that approves with conditions is mirrored without its conditions, into a record that `CK-GATE-RECORD` then fails | Holds. `record --change` already refuses this case and asks for the conditions | REV-8 |
| 11 | Mirroring always records that there is no single-approver exception, so a review by a person who also wrote the change gives a record that `CK-APPROVER` fails, also where the project allows the exception | Holds | REV-9 |
| 12 | The Independent Verifier's definition names the input list of G6 as its only input, and the orchestrator sends it to four other gates as well | Holds. The verify command writes `<gate>-inputs.yml` | REV-10 |
| 13 | Lite has no Architect, and the orchestrator's table gives the plan and the tasks to the Architect alone, so in Lite nobody writes them | Holds. The Spec Author's Lite definition already allows `plan.md` and `tasks.md`; the two commands do not say so | REV-11 |

Seen on the way: the review itself started `agentic-checks`, through that workflow's `pull_request_review` trigger, and GitHub held the run for a person's approval, as it holds any run that a bot starts. Such a run can be left where it is: the approval checks read reviews by people only. `docs/limits.md` says so; no requirement follows.

## Requirements

| ID | Requirement |
|---|---|
| REV-1 | `Http.request` follows a redirect only to the origin it asked: the same scheme, host and port. Any other redirect is not followed. The answer is then the redirect's own status, with a text that names the host it pointed to. No header of the request reaches another origin. |
| REV-2 | A command that sends with a credential (`connect notify`, `connect run --notify`, `connect fetch`) reads `connect.yml` from the base branch alone when a base branch is given. Where the base branch has no `connect.yml`, nothing is sent: notify says so in its output and its summary and ends as it does with no channel configured, and fetch ends with 2. The checks go on reading the copy that the change brings, which is how the change that adds the file can be checked. Without a base branch nothing changes. |
| REV-3 | In `ci/github-actions.yml` the intake job runs only on the default branch, whatever started it: a schedule runs there by GitHub's rule, and a run started by hand is skipped on any other branch. The file's opening comment says what holds on GitHub: a person chooses the branch of a run started by hand; whoever may push a branch may change the workflow on it, so the condition guards against a slip and not against that person; and a secret that must not be readable from a branch belongs in an environment that only the default branch may use. `docs/adapters/pipeline.md` says the same. |
| REV-4 | In `ci/github-actions.yml` the notify job and the mirror job run only for a run of `agentic-checks` that came from this repository. The comment gives the reason, and what a project has to read and set before it notifies for forks. The mirror job stays closed to forks: it pushes to this repository. |
| REV-5 | Where a base branch is given and has no allowlist, the allowlist that the change brings counts only for a server that the base branch already configures in the same way: the same file, name, launch and address. A server that arrives or changes together with the allowlist fails `CK-TOOL-ALLOWLIST`, and the message says to merge the allowlist first. Where the base branch has an allowlist, and where no base branch is given, nothing changes. |
| REV-6 | For `npx`, `bunx` and `pnpx` an exact version is three numbers, as in `1.4.2`, with or without a pre-release or build part. `@1`, `@1.2` and `@1.x` are not exact. For `uvx` and `pipx` the rule stays as it is: there `@1.2` and `==1.2` name one version. |
| REV-7 | `CK-POST-RELEASE` fails a production check that is dated after today, and one dated before the release of its spec where the audit log gives that date. |
| REV-8 | `connect mirror` writes no record for a review that approves with conditions. The conditions are the reviewer's to state, and a pipeline cannot pick them out of a review. The row says so and names the command a person runs: `record --change` with `--condition`. |
| REV-9 | Where an approving or rejecting reviewer also wrote the change, `connect mirror` records the single-approver exception if the project's `kit.yml` allows it, and writes no record and says why if it forbids it. Where GitHub cannot say who wrote the change, mirroring goes on as before and `CK-APPROVER` judges the record. |
| REV-10 | The Independent Verifier's definition names as its input the list of the gate it reviews, `specs/*/verification/<gate>-inputs.yml`. |
| REV-11 | The orchestrate command and the role command say that in Lite the Spec Author writes the plan and the tasks. |
| REV-12 | The files for GitLab CI and Azure Pipelines compare a build of the default branch with the commit before it. On GitLab a merge request is compared with its target branch and a branch pipeline with `CI_COMMIT_BEFORE_SHA`; where GitLab gives no such commit, which it writes as forty zeros, no base is given. On Azure a build of `main` is compared with `HEAD~1`, as its notify job already does. |

## Acceptance criteria

- **AC-001** (verifies REV-1): Given a service that answers a request with a redirect to another host name and port, Then the second address receives no request, and the answer has the redirect's status and names that host. Given a redirect to another path of the same origin, Then it is followed and the header arrives there.
- **AC-002** (verifies REV-2): Given a base branch without `connect.yml` and a change that brings one with channels and routes, When `connect notify --base-ref` runs with every secret set, Then nothing is sent, the output and the summary say that `connect.yml` is not on the base branch, and the command ends with 0; `connect run --notify --json` says the same under `not_sent`. Given `connect fetch --base-ref` there, Then it ends with 2 and asks no tracker. Given the same file on the base branch, Then the notifications are sent. With no base branch both work as before, which the tests of slice 0.6 show.
- **AC-003** (verifies REV-3): Then the condition of the intake job in `ci/github-actions.yml` holds only on the default branch, the file's comment no longer says that a run started by hand is on the default branch, and `docs/adapters/pipeline.md` names the environment.
- **AC-004** (verifies REV-4): Then the conditions of the notify job and the mirror job each compare the repository of the run that started them with this repository, and the file names `allow-unsafe-pr-checkout`.
- **AC-005** (verifies REV-5): Given a base branch with no allowlist and no server, and a change that adds a server and an allowlist entry for it, Then `CK-TOOL-ALLOWLIST` fails and says that both arrive in the same change. Given a base branch that already configures the server, and a change that adds only the allowlist, Then it passes. Given the same change with the server's launch altered, Then it fails. Given a base branch that has the server and no `kit.yml`, as before the change that installs the kit, Then it passes. Given no base branch, Then the sample passes as before.
- **AC-006** (verifies REV-6): Given `npx` with `server@1`, `server@1.2` or `server@1.x`, Then the launch is not pinned. Given `server@1.4.2` and `@scope/server@2.0.0-rc.1`, Then it is. Given `uvx` with `server@0.9` or `server==0.9`, Then it is, as before.
- **AC-007** (verifies REV-7): Given a production check that passed and is dated after today, Then `CK-POST-RELEASE` fails and says so. Given one dated before the spec's release, Then it fails and names both dates. Given one dated on the day of the release or after it, and not after today, Then the check passes.
- **AC-008** (verifies REV-8): Given a review that carries the gate's line for approval with conditions, When `connect mirror --write` runs, Then no record is written, and the row names `--condition`.
- **AC-009** (verifies REV-9): Given an approving review by a person who is among the change's authors, and a `kit.yml` that allows the exception, When `connect mirror --write` runs, Then the record says `single_approver_exception: true` and `CK-APPROVER` passes. Given a `kit.yml` that forbids it, Then no record is written and the row says why.
- **AC-010** (verifies REV-10): Then the rendered instructions of the Independent Verifier name `<gate>-inputs.yml` and not `G6-inputs.yml`.
- **AC-011** (verifies REV-11): Then the orchestrate command names the Spec Author for the plan and the tasks in Lite, and the role command gives the Spec Author's row the two commands for Lite.
- **AC-012** (verifies REV-12): Then the GitLab file gives `CI_COMMIT_BEFORE_SHA` as the base of a branch pipeline, names the forty zeros, and no longer compares the default branch with itself; and the Azure file gives `HEAD~1` as the base of a build of `main`.

## What this does not do

- It does not make the mirror job work in Lite with one role. That is finding 9, which was not taken.
- It does not change how `kit.yml`, `roles.yml`, the domain packs, the glossary, the capability index and the waiver baseline are read: from the base branch, and from the change where the base branch has none. Those files decide what a check says and send nothing, and the change that installs the kit has to be checked against something. A person's review of that one change is the control, and `CODEOWNERS` names who.
- It does not add a rule to `CK-PIPELINE-SECRETS` for a job that can be started by hand from a branch. The template is corrected; a workflow that a project wrote itself is not judged for it.
- It does not let a pull request from a fork be notified or mirrored. A project that wants the first reads GitHub's page (source 3) and sets the input itself.
- It does not stop GitHub from holding a run of `agentic-checks` that a bot's review started.
- It does not answer the review on GitHub. Whether its threads are answered there is the owner's to say.

## Sources

1. GitHub Copilot's review of pull request 83 of `imatiqul/azure-ai-cloud-healthcare`, submitted 2026-11-27 00:09 UTC, read the same day through GitHub's REST API: https://github.com/imatiqul/azure-ai-cloud-healthcare/pull/83
2. GitHub Docs, "Secure use reference" for GitHub Actions, read 2026-11-27: a user with write access to a repository can read every secret configured in it. https://docs.github.com/en/actions/reference/security/secure-use
3. `actions/checkout` at `3d3c42e5aac5ba805825da76410c181273ba90b1`, files `action.yml`, `README.md` and `src/unsafe-pr-checkout-helper.ts`, fetched and read 2026-11-27. The page its message points to: https://gh.io/securely-using-pull_request_target
4. GitLab Docs, "Predefined CI/CD variables reference", read 2026-11-27 in a search excerpt: `CI_COMMIT_BEFORE_SHA` is forty zeros in merge request pipelines, scheduled pipelines, the first pipeline of a branch, and a pipeline run by hand. https://docs.gitlab.com/ci/variables/predefined_variables
5. GitHub Docs, "Deployments and environments", read 2026-11-27: an environment's secrets go only to a job that names the environment, and its setting for deployment branches and tags can limit it to selected branches. https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
