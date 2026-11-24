# Phases 8 to 10: the showcases, the acceptance lines, and a second look at the whole kit

- **Phase and date:** Phases 8 to 10, the halves that needed the reference; 2026-11-22
- **Upstream and reference:** spec-kit `v1.4.3`; healthcare repository `imatiqul/azure-ai-cloud-healthcare`, `main` at `8d04df3`
- **Requirement IDs exercised:** GOV-6, GOV-9, GOV-17, GOV-20, TRC-16, TRC-19, QLT-2, QLT-4, QLT-12, QLT-15, AGT-10
- **Assumptions:** an acceptance line is judged against the words in `docs/prompts/90-acceptance.md`. Where a line was shown with a scripted stand-in or a recorded response and not with the real thing, it says so and is counted apart
- **Unverified:** no gate of the reference has been passed. The healthcare solution was not built or tested. The owner merged the healthcare branches into `main` with no gate review; he built it and ran its unit tests afterwards; the agent read his results files and did not see the runs. No pipeline has run the kit on a project. Section 9 has the full list

The owner's instruction was to finish everything, look at it again, and wait; he pushes. This report is the end of that. Nothing in it is an approval.

**Updated the same day, after the owner pushed the kit's `main` (`6e217c2`).** The kit repository's pipeline ran for the first time on that push and passed on Python 3.10 and 3.13 (run 45093366953). One acceptance line moved from "in part" to "met"; the places that said the pipeline had not run are changed, and nothing else is. 

**Updated again that evening, after the owner merged the reference work.** He pushed the three branches, opened pull requests #73, #74 and #75 against `main` (not stacked, not as drafts) and merged all three within a minute, with merge commits. `main` of the healthcare repository is now `d78ffe7`, and its files are exactly those of the reviewed `sdd/showcase-proposals` branch: the two trees are the same. What the merge does not change:

- **No gate is passed.** No review carried a gate's line and no decision record exists. The acceptance line about C4's gate decisions stays not met.
- **The C4 change is on `main` and has still not been built or tested.** No workflow of that repository ran on the pull requests or on the merge. `pr-validation.yml` is triggered by a pull request to `main` and did not start; only the hosted code review did.
- **The kit did not notice.** Its checks on `main` (79 pass, 24 fail, 1 not run) report the same three missing gate records as before the merge. It has no rule for a change that reaches the default branch without G5 and G6. That is now in `docs/limits.md`.

Sections 1, 6, 8 and 9 are changed to match; the acceptance counts are not.

**Later that evening: the merged `main` was built and tested, and seven packages were updated.**

- **`dotnet build` on the merged `main` stopped at restore**, with 147 errors. None came from the merge, which changed no project or package file. NuGet's audit reported ten packages with advisories published since the repository's suppression list was last looked at, and the build treats warnings as errors. Nothing had told anyone: no pipeline runs there.
- **With the audit switched off for the run (`-p:NuGetAudit=false`), the owner built the solution and ran the unit test project on `main` at `d78ffe7`, and reported that both passed.** That is the first build of the C4 change with the solution's own packages, analyzers and settings. The output was not captured, so no count is recorded here, and the other half of task T005, the eleven old tests at the base commit, was not run.
- **Seven of the ten packages were moved to versions with no advisory** (healthcare pull request #76, merged by the owner; `main` is `2a8f516`). The versions were chosen from GitHub's advisory database and could not be restored where the change was written. On the owner's machine the unit test project then restored with the audit on and no message, and resolved the intended versions; that was read from its `project.assets.json`. He reported that the build and the tests passed.
- **Three remain, all Aspire 9.3.0**, one of them critical. The only patched version is 13.6.5, a major upgrade of the application host. Until it is made, a restore of the whole solution fails the audit on the two application-host projects.

Sections 1, 8 and 9 are changed again to match.

**And then the test run was captured.** The owner ran the two commands of task T005 with a results file each, and the agent read the two files in his folder.

- **The unit test project on `main` at `2a8f516`: 520 tests, 520 passed.** Among them are all 80 tests of the C4 change.
- **The eleven old audit tests at the base commit `8d04df3`: 11 passed.**

The stand-in runs of Phase 7 had reported the same 80 and the same 11. T005 is recorded through the kit and handed off (`specs/004-audit-identity/evidence/unit-tests.md`; the owner merged it into `main` as pull request #77, `d429369`). It waits for a reviewing agent; T006, the verification repeated on these results, has not started. The characterization check now passes for spec 004.

The kit's checks on `main` now also say that 18 project files changed outside any work item and that a shared component changed with no recorded run of its consumers. Both are right: the package update of pull request #76 was made outside the kit's process, at the owner's request.

**Late that night: the verification was repeated on the real results, one record turned out to name nobody, and the kit got the rule the merge had shown to be missing.**

- **An independent verifier went through the record of the test run, and then through the change again.** It returned the record once: two sentences said more than the results files show. It accepted the corrected record and repeated its verification on the real results (round 3 of `specs/004-audit-identity/verification/G6-report.md`). On those results it finds AC-001, AC-003 and AC-006 shown; AC-002 and AC-004 shown at the middleware and not through a service; AC-005 shown for the check and not for "the build must fail". Of its fourteen earlier findings six are closed, five stay open and three are open in part. Six are new. The first of them says what the kit had not said: the change is on `main` and no gate of the spec has a decision, and the merge came 43 minutes before the first real test run. T005 is done. T006, the verification, is handed off and waits for a reviewing agent other than the verifier, and for the owner at G6.
- **The verifier's own list of what it read breaks the kit's rule for verifier inputs.** To see what had been compiled it read nine project and build-setting files, and listed them. The check on its inputs now fails on that list. Whether a verifier may read build settings is the owner's to decide.
- **The record of that review named nobody.** The review command had been run without `--by`, and the kit wrote "a person with no name" as the one who returned T005 and then accepted it: in the work item, and in two lines of the audit log. No check noticed. Neither did the agent that read the verifier's report and carried the records to the owner's machine; it was found some hours later, when the records were brought into this repository. The reviewer was the verifier agent, and no person reviewed anything. The kit now refuses a review that names nobody, or somebody the project does not know, and the check that an author does not review their own work fails on a record like this one. The log can only be added to, so a fourth run in it says who the reviewer was. The work item still has the empty name, and that check fails on it until a person corrects the file. The change all this is the record of exists because an audit record named nobody.
- **The gate check now reports work that is ahead of its gates.** Once work on a spec's tasks shows in the tree (a ticked task, a work item that is done or was handed off, a commit that names one), it asks for G4 on any branch, and on the default branch also for G5 and G6. On the reference's merged `main` it reports G4, G5 and G6 for spec 004, where it had reported G1 to G3 only. It reports after the merge and does not hold a merge back. That, and how the check knows which branch is the default one, are in `docs/limits.md`.
- **The Aspire upgrade is drafted** as a branch for the owner to build: the application host from 9.3.0 to 13.6.5, the first version without the two advisories. It could not be restored or built where it was written. The owner pushed the branch and merged it the same night as pull request #78, fifteen seconds after opening it; `main` of the healthcare repository is `0ecb2a2`. No workflow of the repository ran on it, and whether it was built before the merge is not known here. It found one more thing in the reference: the host starts each of the eight front-end apps with `npm run start`, and none of them has a `start` script.
- **The README now explains the kit with diagrams**, for someone who is new to it, and `docs/guide/workflow.md` has more. Each diagram was checked against the code and the commands. That found two more things, both now in `docs/limits.md`: the gate views show G4 as open again when a task is ticked off, and the check for code that changes with no spec is skipped in every pipeline the kit ships.

Sections 1, 5, 6, 7, 8 and 9 are changed to match. No acceptance line moved.

**On 2026-11-23, at the owner's request: skills for two coding agents, a way into the README for every engineer, and the documents' commands run on a fresh clone for the first time.**

- **Three skills for Claude Code and GitHub Copilot are in `.claude/skills/`**, in the open Agent Skills format: a tour of the sample, the install, and an independent review that works in any repository. One copy serves both tools, because GitHub's documentation names `.claude/skills` among the folders GitHub Copilot reads; that was read and not tried. The specification's reference validator accepts all three. No coding agent had loaded them when this note was written; the next note says what the owner then ran.
- **The core extension has a ninth command, `/speckit.agentic.guide`**: where a change stands, what is needed next and from whom, and which command to run. On Spec Kit 1.4.3 the install was seen to write it, with the other commands, to `.claude/skills/` in a project with the `claude` integration and to `.github/skills/` in one with the `copilot` integration. Every command of the kit's CLI that it names was run in a new Lite project.
- **The README has three sections ahead of its diagrams**: a way in by what you want, by role, and by coding agent. The table by role was taken from `docs/guide/roles.md`.
- **The documents' commands were run as written on a fresh clone of the public `main` (`7ad074a`)**, the five commands on the sample and the self-test in a Python environment that held only PyYAML, and the install into three new Spec Kit projects, one for each profile. The install could not be run as `docs/install.md` wrote it: the script had no executable bit in the repository, and the clone refused it with "Permission denied". The working copy the kit was built in has the bit, which is why nobody had seen it. The documents now call the script through `bash`, and the bit is set. The acceptance line "a new engineer installs the kit from the README alone" stays "in part": this was the author's agent on a clone, not a new engineer.
- **Three things it showed are not fixed** and are in `docs/limits.md`: a traceback when the list of checks is piped into a command that stops reading, two notes of one check that read wrongly, and that nothing checks the skills and the command files against the CLI.

Section 1 is changed to match. No acceptance line moved, and no count in sections 4 to 6 changed: no check, test or fixture was added.

**Later on 2026-11-23: the owner pushed that commit and ran one skill in both tools.**

- **The kit's `main` on GitHub is `c4a2129`.** The repository's pipeline ran on the push and passed on Python 3.10 and 3.13 (run 45328487459).
- **He ran `/agentic-spec-kit-try` in Claude Code and in GitHub Copilot**, in his clone on Windows, and said so. The agent saw neither session, and what they printed is not on record. What the agent could read is bytecode left in that clone: the kit's CLI ran there under Python 3.12 for Windows that evening. That is the first trace of the CLI running on Windows.
- **Still not run in a coding agent:** the other two skills, the commands the install adds to a project, and the agent files.

The places that said no coding agent had loaded the skills now say this, and section 1 is changed to match. No acceptance line moved.

**Later still on 2026-11-23: two faults found on the fresh clone were fixed, each with a test.**

- **A command whose reader stops early ends with exit code 141 and no traceback.** Before, `agentic.py list | head` ended in a Python traceback and exit code 1, and so did `check` and `doctor`, for which 1 is the code of a failed check. It was tried on Linux, with a reader that had already gone and ten times with `head`. Windows can report a closed pipe as another error; how the kit handles that is simulated in a test and has not been tried there.
- **The three notes of CK-AGENT-SPEC read as sentences.** They were read from `check` in a new Lite project set up with the commands of `docs/install.md`.

While this was being written the owner pushed `666e895`, the commit of the note before this one, and the repository's pipeline passed on it. Sections 1 and 6 are changed to match. No acceptance line moved. Four tests were added; no check or fixture was.

## 1. Where everything is

| What | Where | State |
|---|---|---|
| The kit: six extensions, 105 checks, 16 agents, three pipelines | `imatiqul/agentic-spec-kit`, `main` | Pushed by the owner up to `666e895`, which holds the record of his two runs of the first skill; the repository's pipeline passed on it. The two fixes of the last note are a later local commit, for the owner to push |
| Governance for the reference: constitution version 2, the map, 25 specs, six draft plans, the agent team | Healthcare repository, branch `sdd/reference-plans` (`89a4fc9`) | Merged into `main` by the owner (pull request #74). Still waits at G1 and G2 (nine specs), G3 and G4 (six plans) |
| The C4 change: 14 code files, 80 tests, 39 files of record | Branch `sdd/004-audit-identity` (`1e8d054`), on the branch above | Merged into `main` by the owner (pull request #73). Built and unit-tested by him afterwards: 520 of 520 passed, read from his results file. The record of that run is reviewed and the verification is repeated on it. Still waits on seven amendments, a review of that verification by an agent other than the verifier, and gate reviews |
| Proposals: adoption baseline, threat model and authorization matrix for C2, the setting that shows H4 | Branch `sdd/showcase-proposals` (`a44c57c`), on the branch above | Merged into `main` by the owner (pull request #75). Nothing in it is approved or enforced: the baseline is still a proposal outside the folder the kit reads |
| The verification repeated on the real results, the review of the test record, and the correction to that review's record | Healthcare repository, branch `sdd/004-verification-3b` (`ba610d9`). It holds `sdd/004-verification-3` (`edab4ec`) and one commit more | On the owner's machine. Not pushed |
| The Aspire upgrade of the application host, 9.3.0 to 13.6.5 | Healthcare repository, branch `deps/aspire-13` (`22f9440`) | Merged into `main` by the owner (pull request #78, `0ecb2a2`). Not restored or built where it was written; no workflow ran on it; whether the owner built it is not known here |
| Titles and descriptions for the three pull requests, and for the two branches made later | `examples/healthq/phase-7/pull-requests.md` | Text for the owner to paste |

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
- **The kit is cheap to run.** 531 tests, 105 fixtures and 20 golden results pass offline: in about four minutes in the workspace, and on the owner's machine.

### What using it on real work showed

Twenty-six things, none visible from the fixtures. Ten were fixed with a test each (`docs/release-notes.md`). Six of them in Phase 7: a verifier could not be given source code, `why` stopped at the requirement, a rework hand-off was refused in a shared working copy, a security review was not part of a gate's evidence, `team init` rewrote the settings file, and the figure check could not read code. Two more while this report was being checked on the owner's machine: one test could not finish there, because the duplicate check parsed the system map about 1,300 times on a project of 25 specs (78 seconds, now 2), and its messages listed shared words in an order that changed from run to run. Two more on the night of the merge: the gate check had no rule for work that reaches the default branch without G5 and G6, and a review that named nobody was written down as a person's. Sixteen were not fixed and are in `docs/limits.md`, under "Found by using it on a real change", with four points more that say what those last two fixes leave open. The ones that matter most:

- Work that reaches the default branch without G5 and G6 is reported after the merge, not held back. The owner's merge of the C4 change showed that the rule was missing; the rule that was added reports on the default branch only.
- A review can only accept or return. Real reviewers want to accept with conditions.
- A threat the owner chooses to live with has nowhere to go.
- Records name commits by id, and ids do not survive a rebase, a squash, or being made again on another machine.
- A check that needs a pipeline fails for want of evidence and never says that no pipeline is running.

### What is still weak

- **The central promise has never been exercised live.** A gate is passed by a pull-request review that the kit mirrors and binds to evidence. That path is tested on recorded responses only. No review has been read from GitHub, no branch protection inspected, no agent token examined. For this reason two acceptance lines are met only on recorded responses, one is not met, and one more waits for a pipeline to run the kit on a project.
- **One model played every agent.** Author and reviewers were separated by session and by what they were given, not by model. They still disagreed usefully. Blind spots they share would not show.
- **Evidence is taken as given.** The first test results for the C4 change came from a stand-in project. The records say so in every file because the author wrote that. The kit would have accepted the same numbers without the caveat. The owner's later run of the real solution gave the same counts; the kit took those as given too.
- **It is a lot.** 105 checks, six extensions, 16 agents. For the C4 change the Regulated profile produced 39 files of record, about 2,500 lines, for 14 files of code and tests, about 1,250 lines. Whether that ratio is right for a Critical change to an audit trail is the owner's judgement. Lite exists so that it is not everyone's ratio; nobody has timed Lite.
- **Matching is by words.** Duplicates, the requirement lint, the instruction lint and the figure check all read text. Each misses what is said another way.
- **One repository, one person in every role.** Separation of duties has never been exercised, only recorded as an exception.

### What would raise confidence most, in order

1. One hour on a scratch GitHub repository: branch protection, a pull request, a review that carries a gate's line, the mirror, an agent token. It settles four acceptance lines.
2. A pipeline that runs in the healthcare repository. Every check there that waits on a build, a scan or a bill of materials waits on this.
3. A decision on whether a pull request into the default branch should fail until G5 and G6 are recorded. Today the gate check says so only after the merge.
4. Reviews that can accept with conditions, and a place for an accepted risk.
5. Someone else installing Lite from the README with a clock running, once on Windows.

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
| The healthcare unit test project, and the eleven old audit tests at the base commit | Owner's machine, run by the owner after this report was first written. The agent read the two results files | 520 of 520 passed at `2a8f516`, among them the 80 tests of the change. 11 of 11 passed at `8d04df3` |
| `python -m pytest tests`, with both clones, after the changes of the last note | Workspace, Python 3.13 | 531 passed, in about three minutes |
| `agentic.py selftest`; `golden run`, after those changes | Workspace | 105 fixtures as expected; 10 of 10 in each mode |
| The same three, after those changes | Owner's machine, Python 3.10, on a copy of the files on the virtual machine's own disk. The copy and the owner's folder have the same combined hash | 529 passed, 2 skipped (the two tests that need a clone); 105 fixtures as expected; 10 of 10 in each mode |
| The gate check with the new rule on the healthcare `main` (`d429369`), against `8d04df3` | Workspace, two clones: one with that commit checked out as `main`, one where it has another name beside an older `main` | As `main`: G4, G5 and G6 reported for spec 004, with or without a base. Under the other name: G4, and a note that the branch could not be told; with `--branch main`, all three. The whole run there: 77 pass, 26 fail, 1 not run, as before the rule, because the gate check failed already |
| The kit's checks on the branch with the repeated verification and its correction, checked out as `main` | Workspace | 75 pass, 28 fail, 1 not run. New against `d429369`: the nine verifier inputs, and the two lines that say T005 was returned and accepted by a reviewer the record does not name |
| The kit repository's pipeline on `c8534a5`, the commit with the changes of the last note | GitHub Actions, on the owner's push; read from GitHub's public record of the run | Passed (run 45116965577) |
| Healthcare pull request #78, the Aspire upgrade | GitHub's public record, read just after the merge | Opened at 23:36:47 and merged at 23:37:02 on 2026-11-22 (UTC-6). `main` is `0ecb2a2`. No workflow of the repository started; only the hosted code review did |
| The versions of the Aspire upgrade | NuGet's version lists and package descriptions; GitHub's advisory database; the Aspire source at the tag `v13.6.5` | Each version exists. No advisory is listed for `Aspire.Hosting`, the dashboard package for Windows or MessagePack at the new versions; the same question for 13.6.4 returns the advisory. The two methods the host now calls are in the source with the arguments used. Nothing was restored or built |
| The kit repository's pipeline on `c4a2129`, the commit with the skills | GitHub Actions, on the owner's push; read from GitHub's public record of the run | Passed on Python 3.10 and 3.13 (run 45328487459) |
| The same on `666e895`, the commit that records the owner's two runs of the first skill | GitHub Actions, on the owner's push; read from GitHub's public record of the run | Passed on Python 3.10 and 3.13 (run 45331917091) |
| `python -m pytest tests`, with both clones, after the two fixes of 2026-11-23 | Workspace, Python 3.13 | 535 passed, in about three minutes |
| `agentic.py selftest`; `golden run`, after those fixes | Workspace | 105 fixtures as expected; 10 of 10 in each mode |

No other test project of the healthcare solution has run.

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
| 90 | Made the review of a work item refuse a missing name and a name the project does not know, and made CK-AUTHOR-NEQ-VERIFIER fail on a record whose reviewer is not named | The kit had written "a person with no name" as the reviewer of T005 and said nothing. An unknown name had been written down as a person | `review` and `transition` in `agentic_kit_team/work.py`; `ck_author_neq_verifier` in `agentic_kit_team/checks_team.py` |
| 91 | Appended the correction to the reference's audit log as a fourth run, on a new branch that holds the earlier one, and left the work item as the kit wrote it | The log can only be added to, and a work item may be written only by a kit command or a person. The correction says who the reviewer was; it does not rewrite who the record named | Push `sdd/004-verification-3` and not `sdd/004-verification-3b`. To correct the work item by hand instead: set `reviewer_agent` and the two empty `by` values in `T005.yml` to `independent-verifier` |
| 92 | The new gate rule asks for G5 and G6 on the default branch only, does not ask for G7, counts any finished task or work item as work on the spec, and leaves the shipped pipeline files as they were | On a pull request the work is still in progress; a release may be decided after a merge; two specs may claim one file, so changed files are not used. The agent that built the rule made these choices and wrote them down; they were kept | `ck_gate_record` and `on_default_branch` in `agentic_kit/checks_gov.py`. The choice that most needs the owner: whether a pull request into the default branch should fail until G5 and G6 are recorded |
| 93 | In the Aspire upgrade: the host keeps taking the dashboard and the orchestrator from NuGet and silences the new warning ASPIRE010; the front-end apps keep running `npm run start` with no install step; the Redis client package in the service defaults stays at 9.3.0 | The first keeps the build free of an installed Aspire CLI, as it was. The second keeps the command the host ran before, although no app has a `start` script: changing what the host starts is another change. The third has no advisory | The branch is one commit: change it or drop it |

## 8. What waits on the owner

In the order that unblocks most.

1. **Build `main` of the healthcare repository, which now holds the Aspire upgrade.** Pull request #78 moved the application host to 13.6.5 and was merged at once. It was not restored or built where it was written: `dotnet restore`, `dotnet build` and the application-host tests on the owner's machine are the test, and if he ran them before merging, nothing here records it. If the restore fails, `git revert -m 1 0ecb2a2` takes the upgrade out again and nothing else. Still to push: `sdd/004-verification-3b` in the healthcare repository, which holds the repeated verification and the correction to its record.
2. **Find out why nothing runs in the healthcare repository's pipeline.** `pr-validation.yml` should have run on each of the three pull requests and did not start. The repository's Actions settings are the first place to look.
3. **Spec 004.** Seven amendments in `specs/004-audit-identity/amendment-proposed.md`; two clear failing checks. A review of T006, the repeated verification, by a reviewing agent other than the verifier. A decision on whether a verifier may read build settings (finding V-20: the check on its inputs fails on its own list). The name of T005's reviewer in the work item, which only a person may write. Then reviews for G3 to G6.
4. **Nine draft specs** (017 to 025) at G1 and G2, and **three pairs** the kit lists as similar.
5. **Six draft plans** (001, 003, 004, 005, 006, 013) and the breakdown of 002, at G3 and G4. Amendments proposed in Phase 6 to specs 001, 002, 003, 005 and 007.
6. **The adoption baseline:** approve, change or reject `.specify/agentic/proposals/adoption-baseline.md`.
7. **Settings only an administrator can make:** branch protection, the agent's own GitHub identity, the routing policy (today it names one model for every class of agent).
8. **Observations O1 to O20** in the Phase 6 and Phase 7 reports. None has a spec. O11, O15, O17 and O18 bear most directly on who can reach patient data and whether that is recorded.
9. **The kit:** the twenty points under "Found by using it on a real change" in `docs/limits.md`, and decisions 87 and 92. The first to decide is whether a pull request into the default branch should fail until G5 and G6 are recorded, so that a protected branch cannot be merged without them. Today the gate check reports it after the merge.

## 9. Not verified

- Anything on live GitHub but one thing: a review, branch protection, a token's permissions, a pipeline that runs the kit on a project. The one thing is the kit repository's own test pipeline, which has run once and passed.
- The healthcare solution's unit tests were run by the owner. The agent saw the two results files, not the runs. Its integration, architecture and evaluation tests, coverage, a bill of materials and any deployment have not run at all.
- Any tracker, chat or mail service; Windows PowerShell; a migration on a database; an evaluation of the triage classifier.
- A model put through the planted-instruction tests, or working in parallel mode with the path guard.
- That the HIPAA pack's mapping of controls is right. It is an engineering aid and nobody qualified has reviewed it.
- Why the healthcare repository's workflows do not start. It was read from outside; its settings were not.
- The Aspire upgrade, which is on `main` of the healthcare repository since pull request #78. Its versions and the methods it calls were checked against NuGet, the advisory database and the Aspire source. Where it was written it was not restored, built or run, and no pipeline ran on it.
- The new gate rule in a pipeline. What git says about the branch in each CI system's clone was tried on clones made by hand.
- That the reviewer of T005 was the verifier agent is known from the run that made the review and from its two review steps in the same log, not from the two lines that name nobody.
