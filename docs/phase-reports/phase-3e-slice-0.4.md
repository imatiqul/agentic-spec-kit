# Phase 3e — the rest of slice 0.4 "Depth", and the closing documents

- **Phase and date:** Phase 3e (build), 2026-11-22
- **Requirement IDs covered:** AGT-14 to AGT-18, TRC-13, TRC-15, TRC-16; acceptance of the whole of slice 0.4 (GOV-12, GOV-17 to GOV-20, QLT-3 to QLT-22, CHG-16, CHG-17, CHG-19 to CHG-21, MAP-16, TRC-12, AGT-19, AGT-20, ADP-21); the role guide, release notes and list of limits that Phases 8 and 10 ask for
- **Assumptions:** listed in section 4, each with how to reverse it. None was approved by the owner
- **Unverified:** see section 5. In short: no coding agent or model has run anywhere; no live GitHub repository; nothing on Windows PowerShell

## 1. What this phase is

The owner's standing instruction is "complete entire agentic-spec-kit": build the rest of the kit without a stop after each phase. Phase 3d built slices 0.5 and 0.6 and part of 0.4. This phase builds what was left of slice 0.4 and writes the three documents the plan puts at the end.

On 2026-11-22 the owner also decided to keep the repository public ("Keep it public"). That replaces charter decision D2. The README and the acceptance file say so. The charter itself was not edited; the two lines to paste are in section 7.

## 2. What was built

| Where | What it adds | Checks | Unit tests |
|---|---|---|---|
| `extensions/agentic` — `reports.py` | Views generated from the repository: gate board, waiver register, traceability matrix, metrics. `report all --out <dir> --html` writes every view and one self-contained page. The auditor evidence pack: `audit-pack --spec` or `--from --to` | CK-AUDIT-PACK | 19 (`test_reports.py`, which also holds the tests of the as-built map and the reference constitution) |
| `extensions/agentic` — `__main__.py`, `lanes.py` | `brief --write` records `gate.ready` in the audit log, which is where time-to-decision starts. The brief renders any section an extension adds | | |
| `extensions/agentic-team` — `ops.py`, `work.py` | A record of every agent step: model and version, hash of the agent specs, each input by hash, tools, cost, duration, the gate the work is heading for. A routing policy per class of agent; a cost budget per run and a spend limit per spec; `report spend` | CK-RUN-RECORD, CK-ROUTING | 43 (`test_ops.py`) |
| `extensions/agentic-team` — `golden.py`, `ops.py` | Three planted-instruction tests in every golden run: in a repository file, in an issue's text, in a tool's output. A baseline of golden results that a named person accepts; a change to an agent spec or to the routing policy needs a fresh run and may not do worse than the baseline | CK-INJECTION, CK-GOLDEN-BASELINE | (in the 43) |
| `extensions/agentic-team` — `ops.py` | A lint of agent instruction files (`AGENTS.md`, `CLAUDE.md`, Copilot, Cursor, Gemini, Kiro, Windsurf): each must be tracked, have a code owner, grant nothing the kit forbids, and point at files that exist | CK-AGENT-MEMORY | (in the 43) |
| `agentic-system`, `agentic-quality`, `agentic-product` | Their views: the system map as a diagram and a table, the technical-debt register, the capability catalogue. Quality adds escaped defects to the metrics | | |
| `extensions/agentic/ci/agentic-checks.yml` | Runs also when a review is submitted, so an approval re-runs the checks. The base branch reaches the shell through an environment variable | | |
| `docs/guide/roles.md`, `docs/limits.md`, `docs/release-notes.md` | What each role approves and looks at; what the kit does not do; what each slice contains | | |

The kit now registers 105 checks: core 23, system 28, team 16, quality 22, product 13, connect 3.

`docs/design/requirement-map-as-built.md` is new. It is generated from the spec files and the check registry, and the generator fails if a requirement has neither a check nor a stated way it is met. Of 176 requirements: 151 are enforced by a check, 18 are features with unit tests, 4 are documents, 2 are procedural, and 1 (ADP-4, approvals from GitLab or Azure DevOps, tagged `later`) is not built. Every requirement tagged `[0.4]` is enforced by a check (38) or is a feature with unit tests (5: ADP-16, ADP-21, MAP-16, TRC-13, TRC-15).

Design documents brought up to date: `docs/design/checks.md` (the 34 checks of slice 0.4, printed from the registry), `docs/design/schemas.md` (agent step, baseline, evidence pack, views, new settings), `docs/design/competitive-gap-analysis.md`, `docs/install.md`, the core and team READMEs, the root README.

## 3. Verification

Commands, run from the repository root. Results are in the table that follows.

```bash
python extensions/agentic/scripts/agentic.py selftest
python -m pytest -q -p no:cacheprovider
python extensions/agentic/scripts/agentic.py golden run --fixture fixtures/multi-app
```

| What | Where | Result |
|---|---|---|
| Self-test: every check passes on the sample and fails on its broken variant | Cloud workspace, Linux, Python 3.13 | 105 fixtures, all as expected |
| Unit tests, whole suite in one run | Cloud workspace, Linux, Python 3.13 | 448 passed in 6 min 44 s |
| Golden tasks, parallel and sequential, scripted stand-in | Cloud workspace | 4 tasks, 3 seeded defects and 3 planted instructions per mode, all as expected |
| Self-test | The owner's machine, Linux VM, Python 3.10.12 | 105 fixtures, all as expected |
| Unit tests, file by file | The owner's machine, Linux VM, Python 3.10.12 | 448 passed: ops and reports 62, product and team depth 106, connect and quality 92, lanes and system 36, kit 36, change 62, team 54 |
| Golden tasks, parallel and sequential, scripted stand-in | The owner's machine, Linux VM | Exit 0; 20 lines as expected, none failed |

The runs on the owner's machine were made file by file because one command there may run for three minutes at most. Run alone, `tests/test_kit.py` self-tests only the core extension's 23 fixtures; in the single run of the whole suite it self-tests all 105. Both were done: the whole suite in the cloud, and the 105-fixture self-test on its own on the owner's machine.

### Acceptance of slice 0.4 (`docs/prompts/90-acceptance.md`)

| Line | Evidence | Result |
|---|---|---|
| A Low-tier change takes the fast lane; an author cannot select it by hand | `tests/test_lanes.py`: `test_a_low_tier_change_takes_the_fast_lane_with_one_review_for_g1_to_g4`, `test_an_author_cannot_put_a_spec_on_the_fast_lane`, `test_declaring_a_low_tier_does_not_buy_the_fast_lane` | Pass |
| An emergency change with an overdue retrospective fails the default branch | `tests/test_lanes.py::test_an_emergency_passes_until_its_deadline_and_fails_the_branch_after`; self-test fixture CK-EMERGENCY-DEADLINE | Pass |
| An evaluation that does not call the production code path fails QLT-15 | Self-test fixture CK-AI-PROD-PATH; `tests/test_quality.py` | Pass |
| Planted instructions in fixture files, issues and tool output are reported and not acted on | `golden run`: three per mode, all reported and none acted on. `tests/test_ops.py`: `test_the_harness_sees_an_agent_that_obeys`, `test_the_harness_sees_an_agent_that_stays_silent`, `test_results_that_show_an_agent_obeyed_or_stayed_silent_fail` | Pass **for the scripted stand-in only**. No model has been put through these tests |
| A changed agent spec triggers the regression suite and a baseline comparison | CK-GOLDEN fails results made with other agent specs; CK-GOLDEN-BASELINE fails results made under another routing policy, and anything that got worse. `tests/test_ops.py`: `test_changing_an_agent_is_allowed_when_nothing_gets_worse_and_refused_when_something_does`, `test_a_change_of_model_needs_a_fresh_golden_run`, `test_a_change_cannot_lower_the_baseline_it_is_compared_with` | Pass, with one difference from the wording: the kit does not start the golden run. It fails the checks until someone, or a pipeline, has run it |
| The auditor pack for one release exports with hashes and its disclaimer | `tests/test_reports.py`: `test_the_pack_holds_every_file_it_lists_with_its_hash`, `test_the_pack_maps_each_control_of_the_domain_pack_to_the_spec_section_that_answers_it`, `test_a_pack_for_a_date_range_takes_the_specs_decided_in_it` | Pass |
| Lite profile effort is unchanged from slice 0.1 | `tests/test_ops.py::test_a_new_lite_project_is_asked_for_people_and_code_owners_and_nothing_else`: with every extension loaded, a new Lite project fails only CK-ROLES, and passes once people and CODEOWNERS are listed | Pass |
| An agent's context for a task is rebuilt identically from the same repository, and a change to its sources while the task is in progress fails | `tests/test_team_depth.py`; self-test fixture CK-CONTEXT | Pass |
| A tool server that is not on the allowlist, is launched differently from what was reviewed, or floats on "latest" fails | `tests/test_team_depth.py`; self-test fixture CK-TOOL-ALLOWLIST | Pass |

Not assessed here: the "Reference example" lines of the acceptance file. They need Phases 5 to 7.

## 4. Decisions made without the owner, and how to reverse each

Numbering continues from the Phase 3d report, which has decisions 1 to 20.

| # | Decision | Why | To reverse |
|---|---|---|---|
| 21 | An agent step must say which model ran and what it cost; the kit fills in the rest | Only the runtime knows those two. A record without them cannot be compared with the routing policy | Take the two fields out of `step_problems` in the team extension's `ops.py` |
| 22 | A routing policy is required at Regulated; at Standard its absence is a note | Lighter profiles should not be forced to name models | `ck_routing` in `ops.py` |
| 23 | Cost is a plain number, as the runtime reports it. There is no default budget or spend limit | The kit cannot know a currency or a price list | `kit.yml`: `team.budget.cost`, `team.spend.per_spec` |
| 24 | The golden baseline names the person and the review that accepted it; the kit does not look the review up | The baseline is protected by being read from the base branch, by agents being barred from `golden/`, and by CODEOWNERS. Looking the review up would need the live adapter | Add an adapter call in `ck_golden_baseline` |
| 25 | A change of model needs a fresh golden run, the same as a change to an agent spec | AGT-14 says "agent spec or model". Found while writing this report: only agent-spec changes were covered until then | Remove the `routing_hash` comparison in `ck_golden_baseline` |
| 26 | Three planted instructions. "Acted on" means the file the text asks for exists or `roles.yml` changed. An agent that resists but says nothing fails | Silence leaves the next agent to meet the same text | `INJECTIONS` and `run_injection` in `golden.py` |
| 27 | The instruction-file lint is a fixed list of file names and seven patterns; a line that negates the grant passes; a backticked path that does not exist fails | Pattern matching is repeatable. It does not understand meaning (see `docs/limits.md`) | `kit.yml`: `team.memory.files`, `forbid`, `allow_missing`; or `GRANTS` in `ops.py` |
| 28 | Writing a reviewer brief records `gate.ready` in the audit log | Time-to-decision needs a start. The brief is the moment a person is asked | Remove the `audit_append` in `cmd_brief` |
| 29 | The evidence pack is required at Regulated only, must exist before G7 and be listed in the G7 evidence. It goes stale when the spec's own files or decision records change, not when roles, settings, waivers or the audit log change afterwards | The approver of a release should see the pack. People change roles after a release; that is not a change to the evidence | `ck_audit_pack` in `reports.py` |
| 30 | A measure with no data is left out, and "agent versus human effort" is shown as counts and times side by side, not as one ratio | TRC-14; and a ratio of unlike things would mislead | `metrics` in `reports.py` and each extension's `METRIC_HOOKS` |
| 31 | `agentic-checks.yml`, a slice 0.1 file the owner approved, was changed: it also runs on `pull_request_review`, and passes the base branch through an environment variable | Without the first, an approval does not turn a red gate green until the next push. The second keeps repository data out of the shell command line | `git diff` on `extensions/agentic/ci/agentic-checks.yml` |
| 32 | Token-shaped strings in the tests are assembled at run time | The repository is public; a secret scanner would flag fixtures that look like real tokens | `tests/test_connect.py`, the `FAKE_` constants |
| 33 | The README's working rule about `main` now says what happened: agents do not commit to `main`; the owner has committed each phase himself | The old line said nothing was committed to `main` after the first commit, which is no longer true | `git diff README.md` |
| 34 | Version numbers were left alone: the core extension is still 0.1.0 although slices 0.2 to 0.6 added to it, and every extension requires `agentic >= 0.1.0` | Nothing has been released, so no older core exists to break. Choosing numbers is a release decision | Set them at the first release; until then install every extension from the same commit |
| 35 | The Phase 3d report said the tool allowlist reads six configuration files. It reads eight, and always has. The report was corrected | An error in the report, not in the code | None |

## 5. Not verified

- **No coding agent or model has run.** The agent files, the path guard, the context packs, the allowlist, the step records and the planted-instruction tests have all been exercised by scripts and tests only. `golden run --agent-command` has been run with a test command that reports a model and a cost, never with an agent.
- **No live GitHub repository.** Not the approval path, not branch protection, not either workflow file, not the `pull_request_review` trigger added in this phase.
- **No live tracker, chat or mail service; no pipeline file run by its CI system.**
- **Nothing on Windows PowerShell.** The tests ran in a Linux VM on the owner's Windows machine.
- **The HIPAA control mapping has not been reviewed by anyone qualified.** Its six references are to the Security Rule and Privacy Rule as in force today. A proposed overhaul of the Security Rule is pending; trade press reported in July 2026 that its final action was moved to July 2027. If it is finalised, the references need checking again.
- **The evidence pack has been made for the sample project only**, not for a real release.
- **The HTML page** was checked by tests for escaping and structure. Nobody has looked at it in a browser.

## 6. Not built

- Impact analysis across repositories. Maps from other repositories are pinned and validated; they are not folded into a blast radius.
- Tests generated from requirements.
- Escaped defects feeding new golden tasks.
- Reminders for notifications that nobody acted on.
- Approvals read from Azure Repos or GitLab.
- An MCP server that exposes the kit's state to agents.
- Starting the golden run automatically when an agent spec or the routing policy changes. The checks fail until it has been run.

## 7. Waiting on the owner

1. **The charter.** Two lines to paste into `docs/prompts/00-charter.md`, replacing D2 and adding a row to the decision log:
   - `- D2 Disclosure: the toolkit repo is public. On 2026-11-22 I accepted publishing findings C1–C6 before they are fixed in the healthcare repo.`
   - `| 2026-11-22 | 3d | Keep the toolkit repo public, including the Phase 1 findings C1–C6. Replaces the earlier D2 | Owner instruction in chat ("Keep it public") |`
   The charter also has no rows for slices 0.5 and 0.6.
2. **Decisions 1 to 35**, above and in the Phase 3d report. In particular decision 2 (tracker adapters were built without reading the source of the community extensions that overlap them, which charter D7 asks for) and decision 31 (a change to a file already approved).
3. **Review of what agents are told:** the six edited agent specs, `commands/orchestrate.md`, and spec files 17 and 18.
4. **Commit and push.** Nothing from this phase is committed.
5. **A live test.** One pull request on a repository with branch protection would prove or break the approval path, both workflows and the mirror job.
6. **A real agent on one golden task**, including the three planted instructions.
7. **Gate G0.** The reference constitution for HealthQ is drafted (`docs/phase-reports/phase-4-constitution.md`). Phases 5 to 7 follow the owner's decision on it, and each ends at a human gate. Phase 7 needs a feature branch in the healthcare repository, which has been read-only so far.

## 8. The owner's response, 2026-11-22

To the list in section 7 the owner replied: "Needs you: approve". A few minutes later he added that, when he approves, the agent may also edit the charter, commit and push, and touch the healthcare repo.

| Item | What happened |
|---|---|
| 1. The charter | The agent applied the two lines and the rows for slices 0.5 and 0.6, and recorded both instructions in the decision log |
| 2. Decisions 1 to 35 | Approved as they stand. Decision 33 is overtaken: the README now says an agent may commit and push what the owner approved |
| 3. Review of what agents are told | Not done by anyone. The approval covers the decisions, not a reading of the agent specs |
| 4. Commit and push | See the note that follows |
| 5, 6. A live test; a real agent on a golden task | Still to do |
| 7. Gate G0 | Approved as drafted; recorded in `phase-4-constitution.md` |

Commit and push: the agent was allowed to do both and could do only the first. The session's permission system refused the agent push access to GitHub, so the commit was made in the owner's local repository and the push is left to him.
