# Phase 12: one change, seen whole

- **Phase and date:** Phase 12 (features); 2026-11-26. Not a phase of the original plan, which ends at 10
- **What this is:** what the owner asked for, what the kit had and lacked, what was built, how it was reviewed and merged, what was run, and what is his to decide
- **Assumptions:**
  1. On 2026-11-26 the owner brought a public post about another spec-driven tool, called Intent, whose unit of work is a "changeset". He asked which of its features the kit lacks and for a plan, and then asked for the features to be built in parallel and tested on the reference project with GitHub. This report covers the build. The test on GitHub had not started when it was written; its last section says where that test stands.
  2. Nothing of that tool was installed or used. What is said of it comes from the post, in my words.
  3. Questions the owner did not answer were decided as recommended. Each such decision is listed in its feature's spec as his to change, and the ones that matter most are at the end of this report.
- **Unverified:** nothing of Phase 12 has read GitHub, a tracker or a chat service. No coding agent has used any of it. When this was written, none of it had run on Windows: the pull request that brings it is its first run there. (Added later on 2026-11-26: that run happened; see the end of "What was run".)
- **Who "I" is:** the session that planned the phase, wrote two of the pieces and merged the rest. Five other agents each built one feature.

## What was asked, and where the kit stood

The post lists ten things its tool keeps or does for one change. Against `main` as it was that morning:

| # | The post's tool | The kit before | The kit now |
|---|---|---|---|
| R1 | Everything about a change is one object | In the repository, in seven places; no page showed one change whole | `changeset`: one page, built from those seven places |
| R2 | The conversation that started it | The request was kept; the discussion was not | A summary that a person confirms, links, and a count and a hash of an item's comments |
| R3 | Decisions, each with an owner and an outcome | Six kinds of decision had a record; a choice made inside a change had none | A decision log for each change, part of the evidence of G5 |
| R4 | Specs versioned against the code | Had it | The page lists each version and the decisions made on it |
| R5 | A plan for each repository | Programme specs plan it; a parent could not see its children | The parent's page shows where each child stands |
| R6 | The repositories indexed for search | No search | `search`, ordered by the system map; no index |
| R7 | The branches and pull requests | Recorded in three places; nothing put them together | A ledger of commits, branches and pull requests, on the page |
| R8 | Nothing to reconcile | By design the kit does not replace the tracker | Unchanged; R2 and R3 close the gap that mattered |
| R9 | In the repository | Had it | Unchanged |
| R10 | Through MCP | The kit was not an MCP server | A read-only MCP server, as an optional extension |

A first reading had R5 as missing. The kit already had programme specs (MAP-14, `CK-PROGRAMME`), so feature 7 became a view and no more.

The specs of this phase call its plan `phase-12-changeset-gap-analysis`, or "the Phase 12 review", and number its proposals 1 to 7. That plan is in the owner's project notes and not in this repository. The table above carries what matters of it, and the proposals are the rows of the next table, in this order: 1 and 4 the page with its branches and pull requests, 2 the decision log, 3 the conversation, 5 the search, 6 the MCP server, 7 the programme.

## What was built

Each feature has a spec under `docs/design/`, committed before its code, and a test named after each acceptance criterion.

| Feature | Spec | Requirements | Tests | Where it lives |
|---|---|---|---|---|
| A page for each change, and its branches and pull requests | `changeset.md` | CHS-1 to CHS-12, DLV-1 to DLV-10 | 23 | Core, so Lite has it |
| A decision log for each change | `decision-log.md` | DEC-1 to DEC-19 | 46 | Core, with the hand-off and the context pack in the team extension |
| The conversation behind a change | `conversation.md` | CNV-1 to CNV-14 | 29 | Product and connect extensions |
| Search that knows the system map | `search.md` | SRC-1 to SRC-14 | 19 | Core |
| An MCP server, read-only | `mcp-server.md` | MCP-1 to MCP-21 | 33 | A new optional extension, `agentic-mcp` |
| A programme seen from its parent | `programme-view.md` | PRG-1 to PRG-12 | 14 | System extension, with three reading methods on the adapters |
| A pull request opened by a workflow | `pull-request-by-workflow.md` | BOT-1 to BOT-6 | 5 | A template beside the kit's pipeline file, and `init --open-pr-workflow` |
| The places where they meet | | | 2 | `tests/test_phase12_together.py` |

Two checks were added, `CK-DECISION-LOG` and `CK-CONVERSATION`, each with a passing and a failing fixture. That makes 107. No gate was added, and no rule about who approves changed.

The last row but one is not from the post. It answers a finding of Phase 11: one person with one account cannot pass a gate on GitHub, because the author of a pull request may not approve it. A pull request that a workflow opens has the workflow's account as its author.

## How it was built

Five features were built at the same time, each by an agent in a working copy of its own, from one written brief: the spec first and alone in a commit, then the code; the three pipeline steps on the final tree; no edit to the shared documents. I wrote the workflow and, once the page existed, the view of a programme. One line of code went in before all of it: the list that other extensions add sections of a change's page to.

I read each branch before I merged it: the spec, every change to a file that existed, and the new code where it touches a gate, a path or a network. What the review changed:

- **The MCP server met the modules it was written for.** Its tools had only been tried on stand-ins, because the search and the page did not exist yet. The kit's search gives a list of hits that also knows how many hits there were and what to tell the caller. Passed on as a list, that was lost; the tool now passes on the whole answer. The tool's description said that a spec narrows a search, where it puts the spec's nodes first. AC-025 was added, and it compares the three tools with the commands.
- **The setting that the workflow needs does more than its use.** "Allow GitHub Actions to create and approve pull requests" is one switch for both. BOT-6 was added: the workflow's header says so, and a test shows that the kit's gate refuses an approval by the workflow's account.
- **Nothing else was changed in the agents' code.** The decision-log agent had found and corrected one thing in an existing check, and I kept it: `CK-CONTEXT` looked for a context pack's mark in its first 1,200 characters, and a pack with ten sources has its mark past them.

Then I checked what no single branch could: with every extension loaded, the page of the sample project has the sections of all features in a fixed order; writing the page changes the result of no check and the evidence of no gate; and the evidence of a spec with no decision log is byte for byte what it was.

## What was run

On the merged tree, on Linux with Python 3.12.3, pytest 9.2.0 and Spec Kit 1.4.3:

- `python -m pytest tests -q`: 739 passed and 3 skipped, of 742. Two of the skipped need a clone of the reference repository, and one needs the official `mcp` package.
- `agentic.py selftest`: every check behaved as expected on 107 fixtures.
- `agentic.py golden run --fixture fixtures/multi-app`: exit 0, 10 of 10 in each mode.
- The same three with git set as Git for Windows sets it and Python made to write CRLF, on Linux, on the merged code before the last documents were written: 739 passed and 3 skipped, 107 fixtures, 10 of 10 in each mode. That emulates line ends and nothing else of Windows.
- All 33 tests of the MCP server in an environment that has the official `mcp` package for Python, version 2.3.0: 33 passed, the one that opens the server with that client among them.
- The unit tests with Spec Kit taken off the path, as the Linux jobs of the kit's own pipeline have it: 733 passed and 9 skipped. The six more are the five of the install walk and the one in which Spec Kit installs the MCP extension.
- The three steps on Python 3.10.20 with pytest 9.2.0 and on Python 3.13.18 with pytest 9.1.1, the two pairs of that pipeline, without Spec Kit: 733 passed and 9 skipped on each, 107 fixtures, 10 of 10 in each mode. That run was on this tree but for this one line.

The agents ran the three steps on their own branches as well, and parts of their tests on Python 3.10, 3.11 and 3.13.

Added later on 2026-11-26, after the owner had pushed and merged this as pull request #4: the kit's own pipeline ran the merged code, on the pull request and on `main` at `43f672e` (run 45904789012).

- Linux, Python 3.10 with pytest 9.2.0 and Python 3.13 with pytest 9.1.1: both jobs passed.
- Windows Server 2025, Python 3.12.10, git 2.56.1, Spec Kit 1.4.3: of 747 unit tests 743 passed, 3 were skipped and 1 failed; the self-test passed on 107 fixtures, and the golden tasks and the demo passed.
- The one failure was the test of AC-012 of the MCP server, and the fault was the test's: on that runner one path was longer than a work item's id may be, the server refused it for its length, and the test waited for the words of another refusal. `docs/release-notes.md` says how the test changed. That change had not run on Windows when this was added.

Added on 2026-11-27: with the test corrected, the same pipeline passed on pull request #5 and on `main` at `c08eb5b` (runs 45914255887 and 45914573007). On Windows 744 unit tests passed and 3 were skipped, of 747; the self-test passed on 107 fixtures, and the golden tasks and the demo passed.

## What was not run

- Anything against GitHub, when this was written. `pulls`, the three methods that read another repository, the comments of an issue, and the workflow that opens a pull request had met only answers written by hand from GitHub's documents. Since 2026-11-27 the comments of one issue, `pulls` and the workflow that opens a pull request have run on GitHub; the last section says what else has run there. The three methods that read another repository have not.
- Anything against Jira or Azure DevOps.
- The MCP server with a coding agent such as Claude Code, GitHub Copilot or Cursor.
- Any of the new commands by a coding agent, and a hand-off by one that writes a decision log.
- Any of it on Windows, when this was written. Since then the kit's tests have run there, and no person has.
- The search on a real large repository.

## What changes for a project that already has the kit

1. `specs/<spec>/changeset.md` is a name the kit takes. A file of that name is never gate evidence.
2. `report all` writes a ninth view, `changesets`. Where the adapter is GitHub, that view, `changeset` and `audit-pack` ask GitHub once for each commit of a change, for at most fifty of each spec.
3. The manifest of an evidence pack has a new key, `delivery`.
4. `connect fetch` asks once more for each item of Jira, Azure DevOps and GitHub, for its comments. A row of `connect fetch --json` has a new key, `discussion`.
5. Where a spec has a decision log, the log is part of the evidence of G5. A spec with none has the evidence and the hash it had.
6. A brief may have two new sections: "Decisions", where the spec has a log, and "The conversation behind it", at the first gate, where one is recorded.
7. With the team extension: `work handoff --question` writes proposals into the decision log, the path guard refuses that log to an agent's file tools, a context pack may show decisions, and `CK-CONTEXT` no longer takes a pack with ten or more sources for an edited one.
8. `CK-VERIFY-INPUTS` refuses the page of a change as a verifier's input.
9. The file that plays GitHub in tests may hold the state of a pull request, and what another repository holds at a commit.

## Decisions that are the owner's to change

Each spec ends with its own list. These are the ones I would look at first.

1. **A decision of the log can be bound to a review.** Changed on 2026-11-28, at the owner's word. Until then a decision's owner was claimed, not proven: the kit cannot tell who typed `decision decide`, and the person who approves G5 is shown every entry. Now the owner can approve a pull-request review with the decision's line, `decision bind` names that review in the entry, and `CK-DECISION-REVIEW` asks the channel who wrote it (`docs/design/decision-review.md`). Binding is optional unless `kit.yml` asks for it, and G5 still approves the log.
2. **`report all` and the evidence pack now ask GitHub.** The other way is to show pull requests only on the page of one change.
3. **Every fetch reads the comments of every item.** One request more for each item, with no setting to turn it off.
4. **The MCP protocol is written by hand**, so that PyYAML stays the kit's only dependency. The server speaks the four revisions with a handshake and the one of 2026-07-28, which has none. The other way is the official library, as a dependency of that one extension.
5. **The MCP server reads only, unless it is started to write into a decision log.** Changed on 2026-11-28, at the owner's word. Until then it only read. Now, started with `--allow-write decision-log`, it also lists `decision_add`, which adds a question to a spec's decision log as a proposal and decides nothing (`docs/design/mcp-first-write.md`).
6. **A parent's release waits for its children.** Changed on 2026-11-28, at the owner's word. Until then a parent's gate did not wait for its children, and the view of a programme added no rule. Now `CK-PROGRAMME-RELEASE` holds a parent's release, G7, until each child has passed its own gates (`docs/design/programme-release.md`); the view itself still adds none.
7. **Only fixed words cross from another repository onto a programme's page**: no title and no name.
8. **The workflow that opens a pull request needs a setting that also lets a workflow approve.** The other way is a second account or a GitHub App.
9. **"One edge away" in the search counts an edge in either direction**, where the impact report follows it one way.
10. **`CK-CONTEXT` was changed**, to correct what is described above. It is a change to an existing check.

## The test on GitHub

The owner asked for the features to be proven on the reference project with a GitHub repository, issues, a Project and Actions. That had not started when this report was written. Its plan is in the project's notes, in stages: an issue with its discussion, a pull request that installs the kit into the reference repository, a fetch in Actions, a change branch whose pull request the workflow opens, a first real gate approved by the owner in a review, and then the page, the search and the MCP server on the result. Nothing is created on GitHub before the owner has seen and approved what would be created. Its results, whatever they are, go into `docs/limits.md`.

Added on 2026-11-27: the test began on 2026-11-26, and its first three stages are done.

- **The issue**, with two comments, in a Project of the owner's account.
- **The installation.** The kit's seven extensions and three workflows went into the reference repository as one pull request, which the owner merged. The kit's checks ran on that pull request and on `main`, and the notify job after them: the first runs of the kit's workflows on GitHub.
- **The fetch.** Started by hand in Actions, `connect fetch` read the issue by its label, the same issue as an item of the Project, and its two comments, and the job opened a pull request with the intake record as the workflow's own account. Of this phase's features that is the digest of a discussion (CNV-6 to CNV-9), read from a live service for the first time.

Not done when this part was added: a change branch whose pull request the workflow opens, a gate approved in a review, and the page, the search and the MCP server on the result. No decision log, no page of a change and no programme had met GitHub then. The part added after it says what changed.

Two things came of those stages that this report did not foresee. The installation and the runs showed ten faults and gaps in the kit, among them that two checks could not see what they judge with a pipeline's own token (`docs/design/first-live-runs.md`). And GitHub Copilot reviewed the pull request of the installation, as that repository's rules ask: thirteen findings in the kit's code, of which twelve held when checked (`docs/design/first-outside-review.md`). Both sets are fixed, and `docs/limits.md` has what was wrong and what was left.

Added later on 2026-11-27: stages 3a to 5 are done, and stage 6 in part.

- **The fixes reached GitHub.** The owner merged them into the kit as pull request 6; its jobs passed on Linux and on Windows, where 771 unit tests passed and 3 were skipped. The reference repository took the fixed kit in a second setup pull request.
- **Where the change came from.** The spec of the change, spec 020 of the reference repository, got its origin: the intake record of the issue, a summary of the conversation that the owner confirmed, and an entry in its decision log that he decided, in his words from the issue.
- **The first gate on GitHub.** The workflow that opens a pull request opened one as `github-actions[bot]`. The owner approved its held checks, then G1 and G2 of spec 020 in a review that carried the two lines `gate` printed. `record --change` read that review from GitHub and wrote the records. Pushed onto the same pull request, the records made GitHub dismiss the review, because that repository dismisses an approval on a push. The owner approved again and merged, the records were written again after the merge on a branch of their own, and on that pull request the pipeline passed `CK-APPROVER` and `CK-GATE-MIRROR` for both. Phase 11 found that one person with one account could not pass a gate on GitHub; this is how one did.
- **The page, the search and the MCP server on the result.** `changeset` read the change's four pull requests from GitHub; `search` put the one hit in the nodes the spec touches first; the MCP server answered the official MCP client against a checkout of that repository.

What those stages showed is in `docs/design/first-gate-on-github.md` (FGR-1 to FGR-15), fixed except for one decision that is the owner's: how the kit records a gate where approvals are dismissed on a push. On 2026-11-28 he answered it: both ways, which `docs/design/both-ways-to-record.md` builds. Not done: a programme with a child in a second repository. No coding agent has used any of it.

## Added on 2026-11-28

On 2026-11-28 the owner gave his word on four decisions: the open question of the first gate on GitHub ("both can be accepted"), and decisions 1, 5 and 6 above, each taken the other way. Four features came of it. Each has its spec in `docs/design/`, committed before its code, and one test for each of its acceptance criteria, which fails on the kit as it was and passes now:

- `both-ways-to-record.md` (BWR-1 to BWR-8): a gate recorded either way where approvals are dismissed on a push. Seven tests.
- `programme-release.md` (PRR-1 to PRR-8): a programme's release waits for its children, with the check `CK-PROGRAMME-RELEASE`. Seven tests.
- `mcp-first-write.md` (MCW-1 to MCW-8): the MCP server's first tool that writes, `decision_add`, listed only where the server is started with `--allow-write decision-log`. Eight tests.
- `decision-review.md` (DRV-1 to DRV-8): a decision of the log bound to a review, with the check `CK-DECISION-REVIEW`. Seven tests.

The two checks make 109. On the way, `CK-PROGRAMME` was found to stop the whole check run with a Python error on a child entry that is a plain word; it now fails that entry (PRR-8). `docs/release-notes.md` says what ran. None of it has run on GitHub or on Windows.
