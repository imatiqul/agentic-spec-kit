# What the first runs on GitHub showed, and what changes

- **Phase and date:** Phase 12, the live test on HealthQCopilot, after its stage 2; 2026-11-27 (UTC)
- **Upstream and reference:** github/spec-kit `v1.4.3`; `imatiqul/azure-ai-cloud-healthcare` at `0d42aac`
- **Requirement IDs covered:** LIV-1 to LIV-11, new with this document. They change how the GitHub adapter asks, what two checks can see, and what the install scripts say. No gate rule changes
- **Assumptions:**
  1. The owner said on 2026-11-26 that each failure of the live test is reported as it is and fixed on a local branch of the kit, which he pushes.
  2. A repository may protect its default branch with rulesets, with branch protection, or with both. Where either asks for a review, a review is asked for.
  3. Inside GitHub Actions the built-in token acts as `github-actions[bot]`. GitHub's documents say so.
- **Unverified:** nothing here has run on GitHub when this is written. The answers of GitHub in the tests are copied in shape from what `imatiqul/azure-ai-cloud-healthcare` answered on 2026-11-27, with invented names. Whether the built-in token may read a ruleset's list of bypass actors is not known; LIV-3 says what happens where it may not. `install.ps1` is changed and has not been run here: this machine has no PowerShell

## What happened

On 2026-11-26 the kit was installed into HealthQCopilot for its pipeline, and in the minutes around midnight UTC on 2026-11-27 its workflows ran on GitHub for the first time: `agentic-checks` on pull request 83 and on the push to `main`, and `agentic-connect` after it. The self-test passed on 107 fixtures. The checks reported 83 passed, 21 failed and 2 not run; in a workspace under the owner's own account the same files gave 82, 23 and 1. The notify job passed and wrote its summary.

| What was seen | Why |
|---|---|
| `CK-CRED` could not run in the pipeline | The adapter asks GitHub who the credential is (`GET /user`). GitHub refuses that to the token of an app's installation, and the pipeline's built-in token is one: "Resource not accessible by integration" |
| `CK-ENFORCE-SETUP` passed in the pipeline with the note "not checkable: branch protection" | The adapter asks for branch protection, which only an administrator may read. The repository protects `main` with two rulesets. GitHub answers the rules of a branch to anyone who can read the repository; that was tried with a read-only credential on 2026-11-27 |
| The notify summary said "21 failed, 2 not run" and, below it, "23 check(s) failed" with 12 names | The event counts the checks that failed and those that could not run, calls all of them failed, and names the first 12 without saying that there are more |
| GitHub warned that two actions were made for an older Node | `agentic-checks.yml` pins checkout 4.4.0 and setup-python 5.6.0. `agentic-connect` pins 7.0.1 and 7.1.0 and got no warning |
| The notify job's cache step warned that there was nothing to save | With no channel configured nothing is sent, and the ledger file is never written |
| `CK-PIPELINE-SECRETS` failed a line that references the secret store | The line had a YAML comment after the reference, and the check read the comment as part of the value |
| The install left compiled Python and two lock files, none of them ignored | Python compiles the kit where it runs; Spec Kit leaves the lock files. Nothing writes an ignore line |
| The install ran on a repository that Spec Kit never set up, and said nothing | The script asks only whether `.specify/` exists. The extensions are copied; no coding agent gets a command; `CK-UPSTREAM-PIN` cannot run |
| A path of the installing machine in a file meant to be committed | Spec Kit writes the folder a workflow was installed from into `.specify/workflows/workflow-registry.json`, and the install script installs from a local folder |
| The plan named the wrong kind of token for a Project | `docs/adapters/trackers.md` does not say which kind of token reads what. GitHub's fine-grained tokens cannot read a Project that a user account owns |

## Requirements

| ID | Requirement |
|---|---|
| LIV-1 | `setup_report` of the GitHub adapter asks GitHub for the rules that apply to the default branch (`repos/{repo}/rules/branches/{branch}`). A `pull_request` rule answers "pull request reviews required" with its `required_approving_review_count` and "code owner review required" with its `require_code_owner_review`. A `required_status_checks` rule answers "agentic-checks is a required status check" with the names it requires. |
| LIV-2 | The adapter still asks for branch protection. Each of those three items passes when the rules or the protection say so. When neither says so, the item fails if protection was read or the branch has none, and is `not-checkable` if the branch has protection that this credential may not read. The branch has none when GitHub answers "Branch not protected", or when GitHub refuses the question and the branch's own entry (`repos/{repo}/branches/{branch}`) says that protection is not enabled; anyone who can read the repository may ask that. Where the rules cannot be read, protection alone decides, as before. |
| LIV-3 | "administrators are not exempt" passes when protection enforces its rules for administrators, or when a ruleset asks for the review and names nobody who may bypass it. It fails when such a ruleset names a bypass actor; the detail names the ruleset and the kinds of actor. It is `not-checkable` when GitHub does not say who may bypass that ruleset: the answer has no list, the request fails, or the ruleset belongs to an organization. |
| LIV-4 | Where GitHub refuses `GET /user` with "Resource not accessible by integration", the credential is an app installation's token and has no user. `agent_credential` then answers instead of failing: account type `Bot`, the permissions that `repos/{repo}` reports, and as identity `github-actions[bot]` inside GitHub Actions (`GITHUB_ACTIONS` is `true`), or nothing elsewhere. `agent_identity` answers the same identity. Any other failure of that request is still a check that could not run. |
| LIV-5 | `CK-PIPELINE-SECRETS` judges the value of a line without a YAML comment that follows it. A `#` inside quotes is not a comment. |
| LIV-6 | The text of the `check-failed` event says what it counts: checks that failed or could not run. Where an event names fewer identifiers than it counts, the text says how many more there are. |
| LIV-7 | `agentic-checks.yml` pins the releases of `actions/checkout` and `actions/setup-python` that `agentic-connect` pins. |
| LIV-8 | `connect notify --ledger <file>` leaves that file in place when it ends, also when nothing was sent. |
| LIV-9 | Both install scripts write `.specify/extensions/.gitignore` with one rule, for compiled Python, when no such file is there. They leave an existing one alone. |
| LIV-10 | Both install scripts end with a plain note when Spec Kit was never set up in the project (no `.specify/init-options.json`, the file `CK-UPSTREAM-PIN` reads): the kit's code is installed, no coding agent has its commands, and `CK-UPSTREAM-PIN` cannot run until `specify init` has run. The exit code stays 0. |
| LIV-11 | `docs/install.md` says what to look at before `.specify/` is committed: the two lock files, and the folder paths in Spec Kit's list of workflows. `docs/adapters/trackers.md` says which kind of token reads a GitHub Project, and that one owned by a user account needs a classic token with the scope `read:project`. `docs/limits.md` records what these runs showed. |

## Acceptance criteria

- **AC-001** (verifies LIV-1): Given rules for the branch with a `pull_request` rule that asks for one approval and a code owner's review, and no branch protection that can be read, Then the first two items pass. Given a `required_status_checks` rule that names `agentic-checks`, Then the third passes.
- **AC-002** (verifies LIV-2): Given no rule that asks for a review, Then the item fails when GitHub answers "Branch not protected", fails when protection is refused and the branch's entry says it is not enabled, is `not-checkable` when protection is refused and the entry says it is enabled, and passes when protection asks for the review. Given that the rules cannot be read, Then protection alone decides, as before this change. Given that neither can be read, Then there is one row, `not-checkable`.
- **AC-003** (verifies LIV-3): Given a ruleset that asks for the review and names a repository role that may always bypass it, Then "administrators are not exempt" fails and its detail names the ruleset and `RepositoryRole`. Given the same ruleset with an empty list, Then it passes. Given an answer without the list, Then it is `not-checkable`.
- **AC-004** (verifies LIV-4): Given `GET /user` refused with GitHub's words for an installation token, and `GITHUB_ACTIONS=true`, Then `agent_credential` gives `github-actions[bot]`, `Bot` and the repository's permissions, and `CK-CRED` runs and passes for a token that may only read. Given the same refusal outside GitHub Actions, Then the identity is empty and the check still runs. Given another failure, such as bad credentials, Then `CK-CRED` is not run.
- **AC-005** (verifies LIV-5): Given `NAME: ${{ secrets.NAME }}   # why`, Then `CK-PIPELINE-SECRETS` passes. Given `NAME: abc # why`, and given `NAME: "a # b"`, Then it fails for a literal value, as before.
- **AC-006** (verifies LIV-6): Given 21 failed checks and 2 that could not run, Then the event's text says 23 checks failed or could not run, names 12 and says "and 11 more". Given one failed check and none that could not run, Then the text is "1 check(s) failed" and its name, as before.
- **AC-007** (verifies LIV-7): Then every `uses:` line of `agentic-checks.yml` that names `actions/checkout` or `actions/setup-python` carries the same commit id as the lines of `ci/github-actions.yml` of the connect extension.
- **AC-008** (verifies LIV-8): Given a ledger path in a folder that does not exist and no channel, When `connect notify` has run, Then the file exists and is empty. Given a ledger that already has lines, Then they are still there.
- **AC-009** (verifies LIV-9, LIV-10): Given a folder with `.specify/` that Spec Kit never set up, When the install script has run, Then it ended with 0, `.specify/extensions/.gitignore` holds the rule for compiled Python, and the output says that Spec Kit was never set up here. Given an ignore file that is already there, Then it is unchanged. Given a project set up by `specify init`, Then the note is not printed. The test is skipped where `specify` is not installed, and runs through each install script the machine has a shell for.
- **AC-010** (verifies LIV-11): Then `docs/install.md` names `workflow-registry.json` and the two lock files, and `docs/adapters/trackers.md` names `read:project`.

## What this does not do

- It does not make the kit read who may bypass a ruleset where GitHub does not say. The item is then `not-checkable`, and `CK-ENFORCE-SETUP` notes it.
- It does not change `CK-UPSTREAM-PIN`: a project without Spec Kit's own setup still cannot say which Spec Kit it has.
- It does not remove the path from Spec Kit's list of workflows. That file is Spec Kit's; the kit says where to look.
- It does not change the kit's own pipeline file, `.github/workflows/tests.yml`, which pinned the same two older releases. That is a commit of its own, made on 2026-11-27.
