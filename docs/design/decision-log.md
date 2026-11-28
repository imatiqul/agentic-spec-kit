# A decision log for each change

- **Phase and date:** Phase 12 (features), proposal 2 of the Phase 12 review; 2026-11-26
- **Requirement IDs covered:** DEC-1 to DEC-19, new with this document. They add one check, `CK-DECISION-LOG`, and one file to the evidence of G5. Where a spec has no log, every existing check judges what it judged before, with one exception that DEC-19 names: `CK-CONTEXT` no longer takes a pack with a long list of sources for an edited one
- **Assumptions:**
  1. The owner said on 2026-11-26 to build the features of the Phase 12 review; this is its proposal 2. He left the choice between a log of its own and the records under `docs/adr` to the agent. A log of its own was chosen. The last section says why, and the choice is his to change.
  2. "Once G5 is decided" is read as: once the spec has a decision record for G5 that approves. A rejection sends the work back, and questions come up again after it.
- **Unverified:** nothing here has run on Windows, and no coding agent has used it: in the tests a hand-off is made by the test itself. The reviews in the tests come from the file adapter; none of this has read GitHub. The page of a change that will call the hook of DEC-17 is built elsewhere; here the hook is called on its own.

## Why

Six kinds of record hold a decision today: a gate decision, a clarification approved at G2, a record under `docs/adr`, what was done with an incoming request, a waiver, and an escalation. A choice made inside a change that is none of those has no record: which of two readings of a requirement was built, or what a task did about a case the plan left out. It stays in a chat, or in the code.

An agent that hands off a task may leave open questions. `work handoff` writes them into the work item, and nothing reads them after that: no check, no brief, no view. The golden tasks look there for a planted instruction that was reported, and that is all.

And nothing lists the decisions of one change together, for the person who approves it.

## What it does

| ID | Requirement |
|---|---|
| DEC-1 | A change may keep a decision log: `specs/<spec>/decision-log.yml`, with `schema: agentic-decision-log/1` and a list `entries`. An entry has an `id` (`D-001`, `D-002` and so on), a `title`, which is the question, and a `state`: `proposed`, `open`, `decided` or `superseded`. It may have an `outcome`, a `why`, an `owner` (a person id from `roles.yml`), `decided_on` (a date), `proposed_by` (an agent id or a person id), `affects` (a list of `FR-001`, `T003`, `node:<map node id>` and `adr:<file>`), a `source` (a link) and `superseded_by` (the id of another entry). |
| DEC-2 | `agentic_kit.decision_log.entries(ctx, spec)` gives the entries of a spec's log as a list, for the rest of the kit to read. Every entry has every field of DEC-1, and a date is given as text. Where the spec has no log, or the log cannot be read, the list is empty. |
| DEC-3 | `decision add --spec <spec> --title "<the question>"` adds an entry with the next free id. Its state is `open`. With `--by <id>` the entry names who asked: where `roles.yml` lists the id as a person the state stays `open`; any other id is taken for an agent's, and the state is `proposed`. `--affects` and `--source` may be given. `add` takes no outcome, and no owner, reason or day either. |
| DEC-4 | `decision decide --spec <spec> --id <entry> --outcome "<what was decided>" --owner <person>` sets an entry that is open or proposed to `decided`, with the day: `--on <date>`, or today. `--why`, `--source` and more `--affects` may be given. `--id`, `--outcome` and `--owner` are all needed, and the owner has to be a person in `roles.yml`. An entry that is decided or superseded is not decided again: a changed decision is a new entry. |
| DEC-5 | `decision supersede --spec <spec> --id <entry> --by <other entry>` sets an entry to `superseded` and names the entry that replaces it. Both have to be in the log, and they have to differ. What the entry held stays. |
| DEC-6 | `decision list --spec <spec>` prints the entries as a table. With `--json` it gives them as DEC-2 does. |
| DEC-7 | A `decision` command that cannot do what it was asked writes nothing, says why, and ends with 2. One that writes says that writing an entry approves nothing, as `record` says of its record. When G5 of the spec is already approved it also says that the log has changed and G5 is open again. It appends one line to the spec's audit log, with the kit as the actor: the kit cannot know who ran it. |
| DEC-8 | The log is part of the evidence of G5 of its spec, and of no other gate. `gate`, `record`, `brief` and the gate board take it up as they take up any evidence file. So the person who approves the implementation approves the decisions it rests on, and an entry added or changed after that changes the evidence hash, which opens G5 again. |
| DEC-9 | Where a spec has no log, nothing changes: its evidence and its evidence hash are what they were, its briefs and context packs read as before, and a hand-off with no question writes what it wrote before. |
| DEC-10 | The check `CK-DECISION-LOG` reads the log of every spec, in every profile. A spec with no log passes. It fails when the file is not a log: it is not valid YAML, it has another schema, `entries` is not a list, or an entry is not a mapping, has no title, or has an `affects` that is not a list. It fails when an id is not `D-` and three digits or more, or is used twice, and when a state is not one of the four. |
| DEC-11 | It fails when a decided entry has no outcome, no date or no owner, or an owner that `roles.yml` does not list as a person. It fails when an entry that is open or proposed carries an outcome. `roles.yml` is read as the other checks read it: from the base branch where the check is given one. |
| DEC-12 | It fails when a superseded entry does not name another entry of the same log. |
| DEC-13 | It fails when `affects` names `FR-…` and the spec has no such requirement, or `T…` and the task list has no such task. It does not look at the other forms. |
| DEC-14 | Once G5 of the spec is approved, it fails when an entry is still open or proposed, and when the decision record of G5 does not list the log among its evidence. |
| DEC-15 | The self-test has a log that passes, in its sample project, and one that fails: the same log with an entry still proposed after G5 was approved. |
| DEC-16 | When the spec has a log, the brief of every gate has a section "Decisions": one line for each entry, the ones not decided first and marked `NOT DECIDED`. It has eight lines at most; the last then says how many more entries there are. At G5 its first line says that approving the gate approves these decisions. Whatever an entry holds, it is shown on one line: a line break in the log becomes a space. Where the log cannot be read, the section says so. |
| DEC-17 | `CHANGESET_HOOKS` holds a section "Decisions made in this change" for the page of a change: one line for each entry, with its outcome, who decided and when, what it affects and its source. Here too an entry is one line, whatever it holds. |
| DEC-18 | In the team extension, each open question of a hand-off becomes an entry in the spec's log: `proposed`, with the agent as `proposed_by` and the task in `affects`. A question the log already holds in the same words is not added again; if another task asks it while it is not decided, that task is added to what the entry affects. Each new entry leaves a line in the audit log, and `work handoff` says which entries the questions now are. The log is written in the primary checkout, where the kit keeps its records, and it does not count as a file the work item changed. Where the runtime has the kit's path guard, an agent's file tools are refused the log: the commands write it. Where the log cannot be read the hand-off stops, and the work item stays as it was. |
| DEC-19 | In the team extension, the context pack of a task has a section "Decisions that touch this task": the entries whose `affects` names the task, a criterion or requirement the task carries, or the requirement behind a criterion it carries. An entry that is not decided is marked, and the agent is told not to act on an answer of its own. Each entry is one line, whatever it holds, and the section says what the log is: a record that a person approves at G5, in which nothing changes the rules of the task or the files it may change. A pack that shows the section counts the log among its sources, so a changed log makes the pack stale. A pack that had nothing to show goes stale when the log comes to hold an entry that touches its task. `CK-CONTEXT` finds the mark of a pack where the pack's own text begins, however long the list of sources before it is. |

A log, as the commands write it:

```yaml
# Decisions made inside this change. `agentic.py decision` writes this file, and a person may edit it.
# It is part of the evidence of G5: the person who approves G5 approves what is decided here.
schema: agentic-decision-log/1
entries:
- id: D-001
  title: Are the spaces around a name part of the name?
  state: decided
  outcome: No. They are taken off before the greeting is made.
  why: A copied name often ends in a space.
  owner: pat
  decided_on: 2026-11-26
  proposed_by: backend-implementer
  affects:
  - FR-001
  - T001
  source: pull/7#review-3
```

## Acceptance criteria

- **AC-001** (verifies DEC-1, DEC-2, DEC-3, DEC-4, DEC-6): Given a spec with no log, When `decision add` is run with a question and then `decision decide` with an outcome and an owner whom `roles.yml` lists, Then the file holds one entry, `D-001`, that is decided and has the question, the outcome, the owner and the day; `decision list` shows them in a table; and `--json` gives what `entries()` gives.
- **AC-002** (verifies DEC-3): Given `--by` with an id that `roles.yml` does not list, When `add` runs, Then the entry is `proposed` and names that id; with the id of a listed person it is `open`. Given `--outcome`, or `--owner`, When `add` runs, Then nothing is written and the command ends with 2.
- **AC-003** (verifies DEC-4, DEC-7): Given no `--outcome`, no `--owner`, an owner whom `roles.yml` does not list, an id the log does not hold, or an entry that is already decided, When `decide` runs, Then the file is what it was and the command ends with 2.
- **AC-004** (verifies DEC-5, DEC-7): Given two entries, When `supersede --id D-001 --by D-002` runs, Then `D-001` is `superseded`, names `D-002` and keeps its outcome. Given an entry the log does not hold, or the entry itself after `--by`, Then the file is what it was and the command ends with 2.
- **AC-005** (verifies DEC-7): `add`, `decide` and `supersede` each say that writing an entry approves nothing, and each leaves one line in the spec's audit log whose actor is the kit.
- **AC-006** (verifies DEC-10): Given a spec with no log, and a spec whose log is well formed, When the check runs, Then it passes.
- **AC-007** (verifies DEC-2, DEC-10): Given a file that is not valid YAML, one with another schema, one whose `entries` is not a list, and one with an entry that has no title, When the check runs, Then each fails and names the file. For the file that is not valid YAML `entries()` gives an empty list.
- **AC-008** (verifies DEC-10): Given the id `D-1`, and given one id used by two entries, When the check runs, Then each fails and names the id.
- **AC-009** (verifies DEC-10): Given the state `accepted`, When the check runs, Then it fails and names the four states.
- **AC-010** (verifies DEC-11): Given a decided entry with no outcome, one with no date and one with no owner, When the check runs, Then each fails and says what is missing.
- **AC-011** (verifies DEC-11): Given a decided entry whose owner `roles.yml` does not list, When the check runs, Then it fails and names the owner. Given a change that also adds that owner to its own `roles.yml`, When the check reads the roles from the base, Then it still fails.
- **AC-012** (verifies DEC-11): Given an open entry that carries an outcome, When the check runs, Then it fails.
- **AC-013** (verifies DEC-12): Given a superseded entry that names no entry, one that names an id the log does not hold, and one that names itself, When the check runs, Then each fails.
- **AC-014** (verifies DEC-13): Given `affects` with `FR-009` where the spec has no such requirement, and with `T009` where the task list has no such task, When the check runs, Then each fails and names the reference. Given `node:` and `adr:` references to things that do not exist, Then it passes.
- **AC-015** (verifies DEC-14): Given a spec whose G5 is approved and a log with an entry that is open, or proposed, When the check runs, Then it fails and names the entry. The same log passes while G5 has no decision record, and while its record is a rejection.
- **AC-016** (verifies DEC-14): Given a spec whose G5 was approved before it had a log, When a log with one decided entry is added, Then the check fails and says that G5 was approved without the log, and `gate` says that the approval is for different evidence.
- **AC-017** (verifies DEC-9): Given a spec with no log, When `gate` runs for G5, Then the evidence it lists holds no log, and the hash it prints equals the value that the formula of `agentic-evidence/1` gives, worked out by hand over those files.
- **AC-018** (verifies DEC-7, DEC-8): Given a spec whose G5 was approved with the log in its evidence, When `decision add` adds an entry, Then the command says that G5 is open again, `gate` prints "approve recorded for DIFFERENT evidence", and the gate board shows G5 as `open`. The log is in the evidence of no gate but G5.
- **AC-019** (verifies DEC-9, DEC-16): Given a log with a decided, a proposed and a superseded entry, When the brief of any gate is built, Then its section "Decisions" has one line for each, the proposed one first and marked `NOT DECIDED`; at G5 the section starts with the sentence about approving. Given ten entries, Then the section has eight lines and the last says how many more there are. Given an entry whose title, outcome and owner hold line breaks and headings, Then it is one line and the brief has no heading more. Given no log, Then the brief has no such section.
- **AC-020** (verifies DEC-9, DEC-17): Given the same log, When the hook in `CHANGESET_HOOKS` is called, Then it gives one section, "Decisions made in this change", with one line for each entry; the line of the decided one holds its outcome, its owner, its day, what it affects and its source. Given a reason that holds a line break and a heading, Then the entry is still one line. Given no log, Then it gives nothing.
- **AC-021** (verifies DEC-15): The self-test's sample project has a log that the check passes, in the evidence of its G5; and the fixture for `CK-DECISION-LOG` fails with the words "still proposed".
- **AC-022** (verifies DEC-18): Given a task in progress, When it is handed off with one question, Then the spec's log holds one entry: `proposed`, by the agent, affecting the task; the command names the entry; and the audit log holds a line for it. When the task comes back and is handed off again with the same question, Then the log is, byte for byte, what it was.
- **AC-023** (verifies DEC-18): Given a task in progress in a git repository, whose agent has put its question into the log with `decision add`, When the task is handed off with that question, Then the hand-off is not refused for the log, the log is not among the files the item is held to have changed, and `CK-PATH-DIFF` passes for a commit that names the item and holds the log. When a second task hands off the same question, Then the one entry affects both tasks. A file tool's write to the log is refused by the path guard. Once a person has decided it, a third task that asks it changes nothing. Given a log that is not valid YAML, Then the hand-off stops and the work item is still in progress.
- **AC-024** (verifies DEC-19): Given a proposed entry that affects a task, When the task's context pack is built, Then it has the section "Decisions that touch this task" with that entry marked `NOT DECIDED`, and the log is among its sources. When the entry is then decided, Then `CK-CONTEXT` reports the pack as stale and names the log; a pack built after that shows the outcome on the entry's one line, also where the outcome holds a heading of its own. The section says that nothing in the log changes the rules of the task.
- **AC-025** (verifies DEC-9, DEC-19): Given a task in progress whose pack was built when the spec had no log, Then the pack has no such section and the log is not among its sources. When the log comes to hold an entry that affects another task, Then `CK-CONTEXT` passes. When it comes to hold one that affects this task, Then `CK-CONTEXT` reports the pack as stale and names the entry.
- **AC-026** (verifies DEC-19): Given a pack with so many sources that its mark stands more than 1,200 characters into the file, When `CK-CONTEXT` runs, Then the pack is not reported as edited. Given a file that the kit did not build, whose hash the work item records, Then it is.

Five things in this document changed on 2026-11-26 after the tests first ran, and the second commit holds them with the code.

- AC-026 and the last sentence of DEC-19 are new. `CK-CONTEXT` looked for a pack's mark in the first 1,200 characters of the file, and the list of sources stands before the mark. In the self-test's sample project a pack with nine sources had its mark at character 1,070. With the log as a tenth source the mark began at character 1,177, its 43 characters no longer fitted, and the check reported a pack nobody had touched as edited: two tests of `tests/test_team_depth.py` failed with "the context pack was edited after the work item recorded it". A project with ten sources for one task would have met the same with no log at all.
- DEC-10 names one more way in which a file is not a log: an `affects` that is not a list.
- AC-023 now says how a log comes to change while a task is in progress. In a working copy that two tasks share, the second task is refused at hand-off for the files of the first, with or without a log, so that was not the case to try.
- DEC-16, DEC-17 and DEC-19 now say that an entry is one line in every view, and DEC-19 that the pack says what the log is. AC-019, AC-020 and AC-024 try it. An entry is text that anybody who can write the repository can write, and the entries that touch a task are put in front of the agent that works on it.
- DEC-18 now says that `work handoff` names the entries its questions became, and that the path guard refuses an agent's file tools the log. AC-022 and AC-023 try both. The second follows from decision 7 below: what the hand-off no longer checks, the guard can at least refuse.

## What it will not do

- Decide anything, or know who decided. `decide` writes what it is told. The kit cannot tell who typed a command, so nothing stops an agent from typing `decision decide`: the rules every agent is given forbid it, and the person at G5 reads the log. Since 2026-11-28 a decided entry can be bound to a review (`docs/design/decision-review.md`): its owner approves a pull-request review with the line that `decision line` prints, `decision bind` names that review in the entry, and `CK-DECISION-REVIEW` asks the channel who wrote it. That proves who approved the outcome, and still not who typed `decide`.
- Replace the records under `docs/adr`. An entry can point at one with `adr:<file>`. The check does not follow that pointer, nor a `node:` one.
- Show on the gate board that a log was added after G5 was approved. The board reads the files a decision lists. `gate` shows the changed evidence, and `CK-DECISION-LOG` fails (DEC-14).
- Fail a check when a decided entry is changed after G5 was approved. The hash changes and G5 is open again, on the board and in `gate`, as for any other evidence of G5.
- Turn the open questions of work items that were handed off before this existed into entries.
- Keep a comment a person wrote into the file. A command reads the log and writes it again.
- Guard the file against two commands that write it at the same moment. The later one wins, as with the audit log.
- Bring two copies of a log together. In an isolated working copy `decision add` writes that copy's log, and a hand-off writes the log of the primary checkout. Where both happen for one spec, `work integrate` meets two versions of the file and may stop. An agent in a working copy of its own gives its questions to the hand-off.
- Look for an agent of the name given to `--by`. The core does not know the team extension.
- Keep one agent's words from another agent. A question that one agent hands off is shown, as the question it is, to the agent whose task it touches. The pack keeps it to one line, says that nobody has decided it, and says that nothing in the log changes the rules of the task. A person reads the log at G5, and not before.

## Decisions made here that are the owner's to change

1. **A log of its own, and not more records under `docs/adr`.** A record there is for a decision that outlives the change and binds later ones. It has no place for a question that is still open, for the task it touches, or for an agent's proposal, and it is not part of what a gate approves. The other way is to write each such choice as a record under `docs/adr` and let `CK-ADR` judge it.
2. A rejection at G5 does not close the log. Only an approval does (assumption 2).
3. `CK-DECISION-LOG` asks for three things the task did not name: that an entry has a title, that an entry which is not decided carries no outcome, and that an approved G5 lists the log among its evidence. Without the last, a log first written after the approval would pass every check, and only `gate` would show it.
4. `--by` with the id of a person in `roles.yml` gives `open`. Any other id gives `proposed`. So a name that is typed wrongly is taken for an agent's.
5. A decided entry is not decided again. To change a decision, add an entry and supersede the old one.
6. One question is one entry in a log, whichever task asks it.
7. A hand-off writes the log itself, so the log is left out of what the work item is held to have changed, at hand-off and in `CK-PATH-DIFF`. An agent that edits the log through a shell is therefore not caught there. Its file tools are refused the log where the runtime has the path guard, and the rest is caught where a person reads the log: at G5.
8. The whole log is the source of a pack that shows a decision, as the whole spec is: an entry for one task makes the packs of the other tasks that show a decision stale as well. The other way is to record only the entries that touch the task.
9. The self-test's sample project has a log. So its briefs, and the context packs built from it, show decisions.
10. The registry lists the check under GOV-5 and TRC-18, which it serves for this one file. `gen_as_built_map.py` knows only the requirement IDs of `docs/prompts/spec`, and DEC-1 to DEC-19 are not there.
11. Each writing command appends a line to the audit log.
12. `supersede` takes the replacing entry after `--by`, the flag that `add` uses for who asked.
13. In the team extension three things go beyond what the task named, each because the feature does not hold without it. `CK-CONTEXT` looks for a pack's mark in another place (AC-026). `CK-PATH-DIFF`, the hand-off and the path guard take the log for the kit's own writing (decision 7). And `work handoff` prints one more sentence. Besides `work.py` and `context.py`, two files changed for it: `checks_team.py` by one line, and the extension's `__init__.py` by three.
