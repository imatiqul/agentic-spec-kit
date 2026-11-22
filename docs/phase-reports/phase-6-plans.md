# Phase 6 — plans and tasks for the reference (drafts, waiting at gates G3 and G4)

- **Phase and date:** Phase 6, 2026-11-22
- **Upstream and reference:** spec-kit `v1.4.3`; healthcare repository `imatiqul/azure-ai-cloud-healthcare` at commit `8d04df3` (`main` after pull request 72), read only
- **Requirement IDs exercised:** GOV-10, GOV-20, MAP-5, MAP-6, MAP-10 to MAP-14, CHG-1 to CHG-5, CHG-18, CHG-19, QLT-3, QLT-6 to QLT-9, QLT-13 to QLT-16, TRC-1 to TRC-3
- **Assumptions:** the decisions each plan lists as its own, and the decisions in section 7
- **Unverified:** every plan was written from reading the code. Nothing in the healthcare repository was built or run. No gate is passed. See section 9

## 1. What this is

The owner wrote on 2026-11-22: "continue to finish everything and reevaluate then wait to push by myself". So these are drafts, written without a stop, and each says at its top which gate it waits at.

The kit agrees that no gate is passed. Its gate check now fails on every spec that has a plan, because no pull-request review has approved G1 or G2 for it; approvals in conversation are not decision records. That failure is correct and is left in place. Section 3 lists it with the other things only a person can clear.

## 2. What was written

In `examples/healthq/project/specs/`:

| Spec | Finding | Written | Waits at |
|---|---|---|---|
| `001-fail-closed-auth` | C1 | plan, tasks, threat model, test strategy, trace manifest, briefs | G3, G4 |
| `003-identity-from-token` | C3 | plan, tasks, threat model, privacy impact, test strategy, rollout, trace manifest, briefs | G3, G4 |
| `004-audit-identity` | C4 | the same, and the characterization record | G3, G4 |
| `005-triage-validation` | C5 | the same as 003, and the evaluation design and the safety case | G3, G4. It cannot pass G3 as it stands: section 6, item 3 |
| `006-eval-production-path` | C6 | plan, tasks, threat model, test strategy, rollout, evaluation design, safety case, trace manifest, briefs | G3, G4 |
| `013-migrations-production-engine` | H5 | plan, data-change plan, threat model, privacy impact, rollout, brief | G3 |
| `002-endpoint-authorization` | C2 | `programme.md`: ten proposed child specs, the shared contract, the rollout order | The owner. It is a proposal, not applied to the spec |

Impact reports were regenerated for all twenty-five specs.

Every plan has the same parts: what the code does today, with file and line; the change; the decisions the plan makes; requirements to criteria to tests to tasks; the risks it carries; what was found while planning that is not part of the change; and what the reviewer at G3 has to decide.

## 3. What the kit refuses, and who can clear it

These checks fail on the reference project. Each failure is the true state. A test in `tests/test_reference.py` holds the list exact: if one more thing failed, or one of these stopped failing without its cause, the test would fail.

| Check | Fails on | Why | Cleared by |
|---|---|---|---|
| CK-GATE-RECORD | The six specs with a plan | No pull-request review approved G1, G2 or G3 | The owner's reviews, mirrored by the kit. That needs the agents to have a GitHub identity of their own |
| CK-CHARACTERIZATION | The same six | The tests that pin today's behaviour have not been run by anyone, and for five specs are not written | A run of the tests. For 004 they exist: eleven tests of the audit middleware |
| CK-AI-EVAL | 005, 006 | No clinician has signed a golden set | A clinician. Nobody in `roles.yml` is one |
| CK-AI-SAFETY-CASE | 005, 006 | Nobody has accepted the safety case through a review | A named person's review |
| CK-AI-PROD-PATH | The evaluation harness | The harness never names the classifier. This is finding C6, found by the kit on the real code | Spec 006 |
| CK-THREAT-MODEL | 004 | Two threats are tested by criteria the approved spec did not write as abuse cases | An amendment to the spec: section 6 |
| CK-DUPLICATE | 014, 019, 021 | Three similar pairs nobody has decided | The Product Owner |

All other checks that read a spec, a plan or a task list pass on all twenty-five specs.

## 4. What planning found in the healthcare code

None of these is among the 27 findings of Phase 1. Each was read in the code at `8d04df3`; none was shown by running anything. They are observations for the owner to rate.

| # | Observation | Evidence | Found while |
|---|---|---|---|
| O1 | The local emulator's database password is a literal in source. Its value is not recorded in this repository | `src/HealthQCopilot.AppHost/Program.cs:114` | Writing spec 024 |
| O2 | The idempotency middleware answers a repeated request from its cache before authentication and authorization run. The cache key has no user and no tenant. Whoever holds a key gets the stored clinical response for 24 hours, with no token | `src/HealthQCopilot.Infrastructure/Middleware/IdempotencyMiddleware.cs:59-79, 117-119`; `src/HealthQCopilot.Agents/Program.cs:392-394` | Planning 004 |
| O3 | The consent middleware never checks consent. It runs before authentication, sees no user, and passes every request on. When it does see one it treats the caller as the patient, and it allows access whenever the identity service cannot be reached | `src/HealthQCopilot.Fhir/Middleware/ConsentEnforcementMiddleware.cs:55-63, 96-111`; `src/HealthQCopilot.Fhir/Program.cs:85-86` | Planning 004 |
| O4 | No workflow runs the architecture test project or the evaluation test project | `.github/workflows/pr-validation.yml:50, 57`; `microservice-deploy.yml:282, 291`; `agent-eval.yml:55` | Planning 004 and 006 |
| O5 | No workflow of the repository has run since May 2026, apart from Dependabot's and the Copilot reviewer's. The last run on a pull request was 2026-05-04, on a push 2026-04-30, on a schedule 2026-05-10. Pull request 72 and the two latest commits on `main` have no check run. Pull request 72 was merged by its author with one review, from the Copilot reviewer, which commented and did not approve | The repository's public record on GitHub, read on 2026-11-22 | Looking for a run of 004's existing tests |
| O6 | A migration that fails because something already exists is recorded as applied, although the rest of it did not run. A failure to initialise a database is logged and the service starts | `src/HealthQCopilot.Infrastructure/Persistence/DatabaseExtensions.cs:135-164, 122-125` | Planning 013 |
| O7 | A break-glass grant is published under two topic names, from two places. The comments say supervisors are notified through it. Nothing in the repository subscribes to either. 25 of 33 published topics have no subscriber in the repository | `src/HealthQCopilot.Identity/Endpoints/BreakGlassEndpoints.cs:65`; `EventHandlers/BreakGlassAccessHandlers.cs:31`; the system map | Correcting finding N9 |
| O8 | By the rules as written, a confirmed appendicitis in the golden set is classified non-urgent, and a non-urgent result is completed with no clinician and announced to three services. Two of the five golden cases get their expected level | `src/HealthQCopilot.Agents/Plugins/TriagePlugin.cs:17-39`; `src/HealthQCopilot.Domain/Agents/TriageWorkflow.cs:96-120`; case TR-003 | Planning 005. The rules were applied by a script, not by running the code |
| O9 | The topic `revenue.prior-auth.status-changed` has a subscriber and no publisher | `src/HealthQCopilot.RevenueCycle/Controllers/RevenueSubscriberController.cs:89` | Correcting finding N9. It is in spec 025 |

O5 changes what the reference can show. Several acceptance criteria say "when the pull request's checks run". Today they do not run. Whether GitHub Actions is switched off for the repository, or something else stops it, cannot be seen from outside; the owner can see it in the repository's settings.

## 5. Two things Phase 1 got wrong

Both are corrected in `docs/phase-reports/phase-1-verification.md`, section 9, with the original text left in place.

1. **Finding N9.** It said two topics had no publisher and 27 publish calls did not name their topic with a literal. The pattern did not read a call that names its arguments across lines. In fact 33 topics are published from 38 call sites, and 2 of those choose between two literals. An automated review of pull request 72 pointed to the two publishers. Spec 025, a draft, is rewritten.
2. **The draft map** lacked 20 topics, 22 publishers and 7 build edges. The project's map has them now, each citing its file. Eight impact reports changed: a change to the agent service reaches the scheduling, population health, revenue and notification services, which act on its events.

The error was mine, and the kit could not have caught it: its discovery did not read event topics. It does now (section 7), and the drift check passes against the real code.

## 6. The review of pull request 72, and what it means for approved specs

The Copilot reviewer left five comments on the pull request that brought batch 1 into the healthcare repository. The pull request was merged with them open. Each was checked against the code and the specs. All five are right.

| # | Comment, in short | Checked against | What is proposed |
|---|---|---|---|
| 1 | The map omits the agent service as publisher of two topics, so spec 005's impact leaves out the services downstream | `TriageCompletedHandler.cs:37`, `EscalationRequiredHandler.cs:32`, `TriageOrchestrator.cs:299-302` | Done: section 5. The map, the impact reports and the kit are corrected |
| 2 | In spec 003, FR-006 forbids reading a tenant header and FR-002 requires reading it to compare | The spec | An amendment to FR-006: "The build MUST fail when code takes the acting tenant, user or role from a request header or body". The plan follows that reading and says so |
| 3 | In spec 005, condition A1 lets a higher priority take effect unconfirmed; the constitution's P-12 lets no triage level take effect without a clinician | The spec and `constitution.md` | A decision for the owner and a clinician: keep P-12 and change A1 and FR-007, or amend P-12 at G0. The plan offers a design that meets both as written, and stops there |
| 4 | Spec 007's export covers the nine tables and omits the consent and decision events that go only to the event stream | `TriageOrchestrator.cs:110-119, 280-288` | An amendment to 007: the event stream is a source of the export, with a rule for records present in both |
| 5 | Spec 007 says an export is limited to the patient asked for; the record has no patient, and no requirement scopes it | The spec; `AuditDbContext.cs:38-47` | An amendment to 007: either depend on 016, which adds the patient to the record, and add the criterion, or withdraw the sentence |

Planning found five more places where an approved spec needs amending. None is applied; each waits for the owner, and each is an amendment that re-opens G1 and G2 for that spec.

| Spec | Amendment | Why |
|---|---|---|
| 003 | Add `agent-service` to `touches` | Three of the header reads are there. The kit would refuse the change otherwise |
| 005 | Add `lib-domain` to `touches` | The rule that only P1 and P2 wait for a clinician is in the domain library |
| 004 | Mark AC-004 and AC-005 as abuse cases | They test two real threats; the kit requires a threat's test to be written as one |
| 001 | Add `ci-pipeline` to `touches` | FR-003 changes the deploy workflow |
| 002 | The `programme` block in `programme.md`; its order line changed again, to follow 025 | The breakdown; and 025 now changes the revenue service |

One change to approved specs was applied, because the kit cannot check the constitution's P-21 without it: the six specs with a plan now say `changes_existing_code: true` in their front matter, and the project's settings say it is an adopted codebase. No requirement or criterion changed. It is listed here so that it is seen.

## 7. Decisions made by the agent in this phase, each reversible

Numbering continues from the batch 3 and 4 report.

| # | Decision | Why | To reverse |
|---|---|---|---|
| 59 | Kit: a Critical change's rollback rehearsal is planned at G3 and shown at G7 | The check asked for the rehearsal's evidence as soon as a plan existed. No plan could have it. This was the first Critical spec the check had seen | `ck_progressive` in `checks_release.py` |
| 60 | Kit: a Critical change's test strategy answers for each external system it may rely on with a test or a stated reason; systems under `depends_on` are included and need a test; a placeholder fails | For 004 the kit asked for resilience tests against five services the change does not call, and did not ask about the identity provider, which it relies on | `ck_test_strategy` in `checks_quality.py` |
| 61 | Kit: discovery reads Dapr topics, publishers and subscribers in C# | Section 5. The drift check can only be as complete as discovery | The `dapr` adapter in `discover.py` |
| 62 | Kit: impact analysis reaches the events a touched component publishes, and their subscribers | A change to a publisher did not reach the services that act on its events. The rollout-order check already treated publishing this way | `blast_radius` in `mapmodel.py` |
| 63 | The project's map is reconciled with the kit's discovery: what discovery finds and the draft lacks is added and marked; discovery's names become aliases; three things are ignored with reasons | So that the drift check compares the map with the code. Before, it reported 26 differences that were only names | `reconcile` in `convert_map.py` |
| 64 | The project is marked as an adopted codebase, and planned specs say they change existing code | The constitution names the characterization check for P-21. Without the setting the check does nothing | `adoption` in `kit.yml`; the flag in six specs |
| 65 | Spec 025 is rewritten to the corrected finding | Its first requirement rested on a wrong statement | The previous text is in the repository's history |
| 66 | The breakdown of 002 is a document, not ten child specs | "Breakdown only". The children are specs with gates of their own once the owner agrees the shape | Write the children; the kit's programme check then applies |
| 67 | Threat models list every threat, including two whose tests the approved spec did not mark as abuse cases | A threat model that leaves out a known threat to pass a check is worse than one that fails it | Remove TH-2 and TH-3 from `004-audit-identity/threat-model.yml` |
| 68 | 004's order test goes in the unit test project | No workflow runs the architecture test project | Move the file; add the project to a workflow |
| 69 | 013 includes removing the "recorded as applied" behaviour | Without it FR-006 cannot be met; the spec does not name it | Section "For the reviewer at G3" of that plan |

Decisions 59 to 62 change the kit's code. Each has a test: `tests/test_quality.py` (two), `tests/test_system.py` (two).

## 8. Verification

| What | Result |
|---|---|
| Every check on the reference project | 84 pass, 19 fail, 1 is not run. The 19: the seven of section 3, and twelve that need the healthcare source or record gaps of adoption |
| The kit over a copy of the healthcare repository | 82 checks pass, 21 fail, 1 is not run (no agent specs are installed there). Before the plans: 88, 15 and 1. The six more are the first six rows of section 3 |
| The map against the code | The drift check passes; every derived fact cites a file that exists at `6e0879d2` |
| `tests/test_reference.py` | 39 passed in the cloud, with the clone. On the owner's machine: 38 passed, 1 skipped (the test that needs a clone) |
| The whole suite | 493 passed in the cloud, in one run, after the four changes to the kit's code. On the owner's machine: the four files that test the changed code (34, 17, 63 and 20 passed); the whole suite is run there at the final verification |
| Self-test | 105 fixtures behave as expected, in the cloud and on the owner's machine |
| The healthcare clone | Unchanged |

## 9. Not verified, and not done

- Nothing was built or run in the healthcare repository. An attempt was made on 2026-11-22: the .NET 10 SDK installs in the agent's workspace from the system's package index, but the solution's packages cannot be restored there, because the package registry is not reachable from the workspace or from the owner's machine's sandbox. So every statement about the code's behaviour comes from reading it.
- Line numbers are those of commit `8d04df3`.
- The plans for 001, 003, 005, 006 and 013 are not implemented. 004 is the one the walkthrough implements.
- No clinician has seen 005 or 006. The numbers in their evaluation designs are an agent's, and say so.
- No production database was looked at. 013's data-change plan is written for the worst case because of that.
- The observations of section 4 were not confirmed by a test.
