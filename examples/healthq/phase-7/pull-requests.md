# Pull requests for the three branches of the healthcare repository

- **Phase and date:** Phase 7, 2026-11-22
- **Upstream and reference:** spec-kit `v1.4.3`; `imatiqul/azure-ai-cloud-healthcare`, `main` at `8d04df3`
- **Requirement IDs exercised:** GOV-9, GOV-20
- **Assumptions:** the owner opens each as a draft, in this order, each based on the one before
- **Unverified:** these texts were not used. On 2026-11-22 the owner opened pull requests #73, #74 and #75 against `main`, not stacked and not as drafts, and merged them within a minute. No workflow of the repository ran on them. The texts are kept as what each branch holds and what its review was meant to look at

When this was written the branches existed only on the owner's machine (he has since pushed and merged them; see "Unverified" above), as local branches of `azure-ai-cloud-healthcare` on top of `origin/main`: `sdd/reference-plans` at `89a4fc9`, `sdd/004-audit-identity` at `1e8d054`, `sdd/showcase-proposals` at `a44c57c`. Each text below is a description to paste. A gate is passed by a review of the pull request, not by merging it and not by anything written here.

```bash
git push -u origin sdd/reference-plans sdd/004-audit-identity sdd/showcase-proposals
gh pr create --draft --base main --head sdd/reference-plans
gh pr create --draft --base sdd/reference-plans --head sdd/004-audit-identity
gh pr create --draft --base sdd/004-audit-identity --head sdd/showcase-proposals
```

The records inside the second branch name commits by the ids they had where the change was written. `commit-map.md`, beside this file, gives the id each has on the owner's machine.

## 1. `sdd/reference-plans` into `main`

**Title:** Governance: constitution version 2, the corrected system map, specs 009 to 025, draft plans, the agent team

Governance files only. No code changes.

- Constitution version 2: one sentence of P-7 changed, as approved on 2026-11-22.
- The system map: 100 components. Finding N9 of the first review was wrong and is corrected; 20 event topics and their publishers were missing and are added.
- Specs 009 to 025. 009 to 016 were approved at G1 and G2 in conversation. 017 to 025 are drafts that wait at those gates.
- Draft plans for 001, 003, 004, 005, 006 and 013, and a breakdown of 002 into ten parts. They wait at G3 and G4.
- The agent team: 16 specs under `.specify/agentic/agents/`, and a model routing policy that names the one model used so far.

What to review: the nine draft specs (G1, G2); three pairs of specs the kit lists as similar and nobody has decided; the six plans (G3, G4).
Known: the kit's gate check fails on every spec that has a plan, because no decision record exists. It should.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01A2CG7WvPeDnyLubfj4wQM5

## 2. `sdd/004-audit-identity` into `sdd/reference-plans`

**Title:** 004: audit records name the authenticated user (finding C4)

The PHI audit record named nobody: every row said `anonymous`. This change makes it name the caller the service authenticated.

- `PhiAuditMiddleware.cs`: the user is the subject of the authenticated identity, read after the rest of the pipeline has run. No identity: `(unauthenticated)`. An identity with no subject: `(no-subject)`. The event and the middleware's log lines name the same user.
- Nine `Program.cs` files: the audit middleware runs directly after authentication and before authorization.
- 80 tests in four files, one of which fails the build, naming the service, when the order is wrong.
- The record of how it was made: work items, the run, a security review and an independent verification by agents that had not written it (two rounds, one rework), the trace from each changed line.
- One correction to the system map: the nine services write the audit event stream.

**Not built and not run.** The solution's packages could not be restored where this was written. The tests ran in a stand-in project against the real ASP.NET Core; `specs/004-audit-identity/evidence/` says exactly what that shows and what it does not. Task T005 is the real run; T006 repeats the verification on it.

**Commit ids in the records** (work items, the two reviews, `evidence/trace-lines.md`) are those of the workspace where the change was written. `examples/healthq/phase-7/commit-map.md` in `imatiqul/agentic-spec-kit` maps each to its id here.

**Before this can pass G5:** read `specs/004-audit-identity/amendment-proposed.md`. Seven things in the approved spec are wrong, say more than the code can do, or leave a decision open. Two of them clear failing checks.

**It does not close:** a caller with no token is refused at the gateway, which writes no audit record; the bff and service-to-service calls carry no user; without an identity provider every record names `demo-user`. The plan lists these under "Found while planning".

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01A2CG7WvPeDnyLubfj4wQM5

## 3. `sdd/showcase-proposals` into `sdd/004-audit-identity`

**Title:** Proposals: an adoption baseline, the threat model and authorization matrix for C2, and a setting that lets the kit see H4

Governance files only. Nothing here is approved or enforced.

- `.specify/agentic/proposals/adoption-baseline.md`: the 635 suppressions and open map questions the kit finds, in 14 groups, each with a proposed owner and one proposed date. Approving it is a review of this pull request; the file the kit reads is added afterwards.
- `specs/002-endpoint-authorization/threat-model.yml` and `authorization-matrix.yml`: analysis for finding C2. Three threats tested by the spec's abuse cases, six the spec has no test for, and 20 rows of who may reach what. No row has been run.
- `kit.yml`: the kit now reads the endpoint files for figures with no recorded source. It reports 60, among them `aiAccuracyRate = 94.2` (finding H4).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01A2CG7WvPeDnyLubfj4wQM5
