# Phase 5, batch 2 — reference specs for the High findings (approved at gates G1 and G2 on 2026-11-22)

- **Phase and date:** Phase 5, batch 2 of 4, 2026-11-22
- **Upstream and reference:** spec-kit `v1.4.3`; healthcare repository `imatiqul/azure-ai-cloud-healthcare` at commit `6e0879d2`, read only
- **Requirement IDs exercised:** GOV-9, GOV-10, GOV-15, MAP-4, MAP-8, MAP-10 to MAP-13, TRC-1, PRD-1 to PRD-4, INT-5
- **Assumptions:** the 18 questions written into the specs, and the decisions in section 5. Section 7 says what the owner decided
- **Unverified:** nothing was built or run in the healthcare repository, and no migration was applied to any database. One agent wrote these specs. See section 6

## 1. What this is

The owner approved batch 1 at G1 and G2 on 2026-11-22. This is batch 2: the six High findings and two of the findings from Phase 1 that an agent proposed as High (N3 and N4).

The work stopped here for the owner's decisions on G1 and G2. Section 7 records them.

Finding N5 has no spec of its own. Spec 005, approved in batch 1, covers what it says.

## 2. The specs

| Spec | Finding | Says | Owner role | Tier | Requirements, criteria (abuse cases) |
|---|---|---|---|---|---|
| `009-phi-protection` | H1 | Identifiers are removed before text reaches a model provider or a log, whatever a flag says; PHI fields are encrypted; nothing about a patient stays in browser storage | security-compliance | critical | 8, 8 (2) |
| `010-bff-authorization` | H2 | The GraphQL BFF requires a token, names a policy per field, forwards the caller's token, and limits depth and cost | backend | high | 6, 6 (3) |
| `011-frontend-route-guards` | H3 | Every route declares its roles; a refused route requests no data; sign-in fails visibly when it is not configured | frontend | high | 6, 6 (2) |
| `012-no-fabricated-data` | H4 | No hardcoded metrics in a production build; a figure with no measurement reads "unavailable"; demo and seed endpoints exist only in Development | backend | critical | 6, 6 (2) |
| `013-migrations-production-engine` | H5 | Migrations are generated for, and applied in the pipeline on, the production engine; no migration warning is suppressed | data-owner | critical | 7, 7 (1) |
| `014-pipeline-gates` | H6 | Every escape is removed or waived with an owner and an expiry; actions are pinned to commits and images to digests | devops-sre | high | 6, 6 (1) |
| `015-audit-write-durable` | N3 | A request fails when its audit record cannot be written; no record is lost on the way to the event stream | security-compliance | critical | 5, 5 (1) |
| `016-audit-record-content` | N4 | The record carries tenant, patients and outcome; endpoints declare themselves audited | security-compliance | critical | 7, 7 (1) |

In all: 51 requirements and 51 acceptance criteria, 13 of them abuse cases, in 635 lines. With batch 1 the reference has 16 specs, 99 requirements and 104 criteria.

Three of the High findings carry the tier Critical here. A spec's tier may not be lower than that of a component it changes, and 009, 012 and 013 change Critical components.

### Reviewers the kit derives

| Spec | Added at G3 | Added at G5 | Change packs |
|---|---|---|---|
| 009 | backend, data-owner, frontend, platform, security-compliance | backend, frontend, platform, security-compliance | shared component |
| 010 | backend, security-compliance, solutions-architect | backend, security-compliance, solutions-architect | contract |
| 011 | frontend, platform, security-compliance | frontend, platform, security-compliance | shared component |
| 012 | backend, data-owner, security-compliance | backend, security-compliance | none |
| 013 | backend, data-owner, platform, security-compliance | backend, data-owner, platform, security-compliance | data store, shared component |
| 014 | devops-sre, platform | devops-sre, platform | shared component |
| 015 | backend, platform, security-compliance | platform | shared component |
| 016 | backend, data-owner, platform, security-compliance | data-owner, platform, security-compliance | data store, shared component |

### The order between the sixteen specs

The kit requires any two specs in flight that change the same component to be ordered. `examples/healthq/phase-5/order_specs.py` now holds one list and derives every pair from it:

001, 003, 004, 007, 008, 006, 005, 015, 016, 009, 013, 010, 011, 012, 014, and 002 last.

Nine of the sixteen change the shared infrastructure library, so those nine form one queue. That is true to how such changes collide, and it is heavy. A finer map, with the library split into its authentication, audit, persistence and AI parts, would loosen it. That is a decision for when the map is confirmed.

## 3. Verification

| What | Result |
|---|---|
| The 18 spec, map and constitution checks, on all sixteen specs | All pass |
| `order_specs.py --check` | The order written in each spec is the one the list gives |
| Every derived fact in the map, including the new pipeline component, cites a file in the healthcare repository | Pass, against the clone at `6e0879d2` |
| `tests/test_reference.py` | 26 passed in the cloud with the clone. On the owner's machine: 25 passed, 1 skipped (the test that needs a clone) |
| The whole suite | Not re-run for this batch. Nothing under `extensions/` changed since the run of 473 passed and 1 skipped |
| The healthcare clone | Unchanged |

## 4. For the owner at this stop

1. **G1 for each of the eight specs.**
2. **Four more pairs the kit lists as similar.** Recommended: `distinct` for each.
   - `002` and `010`: the services' endpoints, and the GraphQL door in front of them.
   - `004` and `016`: who the record names, and whose data, which tenant and what outcome it records.
   - `007` and `015`: an export that covers every store, and a write that is never lost.
   - `007` and `016`: the export, and the content of what is exported.
3. **G2, the 18 assumptions.** All are engineering or policy defaults the owner can settle himself. Two carry a number or an absolute and deserve a second look: no waiver runs longer than 90 days (014 A2), and nothing about a patient stays in the browser, even encrypted (009 A3). The recall threshold for redaction (009 A2) is left to the evaluation plan at G3.
4. **An amendment to the constitution, P-7.** As approved it says PHI is redacted "before it reaches a model provider, a log or a browser". Read literally, that forbids showing a patient's record to their clinician. The agent wrote that sentence, and it is wrong. Proposed: drop "or a browser"; the sentence that follows, on browser storage, already says what finding H1 needs. An amendment is a new version and G0 again.
5. **Batch 1's branch in the healthcare repository** is still to be pushed. This batch would go onto it as a second commit once approved.

## 5. Decisions made by the agent in this batch, each reversible

Numbering continues from the batch 1 report.

| # | Decision | Why | To reverse |
|---|---|---|---|
| 45 | No spec for N5; 005 covers it | Approved with batch 1 as decision 41 | Write `017` for N5; the kit will list 005 as similar and the owner decides |
| 46 | The pipeline is added to the system map as `ci-pipeline` (78 components now) | Finding H6 changes it, and a spec must touch something on the map | `EXTRA_NODES` in `convert_map.py` |
| 47 | The order of the sixteen specs is one list in `order_specs.py`; 002 stays last | Nothing may wait on the analysis-only spec | Edit `ORDER` and run the script |
| 48 | The order line of `002`, an approved spec, changed: it now also comes after 009, 012, 013, 015 and 016 | A consequence of decision 47. No requirement or criterion of 002 changed | Move 002 earlier in `ORDER`; the five then wait on it |
| 49 | 013 declares the nine services and their nine schemas as touched | The migration files sit in the service projects and change the schemas | `touches` in the spec |
| 50 | 009 keeps redaction, field encryption and browser storage in one spec | One spec per finding, as the reference brief asks | Split into three specs; they would share components and need ordering |

## 6. Not verified, and not done

- No agent team was used, and nothing ran in the healthcare repository's pipeline.
- No kit decision record exists for any gate of the reference.
- Spec 013 says what a migration test must show. No migration was applied to a database, and what production databases hold today is unknown.
- No adoption baseline has been drafted. Spec 014 assumes one (A1).
- The remaining two batches: five Medium findings (M1 to M5) and five more from Phase 1 (N6, Medium; N7 to N10, Low). Not started. With them the reference will have 26 specs for 27 findings, N5 being covered by 005.

## 7. The owner's decision, 2026-11-22

Sections 1 to 6 are the report as the owner saw it. At 13:11 Central time he answered:

> Batch 2, waiting on you: go ahead
> Before Phase 7: merged PR, continue to finish everything and reevaluate then wait to push by myself

| Item of section 4 | Recorded as | Where |
|---|---|---|
| 1. G1 for the eight specs | Approved | Each spec's header; the charter's decision log |
| 2. Four similar pairs | `distinct`, as recommended, under the owner's name as Product Owner | `origin.yml` of 002, 004, 007, 010, 015 and 016. CK-DUPLICATE passes |
| 3. G2, the 18 assumptions | All accepted as written | "Decided at G2" in each spec |
| 4. The amendment to P-7 | Approved: the constitution is at version 2 | `constitution.md` ("Amendments"), `constitution.map.yml` (`version: 2`), `.specify/agentic/constitution/amendment-v2.md` |
| 5. The branch in the healthcare repository | The owner pushed it and merged it himself: pull request #72, `main` at `8d04df3` | Checked on the remote |

None of this is a kit decision record.

The owner had already committed and pushed this batch's files as they stood (`978f706`). The second line of his answer lifts the stop after each remaining batch and gate, and keeps pushing for himself. It does not pass any gate: what is drafted from here on is marked as waiting for the gate it has not passed.
