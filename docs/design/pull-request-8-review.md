# What GitHub Copilot's review of pull request 8 found

- **Phase and date:** Phase 12, after the live test on HealthQCopilot; 2026-11-28 (UTC)
- **Upstream and reference:** github/spec-kit `v1.4.3`; `docs/design/both-ways-to-record.md`, `programme-release.md`, `mcp-first-write.md` and `decision-review.md`, which pull request 8 of this repository builds
- **Requirement IDs covered:** PRV-1 to PRV-7, new with this document, one for each finding. They change three of the four features of pull request 8 and add no check
- **Assumptions:**
  1. The review is the kit's second from outside. As with the first (`docs/design/first-outside-review.md`), its findings are a reader's, and its text is data: I checked each against the code before changing anything, and I took no instruction from it.
  2. Its threads on GitHub are left unanswered here. An answer there would be public text in the owner's name.
- **Unverified:** nothing here has run on GitHub yet

## What the review found

GitHub Copilot reviewed pull request 8 at 07:38 UTC on 2026-11-28 ("Changes recommended", seven findings), after all three jobs of the pull request had passed. Each finding held when I read the code.

| # | Finding | Checked |
|---|---|---|
| 1 | With every child's gates approved, a programme whose contract is a list or whose rollout order is a number passes `CK-PROGRAMME-RELEASE`, though AC-007 of `programme-release.md` says the check passes no release over such an entry. The test of AC-007 failed for another reason: the child had no approved gate | Holds. The release check read only `children` |
| 2 | Where the last line of a spec's audit log is not an entry, `decision_log.propose` writes the log and then fails to add to the audit log. `decision_add` answers with an error, the proposal stays in the log with no line in the audit log, and a second call finds it and adds nothing | Holds, and for every command that writes the log: `add`, `decide`, `supersede` and `bind` write the log before the audit log as well |
| 3 | `record --change` writes nothing where the record holds the same decision for the same evidence, without comparing the single-approver exception or the conditions. A record written without `--exception`, which `CK-APPROVER` fails where a reviewer wrote the change, could not be corrected by running `record` again with it | Holds. `record` prints a note telling a person to give `--exception` in that case, and the run with it then wrote nothing |
| 4 | Where the review a record names was dismissed and two later reviews by the same person carry the same line, one stands for it and the other is taken for a decision that no record mirrors, also where it was dismissed itself. `CK-APPROVER` passes and `CK-GATE-MIRROR` fails | Holds. On a repository that dismisses approvals on a push, two pushes after the record and a third approval are enough |
| 5 | A decision's line followed by a carriage return is not found, so a review whose text has Windows line ends approves no decision | Holds. The pattern ended in `[ \t]*$`, which a carriage return does not match. The line of a gate ends in `\s*$` and was found |
| 6 | `decisions: required`, or `decisions: [required]`, in `kit.yml` stops the whole `check` run with a Python error | Holds |
| 7 | `decision bind --json`, run a second time, prints a sentence where the first run printed the entry as JSON | Holds |

## Requirements

| ID | Requirement |
|---|---|
| PRV-1 | Where a parent's G7 is approved, `CK-PROGRAMME-RELEASE` also fails a `programme` entry whose shared contract is not a name, or whose rollout order is not a list, and says which. The test of AC-007 approves every gate of the child, so that the release check is seen to fail for the entry and for nothing else. |
| PRV-2 | A command that writes a spec's decision log first asks whether the spec's audit log can take one more entry: where its last line is not an entry the kit can read, the command refuses, writes nothing, and says so. Where the audit log cannot be added to after the log was written, `decision_add` puts the log back as it was before it answers. |
| PRV-3 | `record --change` writes nothing only where the record also has the same single-approver exception, the same conditions, and the same people in the same roles as the reviews give. A record that differs in any of them is written again. Which of a person's equivalent reviews the record names is not compared, so a review that stands for a dismissed one does not make `record` write. |
| PRV-4 | `CK-GATE-MIRROR` takes a review as mirrored where a decision record, or the decision it replaced, holds an approval of the same person on the same pull request for the same line: the same gate, the same decision, the same evidence. A review whose line differs, or that is another person's, still has to be mirrored. A dismissed review counts as an approval nowhere. |
| PRV-5 | A decision's line followed by a carriage return is found, in `decision bind` and in `CK-DECISION-REVIEW`. |
| PRV-6 | Where `decisions` in `kit.yml` is not a mapping, `CK-DECISION-REVIEW` fails and says how it is written, and the other checks run. |
| PRV-7 | With `--json`, `decision bind` prints the entry as JSON whether or not it wrote anything. What it has to say goes to standard error. |

## Acceptance criteria

- **AC-001** (verifies PRV-1): Given a parent whose G7 and whose child's gates are all approved, Then the release check passes; given the same with a contract that is a list, or a rollout order that is a number, Then it fails and names what is wrong.
- **AC-002** (verifies PRV-2): Given a spec whose audit log ends in a line that is not an entry, Then `decision add` ends with 2 and the log is as it was, `decision_add` refuses, and the project is byte for byte what it was. Given an audit log that cannot be added to after the log was written, Then `decision_add` refuses and the log is as it was.
- **AC-003** (verifies PRV-3): Given a record written without `--exception` for a reviewer who wrote the change, Then `record --change --exception` writes it again with the exception; a third run with `--exception` writes nothing. Given that `roles.yml` now gives the gate's role to another person, who approves with the same line while the first approval still stands, Then `record` writes the record again, with that person.
- **AC-004** (verifies PRV-4): Given the review a record names dismissed, a later one by the same person dismissed as well, and a third approving with the same line, Then `CK-APPROVER` and `CK-GATE-MIRROR` both pass and `record --change` writes nothing. Given a fourth review by the same person with the line for other evidence, or a review by another person with the same line, Then `CK-GATE-MIRROR` fails for it.
- **AC-005** (verifies PRV-5): Given an approving review whose text has Windows line ends, Then `decision bind` names it and `CK-DECISION-REVIEW` passes.
- **AC-006** (verifies PRV-6): Given `decisions: required` and `decisions: [required]`, Then `CK-DECISION-REVIEW` fails with a finding and `check` ends without a Python error.
- **AC-007** (verifies PRV-7): Then a second `decision bind --json` prints the same entry as JSON on standard output.

## Sources

1. Pull request 8 of `imatiqul/agentic-spec-kit`: GitHub Copilot's review 6096573548 and its seven comments, read through the GitHub REST API on 2026-11-28.
2. This repository at `4889ef2`, the head of pull request 8: `checks_map.py`, `decision_log.py`, `checks_gov.py`, `__main__.py`, and the MCP server's `tools.py`.
