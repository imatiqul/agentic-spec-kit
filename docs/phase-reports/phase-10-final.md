# Phases 8 to 10: the showcases, the acceptance lines, and a second look at the whole kit

- **Phase and date:** Phases 8 to 10, the halves that needed the reference; 2026-11-22
- **Upstream and reference:** spec-kit `v1.4.3`; healthcare repository `imatiqul/azure-ai-cloud-healthcare`, `main` at `8d04df3`
- **Requirement IDs exercised:** GOV-6, GOV-9, GOV-17, GOV-20, TRC-16, TRC-19, QLT-2, QLT-4, QLT-12, QLT-15, AGT-10
- **Assumptions:** an acceptance line is judged against the words in `docs/prompts/90-acceptance.md`. Where a line was shown with a scripted stand-in or a recorded response and not with the real thing, it says so and is counted apart
- **Unverified:** no gate of the reference has been passed. The healthcare solution was not built or tested. The owner merged the healthcare branches into `main` with no build, no test run and no gate review, and no pipeline has run the kit on a project. Section 9 has the full list

The owner's instruction was to finish everything, look at it again, and wait; he pushes. This report is the end of that. Nothing in it is an approval.

**Updated the same day, after the owner pushed the kit's `main` (`6e217c2`).** The kit repository's pipeline ran for the first time on that push and passed on Python 3.10 and 3.13 (run 45093366953). One acceptance line moved from "in part" to "met"; the places that said the pipeline had not run are changed, and nothing else is. 

**Updated again that evening, after the owner merged the reference work.** He pushed the three branches, opened pull requests #73, #74 and #75 against `main` (not stacked, not as drafts) and merged all three within a minute, with merge commits. `main` of the healthcare repository is now `d78ffe7`, and its files are exactly those of the reviewed `sdd/showcase-proposals` branch: the two trees are the same. What the merge does not change:

- **No gate is passed.** No review carried a gate's line and no decision record exists. The acceptance line about C4's gate decisions stays not met.
- **The C4 change is on `main` and has still not been built or tested.** No workflow of that repository ran on the pull requests or on the merge. `pr-validation.yml` is triggered by a pull request to `main` and did not start; only the hosted code review did.
- **The kit did not notice.** Its checks on `main` (79 pass, 24 fail, 1 not run) report the same three missing gate records as before the merge. It has no rule for a change that reaches the default branch without G5 and G6. That is now in `docs/limits.md`.

Sections 1, 6, 8 and 9 are changed to match; the acceptance counts are not.

## 1. Where everything is

| What | Where | State |
|---|---|---|
| The kit: six extensions, 105 checks, 16 agents, three pipelines | `imatiqul/agentic-spec-kit`, `main` | Pushed by the owner at `6e217c2`. This update to the report is a later local commit |
| Governance for the reference: constitution version 2, the map, 25 specs, six draft plans, the agent team | Healthcare repository, branch `sdd/reference-plans` (`89a4fc9`) | Merged into `main` by the owner (pull request #74). Still waits at G1 and G2 (nine specs), G3 and G4 (six plans) |
| The C4 change: 14 code files, 80 tests, 39 files of record | Branch `sdd/004-audit-identity` (`1e8d054`), on the branch above | Merged into `main` by the owner (pull request #73). Not built. Still waits on seven amendments, a test run, and reviews |
| Proposals: adoption baseline, threat model and authorization matrix for C2, the setting that shows H4 | Branch `sdd/showcase-proposals` (`a44c57c`), on the branch above | Merged into `main` by the owner (pull request #75). Nothing in it is approved or enforced: the baseline is still a proposal outside the folder the kit reads |
| Titles and descriptions for the three pull requests | `examples/healthq/phase-7/pull-requests.md` | Text for the owner to paste |

The three branches were written in a workspace that cannot push. They were carried to the owner's machine as one bundle and made again there commit by commit, under his name, without checking anything out. Each ends in exactly the files that were reviewed: the script compares the tree of each branch with the one from the workspace and stops if they differ. Commit ids changed on the way, and the records name the old ones; `examples/healthq/phase-7/commit-map.md` maps them.

## 2. The showcases (Phase 9)

`docs/prompts/30-phases.md` asks for the 0.4 groups to be applied to findings that show them. Each row says what was produced and what it is not.

| Finding | What was applied | Result | What it is not |
|---|---|---|---|
| C4 | The agent team, work items, a security review and an independent verification, evidence for G5 to G7 | `docs/phase-reports/phase-7-c4-walkthrough.md` | Not built, not approved |
| C2 | Threat model and authorization matrix (`specs/002-endpoint-authorization/`) | Three threats, each tested by an abuse case of the approved spec. Six gaps the spec has no test for, among them that every authorization policy admits the Admin role. A matrix of 20 rows: role, tenant, resource, expected answer | Analysis. Every row says `not-run`. No endpoint was called |
| H5 | Data-change plan for the migrations spec (`specs/013-migrations-production-engine/`), from Phase 6 | A draft plan that names the production engine and every reader and writer of each store | No migration was applied to any database |
| C5, C6 | AI evaluation design in the plans of specs 005 and 006, from Phase 6 | The kit's CK-AI-PROD-PATH fails on the code as it is: the evaluation does not call the classifier that production runs | No evaluation was run |
| H6, M3, M5 | Waiver register: a proposed adoption baseline (`.specify/agentic/proposals/adoption-baseline.md`) | 635 suppressions and open map questions in 14 groups, each with an owner role and a proposed expiry | Not a baseline. It sits outside the folder the kit reads, with `approved_by` blank, so it waives nothing |
| H4 | The check for figures with no recorded source, pointed at the endpoint files | 60 findings in two files, among them `aiAccuracyRate = 94.2` at `DemoDataEndpoints.cs:43` | The check sees a number given to a name. It does not know whether the figure is true |

To see H4 the check had to be extended to read code, and to give a verifier the C4 code the kit had to learn which files a spec's components own. Both are in `docs/release-notes.md`.

## 3. The sample evidence pack (Phase 10)

`examples/healthq/phase-10/audit-pack-004/`, made by `agentic.py audit-pack --spec 004-audit-identity`. Eight files: a cover page with the disclaimer, a manifest with the SHA-256 of every file and the hash of the spec section that answers each of the seven HIPAA-pack controls, the spec's audit log (intact), its trace, and the configuration.

It shows the shape of a pack and not a release. It lists no approvals, because none exist, and no waivers. It was made from the reference project without the healthcare code under it, so the day's check results in it (76 passed, 22 failed, 1 not run, 5 not required by the profile) are fewer than on the branch.

## 4. Acceptance

Every line of `docs/prompts/90-acceptance.md`, in its order. The earlier phase reports hold a first reading of slices 0.1, 0.3 and 0.4; this is the reading today, with today's runs (section 6). Test names are in `tests/`; a fixture is one of the 105 the self-test runs.

**Count: 54 lines. 39 met. 5 met only with a stand-in. 6 met in part. 3 not met. 1 not measured.**

### Slice 0.1, Govern

| Line | Result | Evidence |
|---|---|---|
| A new engineer installs the kit from the README alone | In part | `scripts/install.sh` installed it into a new project in Phase 3a and into the reference in Phase 5. Nobody but the author has tried, and `install.ps1` has never run |
| Lite is adopted in under an hour | Not measured | Nobody has timed it |
| Every gate shows its accountable role and approver | Met | `test_gate_command_prints_the_line_to_paste`, `test_the_gate_board_names_who_is_needed_next` |
| A decision by an agent, by the author, or with no matching review is rejected | Stand-in | `test_agent_identity_cannot_approve`, `test_bot_account_cannot_approve`, `test_missing_review_is_reported`, `test_review_on_another_commit_does_not_count`, on the file adapter and on recorded GitHub responses. No live review has been read |
| Every principle is machine-checked or marked human-judged | Met | Fixture CK-CONSTITUTION; `test_the_reference_constitution_maps_every_principle_and_answers_every_finding` |
| An unrecorded suppression fails; an expired waiver fails | Met | `test_expired_waiver_fails`, `test_baseline_count_can_only_go_down`. On the reference the check fails on 635 |
| A missing or orphaned trace link fails | Met | `test_orphans_are_reported`; fixture CK-TRACE |
| An edited audit log entry is detected | Met | `test_deleted_audit_entry_is_detected`; fixture CK-AUDIT-CHAIN |
| Every check has a passing and a failing fixture, and CI shows the failing one fail | Met | 105 fixtures behave (`selftest`). The kit repository's pipeline (decision 83) ran on the owner's push of `6e217c2` and passed on Python 3.10 and 3.13; its self-test step prints each broken fixture failing (GitHub Actions run 45093366953). No project's pipeline has run the kit |
| The documentation lists what is not enforced | Met | `docs/limits.md`, `docs/admin-setup.md` |

### Slice 0.2, System

| Line | Result | Evidence |
|---|---|---|
| Discovery produces a map with every node owned and every derived fact citing a file | Met | `test_discovery_finds_the_fixture_and_cites_files`. On the reference: `test_every_derived_fact_in_the_map_cites_a_file_in_the_healthcare_repository`, run against a clone |
| A change that modifies an undeclared node fails | Met | `test_undeclared_touch_fails_and_declared_touch_passes`. It fails on the C4 change, for the audit event stream |
| A shared-library change adds each consumer's owner as a reviewer and runs the consumer matrix | In part | Reviewers: `test_shared_library_change_reaches_both_services_and_their_owners`. The matrix: the kit fails until each consumer has a recorded build (`test_every_consumer_must_be_built_against_the_changed_library`). It starts no build |
| A breaking contract change is detected and blocks | Met | `test_removed_response_field_is_breaking_until_a_spec_declares_it`; golden defect `breaking-described-additive` |
| A destructive data change without a plan and Data Owner approval is blocked; a migration tested on another engine fails | Met | `test_destructive_change_approved_without_the_data_owner_fails`, `test_migration_written_for_another_engine_fails_and_a_baseline_can_carry_it` |
| Two in-flight specs touching the same node are reported and ordered | Met | Fixture CK-CROSS-SPEC; `test_dependency_must_pass_a_gate_first`. On the reference: `test_the_specs_that_share_a_component_are_ordered_and_nothing_waits_on_the_analysis_only_spec` |
| A spec's tier rises to the highest tier it touches | Met | `test_tier_must_rise_to_the_highest_touched` |

### Slice 0.3, Team

| Line | Result | Evidence |
|---|---|---|
| The minimum team of four completes a fixture task end to end, stopping at every gate | Stand-in | Golden task `minimum-team`, with a scripted driver. Apart from the fixture: one model worked the C4 change through the same machinery in Phase 7 |
| The same task completes in sequential mode with the same gates and evidence | Stand-in | `test_golden_tasks_complete_in_both_modes_stopping_at_every_gate` |
| Seeded defects are caught by the reviewer or verifier | In part | Two of three by checks (CK-TOUCH, CK-CONTRACT-BREAK). The missing tenant filter is caught by a scripted rule; a model has to make that judgement. In Phase 7 two reviewing agents found four real defects in a real change |
| An agent editing outside its declared paths is detected | Met | `test_handoff_is_refused_when_files_outside_the_item_changed`, `test_a_commit_that_names_a_work_item_but_changes_other_files_is_caught`, the guard tests |
| A third rework round does not happen | Met | `test_a_third_rework_round_does_not_happen_the_disagreement_is_escalated` |
| No agent credential can approve, merge, publish or deploy; shown, not asserted | Not met | `test_agent_credential_rules` reads recorded responses. Showing it needs a live repository and a real agent token |

### Slice 0.4, Depth

| Line | Result | Evidence |
|---|---|---|
| A Low-tier change takes the fast lane; an author cannot select it | Met | `test_a_low_tier_change_takes_the_fast_lane_with_one_review_for_g1_to_g4`, `test_an_author_cannot_put_a_spec_on_the_fast_lane` |
| An emergency with an overdue retrospective fails the default branch | Met | `test_an_emergency_passes_until_its_deadline_and_fails_the_branch_after` |
| An evaluation that does not call the production code path fails | Met | Fixture CK-AI-PROD-PATH. It fails on the reference code (finding C6) |
| Planted instructions in files, issues and tool output are reported and not acted on | Stand-in | `golden run`: three in each mode. `test_the_harness_sees_an_agent_that_obeys` shows the test can fail. No model has been put through it |
| A changed agent spec triggers the regression suite and a baseline comparison | Met | `test_changing_an_agent_is_allowed_when_nothing_gets_worse_and_refused_when_something_does`, `test_a_change_of_model_needs_a_fresh_golden_run` |
| The auditor pack for one release exports with hashes and its disclaimer | Met | `test_the_pack_holds_every_file_it_lists_with_its_hash`; the sample of section 3 |
| Lite effort is unchanged from slice 0.1 | Met | `test_a_new_lite_project_is_asked_for_people_and_code_owners_and_nothing_else` |
| An agent's context is rebuilt identically, and a change to its sources during the task fails | Met | `test_the_same_repository_gives_the_same_pack`, `test_a_pack_goes_stale_when_what_it_was_built_from_changes` |
| A tool server off the allowlist, launched differently, or on "latest" fails | Met | `test_an_unlisted_server_fails`, `test_a_server_that_could_run_different_code_tomorrow_fails_even_when_listed` |

### Slice 0.5, Truth

| Line | Result | Evidence |
|---|---|---|
| A repeated requirement is a candidate, and the first gate waits for a Product Owner | Met | `test_a_likely_duplicate_blocks_the_first_gate_until_a_product_owner_decides`. On the reference three pairs wait |
| Personal data and credentials are replaced before the record is written | Met | `test_personal_data_and_credentials_are_removed_before_a_record_is_written` |
| A vague requirement, two obligations in one, and an oversized spec fail before the first gate, and not after approval | Met | `test_wording_an_agent_could_misread_fails`, `test_size_limits_come_from_kit_yml`, `test_approved_wording_is_left_alone_until_it_changes` |
| A living spec edited by hand fails; so does a merge before release and an edit to a merged delta | Met | `test_history_cannot_be_rewritten`, `test_merge_is_refused_before_release_and_writes_the_living_spec_after`, `test_a_sealed_change_never_changes` |
| One command merges after release; the finished change is sealed and left out of agent context | Met | The merge test above; `test_sealing_needs_a_merge_first`, `test_finished_work_is_not_a_source_of_tasks` |
| From one line of code, one command names the request, the requirement, the capability and the approvers | Met | `test_why_follows_a_file_back_to_the_request_and_the_approvals`. On the C4 change it names everything but approvers; there are none |

### Slice 0.6, Connected

| Line | Result | Evidence |
|---|---|---|
| Requirements from each tracker and from documents arrive in one record shape, with no test using a network | Met | The adapter tests in `tests/test_connect.py`, on recorded responses: Jira, Azure DevOps, ClickUp, GitHub Issues and Projects, documents in five formats. No live tracker has been read |
| One command runs the whole kit in a pipeline with no prompt | In part | `test_run_reports_and_exits_with_the_check_result`. The command has never run in a pipeline |
| A notification contains no requirement text | Met | `test_no_channel_ever_carries_requirement_text`, `test_a_notification_cannot_be_configured_to_carry_text` |
| An event is announced once across repeated runs | Met | `test_delivery_to_every_channel_once`, `test_a_note_is_not_repeated_even_without_a_ledger` |
| A webhook address or token in a configuration or pipeline file fails | Met | `test_connection_settings_are_checked`, `test_other_ci_systems_are_scanned_for_stored_secrets` |
| A pipeline that lets a proposed change or an agent step read a credential fails | Met | `test_pipeline_rules`, `test_an_agent_step_is_judged_by_everything_it_can_read` |
| A review is mirrored only with the gate's line for the current evidence and every required role | Stand-in | `test_a_review_with_the_approval_line_is_mirrored_into_a_decision_record`, `test_an_approval_of_other_evidence_is_not_mirrored_and_a_rejection_is`, on recorded responses |

### Reference example

| Line | Result | Evidence |
|---|---|---|
| Every finding has a verification status with reproducible evidence | Met | `docs/phase-reports/phase-1-verification.md`; `examples/healthq/phase-1/verify-findings.sh` and its output. Planning later corrected one of them (N9) and the map |
| One spec per confirmed or corrected finding, with touches, owner and reviewers | Met | 25 specs for 27 findings; N5 is covered by 005 and N10 by 021. `test_there_is_one_spec_for_each_finding_drafted_so_far`, `test_every_spec_has_an_impact_report_and_a_brief_for_its_first_gate` |
| Any line of the C4 change traces back to a principle and forward to what it affects | Met | `agentic.py why <file>:<line>`, for one line of each of the 14 files in `specs/004-audit-identity/evidence/trace-lines.md`; `test_a_line_of_the_c4_change_traces_back_to_the_principle_and_forward_to_what_it_reaches`. Forward means what the map says the spec reaches |
| Every C4 gate decision is a human review mirrored in the record | Not met | No decision record exists for any gate. G1 and G2 were approved in conversation. G3 to G7 wait. The owner has since merged the change; a merge is not a gate decision |
| No suppression remains without a dated, owned waiver | Not met | 635 remain. The baseline that would carry them is a proposal |
| The C5/C6 evaluation design provably runs the production classifier | In part | The design is in the draft plans of 005 and 006, and the check proves the opposite of today's code. Nothing has been built or run to prove the design |

### Overall

| Line | Result | Evidence |
|---|---|---|
| The toolkit repository is public by the owner's decision. Nothing was merged, and no real data or secrets are in either repo | Met | Charter D2 as updated. No agent merged anything; the owner merged pull request #72 himself. Every commit's staged changes were scanned for credential patterns. One credential was already in the healthcare source before this work, for a local development container (`src/HealthQCopilot.AppHost/Program.cs:114`, observation O1); no spec covers it, and its value is written nowhere here |
| Every artifact carries the header | In part | Phase reports, design documents, and the reference's specs and plans carry it. These do not: `docs/install.md`, `docs/admin-setup.md`, the four pages under `docs/adapters/`, the generated requirement map, one pull-request text, and what the kit generates or parses in the reference (briefs, impact reports, context packs, task lists, the privacy and safety documents) |
| Upstream and community components are attributed and their reviews recorded | Met | `NOTICE.md`; `docs/design/source-review.md`. No code was copied from the three reference projects |

## 5. A second look at the kit

### What held

- **Nothing passed a gate on an agent's word.** Told to carry on without stopping, the work went to the end and still recorded no approval. Every artefact in front of a gate says it is waiting, and the gate check fails on all of them.
- **The reviewers earned their place.** Two agents that had not written the change, each in a new session with a fixed list of what it could read, made 29 findings in their first round. They come to fifteen things to act on: four defects in the change or its tests, four statements in the plan's documents that were wrong, written by the author, and seven in the spec the owner had approved. The kit's checks report two of the fifteen (the component the spec does not declare, and two criteria not marked as abuse cases). The other thirteen were found by reading.
- **The checks found real things in real code:** the change touching a component its spec did not declare, two floating container tags, an evaluation that does not call production code, accuracy figures written into an endpoint, 635 suppressions.
- **The kit is cheap to run.** 507 tests, 105 fixtures and 20 golden results pass offline: in about four minutes in the workspace, and on the owner's machine.

### What using it on real work showed

Twenty things, none visible from the fixtures. Eight were fixed with a test each (`docs/release-notes.md`). Six of them in Phase 7: a verifier could not be given source code, `why` stopped at the requirement, a rework hand-off was refused in a shared working copy, a security review was not part of a gate's evidence, `team init` rewrote the settings file, and the figure check could not read code. Two more while this report was being checked on the owner's machine: one test could not finish there, because the duplicate check parsed the system map about 1,300 times on a project of 25 specs (78 seconds, now 2), and its messages listed shared words in an order that changed from run to run. Twelve were not fixed and are now in `docs/limits.md`, under "Found by using it on a real change". The ones that matter most:

- A change that reaches the default branch without G5 and G6 is not reported as such. The owner's merge of the C4 change showed it.
- A review can only accept or return. Real reviewers want to accept with conditions.
- A threat the owner chooses to live with has nowhere to go.
- Records name commits by id, and ids do not survive a rebase, a squash, or being made again on another machine.
- A check that needs a pipeline fails for want of evidence and never says that no pipeline is running.

### What is still weak

- **The central promise has never been exercised live.** A gate is passed by a pull-request review that the kit mirrors and binds to evidence. That path is tested on recorded responses only. No review has been read from GitHub, no branch protection inspected, no agent token examined. For this reason two acceptance lines are met only on recorded responses, one is not met, and one more waits for a pipeline to run the kit on a project.
- **One model played every agent.** Author and reviewers were separated by session and by what they were given, not by model. They still disagreed usefully. Blind spots they share would not show.
- **Evidence is taken as given.** The test results for the C4 change come from a stand-in project. The records say so in every file because the author wrote that. The kit would have accepted the same numbers without the caveat.
- **It is a lot.** 105 checks, six extensions, 16 agents. For the C4 change the Regulated profile produced 39 files of record, about 2,500 lines, for 14 files of code and tests, about 1,250 lines. Whether that ratio is right for a Critical change to an audit trail is the owner's judgement. Lite exists so that it is not everyone's ratio; nobody has timed Lite.
- **Matching is by words.** Duplicates, the requirement lint, the instruction lint and the figure check all read text. Each misses what is said another way.
- **One repository, one person in every role.** Separation of duties has never been exercised, only recorded as an exception.

### What would raise confidence most, in order

1. One hour on a scratch GitHub repository: branch protection, a pull request, a review that carries a gate's line, the mirror, an agent token. It settles four acceptance lines.
2. A pipeline that runs in the healthcare repository. Every check there that waits on a build, a scan or a bill of materials waits on this, and so does task T005.
3. Reviews that can accept with conditions, and a place for an accepted risk.
4. Someone else installing Lite from the README with a clock running, once on Windows.

These are proposals. None was started.

## 6. What was run for this report

| What | Where | Result |
|---|---|---|
| `python -m pytest tests`, with clones of the reference and of the C4 branch | Workspace, Python 3.13 | 507 passed, in about three minutes |
| The same with an empty home directory, no proxy settings and no clones | Workspace | 505 passed, 2 skipped (the two tests that need a clone) |
| `agentic.py selftest` | Workspace | 105 fixtures as expected |
| `agentic.py golden run --fixture fixtures/multi-app` | Workspace | 10 of 10 in each mode |
| The kit's checks on the recreated C4 branch, compared with the original | Workspace, rehearsal copy | 80 pass, 23 fail, 1 not run on both; no line differs once ids are set aside |
| The kit's checks on the C4 branch, twice with different hash seeds | Workspace | The two outputs are the same byte for byte; 17 seconds each |
| `agentic.py why` on a changed line of the recreated branch | Workspace, rehearsal copy | Same work item, task, criteria and principle as on the original |
| The pins of the two actions in the pipeline files | `git ls-remote` against GitHub | Both tags point at the pinned commits |
| The new pipeline file against the kit's own rules | `test_the_kits_own_pipeline_follows_the_kits_own_rules` | Passes; fails when an action floats on a tag |
| The kit repository's pipeline, first run | GitHub Actions, on the owner's push of `6e217c2`; read from GitHub's public record of the run | Both jobs passed, every step: Python 3.13 in 2 minutes, Python 3.10 in 4. The second run, on `d26db20`, passed too |
| The healthcare `main` after the owner's merge | Fetched from GitHub into the workspace | `d78ffe7`. Its tree is the tree of the reviewed `sdd/showcase-proposals`. The three branch tips are in its history, so the ids in `commit-map.md` are the ids on GitHub |
| The kit's checks on that `main`, against `8d04df3` | Workspace | 79 pass, 24 fail, 1 not run. For spec 004: the same missing records for G1 to G3 as before the merge, and nothing about G5 or G6 |
| Workflows of the healthcare repository on the three pull requests and the merge | GitHub's public list of runs, read two minutes after the merge | None started except the hosted code review of each pull request. `pr-validation.yml` is triggered by a pull request to `main` and has no run |
| The three branches on the owner's machine | Owner's machine | Trees equal to the workspace's. His checkout (`main`, `6e0879d`), working tree and other branches unchanged. No lock file left |
| `python -m pytest tests`, in pieces that fit the three-minute limit for a command there | Owner's machine, Python 3.10, on a copy of the files on the virtual machine's own disk. The copy and the owner's folder have the same combined hash | 505 passed, 2 skipped |
| The same, in the owner's folder itself | Owner's machine, through the folder shared into the virtual machine | Stopped at 372 passed, none failed. One test cannot finish there: reading through the share is slow, and the test that takes 3 seconds on the local disk takes more than 90 |
| `agentic.py selftest`; `golden run` | Owner's machine, the same copy | 105 fixtures as expected; 10 of 10 in each mode |

The healthcare solution's own tests are not in this table. They have not run.

## 7. Decisions made without the owner, and how to reverse each

Numbering continues from the Phase 7 report, which ends at 82.

| # | Decision | Why | To reverse |
|---|---|---|---|
| 83 | Gave the kit repository a pipeline of its own: `.github/workflows/tests.yml`, read-only, no secret, on pull requests and pushes to `main` | An acceptance line asks that CI shows a failing fixture fail, and the kit that checks other people's pipelines had none. It ran on the owner's push and passed | Delete the file |
| 84 | The healthcare commits carry the name and address of the owner's own latest commit in that repository (`1b74f48`), which is his GitHub no-reply address | That repository has no identity configured where the commits were made, and the address configured in the kit repository is a personal one | Delete the three local branches and run `rebuild_from_bundle.py` again with another `--identity-of` |
| 85 | Ran `git fetch origin main` in the owner's healthcare repository | The branches stand on the merged state, `8d04df3`, which his clone did not have. It moved `origin/main` and nothing else | Nothing to reverse |
| 86 | Left the records that name workspace commit ids as they were, and added a map | The reviews and the evidence are what a decision is bound to. Editing 20 ids in them would have changed what the reviewers wrote | `examples/healthq/phase-7/commit-map.md` |
| 87 | Did not add the header to the guides and generated files that lack it | Their phase and requirement IDs would have been reconstructed, not known | Say which should carry it |
| 88 | Did not ask for GitHub API access to read pipeline runs | In this session that access comes with the right to push, which the owner kept for himself | Section 9 lists it as unverified |
| 89 | Changed kit code after the acceptance run: parsed YAML is kept by its text, and tied words are listed in alphabetical order | A test could not finish on the owner's machine, and the cause was the kit's. Every run in section 6 was made again after the change, except the stopped one | `Source.yaml` in `agentic_kit/core.py`; `cosine` in `agentic_kit_product/text.py` |

## 8. What waits on the owner

In the order that unblocks most.

1. **Build and test the healthcare `main`.** It now holds the C4 change, which no build has ever compiled. On a machine that can restore the packages: `dotnet build`, then `dotnet test tests/HealthQCopilot.Tests.Unit`. If it does not build, fix it on a branch, or put the 14 code and test files back as they were (`git checkout 8d04df3 -- src tests` on a branch, then a pull request). Reverting the merge of pull request #73 would also undo the governance update, which arrived with it.
2. **Find out why nothing runs in the healthcare repository's pipeline.** `pr-validation.yml` should have run on each of the three pull requests and did not start. The repository's Actions settings are the first place to look.
3. **Spec 004.** Seven amendments in `specs/004-audit-identity/amendment-proposed.md`; two clear failing checks. Then task T005 on a machine that can restore the solution's packages: the eleven existing audit tests at `8d04df3`, then `dotnet test tests/HealthQCopilot.Tests.Unit` on the branch, both recorded. Then T006, and reviews for G3 to G6.
4. **Nine draft specs** (017 to 025) at G1 and G2, and **three pairs** the kit lists as similar.
5. **Six draft plans** (001, 003, 004, 005, 006, 013) and the breakdown of 002, at G3 and G4. Amendments proposed in Phase 6 to specs 001, 002, 003, 005 and 007.
6. **The adoption baseline:** approve, change or reject `.specify/agentic/proposals/adoption-baseline.md`.
7. **Settings only an administrator can make:** branch protection, the agent's own GitHub identity, the routing policy (today it names one model for every class of agent).
8. **Observations O1 to O20** in the Phase 6 and Phase 7 reports. None has a spec. O11, O15, O17 and O18 bear most directly on who can reach patient data and whether that is recorded.
9. **The kit:** the twelve items under "Found by using it on a real change" in `docs/limits.md`, and decision 87. The first to fix is the missing rule for a change merged without G5 and G6.

## 9. Not verified

- Anything on live GitHub but one thing: a review, branch protection, a token's permissions, a pipeline that runs the kit on a project. The one thing is the kit repository's own test pipeline, which has run once and passed.
- The healthcare solution: restore, build, its own tests, analyzers, coverage, a bill of materials, any deployment.
- Any tracker, chat or mail service; Windows PowerShell; a migration on a database; an evaluation of the triage classifier.
- A model put through the planted-instruction tests, or working in parallel mode with the path guard.
- That the HIPAA pack's mapping of controls is right. It is an engineering aid and nobody qualified has reviewed it.
- Why the healthcare repository's workflows do not start. It was read from outside; its settings were not.
