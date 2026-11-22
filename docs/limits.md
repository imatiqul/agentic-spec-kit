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

## Never run

As of 2026-11-22 none of the following has happened, so everything that depends on it is unproven:

- a pull request, a review or branch protection on a live GitHub repository;
- a real coding agent using the agent files, the path guard, a context pack or the allowlist;
- any tracker, chat or mail adapter against its live service;
- any of the three pipeline files in its CI system;
- the install or any command on Windows PowerShell;
- a migration applied to a database.
