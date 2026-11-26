# A demo that closes a gate, and opens it again

- **Phase and date:** Phase 11 (adoption), proposal 5; 2026-11-25
- **Requirement IDs covered:** DEMO-1 to DEMO-9, new with this document. They add no rule. They show three that exist: GOV-6 (only a listed person with the right role approves a gate), GOV-7 (an author does not approve their own work) and TRC-18 (an approval is bound to exactly what was reviewed)
- **Assumptions:**
  1. The owner's "continue" of 2026-11-25 is the go-ahead to build this proposal as `docs/phase-reports/phase-11-adoption-barriers.md` describes it.
  2. A newcomer runs it from a clone of the kit or from a project that has the kit, with Python, PyYAML and git.
- **Unverified:** not run on Windows. No coding agent has run it.

## Why

The tour's five commands write nothing, and the last thing they show is the line a person would paste. A newcomer never sees a gate close, or open again when the approved file changes, and that is what the kit is for. On 2026-11-25 it took a handful of commands and a hand-written JSON file to see it (finding 8 of the report above).

## What it does

| ID | Requirement |
|---|---|
| DEMO-1 | `agentic.py demo` writes a small project of its own into a temporary folder and works only there. It reads and writes nothing in the folder it is run from, and it ignores `--root`. |
| DEMO-2 | It needs no network, no GitHub and no coding agent: Python with PyYAML, and git. |
| DEMO-3 | It runs the kit's own commands (`report gates`, `brief`, `gate`, `record`, `check`) and prints what they print. It has no logic of its own that decides an approval. |
| DEMO-4 | It shows three things, in this order. An approval by the agent's own account fails `CK-APPROVER`. An approval by a person listed in `roles.yml` passes `CK-APPROVER`, `CK-GATE-MIRROR` and `CK-GATE-RECORD`, and the gate board shows the gate approved. A change to the approved spec makes `gate` report different evidence, and the board shows the gate open. |
| DEMO-5 | It says at the start and at the end that a file plays GitHub, that this proves nothing about who approved, and that on a real project the review is a pull-request review. |
| DEMO-6 | At each step it checks that the kit did what the demo says it does. If a step did not, the demo says which one and ends with 1. Otherwise it ends with 0. |
| DEMO-7 | It deletes its folder when it ends. `--keep` leaves the folder and prints where it is. |
| DEMO-8 | Its project uses the Lite profile and only what the core extension has, so the demo runs wherever the kit runs. |
| DEMO-9 | The README's first day ends with it. So does the tour skill. |

## Acceptance criteria

- **AC-001** (verifies DEMO-1, DEMO-7): Given an empty folder, When `demo` runs there with `--root` naming it, Then the folder is still empty, and the folder the demo named no longer exists.
- **AC-002** (verifies DEMO-4): Given the demo's project, When the agent's own account is the reviewer, Then the output holds `FAIL     CK-APPROVER` and the words "the agent's or CI's own identity".
- **AC-003** (verifies DEMO-4): Given the demo's project, When a person listed in `roles.yml` is the reviewer, Then `CK-APPROVER`, `CK-GATE-MIRROR` and `CK-GATE-RECORD` print `ok`, and the board shows G1 as `approved`.
- **AC-004** (verifies DEMO-4): Given an approved gate, When the spec is edited, Then `gate` prints "approve recorded for DIFFERENT evidence", and the board shows G1 as `open`.
- **AC-005** (verifies DEMO-5): The first and the last block of the output both hold the words "proves nothing about who approved".
- **AC-006** (verifies DEMO-6): Given a kit command that does not print what the demo expects, When the demo runs, Then it names the step and ends with 1.
- **AC-007** (verifies DEMO-7): Given `--keep`, When the demo ends, Then the folder it names exists and holds the project.
- **AC-008** (verifies DEMO-3): Every command line the demo prints is one the CLI's own parser accepts.
- **AC-009** (verifies DEMO-2, DEMO-8): The demo's `kit.yml` names the Lite profile and the file adapter, and the run ends with 0 when only the core extension is loaded.

DEMO-9 is a matter of documents. The test that compares the documents' command lines with the CLI reads the new lines.

## What it will not do

- Prove who approved. The file adapter can be written by anyone who can write the repository; `docs/limits.md` says so, and `doctor` says so wherever that adapter is configured.
- Read GitHub, or stand in for the first real gate on a live repository. That is proposal 3 of the report, and it still has to happen.
- Touch a project. It has no way to: it never reads `--root`.

## Decisions made here that are the owner's to change

1. The command is called `demo`.
2. The demo writes its own small Lite project, and does not copy `fixtures/multi-app`. A copy would tie the demo to a clone of the kit; this way it also runs in a project that has the kit installed.
3. In its second step the demo says that the gate board still lists the agent's decision as approved. That is what the board does today: it shows what is recorded, and the checks judge it (finding 6). If proposal 4 changes the board, this sentence changes with it.
4. The demo does not pause between steps. It prints everything and ends, so that a coding agent or a pipeline can run it.
