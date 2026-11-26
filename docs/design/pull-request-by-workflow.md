# A pull request opened by a workflow, so that one person can pass a gate

- **Phase and date:** Phase 12 (features), prepared for the live test on the reference project; 2026-11-26
- **Requirement IDs covered:** BOT-1 to BOT-6, new with this document. BOT-6 and AC-006 were added the same day, after the code for the first five: a second look at the repository setting showed what else it allows
- **Assumptions:**
  1. On 2026-11-26 the owner chose this way for the live test: a workflow opens the test pull requests, so that he can approve them as himself.
  2. GitHub behaves as its documents say on 2026-11-26: the author of a pull request cannot approve it; a pull request opened with a workflow's own token has `github-actions[bot]` as its author; and the workflows on such a pull request start once a person with write access approves the run.
- **Unverified:** all of it, on GitHub. The template has not run. Whether a review by the person who pushed the branch counts depends on the repository's own rules as well: a rule that asks for approval of the most recent push by someone else would not accept it. The live test is what shows it.

## Why

`docs/limits.md` says, from the newcomer's walk of 2026-11-25: one person with one account cannot pass a gate on GitHub. The checks accept a review only in the state `APPROVED`, and GitHub does not let the author of a pull request approve it. The first person who tries the kit, before showing it to a team, meets that wall at the first gate. Until now the only way round it was a second account.

## What it does

| ID | Requirement |
|---|---|
| BOT-1 | The kit ships a workflow, `agentic-open-pull-request.yml`. It is started by hand with a branch and a title, and opens a pull request from that branch to the default branch. The pull request's author is the workflow's own account. |
| BOT-2 | The workflow uses no secret. Its one job may read the repository and write pull requests, and nothing else. What a person types reaches the command through the environment and is never pasted into it. |
| BOT-3 | It refuses the default branch as the branch to open from. Where a pull request for the branch is already open, it says so, names it and ends well. |
| BOT-4 | `init --open-pr-workflow` writes the workflow into `.github/workflows/`. Without that option `init` writes what it wrote before. |
| BOT-5 | Nothing about approval changes. The checks still read who wrote the commits. Where the reviewer is among them, the gate needs `gates.single_approver_exception: allowed`, and the record says that the exception was used. |
| BOT-6 | The workflow's own header says what the repository setting it needs also allows: a workflow may then approve a pull request, not only open one. It says that the kit's gate never counts such an approval, and that a branch rule which only counts approvals may. |

## How we will know

- **AC-001** (verifies BOT-1, BOT-2): The shipped file is valid YAML; it starts only by hand, takes a branch and a title, names no secret, and gives its job read access to the contents and write access to pull requests only.
- **AC-002** (verifies BOT-2): No expression of the workflow language stands inside a command. Each one is under `env:`.
- **AC-003** (verifies BOT-4): `init --open-pr-workflow` writes the file; `init` alone does not.
- **AC-004** (verifies BOT-3): The command refuses the default branch and ends well when a pull request is already open. Shown with a stand-in for the `gh` program, since nothing here reaches GitHub.
- **AC-006** (verifies BOT-6, BOT-5): The header of the shipped file names the setting and says that it lets a workflow approve. Given a review in the state `APPROVED` by `github-actions[bot]`, an account of the type `Bot`, in the form GitHub's API gives it, When the approval is judged, Then it is refused twice over: the account is not a person's, and it is the pipeline's own. That holds also where `roles.yml` lists the account.
- **AC-005** (verifies BOT-1, BOT-5): On GitHub, a pull request opened by the workflow has the bot as its author, the person who pushed the branch approves it, and `CK-APPROVER` accepts that review with the exception recorded. This needs GitHub. It is met only when the live test has shown it.

## What it will not do

- Approve anything, or make a review count that the repository's rules refuse.
- Push a branch. A person, or an agent under its own account, pushes; the workflow only opens the pull request.
- Start the kit's checks. GitHub holds the workflows of a pull request that a workflow opened until a person approves the run.
- Keep a workflow from approving. The setting this needs, "Allow GitHub Actions to create and approve pull requests", is one switch for both. GitHub's note of 2022-01-14 says the switch was made so that nobody could use Actions to meet a "Required approvals" rule and merge a change no other person had reviewed. Turning it on gives that up for the whole repository: any workflow there whose job may write pull requests can then approve one. Whether GitHub counts such an approval towards a rule of a given repository was not tried. The kit's gate does not count it (BOT-6).

## Decisions made here that are the owner's to change

1. The workflow is offered and not installed by default: a team of two or more does not need it.
2. It is started by hand. Opening a pull request for every pushed branch would be the other way.
3. The pull request's text says who asked for it and why its author is a bot.
4. The way that needs no such setting is a second account, or a GitHub App with its own token, to open the pull request. Both are more to set up, and neither is built here.

## Sources

- GitHub Changelog, "Bot-created pull requests can run workflows if approved", read 2026-11-26: https://github.blog/changelog/2026-05-21-bot-created-pull-requests-can-run-workflows-if-approved
- GitHub Changelog, "GitHub Actions: Prevent GitHub Actions from approving pull requests", 2022-01-14, read 2026-11-26: https://github.blog/changelog/2022-01-14-github-actions-prevent-github-actions-from-approving-pull-requests
- GitHub Changelog, "GitHub Actions: Prevent GitHub Actions from creating and approving pull requests", 2022-05-03, read 2026-11-26: https://github.blog/changelog/2022-05-03-github-actions-prevent-github-actions-from-creating-and-approving-pull-requests/
- GitHub Docs, "Approving a pull request with required reviews", read 2026-11-25: https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/approving-a-pull-request-with-required-reviews
