# Release notes

- **Phase and date:** closing documents, 2026-11-22
- **Requirement IDs covered:** all slices; see `docs/design/requirement-map.md` and each phase report
- **Assumptions:** none
- **Unverified:** see `docs/limits.md`, "Never run"

Nothing here has been released. These notes say what each slice contains, so a reader can tell what they are installing. Counts are from the code on 2026-11-22: 105 checks, each with a passing and a failing fixture.

## 0.1 Govern — `extensions/agentic`
Roles, gates G0 to G7, three profiles, risk tiers, waivers and the adoption baseline, the trace manifest, the hash-chained audit log, drift detection, and decisions mirrored from pull-request reviews and bound to a hash of the evidence. 18 checks.

Added to it in slice 0.4: the fast lane, the emergency lane, amendments that re-open only the gates they affect, the one-page reviewer brief (CK-LANE, CK-EMERGENCY-DEADLINE, CK-AMENDMENT, CK-BRIEF), the report views, and the auditor evidence pack (CK-AUDIT-PACK). 23 checks in all.

## 0.2 System — `extensions/agentic-system`
A system map of services, data stores, contracts, shared components and external systems, with discovery, impact analysis and reviewers derived from what a change touches. Change packs for data stores, contracts, shared components, external dependencies and the supply chain. 28 checks.

## 0.3 Team — `extensions/agentic-team`
Sixteen agents described once and rendered for Claude Code, GitHub Copilot and a sequential mode. Work items with a state machine, path locks, isolated working copies, a rework limit, run budgets, a path guard, and golden tasks with seeded defects. 9 checks.

Added to it in slice 0.4: context packs, the tool allowlist, run records, routing and spend, the golden baseline, planted-instruction tests and the instruction-file lint. 16 checks in all.

## 0.4 Depth — `extensions/agentic-quality`, and the additions above
Quality packs that switch on from a spec's tier and what it touches: threat model and security evidence, privacy impact, test depth, AI evaluation and safety, infrastructure and release readiness, decision records and the incident loop. 22 checks.

## 0.5 Truth — `extensions/agentic-product`
Intake records, requirement linting, a glossary, living capability specs fed by deltas and rebuilt by replay, duplicate detection decided by a Product Owner, outcomes, sealing, and lineage from a line of code. 13 checks.

## 0.6 Connected — `extensions/agentic-connect`
Requirements from Azure DevOps, Jira, ClickUp, GitHub Issues and Projects, and documents. One pipeline command, with files for GitHub Actions, Azure Pipelines and GitLab CI. Review mirroring. Notifications to Slack, Teams, email and the originating work item. 3 checks.

## Since the slices, from using the kit on the reference project
- The pinning check (CK-PIN) reads the containers a .NET Aspire application host starts, and treats a tag that ends in `-latest` as floating. Before, finding N8 of the reference (two floating tags in such a file) was one the kit could not see.
- Writing a reviewer brief that has not changed no longer adds a second `gate.ready` entry to the audit log.
- Discovery finds Dapr event topics in C#, with who publishes and who subscribes, reading calls that name their arguments across lines. The reference map had been drawn without two publishers, and a reviewer caught it; the drift check could not have.
- Impact analysis reaches the events a touched component publishes, and their subscribers. Before, a change to a publisher did not reach the services that act on its events.
- A Critical change plans its rollback rehearsal at G3 and shows it at G7. Before, the check asked for the rehearsal's evidence as soon as a plan existed, which no plan could have.
- A Critical change's test strategy answers for each external system it may rely on: a resilience test, or a stated reason why the change does not rely on it. Systems the spec lists under `depends_on` are included and cannot be reasoned away; a placeholder no longer passes.
- The independent verifier may be given the code it verifies in a project that says what a spec touches by component. The artifact is the paths the spec's task list names and the files of the components it says it touches; the verifier may also read the files of what the spec says it depends on. Before, only paths written in the spec's front matter counted, so a spec that names components could not list a single source file.
- `why <file>:<line>` goes back to the principle and forward to what the change reaches: the task's criteria (read from the task list), the requirements, the principles the spec is held to, the component the file belongs to, what the spec touches and depends on, and the data stores, contracts, shared components and applications it reaches. A commit that names a work item settles which spec is shown.
- `team init` changes only its own block of `kit.yml`. Before, it rewrote the file and the comments in it were lost.
- The check for figures with no recorded source (CK-METRIC-PROVENANCE) reads code and data files a project lists, and there treats a number given to a name such as `accuracy` or `aiAccuracyRate` as a figure. Before, it read percentages in prose only, so it could not see finding H4 of the reference: accuracy figures written into an endpoint.
- A work item that comes back for rework in a shared working copy is no longer blamed for what others wrote in the meantime. Taking the rework up records what is there at that moment; the hand-off then lists only what the author changed after it. Before, the hand-off of a returned item was refused as soon as any other item had been handed off or a reviewer had written a report.
- What a reviewing agent writes for a gate (`specs/<spec>/reviews/G5-security.md`) is part of that gate's evidence, so a decision is bound to the findings as well. Before, a security review sat beside the evidence, and a gate could be approved on a hash that did not include it.
- A YAML file is parsed once in a process and every caller gets its own copy. Before, a check parsed a file each time it asked for it: on the reference, with 25 specs, the duplicate check parsed the system map about 1,300 times and took 78 seconds. It takes 2 now, the checks on a branch of the reference take 17 seconds, and the kit's own tests take about three minutes where they took nearly eight.
- The duplicate check lists the words two requirements share in the same order in every run. Before, words of equal weight came out in whatever order the run gave them, so two runs on the same files could print different messages.
- The gate check (CK-GATE-RECORD) asks for G4 once work on a spec's tasks has started, and on the default branch also for G5 and G6, as far as the spec's profile and lane have them. Work shows as a ticked task, a work item that is done or was handed off, or a commit that names one, and each finding says which it found. Which branch it is comes from git where the project is a repository of its own, as it is in a pipeline's full clone, or from the caller with `--branch`; where neither can say, the check says so in a note and names what it did not ask for. Before, the check asked for G1 to G3 only: when the owner merged the reference change with no review, the checks on `main` reported the same three missing records as before the merge.
- A review of a work item must name who made it, and the name must be a reviewing agent of the team or a person in the roles file. No state of a work item changes without a name. The check that an author never reviews their own work (CK-AUTHOR-NEQ-VERIFIER) fails on a record whose reviewer is not named, because nothing then shows that it was not the author. Before, `work review` run without `--by` wrote "a person with no name" into the work item and the audit log, and no check said anything: in the reference, one work item was returned and accepted that way. A name the project does not know was written down as a person.

## Added on 2026-11-23, at the owner's request
- Three skills for Claude Code and GitHub Copilot, in `.claude/skills/`, in the open Agent Skills format. `agentic-spec-kit-try` gives a first tour on the sample project. `agentic-spec-kit-install` installs the kit into a Spec Kit project and walks a person through what only people do. `agentic-spec-kit-review` is an independent review of a change from the diff and the requirement alone, and works in any repository. One copy serves both tools: GitHub's documentation names `.claude/skills` among the folders GitHub Copilot reads. The three were checked with the specification's reference validator. The owner ran the first, `agentic-spec-kit-try`, in Claude Code and in GitHub Copilot the same day. No coding agent has run the other two.
- A ninth command of the core extension, `/speckit.agentic.guide`: where a change stands, what is needed next and from whom, and which command to run. The install puts it with the other commands, in `.claude/skills/` or `.github/skills/` according to the project's Spec Kit integration.
- The README has three sections ahead of the diagrams: a way in by what you want, by role, and by coding agent. Its long status paragraph is now under "Status in detail".
- The install script is called through `bash` in every document, and is marked executable in the repository. Before, the documents called it by its path, and a fresh clone refused it with "Permission denied": the file had no executable bit. Found on 2026-11-23, when the documents' commands were first run on a fresh clone of the public repository.
- The documents say that the gate's line stands on a line of its own in the review. The check has always required that. The documents said only that the review contains the line.

## Fixed on 2026-11-23, after the documents were followed on a fresh clone
- A command whose output goes to a program that stops reading, as in `agentic.py list | head`, ends with exit code 141 and no traceback. Before, it ended in a Python traceback and exit code 1, which for `check` and `doctor` is the code of a failed check. 141 is what a shell reports for a program stopped by a closed pipe. Under `set -o pipefail` it fails the step, so a run that was cut short does not read as a pass. Tried on Linux; `docs/limits.md` says what is open on Windows.
- The notes of CK-AGENT-SPEC say in a sentence how each runtime enforces write paths. Before, the notes for GitHub Copilot and for the sequential mode read "paths are enforced not enforced by the runtime; the diff check after the run" and "paths are enforced the diff check after the run (and the event script, where the integration supports events)". `team list` prints the same three texts.
- A test compares every command line written in the skills, the command files and the guides with the CLI's own parser. It fails on a command, an action, a view or a flag the CLI does not have. On the day it was added it read 73 command lines in the 22 skills and command files and 94 in 17 guides, and found nothing wrong. It compares names only; `docs/limits.md` says what it does not see.

## Changed on 2026-11-25, after a newcomer's walk on a fresh clone
- The README's "Try it" makes a virtual environment first, and installs PyYAML alone. Before, it opened with `pip install pyyaml pytest`, which Ubuntu 24.04's own Python refuses with `error: externally-managed-environment`. The kit's own tests are now a line after the self-test, for those who want them.
- `docs/install.md` has a section "Before you start": the line that installs Spec Kit at the pinned release, `specify init`, and `git init`. Before, no document gave any of the three. The skill `agentic-spec-kit-install` says the same.
- `docs/install.md`, the command `/speckit.agentic.guide` and the command `/speckit.agentic-team.orchestrate` say that the reviewer's brief is committed and pushed with the rest of the evidence before anyone reviews. Before, a brief that was written and not committed changed the line that `gate` prints, and nothing said so.
- These are changes to documents and to two command files. No check changed, and no command of the CLI. `docs/phase-reports/phase-11-adoption-barriers.md` is the report of the walk, with every command and its output beside it. `docs/limits.md` lists what the walk found that is not fixed.

## Added on 2026-11-26: a demo of one gate
- `agentic.py demo` writes a small Lite project into a temporary folder and shows three things there with the kit's own commands. An approval by the agent's own account fails `CK-APPROVER`. An approval by a person listed in `roles.yml` passes `CK-APPROVER`, `CK-GATE-MIRROR` and `CK-GATE-RECORD`, and the board shows the gate approved. An edit to the approved spec opens the gate again. The demo reads and writes nothing in the folder it is run from, and deletes its own unless `--keep` is given.
- In that project a file plays GitHub: the file adapter. It proves nothing about who approved, and the demo says so at its start and at its end. It is not the first real gate on a live repository. That has still not happened.
- After each step the demo compares what the kit printed with what the demo says the kit does, and ends with 1 when the two differ. Nine tests run it, each named after an acceptance criterion of `docs/design/demo.md`. That spec was committed before the code.
- The README's first day ends with the demo, and so does the skill `agentic-spec-kit-try`. It was tried on Linux, by hand and by its tests. No coding agent has run it.

## Added on 2026-11-26: the install walked by a test, and a Windows job that has not run
- `tests/test_install_walk.py` does the install as a newcomer does it, with the real Spec Kit: `specify init`, the install script, `init`, `team init`, one person in `roles.yml`, `doctor`, `check`, `selftest`, and one spec taken to an open gate. It uses `install.ps1` through PowerShell on Windows and `install.sh` through bash elsewhere, and both where both shells exist. It is skipped where `specify` is not installed, which is the case in `tests.yml`. On Linux with Spec Kit 1.4.3 its five tests pass.
- `.github/workflows/windows.yml` runs the unit tests, the self-test, the golden tasks and the demo on a Windows runner, with Spec Kit installed, so the walk runs there through both install scripts. It has not run. It starts when a branch other than `main` is pushed, or by hand, and it stays off `main` until it has passed once. `docs/design/windows-job.md` is its spec, committed before it.
- Nothing here makes the kit work on Windows. It is how the first failures there will be seen.

## Added on 2026-11-26: `record --change`, and a warning from `gate`
- `record --spec <spec> --gate <gate> --change pull/<n>` reads the reviews of the pull request and takes the decision, the commit, the reviewer and the role from the review that carries the gate's line for the evidence as it stands. It writes nothing, and says why, when no review carries the line, when a needed role is not covered, or when `--decision` or `--commit` says something else than the review. Before, all five values were copied by hand. The long form still works, and still writes whatever it is given.
- `gate` lists the evidence files that are not committed, and says that a reviewer sees only what is committed and pushed. Its exit code is unchanged. In a folder that is not a git repository it prints what it printed before.
- No rule changed. `CK-APPROVER`, `CK-GATE-MIRROR` and `CK-GATE-RECORD` judge a decision record as before, and a record is still only a mirror. `connect mirror` reads the reviews through the same function and does what it did.
- Fourteen tests, each named after an acceptance criterion of `docs/design/record-finds-review.md`. The spec was committed before the code. Three criteria and their tests came after it, for what the code already did and no test had tried: an approval with conditions is not mirrored until each condition is given, reviews on different commits are not mirrored into one record, and a reviewer who also wrote the change is named. The reviews in the tests come from the file adapter: none of this has read a review on GitHub.

## Installing
`bash scripts/install.sh <project> <lite|standard|regulated>` installs `agentic` and `agentic-team` for every profile, and the other four for Standard and Regulated. Lite is unchanged by slices 0.2 to 0.6.

## Known gaps
`docs/limits.md`.
