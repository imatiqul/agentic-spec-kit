# What the kit does not do

- **Phase and date:** closing documents, 2026-11-22
- **Requirement IDs covered:** QLT-2, GOV-8, AGT-10, AGT-15, AGT-17, INT-5, TRC-16
- **Assumptions:** none
- **Unverified:** see "Never run", at the end

A tool that governs agents is only useful if you know where its guarantees stop. This page is that list.

## It cannot make an approval trustworthy on its own

- Approvals are read from GitHub pull-request reviews. If the default branch is not protected, anyone with push rights can merge without one, and no check here can stop it. `agentic.py doctor` reports what is missing; an administrator has to fix it (`docs/admin-setup.md`).
- The file adapter, used in tests and offline demos, proves nothing about who approved. Anyone who can write the repository can write its file.
- The kit does not stop a person pushing to the default branch. It fails the checks afterwards.
- Approvals made in Azure Repos or GitLab merge requests are not read.

## It does not run your tools

- The quality checks require the record that a scanner, an evaluation, a migration or an accessibility tool ran, bound to the files it ran on. They do not run the tool. A record someone wrote by hand for a run that never happened is a lie the kit cannot detect; the commands tell agents never to write one.
- The software bill of materials, test results and scan reports are read as given.

## It cannot see inside an agent

- **Isolation of the verifier is procedural.** The verifier is given only the artefact, the spec, the constitution and the map. Nothing technical stops a runtime from sharing more.
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

Phase 7 took one change of the reference system through the kit, and the closing checks ran the kit on a second machine. Eight things this showed were fixed (`docs/release-notes.md`). These were not:

- **A change that reaches the default branch without G5 and G6 is not reported as such.** The gate check asks for G1 and G2 once a plan exists and for G3 once a task list exists. It has no rule that says the code of a spec is on the default branch while its build and verification gates have no decision. In the reference the owner merged the C4 change with no review; on `main` the kit reports the same three missing records as before the merge. Where branch protection makes the kit's check a required one, those three failures are what would hold the merge back; here nothing required the check, and that path has never been exercised.
- **A threat the owner decides to live with has no place in the threat model.** Each threat names the criterion that tests it, and that criterion has to be marked as an abuse case. The only other way through is a waiver on the whole check.
- **A review has two outcomes, accept and return.** A reviewer who accepts and still wants something changed later can only say so in prose. In Phase 7 a reviewer wrote "accept" over a list of required changes, and had to be asked which it was.
- **A step's duration is the time between two commands.** When work is recorded after it was done, the duration is that of the recording. The kit cannot tell the difference.
- **The tests-first rule is invisible in sequential mode.** Nothing records which of two tasks was written first when one session does both.
- **A file at the root of the repository is not read as a path in a task line.** A path needs a folder in it. `README.md` in a task is prose to the parser.
- **Records name commits by id.** A change that is rebased, squashed, or made again under another identity keeps its files and loses its ids, and every record that names one then points at history that was not pushed. The work-item trailer in a commit message survives; the `base:` of a work item and an id quoted in a review do not. `examples/healthq/phase-7/commit-map.md` is such a case, mapped by hand.
- **CK-TOUCH passes when it is given nothing to compare.** Without a base to compare with or a list of changed files it looks at no file and passes, with a note that the comparison was skipped. Someone who reads only the count of passes does not see the note.
- **Impact analysis does not follow `writes`.** A component that writes to a data store or an event stream is reached when the store is touched; touching the writer does not reach the store's readers through it.
- **The index of files to components can be wrong in ways no check sees.** The reference map indexed client code to the external system it calls. A change to that code then reads as a change to something the project does not own.
- **A check reads the same file many times.** What it parsed is kept; the read is not, because a command may write a file and read it again. On a slow disk this shows: in a folder shared into a virtual machine, the duplicate check on 25 specs took more than 90 seconds where it takes 3 on a local disk.
- **A check that needs a pipeline fails for want of one, and says nothing about why.** In the reference, nothing has run in CI since May 2026. The kit reports the missing test run, bill of materials and scan as missing evidence. It does not report that no pipeline is running.

## Never run

As of 2026-11-22 none of the following has happened, so everything that depends on it is unproven:

- a pull request, a review or branch protection on a live GitHub repository;
- a coding-agent runtime (Claude Code, GitHub Copilot) loading the rendered agent files, the path guard on that runtime's events, or the allowlist against real tool servers. One model has worked one change through the sequential mode, with a context pack for each task and a separate session for each of the two reviewing agents (`docs/phase-reports/phase-7-c4-walkthrough.md`); that is the only use by a model so far;
- any tracker, chat or mail adapter against its live service;
- any of the three pipeline files the kit ships, in its CI system. This repository's own `.github/workflows/tests.yml` has run: first on the owner's push of 2026-11-22, where it passed on Python 3.10 and 3.13. It runs the kit's tests. It is not the kit running on a project;
- the tests, the build or any pipeline of the reference system: its package registry could not be reached from where the reference change was written, and no workflow has run in that repository since May 2026;
- the install or any command on Windows PowerShell;
- a migration applied to a database.
