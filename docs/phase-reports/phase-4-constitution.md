# Phase 4 — reference constitution for HealthQ Copilot (approved at gate G0 on 2026-11-22)

- **Phase and date:** Phase 4, 2026-11-22
- **Requirement IDs covered:** GOV-11
- **Assumptions:** the 12 topics in `docs/prompts/reference/20-healthq.md` are the minimum; the 27 findings of Phase 1 stand as that report states them; Regulated profile with the HIPAA pack
- **Unverified:** nothing was applied to the healthcare repository, which was not touched. 17 checks the draft names do not exist yet. The numbers marked *proposed* are guesses for the owner to set

## 1. What this is

The phase plan puts the reference constitution after the first three slices and says the phase ends at gate G0. The owner's standing instruction is to carry on without a stop between phases. So the draft was written, and the work stopped there for the owner's decision. Section 6 records that decision.

Files:
- `examples/healthq/phase-4/constitution.md` — 25 principles in seven groups
- `examples/healthq/phase-4/constitution.map.yml` — what checks each principle

## 2. What the draft says, in numbers

| | Count |
|---|---|
| Principles | 25 |
| Enforced only by checks that exist in the kit today | 11 |
| Naming at least one check that is not built | 13 |
| Human-judged (P-12, "a clinician decides", at G3) | 1 |
| Checks to build in the healthcare repository | 17, each tied to the finding whose spec must build it |
| Phase 1 findings that trace to a principle | 27 of 27 |

A principle whose check is not built is stated, not enforced. The map says `status: not built` for each such check, so nobody reads the draft as protection that exists.

## 3. Verification

| What | Result |
|---|---|
| The kit's own check on a Regulated sample project carrying the draft (`CK-CONSTITUTION`) | Pass: every principle is mapped, every kit check it cites exists, every other check is declared |
| Negative control: one principle removed from the map | Fails: "P-9 appears in the constitution but not in the map" |
| Negative control: a kit check that does not exist | Fails: "P-11 names kit check ck:CK-NOT-A-CHECK, which does not exist" |
| `tests/test_reports.py::test_the_reference_constitution_maps_every_principle_and_answers_every_finding` | Pass. It also fails if a finding has no principle, or if a check outside the kit stops being marked "not built" |

## 4. Decisions in the draft for the owner to confirm or change

| # | Decision | Alternative |
|---|---|---|
| 1 | 25 principles. M1, M2, M4 and the Low findings each have a principle to trace to (P-23, P-24) | Fewer principles, with those findings traced to a general engineering principle |
| 2 | P-12, human in the loop, is the only human-judged principle, judged at G3 by the Solutions Architect and the AI Engineer | Judge it at G1 with the Product Owner as well |
| 3 | P-22: changed lines covered at 80 percent or more for High and Critical tiers | Another number, another scope, or no coverage principle |
| 4 | P-24: a source file over 600 lines is split or has a recorded reason | Another limit; the three largest files today are 1,030, 972 and 812 lines |
| 5 | P-10 makes a failed audit write fail the request | Queue and retry with an alarm. Safer for availability, weaker as evidence |
| 6 | P-11 forbids treating unmatched input as non-urgent | A stated default with an explicit "unclassified" level |
| 7 | P-25 puts the kit's own rule, a named person approves, into the constitution | Leave it to the kit and keep the constitution to the product |
| 8 | The draft lives in this repository under `examples/healthq/`. Nothing was written to the healthcare repository | Open a draft pull request there once a feature branch is allowed |

## 5. What approving G0 means, and what follows

Approving this draft makes it the constitution the reference specs are written against. It does not change the healthcare repository.

Until this repository has had a live test, a gate cannot be passed the way the kit prescribes, by a pull-request review. Earlier phases were approved by the owner saying so, and the README's progress table quotes the date. The same works here; the kit's rule that a chat reply is not an approval applies to projects that run the kit, and this draft is not yet in one.

Next, after G0: Phase 5 writes one spec for each of the 27 findings, in four batches by tier, and stops after each batch for G1 and G2.

## 6. The decision

On 2026-11-22 at 11:39 Central time the owner replied to the list of things waiting on him with: "Needs you: approve". That list had gate G0 as its first item and named the two proposed numbers.

Recorded as: **G0 approved as drafted.** All eight decisions in section 4 stand as written, including 80 percent changed-line coverage (P-22) and the 600-line limit (P-24). The constitution is version 1.0.0.

What this record is not: a kit decision record. No file was written under `.specify/agentic/decisions/`, and no agent approved anything. When the constitution reaches a repository with branch protection, G0 should be passed again there by a review, so that the kit's checks can read it.
