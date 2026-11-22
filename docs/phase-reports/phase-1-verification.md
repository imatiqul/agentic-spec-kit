# Phase 1 — Findings verification and system map

- **Phase and date:** Phase 1, 2026-11-21
- **Pinned upstream:** github/spec-kit `v1.4.3` (not used in this phase)
- **Reference repo:** `imatiqul/azure-ai-cloud-healthcare`, branch `main`, commit `6e0879d27bb59017f34544aa60e3033cce75e31d`, dated 2026-08-03
- **Requirement IDs exercised:** MAP-1 to MAP-5, MAP-15
- **Assumptions:** the head of `main` is the right commit; the cloud deployment matches what the repo's workflows describe
- **Unverified:** see section 6. Nothing was built or run; all evidence is from reading files. The clone is unmodified (`git status` clean).

Every count below is reproduced by `verify-findings.sh <repo>`; its output is in `verify-output.txt`. Paths are relative to the healthcare repo.

## 1. Bottom line
- **All 17 findings stand.** 13 are confirmed as written, 4 are corrected (C1, C2, H6 and M1), none is stale or false.
- **Two corrections matter.** C1 and C2 are less exposed from the internet than the wording suggests, because the gateway requires a token on every proxied route and production gateway config has Entra ID set. They are fully exposed service-to-service, and the deploy workflow leaves demo auth on whenever three repository variables are unset.
- **C4 is larger than described.** The audit trail has four further defects beyond middleware order (section 3). They change the scope of the Phase 7 walkthrough, so I need a decision.
- **The system map has 77 nodes and 168 edges**, 16 of them assumed. It surfaced one structural fact no finding mentioned: the audit table exists nine times, once per service database, and the export endpoint reads only one of them.

## 2. Verification results

| ID | Status | Corrected statement or note | Key evidence |
|---|---|---|---|
| C1 | Corrected | Demo identity with Admin, Clinician, PlatformAdmin and Patient roles is used by all 10 services when `AzureAd:ClientId` is absent. The deploy workflow explicitly keeps "demo auth mode" when its Entra variables are unset. Production gateway config does have Entra set. | `src/HealthQCopilot.Infrastructure/Auth/JwtBearerExtensions.cs:27-34, 73-81`; `.github/workflows/microservice-deploy.yml:457-461`; `src/HealthQCopilot.Gateway/appsettings.Production.json:2-7` |
| C2 | Corrected | 263 endpoints (243 minimal API, 20 controller actions). 12 `RequireAuthorization` calls, 0 `[Authorize]`. Three of the calls are on groups covering 10 endpoints. The gateway requires authentication on all proxied routes, so the gap is authorization and scoping, plus any path that reaches a service without the gateway. No tenant or patient scoping found. | `verify-output.txt` C2; `src/HealthQCopilot.Gateway/Program.cs:49` |
| C3 | Confirmed | `X-Tenant-Id` is preferred over the token's `tid` claim (4 reads). Break-glass takes `RequestedByUserId` from the request body and its route group has no authorization. Also: `X-User-Id` is accepted as the user for log context. | `src/HealthQCopilot.Infrastructure/Middleware/TenantContextMiddleware.cs:27-36`; `src/HealthQCopilot.Identity/Endpoints/BreakGlassEndpoints.cs:27-54` |
| C4 | Confirmed | In all 9 services the audit middleware is registered before `UseAuthentication`, and it reads the user before calling the next middleware, so the user is always "anonymous". | `src/HealthQCopilot.Infrastructure/Middleware/PhiAuditMiddleware.cs:62`; line pairs in `verify-output.txt` C4 |
| C5 | Confirmed | `classify_urgency` is three keyword rules with a default of P4. The orchestrator passes transcript plus retrieved text to it. Not in the finding: no negation handling ("denies chest pain" matches P1), and anything unmatched is non-urgent. | `src/HealthQCopilot.Agents/Plugins/TriagePlugin.cs:15-39`; `src/HealthQCopilot.Agents/Services/TriageOrchestrator.cs:148-158` |
| C6 | Confirmed | Worse than stated. The harness scores each case by checking whether the input contains its own expected keywords; P3 cases pass by default. The golden set has 5 cases. No workflow runs that test project. The CI gate that does run uses a stub that echoes the expected phrase, with a baseline of 1.0. Zero references to the classifier in eval code. | `tests/HealthQCopilot.Tests.Eval/ClinicalAccuracyHarnessTests.cs:41-46`; `tests/HealthQCopilot.Tests.Unit/Agents/AgentEvalCiGateTests.cs:14-29` |
| H1 | Confirmed | Two regex redactors; 4 call sites gate redaction on the `HealthQ:PhiRedaction` flag; `PhiEncryptedString` has no use outside its own file; recent patient IDs go to `localStorage`. Also: the chat keeps its last 50 messages in `localStorage`. | `src/HealthQCopilot.Infrastructure/AI/RegexPhiRedactor.cs`; `frontend/apps/shell/src/components/PatientQuickSearch.tsx:81`; `frontend/apps/shell/src/components/CopilotChat.tsx:21` |
| H2 | Confirmed | No authentication, no authorization, no token forwarding on the six typed HTTP clients, no depth or cost rules. The gateway routes `/graphql` to it. | `src/HealthQCopilot.BFF/Program.cs:11-67`; `src/HealthQCopilot.Gateway/appsettings.json:78-80` |
| H3 | Confirmed | No route guard or role check in any frontend app. When the client ID is not configured, sign-in is a no-op that logs a console warning. | `frontend/packages/auth-client/src/client.ts:31-47`; `verify-output.txt` H3 |
| H4 | Confirmed | 22 hardcoded endpoints, including `/api/v1/kpi` with `aiAccuracyRate = 94.2` and per-model accuracy figures, mapped with no environment check. Also: `POST /api/v1/agents/seed` is unauthenticated. | `src/HealthQCopilot.Agents/Endpoints/DemoDataEndpoints.cs:29-55`; `src/HealthQCopilot.Agents/Program.cs:406-409` |
| H5 | Confirmed | 24 of 53 migration files carry SQLite column types; the design-time factory uses SQLite; `PendingModelChangesWarning` is ignored on PostgreSQL, with a comment that says why. | `src/HealthQCopilot.Infrastructure/Persistence/DatabaseExtensions.cs:46-52`; `src/HealthQCopilot.Agents/Infrastructure/AgentDbContextFactory.cs:11` |
| H6 | Corrected | 40 escapes, not 42 (27 `continue-on-error: true`, 13 `\|\| true`). 200 `uses:` lines, none pinned to a commit SHA. 16 `:latest` references. | `verify-output.txt` H6 |
| M1 | Corrected | With the patterns in the script: 128 `catch (Exception)`, 12 bare `catch`, 36 discarded tasks, 7 blocking calls (6 at startup in Agents). The original counts were 107 and 27; the difference is probably the pattern used. | `verify-output.txt` M1; `src/HealthQCopilot.Agents/Program.cs:292-364` |
| M2 | Confirmed | Largest: `VoiceSessionController.tsx` 1,030 lines, `WorkflowOperationsWorkbench.tsx` 972, `FhirEndpoints.cs` 812. | `verify-output.txt` M2 |
| M3 | Confirmed | 191 `test.skip(` calls; at least 31 skip when a live service does not respond, so an outage reports as skipped, not failed. | `frontend/e2e-cloud/cloud-smoke.spec.ts:222-255` |
| M4 | Confirmed | 47 tracked `.map` files under `@mf-types`, a tracked Playwright report that `.gitignore` lists, and README says "Proprietary - all rights reserved" while LICENSE is MIT. | `README.md` licence section; `LICENSE:1` |
| M5 | Confirmed | 5 suppressed advisories, 1 marked critical (HotChocolate.Language). The comment dates the suppression to April 2026. | `Directory.Build.props:11-22` |

## 3. Additional findings (10)
Tiers are my proposal. Several are not Low; I have listed them honestly instead of forcing them into the Low tier.

| ID | Proposed tier | Finding | Evidence | Relates to |
|---|---|---|---|---|
| N1 | Critical | The audit table exists once per service database (9 copies). The audit export endpoint reads only the Identity database, so an export omits access to every other service. | `AddHealthcareDb<AuditDbContext>` in 9 `Program.cs` files; `src/HealthQCopilot.Identity/Endpoints/AuditExportEndpoints.cs:29-67` | C4 |
| N2 | Critical | The audit log is described as append-only with row-level security, but the SQL exists only as a comment. No migration creates or protects the table. | `src/HealthQCopilot.Infrastructure/Persistence/AuditDbContext.cs:31-34`; `verify-output.txt` C4 | C4 |
| N3 | High | Audit writes are fire-and-forget and failures are only logged, so an audit record can be lost without the request failing. | `src/HealthQCopilot.Infrastructure/Middleware/PhiAuditMiddleware.cs:82, 112-115` | C4, M1 |
| N4 | High | The audit record has no tenant, no patient and no outcome detail; it stores user, method, path, status and time only. The audited paths are a hardcoded prefix list. | `src/HealthQCopilot.Infrastructure/Persistence/AuditDbContext.cs:38-47`; `PhiAuditMiddleware.cs:22-36` | C4 |
| N5 | High | Triage has no negation handling and defaults to non-urgent for unmatched input. | `src/HealthQCopilot.Agents/Plugins/TriagePlugin.cs:17-39` | C5 |
| N6 | Medium | CORS allows any header and method with credentials; the fallback origin is localhost. | `src/HealthQCopilot.Gateway/Program.cs:13-22` | — |
| N7 | Low | Production gateway config commits the tenant ID, client ID and internal hostnames. Not secrets, but environment-specific values in source. | `src/HealthQCopilot.Gateway/appsettings.Production.json:2-7, 81` | — |
| N8 | Low | Development containers use floating tags (`2022-latest`, `latest`). | `src/HealthQCopilot.AppHost/Program.cs:112, 117` | H6 |
| N9 | Low | **Wrong as written; corrected in section 9.** Two topics have subscribers but no publisher I could derive; 27 publish calls use non-literal topic names, so event contracts cannot be checked statically. | system map `topic-triage.completed`, `topic-escalation.required` | — |
| N10 | Low | The last commit is 2026-08-03, and advisory suppressions say "revisit" as of April 2026. Review is overdue. | `git log -1`; `Directory.Build.props:11` | M5 |

Things that are in good shape, for balance: all 11 Dockerfiles set a non-root `USER`; Dependabot covers NuGet, npm, Actions and Docker; there are 18 architecture tests and 578 unit and integration tests; a pattern scan found no hardcoded secrets (one credential literal has been found since; see section 9); warnings are treated as errors.

## 4. System map
File: `healthq-system-map.draft.yml`, generated by `gen_map.py` and validated (unique IDs, no dangling edges).

| Node type | Count | | Edge type | Count |
|---|---|---|---|---|
| Events (topics) | 15 | | builds-with | 79 |
| Services | 11 | | calls | 22 |
| Schemas | 9 | | subscribes | 15 |
| External services | 9 | | writes | 11 |
| Frontends | 8 | | publishes | 11 |
| Shared packages | 8 | | authenticates-via | 10 |
| Data stores | 4 | | owns | 9 |
| AI components | 4 | | deploys-with | 7 |
| Shared libraries | 3 | | reads | 4 |
| Contracts, other | 6 | | | |

- **Assumed:** 1 node (the GraphQL contract, which has no committed schema file) and 15 edges (gateway to each service, three service-to-Azure calls, FHIR server, model calls, frontend to gateway).
- **Highest blast radius:** `lib-infrastructure`. Auth, audit, tenant context and persistence all live there and all 11 services build with it. Any C1, C3 or C4 fix is a shared-component change reaching every service.
- **Owners, tiers and classifications are proposals.** You confirm them at the gate.
- **Not mapped:** listed at the end of the file (per-route gateway targets, tables inside each database, Redis and Cosmos contents, deployment topology).

## 5. What this means for the kit and the plan
- **C4 walkthrough scope.** Fixing only the middleware order leaves N1 to N4 in place, and the charter's definition of done asks for an attributable audit trail. Options are in section 7.
- **MAP-10 has a real test case.** A one-line change in `lib-infrastructure` reaches 11 services and 9 databases.
- **CHG-4 has a real test case.** H5 matches "migrations tested on the production engine" exactly.
- **QLT-15 has a real test case.** C6 is an evaluation that never calls production code.
- **GOV-15 has real volume.** 40 CI escapes, 191 skips and 5 suppressed advisories would become about 236 waiver decisions. The kit needs a bulk path for adopting an existing codebase, which the spec does not yet have.

## 6. What I did not verify
- Nothing was compiled or executed. Runtime behaviour is inferred from code.
- Whether the live deployment has the Entra variables set, and whether services are reachable without the gateway.
- How `phi_audit_logs` is created at runtime (no migration found; `InitializeDatabaseAsync` was not read).
- Endpoint counts are pattern matches on `Map*` calls and `[Http*]` attributes; endpoints registered another way would be missed.
- Tenant and patient scoping was checked by searching for filters, not by reading every query.
- Frontend route count and the 31 conditional skips are lower bounds.
- The 15 assumed edges and everything under `not_mapped`.

## 7. Decisions I need from you
1. **Approve the verification** (17 findings stand, 4 with corrected wording).
2. **C4 scope for the walkthrough.** (a) Order and identity only, as planned, with N1 to N4 recorded as residual risk; (b) order, identity, tenant and patient fields, and durable writes, leaving consolidation (N1) and immutability (N2) as separate specs; (c) all of it. I recommend (b): it produces an attributable record and exercises the data-change pack, while (c) is a multi-service migration too large for one walkthrough.
3. **Tiers for N1 to N10**, or accept my proposals. Each becomes a spec in Phase 5.
4. **Confirm or correct the owners and tiers** in the system map, or defer that to the Phase 2 design gate.
5. **Bulk waivers.** Whether to add a requirement for adopting existing suppressions in bulk (see section 5). This would be a spec change to `spec/10-governance.md`.

## 8. What Phase 2 needs from you
Approval of this phase. Phase 2 is design only: schemas, check list, adapter interfaces, agent roster, and the full source review of `spec-gates`, `specassay` and `spec-kit-ado`.

## 9. Corrections made after this report, 2026-11-22

The text above is the report as the owner saw it on 2026-11-21, with two marks that point here. Three of its statements were wrong or incomplete. Each was found while the reference specs and plans were being written.

1. **Finding N9 was wrong.** It said two topics had subscribers and no publisher, and that 27 publish calls named their topic by something other than a literal. The pattern in `gen_map.py` read only calls written on one line with positional arguments. Calls that name their arguments across lines were not read, so their topics were missed and they were counted as "non-literal". An automated review of pull request 72 in the healthcare repository pointed to the two publishers (`src/HealthQCopilot.Agents/EventHandlers/TriageCompletedHandler.cs:37`, `EscalationRequiredHandler.cs:32`, and `src/HealthQCopilot.Agents/Services/TriageOrchestrator.cs:299-302`).
   What the code shows, by the kit's discovery (added to the kit for this, with tests): 35 topics. 33 are published, from 38 call sites; 2 of those choose between two literals at run time. One topic, `revenue.prior-auth.status-changed`, has a subscriber and no publisher. `healthq-dlq` is the dead-letter topic. 25 published topics have no subscriber in the repository. Spec `025` is rewritten to this.
2. **The draft map was missing 20 topics, 22 publisher edges and 7 build edges.** `examples/healthq/system-map.draft.yml` is left as it was. The map the kit checks (`examples/healthq/project/system-map/map.yml`) has them, each citing its file, and the kit's drift check now passes against the code. Impact reports that relied on the missing edges were regenerated: a change to the agent service now reaches the four services that subscribe to its events.
3. **"A pattern scan found no hardcoded secrets" was incomplete.** `src/HealthQCopilot.AppHost/Program.cs:114` sets the password of a local emulator's database as a literal. It is for a development container. The value is not recorded in this repository. A second, wider pattern on 2026-11-22 found no other such literal; neither pattern is a secret scan.

Also learned since, and not an error in this report: the 18 architecture tests it counts are not run by any workflow, and no workflow of the repository other than Dependabot's and the Copilot reviewer's has run since May 2026. `docs/phase-reports/phase-6-plans.md` has the evidence.
