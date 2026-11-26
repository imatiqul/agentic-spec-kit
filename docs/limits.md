# What the kit does not do

- **Phase and date:** closing documents, 2026-11-22
- **Requirement IDs covered:** QLT-2, GOV-8, AGT-10, AGT-15, AGT-17, INT-5, TRC-16
- **Assumptions:** none
- **Unverified:** see "Never run", at the end

A tool that governs agents is only useful if you know where its guarantees stop. This page is that list.

## It cannot make an approval trustworthy on its own

- Approvals are read from GitHub pull-request reviews. If the default branch is not protected, anyone with push rights can merge without one, and no check here can stop it. `agentic.py doctor` reports what is missing; an administrator has to fix it (`docs/admin-setup.md`).
- The file adapter, used in tests and offline demos, proves nothing about who approved. Anyone who can write the repository can write its file. `agentic.py demo` shows a gate close and open again with it, in a throwaway project, and says the same at its start and at its end.
- The kit does not stop a person pushing to the default branch. It fails the checks afterwards.
- Approvals made in Azure Repos or GitLab merge requests are not read.

## It does not run your tools

- The quality checks require the record that a scanner, an evaluation, a migration or an accessibility tool ran, bound to the files it ran on. They do not run the tool. A record someone wrote by hand for a run that never happened is a lie the kit cannot detect; the commands tell agents never to write one.
- The software bill of materials, test results and scan reports are read as given.

## It cannot see inside an agent

- **Isolation of the verifier is procedural.** The verifier is given only the artefact, the spec, the constitution and the map. Nothing technical stops a runtime from sharing more.
- **Who did a step is what the command was told.** `work claim`, `work handoff` and `work review` take a name as an argument. The kit holds the name to what the work item and the team say: the item's owner claims it and hands it off, and a reviewer is a reviewing agent of the team or a person in the roles file, and never the author. It cannot check that whoever ran the command is the one it names.
- **Which model ran and what it cost are reported by the runtime.** The kit requires them and compares them with the routing policy. It cannot prove them. The same holds for the golden tasks: the results record which routing policy was in force when they ran, not proof that the agent command used the models it names.
- **The golden baseline names the person and the review that accepted it.** The kit checks that the person is in `roles.yml` and the reference is well formed. It does not look the review up. The baseline is protected by being read from the base branch, by agents being barred from `golden/`, and by CODEOWNERS on `.specify/`.
- **The path guard works where the runtime has an event before each tool call, and judges file-writing tools only.** A shell command that writes a file is not parsed. Such a write, and any write on a runtime with no such event, is caught at hand-off and in CI, after it was made.
- **The planted-instruction tests ship with a scripted stand-in.** That proves the test detects an agent that obeys or stays silent. Whether a model resists is shown only by running the tests with a real agent.
- **The tool allowlist covers MCP servers in eight known configuration files** (and any a project adds under `team.tools.files`). It does not cover a tool an agent installs for itself at run time, a shell command, or a server configured outside the repository.
- **The instruction-file lint is a list of patterns.** It finds "you may push to main". It does not understand an instruction that says the same thing another way.

## It matches words, not meaning

- Duplicate detection compares vocabulary. Two requirements that say the same thing in different words score as unrelated. Agents and people add those candidates; the kit then insists each one is decided.
- The requirement lint catches "should", "quickly" and two obligations in one sentence. It does not know whether a requirement is right, complete or wanted.
- The glossary check finds a listed synonym. It does not find a new one.
- Discovery reads what its adapters know: .NET projects and their references, Node packages, Compose files, a .NET Aspire application host, contract files, and Dapr publish and subscribe calls in C# whose topic is a literal or a choice between literals. A topic built at run time is not seen, and neither is messaging through any other library. The drift check can only be as complete as discovery.
- Impact analysis follows the map. From a touched component it reaches everything that depends on it, what it owns, and the events it publishes with their subscribers. It does not know that a particular change leaves a particular event alone, so it reaches further than the change does; a plan says what is really affected.
- The pinning check reads images where they are written out: workflow, Compose and Kubernetes files, container files, and the `AddContainer("name", "image", "tag")` calls of a .NET Aspire application host, with `WithImageTag` and `WithImageSHA256` on the same statement. An image named through a variable, built from parts, or set by any other code is not seen.
- The check for figures with no source reads the files a project lists (`metric_claims.scan`; the README when nothing is listed). In prose it sees a percentage on a line that names a measure. In code and data it also sees a number given to a name that contains a measure word, such as `accuracy = 0.94`. A figure computed at run time, shown under another name, or written in a file that is not listed is not seen; and a name such as `precision` that means something else is, until the project allows that line.
- The trace from a line (`why`) rests on the commit that last changed it. A commit that names its work item gives the task, its criteria and its spec. Without that, the trace lists every spec that claims the file, by its paths, its task list or the components it says it touches, which can be several.

## It records; it does not certify

- The evidence pack supports an audit. It does not certify compliance with any law, regulation or standard.
- The HIPAA pack is an engineering aid. It is not legal advice.
- A waiver is a recorded, owned, expiring exception. The kit checks that it exists and has not expired, not that it was wise.
- The audit log records what was done through kit commands. An edit made by hand, a push, or a tool call the kit never saw is not in it. The log's hash chain reveals an entry that was edited or removed. It cannot show that nothing was left out, and someone able to rewrite the whole file can rebuild the chain; review of every change under `.specify/` by a code owner is what guards against that.

## Things it leaves to you

- Notifications are sent once per event. There is no reminder.
- Sealing a finished change keeps its files. Nothing is deleted.
- Federated maps from other repositories are pinned and validated, and a programme spec can span repositories. Impact analysis does not yet fold those maps in, so a provider's blast radius stops at this repository's edge.
- Tests are not generated from requirements.
- There is no MCP server that exposes the kit's state to agents.

## Found by using it on a real change, and not fixed

Phase 7 took one change of the reference system through the kit, and the closing checks ran the kit on a second machine. Ten things this showed were fixed (`docs/release-notes.md`). The ninth is the check for work that reaches the default branch without G5 and G6; the first three points below are what it leaves open. The tenth is that a review of a work item must name who made it; the point about the audit log, further down, is what that leaves open. These were not:

- **Work that reaches the default branch without G5 and G6 is reported after the merge, not held back.** On a pull request the gate check asks for G4 and what precedes it, because work in progress is legitimate there. So a required check does not stop a merge for want of G5 and G6; the default branch fails afterwards. The check reads the records as they are now: a decision recorded after the merge satisfies it.
- **The gate check knows the default branch by the name in `kit.yml`.** If that name is wrong, a caller who passes the real one with `--branch` is read as work in progress; left to git, the check says it cannot tell, as long as no branch has the wrong name. Another long-lived branch, such as a release branch, reads as work in progress. So does a clone that has the default branch checked out under another name with an older `main` beside it, unless something says otherwise. The rule was tried on the reference's merged `main` in such a clone. Compared with the commit before the merges, which that clone's `main` does not hold, the check says it cannot tell. Compared with a branch or with nothing, it says nothing about G5 and G6. `--branch main` settles it. A feature branch compared with a commit of its own past gets the same "cannot tell"; `--branch` with its name quiets that. Where the check cannot tell, it leaves a note, and someone who reads only the count of passes does not see the note.
- **The gate check sees work on a spec's tasks by its marks only.** A ticked task, a work item that is done or was handed off, a commit in the range being checked that names a work item. Code merged with none of these is not seen, and a commit is seen only by the run whose range holds it. A task ticked because the work already existed reads as started work, and a work item that only records evidence counts like one that changes code. A spec merged in parts is asked for G5 and G6 when the first part arrives. An open emergency excuses its retrospective spec as a whole: the check does not ask whether the work on the branch is the emergency's change.
- **A threat the owner decides to live with has no place in the threat model.** Each threat names the criterion that tests it, and that criterion has to be marked as an abuse case. The only other way through is a waiver on the whole check.
- **A review has two outcomes, accept and return.** A reviewer who accepts and still wants something changed later can only say so in prose. In Phase 7 a reviewer wrote "accept" over a list of required changes, and had to be asked which it was.
- **A step's duration is the time between two commands.** When work is recorded after it was done, the duration is that of the recording. The kit cannot tell the difference.
- **The tests-first rule is invisible in sequential mode.** Nothing records which of two tasks was written first when one session does both.
- **A file at the root of the repository is not read as a path in a task line.** A path needs a folder in it. `README.md` in a task is prose to the parser.
- **Records name commits by id.** A change that is rebased, squashed, or made again under another identity keeps its files and loses its ids, and every record that names one then points at history that was not pushed. The work-item trailer in a commit message survives; the `base:` of a work item and an id quoted in a review do not. `examples/healthq/phase-7/commit-map.md` is such a case, mapped by hand.
- **CK-TOUCH passes when it is given nothing to compare.** Without a base to compare with or a list of changed files it looks at no file and passes, with a note that the comparison was skipped. Someone who reads only the count of passes does not see the note.
- **Impact analysis does not follow `writes`.** A component that writes to a data store or an event stream is reached when the store is touched; touching the writer does not reach the store's readers through it.
- **The index of files to components can be wrong in ways no check sees.** The reference map indexed client code to the external system it calls. A change to that code then reads as a change to something the project does not own.
- **Run from a linked git worktree, the kit writes its records into the repository's main working copy.** It treats a linked worktree as an isolated copy of one work item, which is what its own parallel mode makes. Someone who uses `git worktree` for their own reasons and runs `work claim` there finds the run, the work item and the audit entry in another checkout, on whatever branch that one has.
- **The check for characterization tests compares against a spec's `paths` only.** For a spec that names components and no paths it cannot tell whether the tests ran before the code changed, and says so in a note that blames a missing base ref.
- **A check reads the same file many times.** What it parsed is kept; the read is not, because a command may write a file and read it again. On a slow disk this shows: in a folder shared into a virtual machine, the duplicate check on 25 specs took more than 90 seconds where it takes 3 on a local disk.
- **A check that needs a pipeline fails for want of one, and says nothing about why.** In the reference, nothing has run in CI since May 2026. The kit reports the missing test run, bill of materials and scan as missing evidence. It does not report that no pipeline is running.
- **A wrong line in the audit log stays in it.** The log can only be added to. Two lines of the reference's log say that a person with no name returned a work item and then accepted it. It was a reviewing agent: the review command had been run without `--by`, and at that time it did not refuse. A later run in the same log says who it was. Nothing ties that correction to the two lines but its words, and no check reads it. The work item has the same empty name. Only a person can correct that file, because the kit has no command for it, so the check that an author does not review their own work fails on it until someone does.
- **The rule for what a verifier may read does not allow build settings.** In its third round the verifier of the reference change read nine project and build-setting files, to see what had been compiled and with which packages. It listed them, and the check on its inputs then failed on its own list. The rule allows the artifact, the spec, the constitution and the map. Whether build settings belong with them is not decided.
- **The gate views and the amendment check disagree about a ticked task.** `gate` and `report gates` compare every evidence file of a gate. The task list and the trace manifest are evidence of G4, so ticking a task off, or building the manifest again when test results arrive, shows G4 as open again and the gates after it as later. The amendment check leaves progress marks and generated files out on purpose and says nothing changed. Found when the diagrams in the README were checked against the commands.
- **The check for code that changes with no spec does not run in the pipelines the kit ships.** CK-DRIFT-SPEC needs a list of the files that changed (`--changed-files`). The shipped pipeline files pass a base ref and no such list, so there the check is skipped in every run, with a note.

## Found by following the documents on a fresh clone, and not fixed

On 2026-11-23 the commands of the README and of `docs/install.md` were run as written on a fresh clone of the public repository, for the first time. Three things this showed are corrected (`docs/release-notes.md`): the install script could not be run as the documents wrote it, a command whose reader stopped early ended in a Python traceback, and two notes of CK-AGENT-SPEC read wrongly. These were not:

- **A reader that stops early is handled as far as it was tried, which is on Linux.** A command whose output goes to a program that stops reading, as in `agentic.py list | head`, ends with exit code 141 and no traceback. Windows can report a closed pipe as another error than Linux does. The kit treats that error the same way when standard output can no longer be flushed; a test simulates this, and it has not been tried on Windows. On any system the command cannot know of a reader that stops after its last write, and `--help` written to a reader that has gone still ends with 0.
- **Only this repository's own tests compare the skills, the command files and the guides with the CLI, and they compare names.** A test reads every command line written in them and fails when one names a command, an action, a view or a flag the CLI does not have. It does not check what a command does or prints, and it does not see a sentence that describes a command without writing it out. A project that installs the kit gets the command files and not this test: a copy that is edited there is compared with nothing.

## Found by a newcomer's walk on 2026-11-25, and not fixed

On 2026-11-25 the documents were followed on a fresh clone as a new team would follow them: the tour, the Lite install into a new project, and one small spec taken to an open gate. It ran on Linux, and the coding agent's steps were done by hand (`docs/phase-reports/phase-11-adoption-barriers.md`). What it found in the documents is corrected (`docs/release-notes.md`). These were not:

- **A newer Spec Kit fails the first `doctor`.** `init` writes `speckit: "1.4.3"` into `kit.yml` whatever is installed, and on 1.4.5 `CK-UPSTREAM-PIN` fails. The install guide now gives the line for the pinned release. Nothing decides which later releases the kit accepts.
- **Nothing says who opens the pull request, or from which account.** No document says how to give the coding agent an account of its own.
- **An approver who runs `doctor` under their own login gets a failure.** With the GitHub adapter the kit takes the account behind the token in use to be the agent's. Where that account is listed in `roles.yml`, `CK-ENFORCE-SETUP` fails, and on that machine `CK-APPROVER` reads that person's reviews as the agent's own. Read in the code and seen with the file adapter. Not run on GitHub.
- **One person with one account cannot pass a gate on GitHub.** The checks accept a review only in the state `APPROVED`, and GitHub does not let the author of a pull request approve it. `gates.single_approver_exception: allowed` covers a reviewer who is among the authors of the commits, which helps only when another account opened the pull request. Where one person holds every role, `doctor` does not warn of this. Read, not run.
- **The long form of `record` writes whatever it is given.** It does not look the review up; the checks do, afterwards. Since 2026-11-26 `record --change pull/<n>` reads the reviews itself, and writes nothing when none carries the line. It has read reviews from the file adapter only, never from GitHub.
- **In Lite, a record nobody could verify reads as `approved`.** Where GitHub cannot be read, `CK-APPROVER` and `CK-GATE-MIRROR` do not run. Lite treats that as a warning, so `check` ends with 0, and the gate board shows `approved` for a record whose review nobody looked up. The pipeline is where it fails.
- **`gate` cannot tell whether a commit was pushed.** Since 2026-11-26 it lists the evidence files that are not committed. A commit that exists only on the author's machine looks to it like one that was pushed.
- **There is no release.** The repository has no tag, the install needs a clone and points Spec Kit at folders inside it, and no document says how to move a project to a newer kit.
- **In a Lite project with nobody listed, `CK-ROLES` asks for people at G0** as well as at G1, G3 and G5. Lite has three gates.

## Never run

As of 2026-11-22 none of the following has happened, so everything that depends on it is unproven:

- a pull request, a review or branch protection on a live GitHub repository;
- a coding-agent runtime (Claude Code, GitHub Copilot) loading the rendered agent files, the path guard on that runtime's events, or the allowlist against real tool servers. One model has worked one change through the sequential mode, with a context pack for each task and a separate session for each of the two reviewing agents (`docs/phase-reports/phase-7-c4-walkthrough.md`); that is the only use by a model so far;
- Claude Code or GitHub Copilot running two of the three skills in `.claude/skills/`, `agentic-spec-kit-install` and `agentic-spec-kit-review`, or the commands the install adds to a project (added 2026-11-23). The third, `agentic-spec-kit-try`, was run by the owner in Claude Code and in GitHub Copilot on 2026-11-23, in his clone on Windows. Since that run the tour skill has gained a last step, the demo (2026-11-26), and the install skill a few lines (2026-11-25). No coding agent has run either skill as it is now, and the added lines were not checked with the reference validator. The agent that wrote the skills saw neither session, and what they printed is not on record. It has his word, and bytecode left in that clone, which shows that the kit's CLI ran there under Python 3.12 for Windows that evening. That GitHub Copilot reads `.claude/skills/` was taken from GitHub's documentation; his session, in a clone that keeps the skills nowhere else, is the only trial of it. The three skills were checked with the reference validator of the Agent Skills specification and every command they name was run by hand. On Spec Kit 1.4.3 the install was seen to write the commands to `.claude/skills/` for the `claude` integration and to `.github/skills/` for the `copilot` integration;
- any tracker, chat or mail adapter against its live service;
- any of the three pipeline files the kit ships, in its CI system. So what git says about the branch in each system's clone, which the gate check relies on there, has been tried on clones made by hand and not in a run. This repository's own `.github/workflows/tests.yml` has run: first on the owner's push of 2026-11-22, where it passed on Python 3.10 and 3.13. It runs the kit's tests. It is not the kit running on a project;
- any pipeline of the reference system: no workflow of that repository has run since May 2026. Its unit tests were run by the owner on his machine on 2026-11-22, after the reference change had been merged: 520 of 520 passed, read from his results file. Its other test projects have not run. From where the change was written the package registry could not be reached;
- the install on Windows, by either script, and any command on Windows PowerShell as far as the record shows. The first trace of the kit's CLI running on Windows is the bytecode of 2026-11-23 named above; the shell it ran in is not on record. A workflow for a Windows runner was added on 2026-11-26, with a test that walks the install through both scripts (`docs/design/windows-job.md`). It has not run;
- `agentic.py demo`, added on 2026-11-26, on Windows or by a coding agent. It was run by hand and by its tests, on Linux;
- a migration applied to a database.
