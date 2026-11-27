# Administrator setup: what makes an approval trustworthy

The kit's checks read approvals from pull request reviews. They can only be trusted if the repository is configured so that an agent cannot create or bypass them. `agentic.py doctor` reports each item below as pass, fail or not checkable.

## Required settings (GitHub)
| Setting | Why | Checked by |
|---|---|---|
| A ruleset or branch protection on the default branch: require a pull request, at least one approval | Without it, anyone with push rights can merge with no review | doctor. Since 2026-11-27 it reads the rules of the branch, which any credential that can read the repository may ask. Branch protection itself only an administrator's credential can read |
| Require review from code owners | Changes to roles, waivers and the constitution need the owner's review | doctor |
| `agentic-checks` as a required status check | Otherwise a failing check does not block a merge | doctor |
| Do not allow administrators to bypass: no bypass actor on the ruleset that asks for the review, or "Do not allow bypassing" in branch protection | An administrator's token would defeat every rule | doctor |
| A CODEOWNERS file covering `.specify/` | Protects `roles.yml`, `kit.yml`, the constitution map, waivers and the constitution | CK-ENFORCE-SETUP (local) |
| The agent's token is not an approver | An approver's credential in the agent's hands defeats identity binding | CK-ENFORCE-SETUP compares the token's account with `roles.yml` |
| The agent's token cannot approve reviews, merge, or bypass protection | Same reason | Not checked in slice 0.1; see limits |
| Pin the actions in `agentic-checks.yml` to commit SHAs | A moved tag could replace the checker | Not checked in slice 0.1 |

## What is enforced, and what is only convention
| Rule | With the settings above | Without them |
|---|---|---|
| Only a listed human with the right role can approve a gate (GOV-6) | Enforced: the review must exist in GitHub, by that account, on that commit | Convention |
| The author cannot approve their own work (GOV-7) | Enforced, or recorded as a single-approver exception where the project allows it | Convention |
| A pull request cannot add its own approvers | Enforced: `roles.yml` is read from the base branch in CI | Enforced in CI only; a local run reads the working tree |
| An approval is bound to exactly what was reviewed (TRC-18) | Enforced by the evidence hash | Enforced; needs no repository setting |
| Suppressions need a waiver (GOV-15) | Enforced for the patterns the kit knows | Same; unknown patterns are not detected |
| The audit log has not been edited (TRC-5) | Edits and deletions are detected | Same. Someone with push rights can still replace the whole log; the chain head in each approved decision record is what exposes that |

## Limits you should know about
- **One person holding every role.** Identity binding protects against the agent only while the agent cannot use the approver's credentials. Keep the approver's session and tokens out of the agent's environment. Every decision is recorded as a single-approver exception.
- **The file adapter proves nothing.** It reads reviews from a file in the repository and exists for tests and demos.
- **The audit log covers kit commands only.** It records `init`, gate decisions and whatever is appended through `agentic.py audit`. It does not see what an agent or a person does outside those commands.
- **Hooks are advisory.** Spec Kit hooks are instructions to the agent. The kit's guarantees come from CI and from the `agentic-gate` step, not from hooks.
- **Token permissions are not inspected yet.** Slice 0.1 checks which account the agent's token belongs to, not what that token is allowed to do. That check arrives with the agent team in slice 0.3.
- **Independent verification is procedural.** The kit checks the verifier's declared inputs. It cannot prove what a model saw.
- **A pull request is not held back for want of G5 and G6.** Work in progress is legitimate on a pull request, so the checks there ask for G4 and what precedes it. A change merged without G5 and G6 fails the default branch afterwards (CK-GATE-RECORD). The check knows the default branch by its name: `enforcement.default_branch` in `kit.yml` must name yours.
- **Not yet run against a live GitHub repository.** The GitHub adapter is unit-tested with recorded responses only.
