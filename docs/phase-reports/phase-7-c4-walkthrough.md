# Phase 7: the C4 change, taken as far as an agent can take it

- **Phase and date:** Phase 7, 2026-11-22
- **Upstream and reference:** spec-kit `v1.4.3`; healthcare repository `imatiqul/azure-ai-cloud-healthcare`, `main` at `8d04df3`
- **Requirement IDs exercised:** AGT-1 to AGT-6, AGT-10, AGT-17, AGT-19, QLT-1, QLT-3, QLT-5, QLT-7, TRC-19, GOV-17, GOV-20
- **Assumptions:** the stand-ins used to run the tests behave as the real packages do for the calls those tests make. One model played every agent; the two reviewing agents each started from a new session with a list of what they could read
- **Unverified:** the healthcare solution was not restored, built or tested: the package registry cannot be reached from the workspace, and no workflow has run in that repository since May 2026. No gate was passed. Nothing was pushed

The owner's instruction for this phase was to carry on without stopping at each gate and then wait. So nothing below is an approval. Every artefact that stands in front of a gate says it is waiting there.

## 1. What exists now

Three branches of the healthcare repository, each on top of the one before, built locally for the owner to push:

| Branch | Holds | For which review |
|---|---|---|
| `sdd/reference-plans` | Constitution version 2, the system map (100 components), specs 009 to 025, the plans of Phase 6, the agent team's 16 specs | G1 and G2 of the nine draft specs; G3 and G4 of the six plans |
| `sdd/004-audit-identity` | The change for finding C4: 14 code files, the record of how it was made, two reviews, the evidence for G5 to G7, and one correction to the map | G5 and G6 of spec 004, after the owner's amendments and a test run |
| `sdd/showcase-proposals` | A proposed adoption baseline, a threat model and an authorization matrix for C2, and the setting that lets the kit see finding H4 | The owner's decisions on each |

The change itself, in `sdd/004-audit-identity`:
- `PhiAuditMiddleware.cs`: the user of a record is the subject of the identity the service authenticated, read after the rest of the pipeline has run. No identity is recorded as `(unauthenticated)`, an identity with no subject as `(no-subject)`. Only an authenticated identity is asked for a subject. The event and the middleware's own log lines name the same user as the row.
- Nine `Program.cs` files: the audit middleware is registered directly after authentication and before authorization.
- Four test files, 80 tests: the middleware alone; the middleware in a real request pipeline with the framework's authentication and authorization; and a check of each service's `Program.cs` that fails, naming the service, when the order is wrong or something that can answer a request stands in front of the audit.

## 2. The gates of spec 004, as they stand

| Gate | What exists | State | What it waits for |
|---|---|---|---|
| G1, G2 | `spec.md` | Approved by the owner in conversation on 2026-11-22. No decision record | A pull-request review, and the seven amendments in `amendment-proposed.md` |
| G3 | `plan.md`, `impact.md`, threat model, privacy impact, rollout | Draft, corrected after the reviews | The owner's review |
| G4 | `tasks.md`, test strategy, trace manifest | Draft | The owner's review |
| G5 | Code and tests, evidence per task, the security review (two rounds), the line-by-line trace, `briefs/G5.md` | Evidence prepared. Cannot pass | A run of the solution's own tests (task T005); six failing checks (section 6) |
| G6 | `verification/G6-report.md` (two rounds), `G6-inputs.yml`, `briefs/G6.md` | A first verification, by reading and by a stand-in run. Task T006 is not claimed | T005, then the verification repeated on real results |
| G7 | `release/notes.md`, `release/operational-readiness.md`, `rollout.yml`, `briefs/G7.md` | Evidence prepared, decision pending | A bill of materials (needs a build), the rollback rehearsal and the staging checks (need an environment) |

Acceptance asks that every C4 gate decision is a human review mirrored in the record. That is not met and cannot be met by an agent: no decision exists for any gate of this spec.

## 3. The run log

Recorded with the kit in the working copy of the branch: `.specify/agentic/work/004-audit-identity/`, `.specify/agentic/runs/004-audit-identity/r1.yml`, and the hash-chained audit log. Times are UTC on 2026-11-22.

| Step | Agent | Did | Outcome |
|---|---|---|---|
| | orchestrator | Created six work items from the task list | T001 to T006 ready |
| 1 | backend-implementer | T001: the middleware | Handed off. The eleven existing tests: 8 pass, 3 fail, the three the plan said would |
| 2 | backend-implementer | T002: the nine `Program.cs` files | Handed off |
| 3 | test-agent | T003: the middleware tests and the pipeline tests | Handed off: 33 pass |
| 4 | test-agent | T004: the order tests | Handed off: 49 pass; 11 pass at the base commit; 9 of 9 seeded defects caught |
| 5 | security-reviewer, new session | Review for G5 | 15 findings. Accepts T002. Returns T001 (S-8, S-4), and the spec's documents (S-1, S-2, S-3) |
| 6 | independent-verifier, new session | Verification, with its own seeds and a real host | 14 findings. Returns T003 (V-3, V-4) and T004 (V-5) |
| 7 | backend-implementer | T001, rework 1 | Handed off |
| 8 | test-agent | T003, rework 1 | Handed off: 61 pass |
| 9 | test-agent | T004, rework 1 | Handed off: 80 pass; 24 of 24 seeded defects caught |
| 10 | security-reviewer | Round 2 | Accepts T001, T003, T004. S-1 and S-2 stay with the owner |
| 11 | independent-verifier | Round 2, with 20 more seeds | Accepts T001, T003, T004. V-1, V-2, V-12 stay |
| | orchestrator | Stopped the run | T005 and T006 open |

Three things about this record that a reader should know:
- **The change was written before the run was opened.** The files were then put in place task by task, in order, with the kit recording each claim and hand-off. The order and the content are real. The durations the kit recorded for steps 1 to 4 are those of the recording, not of the work. Steps 5 to 11 happened as recorded.
- **One session played the implementer and the test agent.** The test agent's rule is to write tests before reading the implementation; that was not kept, and each hand-off says so. The verifier's seeds show the cost: five defects passed every test until the rework.
- **No step records a cost.** The runtime did not report one and none was made up. `CK-RUN-RECORD` fails on it, and should.

## 4. What the two reviews found

Both reviewers were given the spec, the plan documents, the constitution, the map and the change, and no work record, hand-off note or conversation. Each listed every file it opened. Their reports are in the spec's folder: `reviews/G5-security.md` and `verification/G6-report.md`.

**In the code and tests, fixed in one rework round:**
- The subject could be read from an identity that was not authenticated (S-8, V-8).
- The log lines written after the pipeline named no user, so the only user on them was the log scope's, which a request header can set (S-4).
- No test looked at the user in the event or in a log line, at a 403, at the markers' text, or at a subject with capitals; three "rejected token" cases took the no-token path (V-3, V-4, S-9).
- The order check could be passed by a tenth service in the old order, in two ways, and looked at nothing in front of authentication (V-5, S-10).

**In the documents the agent had written, corrected:** the privacy impact was wrong about how a request arrives, where the identifier goes and who can read it (S-3, V-7); the threat model said its second threat was mitigated where it is not (S-2); the rollout's signals would have missed the likely failures and fired on a known one (S-12, V-11); the plan claimed a join to user accounts that does not hold (S-7).

**In the approved spec, proposed to the owner and not applied** (`amendment-proposed.md`, seven items): the event stream is touched, not only depended on; two criteria are abuse cases; FR-003 says more than the nine services can do, because the gateway refuses first and audits nothing; "each access to PHI" is each access on an audited path; which identifier accounts for a person; whether logs carry it; and whether the order the spec fixes is still what makes the record right.

**Left after the second round**, listed in the plan: two comments in the middleware that say slightly more than is true, eight of the verifier's further seeds that still pass every test, and four forms the order check does not read. Both reviewers accepted the items knowing this; an accepted item is closed.

## 5. What was verified, and how

| Claim | How | Result |
|---|---|---|
| The changed files compile under the repository's build settings | A stand-in project: the real files, `Directory.Build.props` (warnings are errors), the real ASP.NET Core 10; stand-ins for xUnit, FluentAssertions, NSubstitute and EF Core's in-memory provider (`examples/healthq/phase-7/harness`) | Builds with no warning |
| The tests pass | The same project | 80 passed, 0 failed |
| The existing tests passed before the change | The same project on the files at `8d04df3` | 11 passed, 0 failed |
| The tests fail when the code is wrong | 24 defects, one at a time, in a temporary copy | 24 of 24 caught. The verifier's 20 further seeds: 7 caught, 13 not (section 4) |
| Formatting | `dotnet format whitespace --folder --verify-no-changes` on the 14 files | No change |
| The middleware on a real host | The verifier's own program: Kestrel, routing, authentication, authorization | 401, 403, header, mixed case, two identities: as the tests say. A request that throws leaves no record |
| A changed line traces to its task, criteria, requirement, principle and component | `agentic.py why <file>:<line>` for one line of each of the 14 files (`evidence/trace-lines.md`) | Each resolves. Approvals: none recorded |
| The kit's checks on the branch | `check --base-ref <the governance branch>` | 80 pass, 23 fail, 1 not run |

None of this is a run of the solution's tests. The stand-ins accept what was written against them; the xUnit analyzers, which the real build runs as errors, did not run; no service was compiled or started.

## 6. What the kit refuses for this change, and who can clear it

| Check | Says | Cleared by |
|---|---|---|
| CK-TOUCH | `PhiAuditMiddleware.cs` belongs to the audit event stream, which the spec does not declare in `touches` | The owner: amendment 1 |
| CK-THREAT-MODEL | AC-004 and AC-005 test threats and are not written as abuse cases | The owner: amendment 2 |
| CK-GATE-RECORD | No decision record for G1, G2, G3 | The owner's pull-request reviews |
| CK-CHARACTERIZATION | The tests that pin the old behaviour exist and have not been run | A machine or pipeline that can run them (T005) |
| CK-RUN-RECORD | No step records what it cost | A runtime that reports it |
| CK-SBOM | A release folder exists with no bill of materials | A build |

The other 17 failing checks fail across the repository and are not caused by this change: suppressions with no waiver, unversioned contracts, unpinned images, the two findings the kit reproduces on the code (C6, and now H4 on the third branch), the three pairs of similar specs nobody has decided, and what is missing for the AI specs.

## 7. Found on the way, for the owner

Numbering continues from the Phase 6 report (O1 to O9). Each is in the plan of spec 004 with its evidence.

- **O10. The gateway refuses a caller with no token and writes no audit record.** It authenticates first and has no audit middleware. Inside the services only the OCR routes under an audited prefix have a guard.
- **O11. The bff calls six services directly and sends no token.** Those accesses are recorded with no person.
- **O12. The settings files give no service an identity provider.** The deployment workflow sets one when two repository variables exist and otherwise keeps the demo handler, with a message and exit status 0. In that mode every record names `demo-user` after this change.
- **O13. The application logs hold the user identifier beside the path**, and go to the telemetry store when one is configured.
- **O14. A request that ends in an exception leaves no row and no event.** A FHIR bulk export cut off part-way is one. If the identity provider cannot be reached, the bearer handler may throw; the request then ends in 500 with no record.
- **O15. An account's external identifier is whatever the caller sends**, on endpoints with no guard, and an unguarded endpoint returns the name and e-mail address for an identifier.
- **O16. A caller can make the audit write fail**, for example with a path longer than the column.
- **O17. The audited prefixes are not the routes that hold patient data.** The notification service serves none of them and records nothing.
- **O18. Every authorization policy admits the Admin role**, including the one named PlatformAdmin that guards tenant onboarding and the audit export. The export reads one of nine tables, with no tenant filter.
- **O19. `docs/compliance/FedRAMP-Authorization-Boundary.md:85` lists the user in the audit record as implemented.** Until this change the field held the same word for everyone.
- **O20. The map had the audit event stream with nobody writing to it.** All nine services do. Corrected in the map (206 dependencies, from 197). Who reads the stream is on no map.

## 8. What changed in the kit, from using it here

Each has a test. Details are in `docs/release-notes.md`.

1. A verifier may be given the code it verifies where a spec names components, not paths: the paths its tasks name, the files of the components it touches, and, to read only, the files of what it depends on.
2. `why <file>:<line>` goes back to the principle and forward to what the change reaches; the commit's work item settles which spec.
3. A rework in a shared working copy is no longer blamed for what others wrote meanwhile. Before, the hand-off of any returned item was refused once another item had been handed off.
4. A reviewing agent's findings for a gate are part of that gate's evidence.
5. `team init` changes only its own block of the settings file.
6. The check for figures with no source reads code and data files, so it can see finding H4.

## 9. Decisions made without the owner, and how to reverse each

Numbering continues from the Phase 6 report, which ends at 69.

| # | Decision | Why | To reverse |
|---|---|---|---|
| 70 | Ran the tests in a stand-in project | The packages cannot be restored here. Said in every evidence file that it is not the solution's test run | Ignore `examples/healthq/phase-7/harness`; T005 is the real run |
| 71 | Recorded the already-written change through the kit, task by task | The owner asked for the run log. Section 3 says what is and is not real about it | Delete `.specify/agentic/work`, `runs` and `context` for 004 and redo the tasks under the kit |
| 72 | The routing policy names the one model that ran, for all three classes | A Regulated project must have a policy; this is what happened | `team.routing` in `kit.yml` |
| 73 | No step cost was recorded | It is not known | Record costs if the runtime reports them |
| 74 | The security reviewer and the verifier ran as new sessions with input lists | The kit's sequential mode asks for exactly that | None needed |
| 75 | Asked the security reviewer whether "accept" stood, once told an accepted item cannot change again; it returned T001 | Its report asked for two changes to that file in this change | The question and the answer are in the item's finding text |
| 76 | The logs keep the user identifier | It is what the code did before. The other choice is the owner's (amendment 6) | Three log calls in `PhiAuditMiddleware.cs` |
| 77 | Did not write the record in a `finally`, mark the demo identity, or change which identifier is recorded | Each changes what the approved spec decided or scoped | Amendments 5 and 7; specs 001, 015, 016 |
| 78 | Closed the three items after the second round with leftovers listed, not a third round | Both reviewers accepted and said none needed another round | Ask for the leftovers in the pull request |
| 79 | Put the map correction in the C4 branch | It was found by tracing this change, and the tasks' context packs were built on the map as it was | Move the commit |
| 80 | Three stacked branches | Each is one review: plans, the change, proposals | Push only the last; it contains the others |
| 81 | The adoption baseline is a proposal file outside the folder the kit reads, with one date and an owner role per group | A baseline in that folder with no approval fails, and should | `.specify/agentic/proposals/adoption-baseline.md` |
| 82 | The reference tells the kit to read endpoint files for figures | So the check reproduces H4 | `metric_claims.scan` in `kit.yml` |

## 10. Not verified

- Anything that needs the solution to build: the nine services, the real test libraries and analyzers, coverage, a mutation score, a bill of materials.
- Anything that needs an environment: a real token through a service, PostgreSQL, the identity provider failing, the rollout.
- Whether the variables that switch on the identity provider are set in the repository.
- What reads the audit event stream or the telemetry store.
- The work records name the governance branch by the commit id it had in the workspace, `769efd4`. On the owner's machine the same tree has another id, because the commits there carry his name.
