# Reference system — azure-ai-cloud-healthcare (HealthQ Copilot)

This file is input data about the system used as proof. It adds no kit
requirements; it says which requirements the example exercises.

## System
- Repo: `imatiqul/azure-ai-cloud-healthcare`, referenced by commit SHA.
- Stack: .NET 10 microservices, React micro frontends, Semantic Kernel agents, Azure.
- Profile: Regulated, with the HIPAA domain pack.
- All data in the example is synthetic.

## Constitution topics (minimum)
Fail-closed authentication; authorization on every endpoint with tenant and patient
scoping; identity taken from the token only; minimisation, redaction and field
encryption of protected health information; complete, attributable audit trail;
clinical safety (no unvalidated triage logic, human in the loop, evaluated against a
real golden set); no fabricated data in production builds; CI gates that cannot be
bypassed; migration and dependency hygiene; data-store parity between test and
production; contract and shared-component compatibility; test and coverage standards.

## Findings to verify (claims, not facts, until Phase 1 confirms them)
Critical
- C1 Auth falls back to an all-roles demo identity when AzureAd config is absent
- C2 ~13 of ~240 endpoints enforce authorization; no tenant or patient scoping
- C3 X-Tenant-Id header and break-glass RequestedByUserId are caller-asserted
- C4 PHI audit middleware runs before authentication and logs "anonymous"
- C5 Triage level is set by keyword matching; RAG text pollutes the classifier
- C6 Clinical eval harness never invokes the classifier

High
- H1 Regex-only PHI redaction, flag-gated; PhiEncryptedString unused; patient IDs
  in localStorage
- H2 GraphQL BFF has no auth, token forwarding, or depth/cost limits
- H3 Frontend has no route guards or role checks; silent demo mode
- H4 Hardcoded KPI and model-accuracy endpoints ship in the Agents service
- H5 Migrations scaffolded on SQLite, run on Postgres with warnings suppressed
- H6 42 continue-on-error / `|| true` escapes in CI; tag-pinned actions; `:latest`

Medium
- M1 107 catch-all blocks, 27 fire-and-forget calls, sync-over-async at startup
- M2 Oversized endpoint and component files
- M3 191 test.skip calls that turn live failures into passes
- M4 Generated files and reports tracked in git; README/LICENSE mismatch
- M5 Suppressed NuGet advisories, one critical

Low
- To be derived in Phase 1, at most 10.

## Spec content
One spec per confirmed or corrected finding: user stories, acceptance criteria in
Given/When/Then, non-functional requirements, risks, `touches` and `depends_on`
against the system map, owner role, and gate reviewers derived from impact analysis.

## Showcases — which finding proves which capability
| Finding | Exercises | Depth |
|---|---|---|
| C4 | Full gate path G1–G7, traceability, agent team | Implemented to a draft PR |
| C2 | Impact analysis, programme spec (MAP-10 to MAP-14); later threat model and authorization matrix (QLT-3, QLT-5) | Analysis only, not implemented |
| H5 | Data-change plan (CHG-1 to CHG-4) | Spec and plan |
| C5, C6 | AI governance (QLT-13 to QLT-17) | Spec, eval design, safety case |
| H6, M3, M5 | Waiver register (GOV-15, GOV-16) | Every suppression removed or waived |
| H4 | No fabricated metrics (QLT-19) | Check result |

## C4 walkthrough scope
- Middleware ordering and attributable identity in the audit record.
- C4 depends on C1 and C3. Where they are unfixed, test against a valid token and
  record the residual risk; do not fix them in the C4 change.
- If the audit record's shape or storage changes, a data-change plan is required
  and every reader of the audit store is named from the map.
- Release is out of scope: G7 is recorded as "evidence prepared, decision pending".
