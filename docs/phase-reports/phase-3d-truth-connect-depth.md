# Phase 3d — slices 0.5 "Truth" and 0.6 "Connected", and agent depth for slice 0.4

- **Phase and date:** Phase 3d (build), 2026-11-21 to 2026-11-22
- **Requirement IDs covered:** INT-1 to INT-7, PRD-1 to PRD-16, PIP-1 to PIP-7, NTF-1 to NTF-6, ADP-17 to ADP-21, AGT-19, AGT-20, TRC-19; and the packaging and tests of the quality packs (QLT-3 to QLT-22)
- **Assumptions:** listed in section 4, each with how to reverse it. None was approved by the owner
- **Unverified:** see section 5. In short: no live tracker, chat, mail or CI system; no coding agent; no live GitHub repository

## 1. What the owner asked for

Two messages on 2026-11-21, quoted in full:

> The requirements can come from different formats from different platforms like ADO, JIRA, ClickUp, GitHub projects/tasks, Claude artifacts, etc. There is a possibility that high-level business requirements can be duplicate or already resolved by old specs or features. The whole agentic-spec-kit should run by github actions or any other CI/CD pipelines and send notifications via Slack/Teams and post notes on the related work item on corresponding platform and send an email

> Deeper drive so that it will be a best agentic SDD platforms

The second was read as: compare the kit with the leading tools, find where it falls short, and close those gaps. The comparison is `docs/design/competitive-gap-analysis.md`.

## 2. What was built

| Extension | What it adds | Checks | Unit tests |
|---|---|---|---|
| `agentic-product` (new, slice 0.5) | Intake records; requirement lint, glossary, size limit; living capability specs fed by deltas and rebuilt by replay; duplicate detection decided by a Product Owner; ordering of colliding changes; sealing; outcomes; `why` | 13 | 77 |
| `agentic-connect` (new, slice 0.6) | Sources: Azure DevOps, Jira, ClickUp, GitHub Issues and Projects, documents. One pipeline command. Review mirroring. Events to Slack, Teams, email and the work item. Pipeline files for three CI systems | 3 | 60 |
| `agentic-team` (slice 0.4 additions) | A context pack per task, built and hashed at claim; an allowlist of MCP servers read from the base branch | 2 | 29 |
| `agentic-quality` (slice 0.4, finished) | Manifest, agent command, README, install lines, tests. The 22 checks were written earlier | 0 new | 32 |
| `agentic` (core) | The reviewer brief accepts sections from other extensions. It now leads the first gates with "Behaviour change" and "Similar work" | 0 | 0 |

Also written: `docs/prompts/spec/17-product-truth.md`, `18-connected-delivery.md`, additions to `11`, `15`, `16`, `90-acceptance.md` and the prompt `README.md`; `docs/adapters/trackers.md` and `pipeline.md`; additions to `docs/design/checks.md` and `schemas.md`; agent commands `shape`, `release`, `connect`, `quality`.

Six agent specs were changed so the team uses the new parts: the Spec Author drafts deltas, lists duplicate candidates and drafts outcomes; the Orchestrator dispatches only with a current context pack; the three implementers read the pack first; the Release Agent merges and seals after the last gate.

## 3. Verification

Run in the cloud workspace, Python 3.13:

| Command | Result |
|---|---|
| `python extensions/agentic/scripts/agentic.py selftest` | all self-tests behaved as expected (99 fixtures). Each of the 18 new checks passes on the sample project and fails on its broken variant for the intended reason |
| `python -m pytest tests -q` | 386 passed in 286 s: 188 from earlier slices, 32 quality, 77 product, 60 connect, 29 context and allowlist |

Run on the owner's machine (the desktop app's Linux workspace, Python 3.10.12, pytest 9.2.0 installed in that workspace only), after the files were copied there and the archive's hash was compared:

| Command | Result |
|---|---|
| `python3 extensions/agentic/scripts/agentic.py selftest` | all self-tests behaved as expected (99 fixtures) |
| `python3 -m pytest tests` run file by file, because one call there is limited to three minutes | 386 passed: product and context 106, connect and quality 92, kit, lanes and system 72, change 62, team 54 |

What the tests show, by claim:

- **Personal data and credentials are removed before an intake record is written.** `test_personal_data_and_credentials_are_removed_before_a_record_is_written`; and a record that still holds one fails `CK-INTAKE-RECORD`.
- **A living spec cannot be hand-edited, merged early, or have its history rewritten.** `test_merge_is_refused_before_release_and_writes_the_living_spec_after`, `test_history_cannot_be_rewritten`, `test_a_spec_cannot_be_merged_by_editing_the_index`.
- **A change cannot exempt itself, add its own tool server, or redirect a credential.** Three tests commit a base, change the file in the working tree, and show the check reads the base: `test_a_change_cannot_exempt_itself`, `test_a_change_cannot_add_a_server_and_approve_it_itself`, `test_the_pipeline_uses_the_base_branchs_connections`.
- **No channel carries requirement text.** `test_no_channel_ever_carries_requirement_text` renders every event for Slack, Teams, email and a work-item note and searches the output for the sample's requirement and intake text.
- **Mirroring creates no approval.** A review from someone without the role, a comment, a bot, and an approval of different evidence are each not mirrored; a mirrored record passes `CK-GATE-RECORD`, `CK-APPROVER`, `CK-GATE-MIRROR`, `CK-BRIEF` and `CK-AUDIT-CHAIN`.
- **Adapters send exactly the documented requests.** Each adapter test asserts the method, address, authentication header and body against a scripted transport that fails on any request it was not told to expect.
- **The shipped pipeline files pass the kit's own rules.** `test_the_shipped_pipelines_follow_the_kits_own_rules` runs `CK-PIPELINE-SECRETS` and `CK-PIN` on them. The first version of the GitLab file failed that test; the rule was right to flag a credential in an address, and was then taught to tell a variable reference from a stored value.

## 4. Decisions made without the owner, and how to reverse each

| # | Decision | Why | To reverse |
|---|---|---|---|
| 1 | Two new slices, 0.5 "Truth" and 0.6 "Connected" | The first request needs intake and delivery; the second needs one current truth to compare a requirement against | Delete `extensions/agentic-product`, `extensions/agentic-connect`, their tests and spec files 17 and 18, and the install lines |
| 2 | Built tracker adapters instead of reusing community extensions | Decided from catalogue descriptions only. **Their source was not read**, which charter D7 and the "not a rebuild" non-goal call for | Read `spec-kit-jira-sync`, `spec-kit-ado` and `spec-kit-ghp`. If one meets the three rules in the connect README, have it write intake records and delete the matching adapter |
| 3 | Built 0.5 and 0.6 before the rest of 0.4 | The owner's two requests came mid-0.4; charter D9 says slices ship in order | Nothing to undo; record the order in the charter or finish 0.4 before releasing |
| 4 | Only the Product Owner role decides duplicates and closes intake | Matches gate G1 | `kit.yml`: `intake.owner_roles` |
| 5 | Duplicate matching is by shared words; threshold 0.30 | Repeatable, explainable, no network. It misses the same idea in other words | `kit.yml`: `intake.dedupe.threshold`. Agents list what it misses |
| 6 | Requirement lint applies only until the wording is approved; limits 15 requirements, 45 criteria, 500 lines | An approved spec should not start failing because a word list grew | `kit.yml`: `requirements.limits`, `weak_words`, `allow_words`, `style` |
| 7 | Deltas use the added / modified / removed / renamed layout that OpenSpec made common | Teams may already know it | Change the section names in `living.py`; the format is in one place |
| 8 | Merge within 7 days of release; seal within 30 days; sealing keeps the files | A grace period for a human step; deleting evidence would break earlier checks | `kit.yml`: `product.merge_days`, `product.archive_days` |
| 9 | Outcomes are required from Medium tier | Low-tier changes are often refactors | `kit.yml`: `product.outcomes.from_tier` |
| 10 | Gates G1 and G2 now bind the deltas, `origin.yml` and `outcomes.yml` as evidence | The approver should approve the change in behaviour, not only the prose | Remove `SPEC_EVIDENCE` in the product extension |
| 11 | "Gate ready" is announced only when every check passes | Otherwise people are called to review work the kit already knows is not ready | `notify.detect` in the connect extension |
| 12 | Each event is announced once; no reminders | Reminders need a schedule and a policy on who is chased | Add a scheduled `connect notify` without a ledger |
| 13 | A GitHub workflow that runs on a pull request may not name a tracker or notification secret | The pull request controls that workflow file and the kit's code | Remove the rule in `ck_pipeline_secrets`; not recommended |
| 14 | The mirror job is off by default and needs a GitHub App token | A push with the built-in token does not start workflows | Set the repository variable `AGENTIC_MIRROR` |
| 15 | `connect.yml`, the tool allowlist, the glossary and the exemption list are read from the base branch | A change must not relax the rule it is judged by | None recommended |
| 16 | A context pack is built at claim, with a budget of 20,000 characters; a stale pack fails the checks but does not block hand-off | The agent may be mid-task when the spec changes; the person reviewing should see it | `kit.yml`: `team.context.max_chars` |
| 17 | The allowlist covers MCP servers only, in six known configuration files | These are where agents get tools that run code | `kit.yml`: `team.tools.files` adds more |
| 18 | Six agent specs were edited | So the team writes deltas and reads packs | `git diff extensions/agentic-team/agents/` |
| 19 | `connect.yml` joined the files CODEOWNERS must cover when the connect extension is installed | It names where credentials are sent | Remove the line in the connect extension's `_register` |
| 20 | A requirement typed in by hand gets an id from a hash of its text, not from its title | Ids appear in notifications | `cmd_intake` in the product extension |

## 5. Not verified

- **No adapter has spoken to its service.** Jira, Azure DevOps, ClickUp and Teams endpoints were read from the vendors' references during this work. The GitHub Projects query and the Slack webhook body were written from memory and not re-read.
- **No pipeline file has been run** by GitHub Actions, Azure Pipelines or GitLab CI. The `workflow_run` design in particular needs a live run.
- **No coding agent has read a context pack, written a delta, or been stopped by the allowlist.** The locations of MCP configuration files for each agent were written from memory and not re-read against current documentation.
- **Duplicate detection was tried on a handful of sentences**, not on a real backlog. The threshold is a starting point.
- **The requirement lint was not run on the reference repository's specs.**
- Everything in earlier reports that was unverified still is: no live GitHub repository, no Windows or PowerShell run, no migration applied to a database.

## 6. Not built

From slice 0.4: regression of golden tasks against a baseline (AGT-14), planted-instruction tests (AGT-15), model routing and spend (AGT-16), run records (AGT-17), instruction-file lint (AGT-18), agent and flow metrics (TRC-13), generated views (TRC-15), the auditor evidence pack (TRC-16).

From the comparison: a system map that spans repositories; tests generated from requirements; escaped defects feeding new golden tasks; a reminder cadence; approvals from Azure Repos or GitLab; an MCP server for the kit's own state.

The closing documents (role guide, release notes per slice, the list of what the kit does not enforce) are not written.

## 7. Waiting on the owner

1. **The charter.** It is the owner's file and was not edited. If these slices stay, add to the release-slice table:

   `| 0.5 | Truth | Intake, requirement quality, living capability specs, duplicate detection, outcomes, lineage |`
   `| 0.6 | Connected | Requirement sources, pipelines, review mirroring, notifications |`

   and to the decision log, in the owner's words, the decisions on rows 1 to 3 of section 4.
2. **Decision 2** (reuse or keep the tracker adapters).
3. **Review** of spec files 17 and 18, and of the six changed agent specs. The sixteen agent specs have never been reviewed.
4. **Commit and push.** Slices 0.3 to 0.6 are in the working tree, uncommitted.
5. **The two tests that matter most:** a live GitHub repository with branch protection, and one real agent run of a golden task.
