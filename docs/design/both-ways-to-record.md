# Both ways to record a gate where approvals are dismissed on a push

- **Phase and date:** Phase 12, after the live test on HealthQCopilot; 2026-11-28 (UTC)
- **Upstream and reference:** github/spec-kit `v1.4.3`; `docs/design/first-gate-on-github.md`, open question 1
- **Requirement IDs covered:** BWR-1 to BWR-8, new with this document. They answer open question 1 of `first-gate-on-github.md`. No rule about who approves changes: either way needs an approving review by a person who holds the role, whose text carries the gate's line for the evidence as it stands
- **Assumptions:**
  1. On 2026-11-28 the owner answered open question 1: "both can be accepted".
  2. GitHub lists the reviews of a pull request in the order they were submitted, as it did for pull request 87 of the reference repository on 2026-11-28 (source 2), and the file adapter keeps the order its file has. The kit takes "later" from that order.
  3. A run of `agentic-checks` that a person's merge caused starts the connect workflow; one whose actor is the workflow's own bot does not (`first-gate-on-github.md`, row 2). The job of BWR-6 runs after a push to the default branch, which a person's merge causes.
- **Unverified:** nothing here has run on GitHub. The job that mirrors after the merge, the pull request it opens, and a second approval that the checks accept are tried only on the file adapter's stand-in and on GitHub's answers written by hand

## Why

On 2026-11-27 the reference repository passed its first gate on GitHub. Its rule for `main` dismisses an approval when a commit is pushed. The decision records went onto the reviewed pull request as one more commit, GitHub dismissed the review they cite, and `CK-APPROVER` failed them: "the review state is DISMISSED, not APPROVED". The owner approved again with the same line and merged. The records were then written again after the merge, on a branch of their own, and passed.

`first-gate-on-github.md` named two ways out and left the choice open. The owner accepted both. This document makes the kit take either.

## The two ways

**On the pull request.** The record is committed onto the reviewed pull request, as before. Where the push dismisses the review, the reviewer approves again, with the same line. The record keeps naming the first review. The checks find that it was dismissed, and accept the later approval in its place: by the same person, on the same pull request, carrying the same line for the same evidence. Nothing is written again, so nothing is pushed again and nothing more is dismissed. Each reviewer approves twice.

**After the merge.** The pull request is merged with the reviews on it, and the records follow in a pull request of their own. A new job of the connect workflow does that: after the checks of the push to the default branch, it finds the pull request that was merged, mirrors its reviews into records, and opens a pull request with them. Until that one is merged, the gate shows as open, and for a change whose plan or code needs the gate, `CK-GATE-RECORD` fails on the default branch. `record --change pull/<n>`, run after the merge on a branch of its own, does the same by hand.

## Requirements

| ID | Requirement |
|---|---|
| BWR-1 | A record names one review for each role, as before. Where that review is now dismissed, `CK-APPROVER` and `CK-GATE-MIRROR` take in its place the first later review on the same pull request by the same person, in the state the decision asks for (approved, or changes requested for `reject`), whose text carries the same line: the same gate, the same decision and the same evidence hash. The record is not rewritten. Where there is no such review, the dismissed review is judged as before, and fails. |
| BWR-2 | The review that stands in is held to everything the one it stands for is held to: a person's account, listed in `roles.yml` on the base branch, holding the role, not the agent's or CI's own identity, and the single-approver exception where its author also wrote the change. It need not be on the record's commit. Where its own commit can be read, the evidence files there have to give the record's hash; where they give another, it does not stand in. Each check notes which review stands for which. |
| BWR-3 | `record --change` writes nothing where the gate already has a record for the same decision and the same evidence hash, and each review that record names is still approved, or has a review that stands for it under BWR-1. It says that the gate is recorded already, names the reviews, and ends with 0. So a second approval does not lead to another record, another push and another dismissal. Where the evidence or the decision changed, it writes the record as before, and keeps the earlier one under `superseded`. |
| BWR-4 | The note of FGR-2 names both ways: approve again with the same line, which the checks accept in place of the dismissed review; or commit the record after the merge, on a branch of its own. |
| BWR-5 | `connect mirror --merged <commit>` asks the enforcement adapter's `pulls` for the pull request that was merged as that commit, and mirrors its reviews as `connect mirror --change` does. Each record names the commit that the reviews it mirrors are on. Where the reviews that carry a gate's line are not all on one commit, that gate is not recorded, and its row says why. Where no pull request was merged as that commit, the command says so, writes nothing and ends with 0. `--merged` is given alone, without `--change` and `--commit`. With `--change`, `--commit` may now be left out: the commit is then taken from the reviews, as `record --change` takes it. |
| BWR-6 | `ci/github-actions.yml` gets a job `mirror-after-merge`. It runs after `agentic-checks` on a push to the default branch from this repository, where the repository variable `AGENTIC_MIRROR` is `after-merge`. It checks out the default branch at the commit of that push, with its history, and runs the kit from there: `connect mirror --merged`. Where records were written, it commits them on a branch of its own, `agentic/records-<12 characters of the commit>`, pushes that branch, and opens a pull request into the default branch. It may write contents and pull requests, and uses no secret. The job that mirrors onto the pull request runs, as before, where the variable is `true`. |
| BWR-7 | The opening comment of that file says which to choose. `true`: the records go onto the reviewed pull request, and where approvals are dismissed on a push, each reviewer approves again with the same line. `after-merge`: the records follow in a pull request of their own; the gate shows as open until it is merged; that pull request is opened by the workflow's own bot, so GitHub holds its checks until a person approves them, and the connect workflow does not run for it. |
| BWR-8 | `docs/install.md`, `extensions/agentic/commands/gate.md`, `extensions/agentic-connect/README.md` and `docs/limits.md` name both ways where FGR-1 named one. |

## Acceptance criteria

- **AC-001** (verifies BWR-1, BWR-2): Given a record that names review A, A now dismissed, and a later approving review B by the same person on the same pull request with the same line, Then `CK-APPROVER` and `CK-GATE-MIRROR` pass, and each notes that B stands for A. Given B by another person, B with another evidence hash, B before A, or no B, Then `CK-APPROVER` fails and says that the review is dismissed. Given B's commit in git with evidence files that give another hash, Then `CK-APPROVER` fails.
- **AC-002** (verifies BWR-2): Given B by a person who also wrote the change, and a `kit.yml` that forbids the single-approver exception, Then `CK-APPROVER` fails for B as it would for A.
- **AC-003** (verifies BWR-3): Given a record for the evidence as it stands and the approving review it names, When `record --change` runs again, Then nothing is written, the output says that the gate is recorded already, and the command ends with 0. Given that review dismissed and a later approval by the same person with the same line, Then the same. Given the evidence changed and a review with the new line, Then the record is written, with the earlier one under `superseded`.
- **AC-004** (verifies BWR-4): Given a stand-in that says approvals are dismissed on a push and an open pull request, When `record --change` writes a record, Then the note names both ways.
- **AC-005** (verifies BWR-5): Given a stand-in with a pull request merged as commit M, whose review on commit H carries a gate's line, When `connect mirror --merged M --write` runs, Then the record is written and names H. Given no pull request merged as M, Then nothing is written, the output says so, and the command ends with 0. Given the reviews that carry the line on two commits, Then nothing is written for that gate and its row says why. Given `--merged` with `--change`, Then the command refuses and ends with 2.
- **AC-006** (verifies BWR-6, BWR-7): Then `ci/github-actions.yml` has a job `mirror-after-merge` whose condition names a push, the default branch, this repository and `after-merge`; whose permissions are `contents: write` and `pull-requests: write`; which runs `connect mirror --merged` and `gh pr create` and pushes to `agentic/records-`; which names no secret; and the job `mirror` still runs where `AGENTIC_MIRROR` is `true`. The opening comment names both values. `CK-PIPELINE-SECRETS` passes on the file.
- **AC-007** (verifies BWR-8): Then the four documents each name both ways.

## What this does not do

- It does not stop GitHub from dismissing an approval. That is the repository's own rule.
- It does not make the connect workflow run for a pull request that the bot opened, the records' own among them.
- It does not change a record that names a dismissed review. The record keeps the review that was given first; the check says which one stands for it.
- It does not let anything but a person's review stand in. A review by the bot, a comment, or an approval without the line never does.

## Sources

1. `docs/design/first-gate-on-github.md` of this repository: what happened on the reference repository on 2026-11-27, and open question 1.
2. GitHub's answers on the reference repository, `imatiqul/azure-ai-cloud-healthcare`, asked on 2026-11-28: `repos/<repo>/pulls/87/reviews` listed its four reviews in the order of their `submitted_at`, the dismissed one third; `repos/<repo>/commits/96864d2/pulls` listed pull request 88, whose `merge_commit_sha` is that commit and whose head is `04c485f`; `repos/<repo>/commits/483332d/pulls` listed pull request 87 in the same way. GitHub's REST pages for these two requests were not read.
