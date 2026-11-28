# A decision of the log, bound to a review

- **Phase and date:** Phase 12, after the live test on HealthQCopilot; 2026-11-28 (UTC)
- **Upstream and reference:** github/spec-kit `v1.4.3`; `docs/design/decision-log.md` (DEC-1 to DEC-19); `docs/design/both-ways-to-record.md` (BWR-1)
- **Requirement IDs covered:** DRV-1 to DRV-8, new with this document. They add one check, `CK-DECISION-REVIEW`, one field to an entry of the decision log, and two actions to `agentic.py decision`. `CK-DECISION-LOG` is not changed
- **Assumptions:**
  1. The Phase 12 report lists, as decision 1 that is the owner's to change: "The decision log is evidence of G5, and a decision's owner is claimed, not proven. The kit cannot tell who typed `decision decide`. The person who approves G5 is shown every entry. The other way is to bind a decision to a review, as a gate decision is bound." On 2026-11-28 the owner said to take the other way. The G5 rule stays: binding is added to it, and replaces nothing.
  2. A decision is bound as a gate is (GOV-6, GOV-7): a line that names what was decided goes into the text of a pull-request review that approves, and a record names that review. The checks then ask the channel who wrote the review.
  3. Binding is optional by default, so that a project's logs read as they did. A project that wants every decision bound says so in `kit.yml`.
- **Unverified:** no review of GitHub has carried a decision's line. The reviews in the tests come from the file adapter, which proves nothing about who approved

## Why

`decision decide` writes the owner it is given. Anybody who can run the command, an agent too, can name a person as the owner of a decision that person never made. Until G5 nothing shows otherwise, and at G5 the person who approves the implementation is asked to approve every decision with it. A gate decision does not rest on such a claim: its record names a review, and the checks ask the channel who wrote it. A decision of the log can rest on the same.

## Requirements

| ID | Requirement |
|---|---|
| DRV-1 | An entry of a decision log may name a review: `review: pull/<n>#review-<id>`. `decision_log.entries` gives the field for every entry, `None` where there is none. The page of a change and the reviewer briefs show the review a decided entry names. |
| DRV-2 | The line of a decision is `decision <spec> <id> sha256:<hash>`. The hash is of the spec, the entry's id, its question and its outcome, each taken as one line, so that spaces alone do not change it. `agentic.py decision line --spec <spec> --id <id>` prints the line of a decided entry, says that its owner puts it into the text of an approving review, and names the command that binds it. For an entry that is not decided it refuses and ends with 2. |
| DRV-3 | `agentic.py decision bind --spec <spec> --id <id> --change pull/<n>` reads the reviews of that pull request through the enforcement adapter, and names in the entry the newest one that passes DRV-4. Where none does, it says what the newest review by the owner lacks, or that the owner wrote none, and writes nothing. Where the entry names that review already, it writes nothing. It writes the log and one entry of the audit log, `decision-log.bind`. |
| DRV-4 | A new check, `CK-DECISION-REVIEW`, in every profile. For each decided entry that names a review: the review is in the channel; it is by the entry's owner, from a person's account, which is neither the agent's nor the pipeline's own and which `roles.yml` lists, as for a gate (CK-APPROVER); its state is APPROVED; and its text carries the entry's line with the hash of the entry as it stands. Where the review was dismissed, the first later review on the same pull request by the same person that passes the rest stands for it, as for a gate (BWR-1), and the check says so in a note. A review named in another form fails, and so does an entry that is not decided and names a review. |
| DRV-5 | `kit.yml` may hold `decisions: {bind_to_review: required}`. Then `CK-DECISION-REVIEW` also fails a decided entry that names no review. The default, `optional`, leaves such an entry to G5, as before (DEC-14). Any other value fails the check. |
| DRV-6 | A superseded entry is not looked at: what it held no longer stands, and the review it names, if any, was for that. |
| DRV-7 | The self-test has the check's two fixtures: the sample passes, and with its decided entry naming a review that carries no decision's line, it fails. |
| DRV-8 | `docs/design/decision-log.md` and the Phase 12 report (decision 1) say that a decision can be bound to a review. `docs/limits.md` says what a binding does not prove or do: the kit still cannot tell who typed `decision decide`, and a binding shows only that the owner approved that outcome in the channel; a binding written after G5 was approved opens G5 again, as any change of the log does; and a binding pushed onto a pull request whose approvals are dismissed on a push dismisses the review it names, so the owner approves again with the same line. |

## Acceptance criteria

- **AC-001** (verifies DRV-1, DRV-2): Given a decided entry, Then `decision line` prints its line, which changes with the outcome and not with spaces in it; given a proposed entry, Then it refuses and ends with 2. Then `entries` gives `review` for every entry, `None` where there is none.
- **AC-002** (verifies DRV-3): Given an approving review by the owner that carries the line, Then `decision bind` names it in the entry, the audit log holds `decision-log.bind`, `CK-DECISION-REVIEW` passes, and a second `bind` writes nothing. Given only a review by another person, one that comments, one without the line, one with the line of another outcome, or one from an account that is not a person's, Then `bind` says what is missing, ends with 2 and writes nothing.
- **AC-003** (verifies DRV-4): Given a bound entry, Then the check fails where the review is not in the channel, is by another person, requests changes, lacks the line, carries it for an outcome since changed, or comes from the agent's identity; where `review` is in another form; and where a proposed entry names a review. Given the review dismissed and a later approval by the owner with the same line, Then it passes and says which review stands; with no such later approval, Then it fails.
- **AC-004** (verifies DRV-5): Given `bind_to_review: required`, Then a decided entry with no review fails and a bound one passes. Given `optional` or nothing, Then the entry with no review passes. Given another value, Then the check fails and says so.
- **AC-005** (verifies DRV-6): Given a superseded entry that names a review that is not in the channel, Then the check passes.
- **AC-006** (verifies DRV-1, DRV-7): Then the page of a change and the brief of G5 show the review a bound entry names. Then the self-test passes on the sample and fails on the fixture, and `CK-SELFTEST` finds fixtures for the new check.
- **AC-007** (verifies DRV-8): Then the three documents say what DRV-8 says.

## What this does not do

- Prove who typed `decision decide`, or check that an entry's owner was the one who asked to decide. It proves that the owner approved that outcome in a review.
- Bind a question that is not decided, or a superseded entry.
- Replace G5. The person who approves the implementation still approves the log with it.
- Bind through the MCP server. `decision_add` adds questions only.

## Sources

1. `docs/phase-reports/phase-12-features.md` of this repository, "Decisions that are the owner's to change", decision 1.
2. `docs/design/decision-log.md` of this repository, DEC-3, DEC-4 and DEC-14, and "What it will not do".
