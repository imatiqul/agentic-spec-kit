# Phase 5, batches 3 and 4 — reference specs for the Medium and Low findings (drafts, waiting at gates G1 and G2)

- **Phase and date:** Phase 5, batches 3 and 4 of 4, 2026-11-22
- **Upstream and reference:** spec-kit `v1.4.3`; healthcare repository `imatiqul/azure-ai-cloud-healthcare` at commit `6e0879d2`, read only
- **Requirement IDs exercised:** GOV-9, GOV-10, GOV-15, GOV-20, MAP-4, MAP-8, MAP-10 to MAP-13, TRC-1, TRC-13, PRD-1 to PRD-4, CHG-15
- **Assumptions:** the 19 questions written into the specs, and the decisions in section 5
- **Unverified:** nothing was built or run in the healthcare repository. One agent wrote these specs. No gate is passed for any of them. See section 6

## 1. What this is

On 2026-11-22 the owner approved batch 2 and wrote: "continue to finish everything and reevaluate then wait to push by myself". That lifts the stop after each batch. It does not pass a gate.

So these nine specs are drafts. Each says so in its header, lists its assumptions under "Questions for G2", and has no decision recorded for it anywhere. A test in `tests/test_reference.py` holds that line: a draft may not say it was approved, and an approved spec must say who approved it and how.

They cover the five Medium findings (M1 to M5) and four of the five further findings from Phase 1 (N6, Medium; N7 to N9, Low). N10 has no spec of its own: `021` covers it. With these the reference has 25 specs for the 27 findings of Phase 1; N5 is covered by `005`.

## 2. The specs

| Spec | Finding | Says | Owner role | Tier | Requirements, criteria (abuse cases) |
|---|---|---|---|---|---|
| `017-visible-failures` | M1 | A caught error is logged or rethrown; a started task is awaited or queued; startup does not block on an asynchronous call; the count of old violations only falls | backend | critical | 5, 5 (1) |
| `018-reviewable-files` | M2 | A file over 600 lines is split or has a recorded reason; the three largest are split, behind characterization tests written first | solutions-architect | critical | 4, 4 (0) |
| `019-skipped-tests` | M3 | A test that cannot reach a service it needs fails; every remaining skip has a waiver; the pipeline shows the number skipped | qa | high | 5, 5 (1) |
| `020-repository-hygiene` | M4 | Generated files and test reports are not tracked; the README and the LICENSE file name the same licence | platform | high | 5, 5 (0) |
| `021-advisories-and-review` | M5, N10 | Every suppressed advisory is removed or waived; the waiver for a critical one is approved by Security and Compliance; an expired waiver fails the pipeline | security-compliance | high | 5, 5 (1) |
| `022-cors-allowlist` | N6 | Cross-origin access comes from a configured allowlist; no wildcard with credentials; the gateway does not start in a hosted environment with an empty list | security-compliance | critical | 4, 4 (1) |
| `023-environment-values` | N7 | A value of one hosted environment comes from that environment's configuration store and is not in a tracked file | devops-sre | critical | 4, 4 (0) |
| `024-pinned-dev-containers` | N8 | Every container the application host starts is pinned to a version and a digest and kept current by the update tool | devops-sre | medium | 3, 3 (0) |
| `025-event-contracts` | N9 | Every topic has a publisher; a topic is named by one constant from a shared catalogue | solutions-architect | high | 4, 4 (0) |

In all: 39 requirements and 39 acceptance criteria, 4 of them abuse cases, in 660 lines. The reference now has 25 specs, 138 requirements and 143 criteria, 32 of them abuse cases.

Four of these carry the tier Critical although their findings are rated Medium or Low. A spec's tier may not be lower than that of a component it changes: `017` changes the agent service, `018` the FHIR service, `022` and `023` the gateway.

### Reviewers the kit derives

| Spec | Added at G3 | Added at G5 | Change packs |
|---|---|---|---|
| 017 | backend, data-owner, platform, security-compliance | backend, platform, security-compliance | none |
| 018 | backend, data-owner, frontend, security-compliance | backend, frontend, security-compliance | none |
| 019 | devops-sre, platform | devops-sre, platform | shared component |
| 020 | frontend, platform, security-compliance | frontend, platform, security-compliance | none |
| 021 | platform | platform | none |
| 022 | backend, frontend, security-compliance | backend, security-compliance | none |
| 023 | backend, frontend, security-compliance | backend, security-compliance | none |
| 024 | devops-sre | devops-sre | none |
| 025 | backend, security-compliance, solutions-architect | security-compliance, solutions-architect | contract |

Every spec is on the standard lane, with all seven gates. The fast lane is for Low-tier changes, and the smallest of these, `024`, is Medium.

### The order between the twenty-five specs

`examples/healthq/phase-5/order_specs.py` holds one list and derives every pair from it:

001, 003, 004, 007, 008, 006, 005, 015, 016, 009, 013, 010, 011, 012, 014, 017, 018, 019, 020, 021, 022, 023, 024, 025, and 002 last.

`019` waits for `014` (both change the pipeline). `021` waits for `017` and `020` (all three change the repository's build configuration). `023` waits for `022` (both change the gateway) and for `001`, which already stops a service whose identity settings are missing.

## 3. Verification

| What | Result |
|---|---|
| The 18 spec, map and constitution checks, on all twenty-five specs | All pass |
| The duplicate check | Fails, as it should, on exactly the three pairs of section 4; it passes for the six pairs the owner decided |
| `order_specs.py --check` | The order written in each spec is the one the list gives |
| Every derived fact in the map, including the two new components, cites a file in the healthcare repository | Pass, against the clone at `6e0879d2` |
| `tests/test_reference.py` | 28 passed in the cloud, with the clone. On the owner's machine: 27 passed, 1 skipped (the test that needs a clone) |
| The whole suite | 478 passed in the cloud, in one run, after the two changes to the kit's code. On the owner's machine: the three files that test the changed code (63, 20 and 21 passed) and the self-test; the whole suite is run there at the final verification |
| Self-test | 105 fixtures behave as expected |
| The kit over a copy of the healthcare repository, with the reference project laid on top | 87 checks pass, 16 fail, 1 is not run (no agent specs installed there). Last time: 88, 15 and 1. The one more failure is the duplicate check, on the three pairs |
| The healthcare clone | Unchanged |

## 4. For the owner, when he comes to these

Nothing here stops the work. Each item waits at its gate.

1. **G1 for each of the nine specs.**
2. **Three pairs the kit lists as similar**, all about the waiver register. Recommended: `distinct` for each. Only a Product Owner can record that; the agent has not.
   - `014` and `019`: escapes in workflow files, and skipped tests.
   - `014` and `021`: escapes in workflow files, and suppressed advisories.
   - `019` and `021`: skipped tests, and suppressed advisories.
3. **G2, the 19 assumptions.** Four deserve a look:
   - `020` A1: the licence is MIT, and the README is the file to change. The LICENSE file came with the last commit before this work (`6e0879d`, 2026-08-03); the README's "Proprietary" sentence is from the first commit. Which is right is the owner's to say.
   - `021` A1: an update that fixes an advisory is merged or waived within 30 days, 7 where the advisory is critical. The agent proposed both numbers.
   - `021` A2: no separate spec for N10.
   - `017` A1: the 183 existing violations go into the adoption baseline, and this spec fixes only the six blocking calls at startup and adds the rules.
4. **`002`, an approved spec, has a new order line again.** It now also comes after `017` and `018`, which change services it changes. No requirement or criterion of `002` changed. As with batch 2, this is a change to something approved at G1 and G2.
5. **A new observation, not one of the 27 findings.** `src/HealthQCopilot.AppHost/Program.cs:114` sets the password of the local emulator's database as a literal. It is for a development container, and it is still a credential in source. Its value is not recorded anywhere in this repository. A pattern search of the tracked files finds no other such literal. Proposed: a Low finding, N11, either folded into `024` or given a spec of its own.

## 5. Decisions made by the agent in these batches, each reversible

Numbering continues from the batch 2 report.

| # | Decision | Why | To reverse |
|---|---|---|---|
| 51 | No spec for N10; `021` covers it | N10 says the review of the suppressed advisories is overdue. `021` gives each suppression an owner and an expiry and fails the pipeline when one passes | Write a spec for N10; the kit will list `021` as similar and the owner decides |
| 52 | Two components are added to the system map: `repo-config` (the build configuration, ignore rules, README and LICENSE) and `dev-apphost` (the development application host). 80 components now | Findings M1, M4, M5 and N8 change them, and a spec must touch something on the map | `EXTRA_NODES` and `EXTRA_INDEX` in `convert_map.py` |
| 53 | The end-to-end test folders are indexed to `ci-pipeline` | Finding M3 changes them, and they run only in the pipeline | `EXTRA_INDEX` in `convert_map.py` |
| 54 | The nine go after `014` in the order, and `002` stays last | Nothing may wait on the analysis-only spec | `ORDER` in `order_specs.py` |
| 55 | `022` does not declare a changed endpoint | It changes which web origins may call, not what a caller may do. Declaring it would make the kit ask for a role-by-tenant authorization matrix, which is the wrong evidence for it | Add `endpoints_changed: true` to its front matter |
| 56 | The pinning check now reads the containers a .NET Aspire application host starts, and treats a tag ending in `-latest` as floating | The constitution says principle P-17 is checked by the pinning check and lists N8 under it. The check could not see N8's file. Now it finds N8's two lines, and three more containers there with a version and no digest | Remove `_host_images` and its call in `checks_change.py` |
| 57 | Writing a reviewer brief that has not changed adds nothing to the audit log | Regenerating all briefs added a second `gate.ready` entry for specs nobody had touched. Time-to-decision counts from the first entry, so no measure changes | Remove the comparison in `cmd_brief` |
| 58 | The audit logs of the nine drafts hold one `gate.ready` per gate, from the final draft | Earlier entries came from the agent's own redrafting before anyone was asked | Not applicable |

Decisions 56 and 57 change the kit's code. Each has a test: `tests/test_change.py` (the application host) and `tests/test_reports.py` (the unchanged brief).

## 6. Not verified, and not done

- No agent team was used. Nothing ran in the healthcare repository's pipeline.
- No kit decision record exists for any gate of the reference.
- The counts in the findings are from Phase 1, from file listings on 2026-11-22, and from the kit's own checks over a copy of the repository. None was re-derived by building or running the code.
- The pattern search behind item 5 of section 4 is one regular expression over tracked files. It is not a secret scan.
- No adoption baseline has been drafted yet. `014`, `017`, `019` and `021` assume one. It is part of the work that follows.
