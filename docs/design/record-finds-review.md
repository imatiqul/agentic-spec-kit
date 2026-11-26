# `record` finds the review, and `gate` says when its evidence is not committed

- **Phase and date:** Phase 11 (adoption), the two parts of proposal 4 that change no rule; 2026-11-26
- **Requirement IDs covered:** REC-1 to REC-8, new with this document. They add no rule and change none: `CK-APPROVER`, `CK-GATE-MIRROR` and `CK-GATE-RECORD` judge a decision record exactly as before
- **Assumptions:**
  1. The owner's "next" of 2026-11-26 is the go-ahead to build these two parts as `docs/phase-reports/phase-11-adoption-barriers.md` describes them.
  2. The other two parts of proposal 4 wait for him: what the gate board calls a recorded decision whose review nobody could read, and whether Lite fails or warns in that case.
- **Unverified:** not run against GitHub. The reviews in the tests come from the file adapter. Not run on Windows.

## Why

To mirror a review, a person or an agent copies five values by hand: the decision, the commit, the reviewer, the role and the review's number. And `gate` prints a hash of the evidence as it is on disk, with no word when a file of it is not committed, although a reviewer sees only what was pushed (findings 6 and 7 of the report above).

## What it does

| ID | Requirement |
|---|---|
| REC-1 | `record --spec <spec> --gate <gate> --change pull/<n>` reads the reviews of that change through the project's enforcement adapter, and uses those by a person that carry, on a line of its own, the gate's line for the evidence as it stands now, in the review state that the line's decision asks for. |
| REC-2 | From those reviews it takes the decision, the commit, and one approval for each role the gate needs that a reviewer holds. In Lite one such role is enough, as it is for `CK-APPROVER`. Elsewhere every needed role has to be covered. A review that sends the work back is recorded as a rejection. |
| REC-3 | It writes nothing, says why, and ends with 2 when no review carries the line; when a needed role is not covered; when the reviews it would use are on different commits; when a review approves with conditions and no `--condition` is given; or when `--decision` or `--commit` is given and says something else than the review. |
| REC-4 | The long form, with `--decision`, `--commit` and `--approval`, works as before. One of the two forms has to be given. |
| REC-5 | The record is still a mirror. Writing it approves nothing, the command says so as before, and the three checks read the review again. |
| REC-6 | The pipeline's `connect mirror` uses the same reading of the reviews, and does what it did. |
| REC-7 | `gate` lists the evidence files that are not committed, and says that a reviewer sees only what is committed and pushed. With `--json` the list is under `uncommitted`. Where the folder is not a git repository it says nothing more than before, and `uncommitted` is null. The exit code does not change. |
| REC-8 | When a reviewer whose review it uses is also among the authors of the change, `record --change` says so. It does not set the single-approver exception: `--exception` stays with the person. |

## Acceptance criteria

- **AC-001** (verifies REC-1, REC-2, REC-5): Given one review by a listed person that carries the line, When `record --change` runs, Then the record it writes names the same decision, commit, evidence and approval as the long form does.
- **AC-002** (verifies REC-3): Given no review that carries the line, or one that carries the line for other evidence, When `record --change` runs, Then nothing is written, the output holds the line that is looked for, and the command ends with 2.
- **AC-003** (verifies REC-3): Given a review that carries the line by a person who holds none of the roles the gate needs, When `record --change` runs, Then nothing is written, the output names the role, and the command ends with 2.
- **AC-004** (verifies REC-2): Given a review in the state `CHANGES_REQUESTED` whose line says `reject`, When `record --change` runs, Then the record's decision is `reject`.
- **AC-005** (verifies REC-3): Given `--commit` or `--decision` that differs from the review, When `record --change` runs, Then nothing is written and the command ends with 2.
- **AC-006** (verifies REC-4): The long form writes the record it wrote before. With neither form the command ends with 2 and says what to give.
- **AC-007** (verifies REC-6): The tests of `connect mirror` pass unchanged.
- **AC-008** (verifies REC-7): Given a git repository with a brief that is not committed, When `gate` runs, Then the output names that file under "Not committed"; once it is committed, it does not; and `--json` carries the list.
- **AC-009** (verifies REC-7): Given a folder that is not a git repository, When `gate` runs, Then its output is what it was before.
- **AC-010** (verifies REC-3): Given a review that approves with conditions, When `record --change` runs with no `--condition`, Then nothing is written and the command ends with 2. With the condition given, the record holds it and the three checks pass.
- **AC-011** (verifies REC-2, REC-3): Given a gate that needs two roles, in a project that is not Lite, When one role is not covered, or the two reviews are on different commits, Then nothing is written and the command ends with 2. With both reviews on one commit, the record names both approvals.
- **AC-012** (verifies REC-8): Given a reviewer who is also an author of the change, When `record --change` runs, Then it says so, and the record carries the single-approver exception only when `--exception` is given.

AC-010 to AC-012 and REC-8 were added on 2026-11-26, after the code. The code already did what they ask. No criterion asked for it, and no test tried it.

## What it will not do

- Decide whether a review counts. The checks do, as before.
- Set `--exception`. When the reviewer also wrote the change, `record --change` says so and leaves that flag to the person.
- Change the gate board, or what Lite does when GitHub cannot be read. Those are the owner's two open decisions.
- Tell whether a commit has been pushed. `gate` looks at what is committed.

## Decisions made here that are the owner's to change

1. The short form is an option of `record`, `--change`, and not a new command.
2. `record --change` refuses, and writes nothing, when the reviewer who carries the line holds no role the gate needs. The long form still writes whatever it is given.
3. `gate` warns and does not fail. Its exit code stays 0.
