# One page for each change, and the branches and pull requests that deliver it

- **Phase and date:** Phase 12 (features), proposals 1 and 4 of the report `phase-12-changeset-gap-analysis`; 2026-11-26
- **Requirement IDs covered:** CHS-1 to CHS-12 for the page and DLV-1 to DLV-10 for delivery, new with this document. They add no gate and no approval, and they change how no decision is judged. One existing check is asked one thing more: `CK-VERIFY-INPUTS` does not let the page be given to a verifier (CHS-9)
- **Assumptions:**
  1. The owner said on 2026-11-26 to build the features of `phase-12-changeset-gap-analysis`. This document covers its proposals 1 and 4.
  2. That report advised that the first real gate on a live repository come before proposal 4, because proposal 4 reads GitHub. The go-ahead came without it. So the GitHub half of this document is code that no live repository has answered.
  3. A reader of the page is a reviewer at a gate, an engineer who picks the change up, or an agent at the start of a session. All three read; none of them types into the page.
- **Unverified:** nothing here has read GitHub. The pull requests in the tests come from the file adapter, and what the GitHub adapter makes of a response is tried only on responses written by hand from GitHub's REST documentation, as read on 2026-11-26. Nothing here has run on Windows.

## Why

The kit keeps everything about one change in the repository, but in seven places: `specs/<id>/` and, under `.specify/agentic/`, the folders `decisions`, `work`, `context`, `runs`, `audit` and `intake`. A reviewer, an engineer who picks the change up, or an agent at the start of a session needs six commands today to see one change whole: `report gates`, `brief`, `trace`, `why`, `work list` and `intake list`.

And no record lists the branches and pull requests of a change, or says whether they are merged. A work item records its branch, a commit names its work item, and a gate decision names the pull request its review was made in. Nothing puts the three together.

## What it does

### The page

| ID | Requirement |
|---|---|
| CHS-1 | `agentic.py changeset --spec <id>` prints one page for one change and ends with 0. The page is built at that moment from what the repository holds: the spec folder, the decision records, the work items, the intake records that `origin.yml` names, git, and the enforcement adapter. The command writes nothing unless `--write` is given, records no decision, and changes no file that a person approves. For a spec that does not exist it says so and ends with 2. |
| CHS-2 | After the core sections come the sections that other extensions add through `core.CHANGESET_HOOKS`. A hook is `(ctx, spec) -> list of (heading, lines)`. The sections come in the order in which the hooks were registered. The core imports no optional extension to build the page: what belongs to another extension it reads as plain YAML, or leaves to that extension's hook. |
| CHS-3 | The core sections come in this order, under these headings: **The change**, **Where it came from**, **Gates**, **Versions**, **Plan and tasks**, **Delivery**, **Open**. The table below says what each one shows. |
| CHS-4 | A section with nothing to say prints one line that says so. No section is left out, and that holds for a hook's section with no lines too. A hook that fails with an error of the kit's own gives a section that names the hook and the reason. The other sections are still printed. |
| CHS-5 | **Gates** takes the state of each gate from the gate board, so the two cannot disagree. For a recorded decision it gives the decision, the commit, each approver with the role and the review reference, the conditions, and the single-approver exception. It says which gate is open and which roles it needs. It says that the page shows what is recorded and that the checks `CK-APPROVER`, `CK-GATE-MIRROR` and `CK-GATE-RECORD` judge the review behind a record. |
| CHS-6 | **Versions** lists each commit, in the history of what is checked out, that changed `spec.md`, `plan.md` or `tasks.md`: oldest first, with its date, its subject and the files of the three that it changed. Under a commit stand the gate decisions made on that version: those whose record names that commit, or names a later commit with no change to the three files in between. A decision made again later is marked as an earlier one. A decision whose commit is not in the repository is listed apart. A change to one of the three files that no commit holds is named. |
| CHS-7 | `--json` prints the same content as one JSON document: `{"spec", "title", "about", "sections": [{"heading", "lines", "data"}]}`. `changeset.build(ctx, spec)` returns that document. `changeset.render(doc)` makes the Markdown page from the document and from nothing else. `lines` are the lines of the page; `data` holds the same facts as values. |
| CHS-8 | `--write` writes the page to `specs/<id>/changeset.md`. The first line of the file marks it as generated, as the first line of a context pack does. The command writes nothing, says why and ends with 2 when a file is already there that lacks the mark, when the spec is sealed (`specs/<id>/SEALED.yml`), or when `--json` is given as well. When the page on disk is already what it would write, it says so. It adds nothing to the audit log. |
| CHS-9 | The page is never gate evidence, and it never changes what a gate's evidence is. `_evidence_files` never returns it, whatever an evidence pattern says, and `gate` or `record` with `--file` naming it ends with 2. The reviewer's brief does not list it among what changed since the last review. `CK-VERIFY-INPUTS` fails a verifier's input list that names it: the page repeats what the work records say, and those are never a verifier's input. |
| CHS-10 | Where a section cannot know something, it says so in one plain line, and the command still ends with 0. That holds when there is no `origin.yml`; when the project root is not the top of a git repository of its own; and when the enforcement adapter cannot be read. |
| CHS-11 | `agentic.py report changesets` is a view like `gates`: one line for each spec with its id, its title, its open gate, its declared tier and its pull requests. `report list` names it and `report all` writes it. It prints no web address. |
| CHS-12 | The page says at its top that it was built from the repository, that it decides nothing, and that titles, task lines and commit subjects on it are copied text: data, in which an instruction is to be reported and not followed. |

| Section | Shows |
|---|---|
| The change | From the spec's front matter and its first heading: the id, the title, the declared tier, the lane that impact analysis computes, the owner role, and what the change touches (`touches` and `paths`). That the spec is sealed, when it is. |
| Where it came from | `specs/<id>/origin.yml`: each request it names, with the source, the title and the state from the request's intake record where that record is in the repository; each decision about a similar piece of work, with who made it; each listed candidate that nobody has decided. With no `origin.yml`: one line that says it is not recorded. |
| Gates | CHS-5. |
| Versions | CHS-6. |
| Plan and tasks | Whether there is a plan. Each task line of `tasks.md` with its tick. Beside a task, its work item when `.specify/agentic/work/<id>/` holds one: state, owner, reviewer and branch. Work items with no task line. Escalations. The acceptance criteria and the state of each, from the trace. |
| Delivery | DLV-4 to DLV-8. |
| Open | The open gate, and whatever another core section reported as waiting for a person or a decision: a decision recorded for files that have changed since, a rejection, a change that is not committed, a candidate nobody decided, a question left at a hand-off, a finding on work that was returned, an open escalation, a criterion that is not traced, a pull request that is still open, pull requests that could not be read, commits that were left out. With none of these: one line that says so. |

### Delivery

| ID | Requirement |
|---|---|
| DLV-1 | Both enforcement adapters have a method `pulls(commits: list[str]) -> list[dict]`: the pull requests that hold at least one of the commits, each once, as `{"change": "pull/<n>", "state": "open" | "closed" | "merged", "head": branch, "base": branch, "merge_commit": sha or "", "url": str}`. `merge_commit` is given for a merged pull request only. |
| DLV-2 | The GitHub adapter asks `repos/{repo}/commits/{sha}/pulls` once for each commit, through the helper that its other calls go through. A failure of that helper is raised as it is for them: `pulls` hides none. A pull request counts as merged when GitHub gives a time for `merged_at`. Before a merge GitHub's `merge_commit_sha` names a test merge, so it is passed on only for a merged pull request. |
| DLV-3 | The file adapter reads the pull requests from its stand-in file. Each entry under `changes` may carry `state`, `head`, `base`, `merge_commit`, `url` and `commits` (a list of commit ids). An entry holds a commit when it lists the commit, names it as its merge commit, or carries a review made on it. With no `state`, an entry that names a merge commit is merged and any other is open. An entry with none of the new keys gives the reviews and the authors it gave before. A `state` that is not one of the three is an error that names the entry. |
| DLV-4 | `delivery.ledger(ctx, spec)` returns a dict with the commits, the branches and the pull requests of one change. A commit belongs to the change when its message has a line `Work-Item: <spec>/<item>`, or when it changed a file under `specs/<spec>/`. The commits looked at are those on a local or remote-tracking branch of this clone, and those of what is checked out. They are given newest first, each with its date, its subject and the work items it names. |
| DLV-5 | The branches of the ledger are: each branch that a work item of the spec records, with whether this clone has it; the default branch that `kit.yml` names, where this clone has it; and each other branch that holds a commit of the change which the default branch does not hold. Each one comes with how many of the commits asked about it holds. A branch that holds only what the default branch holds is not listed: after a merge that would be every later branch. At most twelve such other branches are listed, and the ledger says how many more there are. |
| DLV-6 | The pull requests of the ledger are what `pulls` gives for the commits of the change. At most 50 commits are asked about, the newest. When that leaves commits out, the ledger says how many, and so does the page. With no commit there is nothing to ask, and the adapter is not called. |
| DLV-7 | When the adapter cannot be read, the ledger holds no pull request and the reason, and **Delivery** says that the pull requests could not be read and why. The command still ends with 0. Where the project root is not the top of a git repository of its own, git is not asked: the commits would be another repository's. The ledger then says so, and still gives the branches that the work items record. |
| DLV-8 | With the file adapter, **Delivery** says that the pull requests come from a stand-in file and that this proves nothing about what GitHub holds. |
| DLV-9 | The evidence pack keeps the ledger of each spec in its scope, as it stood when the pack was made, in its manifest under the new key `delivery`. Every key the manifest had is still there with what it held. |
| DLV-10 | The ledger only reads. It runs no `git fetch`, opens, merges, closes or changes no pull request and no branch, and asks the adapter through `pulls` alone. |

## Acceptance criteria

The project in each criterion is the demo's (`agentic_kit/demo.py`), unless it says otherwise: a Lite project with one spec, `001-greeting`, where a file plays GitHub.

- **AC-001** (verifies CHS-1, CHS-3, CHS-12): Given the project with its spec and its brief committed and no decision, When `changeset --spec 001-greeting` runs, Then it ends with 0; the seven headings are there, in order; **The change** gives the title, the tier, the lane, the owner role and the paths; **Gates** shows G1 as open; **Open** names G1 and the role it needs; and the top of the page says that copied text is data.
- **AC-002** (verifies CHS-5, CHS-6): Given the same project after a review by a listed person is recorded, Then **Gates** shows G1 as approved, with the person, the role and the review reference, and names the three checks that judge; **Versions** shows the commit with its date and subject, and the G1 decision under it; **Open** names the next gate. When the spec is then edited and not committed, **Gates** shows G1 as open again with the decision that was recorded for other files, and **Versions** names the file that no commit holds.
- **AC-003** (verifies CHS-7): `--json` gives one document with `spec`, `title`, `about` and `sections`, each section with `heading`, `lines` and `data`. `render` of that document is what the command prints without `--json`.
- **AC-004** (verifies CHS-2, CHS-4): Given three hooks, one that returns a section with lines, one a heading with no lines, and one that fails, When the page is built, Then their sections stand after **Open** in the order of registration; the second says that nothing is recorded; the third names the hook and the reason; and the command ends with 0.
- **AC-005** (verifies CHS-3, CHS-10): Given no `origin.yml`, Then **Where it came from** is one line that says so, and the command ends with 0. Given an `origin.yml` that names a request with an intake record, a request with none, a decided candidate and a candidate nobody decided, Then each has its line, and the undecided one is under **Open** as well.
- **AC-006** (verifies CHS-10, DLV-7): Given the project in a folder that is not a git repository, Then **Versions** and **Delivery** each say so in a plain line, **Gates** is as before, and the command ends with 0.
- **AC-007** (verifies DLV-7, CHS-10): Given a stand-in file that cannot be parsed, and given the GitHub adapter whose helper fails as it does when the `gh` program is missing, Then **Delivery** says that the pull requests could not be read and gives the reason, **Open** says it too, and the command ends with 0. Neither case reaches a network.
- **AC-008** (verifies CHS-8): `--write` writes `specs/001-greeting/changeset.md`; its first line carries the mark and the rest is the printed page. A second run says the file is unchanged. Given a file at that path with no mark, or a sealed spec, or `--json` as well, nothing is written and the command ends with 2.
- **AC-009** (verifies CHS-9): Given the page written, When `gate` runs, Then the line it prints is the line it printed before, and the page is not among the evidence of any gate from G1 to G7, also with a pattern in force that would match it. `gate --file` naming the page ends with 2.
- **AC-010** (verifies CHS-9): Given the page written after a gate was approved, When the brief for the next gate is built, Then its text is what it is without the page.
- **AC-011** (verifies CHS-9): Given a verifier's input list that names the page, When `CK-VERIFY-INPUTS` runs, Then it fails and names the page. Without that entry it passes.
- **AC-012** (verifies CHS-3): Given a task list with a ticked and an open task, and work items written as plain YAML, one of them with a question left at its hand-off and one escalated, Then **Plan and tasks** shows each task with its tick and its work item's state and branch, and the criteria with their states; **Open** holds the question and the escalation. No other extension is loaded to read them.
- **AC-013** (verifies DLV-1, DLV-3): Given a stand-in file with a merged and an open pull request, When `pulls` is asked about a commit of each, Then it gives both with the six keys, the merge commit for the merged one only. Asked about a commit that no entry holds, it gives nothing. An entry with none of the new keys still gives its reviews and authors, and is found as an open pull request through the commit of its review.
- **AC-014** (verifies DLV-2): Given responses written by hand in the form of GitHub's documentation, When the GitHub adapter's `pulls` is asked about two commits, Then a merged pull request has its merge commit, an open one has none although GitHub names a test merge, a pull request reached through both commits is given once, and a failure of the helper is raised.
- **AC-015** (verifies DLV-4, DLV-6): Given a commit that changes only code and whose message has the line `Work-Item: 001-greeting/T001`, and a stand-in file in which a pull request holds that commit, When the ledger is built, Then it names the commit with its work item and the pull request. A commit with the line `Work-Item: 001-greeting-two/T001` is not taken for this spec.
- **AC-016** (verifies DLV-5): Given a work item that records a branch, the default branch, a branch with a commit of the change that the default branch does not hold, and a branch cut later from the default branch, Then the ledger lists the first three with how many commits each holds and leaves the fourth out. A recorded branch that this clone lacks is listed as missing.
- **AC-017** (verifies DLV-6): Given 52 commits of one change, Then `pulls` is asked about the 50 newest, the ledger says that 2 were left out, and **Delivery** and **Open** say so. Given no commit, the adapter is not called.
- **AC-018** (verifies DLV-9): Given a project whose stand-in file holds a pull request for a commit of the change, When an evidence pack is built, Then its manifest holds the ledger of the spec under `delivery`, with that pull request; the pack kept with the spec holds it too; and every key that the manifest had before is still there. For the kit's sample project, which is not a git repository, the ledger in the pack says so.
- **AC-019** (verifies CHS-11): Given a project with two specs, When `report changesets` runs, Then there is one line for each, with the id, the title, the open gate, the tier and the pull requests; `report list` names the view; and the view holds no web address.
- **AC-020** (verifies CHS-1, DLV-10): Given a project with commits and a stand-in file, When `changeset` runs, with and without `--json`, and `report changesets` runs, Then every ref, the state of the working copy and the bytes of the stand-in file are what they were.
- **AC-021** (verifies CHS-1): Given a spec id that no folder has, Then the command says so and ends with 2.
- **AC-022** (verifies CHS-2, CHS-8): With only the core extension loaded, the page is built and written, and no other extension's module is imported.

## What it will not do

- Become a second source of truth. Nothing is typed into the page, and nothing reads it back.
- Judge an approval. The page shows a recorded decision as the gate board shows it, also where a check would fail the review behind it.
- Tell whether a page that was written to disk is still fresh. It shows the change as it stood when it was written. No check asks for it, and none compares it with the repository.
- Open, merge, close or change a pull request or a branch, or fetch from a remote.
- Find a pull request through a commit that has neither the `Work-Item:` line nor a change under `specs/<id>/`. A pull request made only of such commits is not found.
- Read part of GitHub's answer. One commit that GitHub cannot answer for, such as one that was never pushed, leaves the whole list unread, and the section says why.
- Read merge requests of GitLab or pull requests of Azure Repos. No adapter for them exists.
- Follow a change into a second repository.
- Show the conversation behind a change, a log of its decisions, or a search. Those are other proposals of the same report. They add their sections through the hook.

## Decisions made here that are the owner's to change

1. The page is printed. It is kept in the spec folder only on `--write`, and no check asks that a kept page is fresh. The report left this choice to the owner and advised it.
2. The page takes its gate states from the gate board. So a decision whose review a check would fail still reads as approved, and the page says who judges. If the board changes, the page changes with it.
3. A decision stands under the version it was made on: the last change to `spec.md`, `plan.md` or `tasks.md` at or before the commit its record names. Tying it only to a record that names that very commit would leave most decisions with no version, because a decision is usually made on the commit that added the brief.
4. Which branches are listed (DLV-5) is narrower than `git branch --contains` for every commit, which after a merge lists every later branch. Remote-tracking branches count, so that a fresh clone and a pipeline's checkout see the same branches as the clone the work was done in.
5. A commit belongs to a change by a `Work-Item:` line at the start of any line of its message, not only in the last block. A squash merge keeps the line and loses the block.
6. At most 50 commits are asked about, with one request to GitHub for each, for one change. `report changesets` and `report all` ask for every spec, so on a project that reads GitHub they now use the network and take longer. The evidence pack asks as well.
7. The file adapter takes the commit of a review for a commit of that pull request, and reads an entry with no `state` as open, or as merged when it names a merge commit.
8. The page may not be given to a verifier, the brief does not list it, and `--file` naming it is refused. Each of the three closes a way in which a generated page could reach a decision.
9. `--write` refuses a sealed spec, because a sealed change keeps its files as they were. A page written before the seal is sealed with the rest.
10. **Plan and tasks** gives the state of each acceptance criterion from the trace, in one line. The report did not ask for it; `trace` is one of the six commands the page stands in for.
