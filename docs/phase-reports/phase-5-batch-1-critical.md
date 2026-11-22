# Phase 5, batch 1 — reference specs for the Critical findings (approved at gates G1 and G2 on 2026-11-22)

- **Phase and date:** Phase 5, batch 1 of 4, 2026-11-22
- **Upstream and reference:** spec-kit `v1.4.3`; healthcare repository `imatiqul/azure-ai-cloud-healthcare` at commit `6e0879d2`, read only
- **Requirement IDs exercised:** GOV-9, GOV-10, MAP-4, MAP-5, MAP-8, MAP-10 to MAP-13, TRC-1, PRD-1 to PRD-4, INT-5
- **Assumptions:** the 18 questions written into the specs, and the decisions in section 6. Section 9 says what the owner decided about them
- **Unverified:** nothing was built or run in the healthcare repository. No agent team wrote these specs; one agent did. See section 7

## 1. What this is

The owner approved the reference constitution at gate G0 on 2026-11-22. The phase plan then asks for one spec per finding, in four batches by tier, with a stop after each. This is the first batch: the six Critical findings, and the two findings from Phase 1 that an agent proposed as Critical (N1 and N2).

The work stopped here for the owner's decisions on G1 and G2. Sections 1 to 8 are the report as he saw it. Section 9 records what he decided and what was done about it.

## 2. What was produced

| Path | What it is |
|---|---|
| `examples/healthq/project/` | The reference as a project the kit can check: Regulated profile, HIPAA pack, roles, the approved constitution and its map, the system map, the specs. It holds no source code from the healthcare repository (charter D1) |
| `examples/healthq/project/system-map/map.yml` | The Phase 1 draft map in the kit's format: 77 nodes, 168 edges, 48 path-index entries |
| `examples/healthq/phase-5/convert_map.py` | The conversion, so that it can be repeated |
| `examples/healthq/project/specs/00N-…/spec.md` | The eight specs |
| `…/impact.md`, `…/briefs/G1.md` | For each spec: the kit's impact report, and the reviewer's one page for G1 |
| `examples/healthq/overlay.py` | Lays the project over a copy of the healthcare repository and runs the kit there. The repository itself is cloned and never changed |
| `examples/healthq/export.py` | Writes the project as it goes into the healthcare repository (added after the owner's decision; see section 9) |
| `tests/test_reference.py` | 26 tests that keep the reference valid against the kit |

## 3. The specs

| Spec | Finding | Says | Owner role | Requirements, criteria (abuse cases) | Comes after |
|---|---|---|---|---|---|
| `001-fail-closed-auth` | C1 | A service with no identity provider refuses to start; the demo identity exists only in Development | platform | 5, 7 (1) | — |
| `002-endpoint-authorization` | C2 | Every endpoint names its policy; reads are limited to the caller's tenant and patients | backend | 7, 7 (3) | 001, 003, 004, 005, 007, 008 |
| `003-identity-from-token` | C3 | Tenant, user and break-glass requester come from the validated token, never a header or body | backend | 6, 6 (3) | 001 |
| `004-audit-identity` | C4 | The audit middleware runs after authentication; each record names the authenticated user | backend | 5, 6 (1) | 001, 003 |
| `005-triage-validation` | C5 | Triage is proven on a clinician's golden set; retrieved text never reaches the classifier; a clinician confirms | ai-engineer | 7, 8 (2) | 004, 006 |
| `006-eval-production-path` | C6 | The evaluation calls the production classifier, scores against the clinician's labels, and runs in the pipeline | ai-engineer | 8, 9 (2) | — |
| `007-audit-export-complete` | N1 | An audit export covers every service that writes audit records, or fails | security-compliance | 5, 5 (1) | 003, 004 |
| `008-audit-append-only` | N2 | The database, by migration, refuses updates and deletions of audit records | security-compliance | 5, 5 (2) | 001, 003, 004, 007 |

In all: 48 requirements, 53 acceptance criteria in Given/When/Then, 15 of them abuse cases, in 641 lines. Every spec has the seven sections the HIPAA pack requires, a risks section, what is out of scope, and its questions for G2.

### Reviewers the kit derives from the system map

The defaults are the Product Owner at G1, the Product Owner and Solutions Architect at G2, the Solutions Architect at G3 and QA at G5. Impact analysis adds:

| Spec | Added at G3 (the plan) | Added at G5 (the implementation) | Change packs |
|---|---|---|---|
| 001 | backend, platform, security-compliance | platform | shared component |
| 002 | backend, data-owner, platform, security-compliance | backend, platform, security-compliance | shared component |
| 003 | backend, data-owner, platform, security-compliance | backend, platform, security-compliance | shared component |
| 004 | backend, data-owner, platform, security-compliance | backend, platform, security-compliance | shared component |
| 005 | ai-engineer, backend, data-owner, security-compliance | ai-engineer, backend, security-compliance | none |
| 006 | ai-engineer | ai-engineer | none |
| 007 | backend, data-owner, security-compliance | backend, data-owner, security-compliance | data store |
| 008 | backend, data-owner, platform, security-compliance | data-owner, platform, security-compliance | data store, shared component |

Each of the first four reaches twelve other components, because all of them change the shared infrastructure library. Spec 006 reaches none: on the map nothing connects the golden set to the classifier, which is finding C6 seen from the map's side.

Under charter D3 one person holds every role, so each of these is the owner acting in that role, with a single-approver exception stated.

## 4. Verification

| What | Result |
|---|---|
| 18 of the kit's checks that judge specs, the map and the constitution, run on `examples/healthq/project` | All pass: constitution map, roles, requirement quality, size, HIPAA sections, tier against the map, touches, trace to principles, ordering of specs that share a component, impact reports, map format and ownership, briefs, lanes, audit chain |
| Negative controls on a copy of the project | Each fails as it should: a vague word; two obligations in one requirement; a requirement with no criterion; a missing HIPAA section; a tier declared lower than the map's; a removed ordering between two specs that share a component; a node that is not on the map; a principle that is not in the constitution; an owner role that does not exist |
| Every check, over a copy of the healthcare repository (`overlay.py`) | 87 passed, 15 failed, 2 not run. The failures are section 5 |
| Every derived fact in the map cites a file that exists in the healthcare repository | Pass (229 failures without the source; none with it) |
| The healthcare clone after all of this | Unchanged: `git status` is empty |
| `tests/test_reference.py` | 26 passed in the cloud with the clone. On the owner's machine: 25 passed, 1 skipped (the test that needs a clone of the healthcare repository) |
| Whole suite | Cloud, one run: 473 passed, 1 skipped, in 6 min 48 s. On the owner's machine the earlier 448 were not re-run; nothing they test changed |

Commands:

```bash
python -m pytest tests/test_reference.py -q
HEALTHQ_REPO=<clone> python -m pytest tests/test_reference.py -q
python examples/healthq/overlay.py <clone> <a new folder>
```

## 5. What the kit says about HealthQ today

From the overlay run, on the code as it is at `6e0879d2`. These are not defects of this batch; they are the state the specs exist to change, and what an adoption baseline would have to record.

| Check | Finds | Phase 1 finding it matches |
|---|---|---|
| CK-PIN | 200 action references not pinned to a commit, and other floating references | H6: "200 `uses:` lines, none pinned" |
| CK-WAIVER | Suppressions with no waiver, among them 5 suppressed advisories | M5: 5 suppressed advisories; H6, M3 |
| CK-MIGRATION-DRIFT | 1 suppressed migration warning | H5 |
| CK-MIGRATION-ENGINE | The map does not say which engine and version production runs, for 4 stores | H5 |
| CK-ENV-PARITY | No record of how test and production differ | H5 |
| CK-CONTRACT-VERSION, -DRIFT, -CONSUMER | 16 contracts with no version, 16 with no stated way to detect drift from the code, 15 consumers with no contract test | N9 |
| CK-SHARED-SEMVER | 11 shared components with no version | — |
| CK-EXTERNAL-DEP | 10 external dependencies with no record of contract, timeout, retry or test double | — |
| CK-AI-VERSION | The 4 AI components have no kind or version | C5, C6 |
| CK-MAP-DRIFT | 26 differences between the map and what the kit's own discovery finds, mostly names (the map says `pkg-auth-client`, the code says `healthcare-auth-client`) | — |
| CK-ENFORCE-SETUP | The account the agent runs under is the account listed as approver | See section 6, decision 44 |
| CK-ROUTING | No model routing policy | — |
| CK-DUPLICATE | Two pairs of specs look alike and nobody has decided | Section 6 |
| Not run: CK-CRED, CK-AGENT-SPEC | No access to the repository's settings from here; the agent team is not installed in the reference | — |

## 6. Decisions

### For the owner, at this stop

1. **G1 for each of the eight specs:** is this the right thing to ask for?
2. **Two pairs the kit lists as similar.** A Product Owner must record a disposition for each before G1 can pass. Recommended: `distinct` for both.
   - `002` and `003` (score 0.31; they share request, tenant, endpoint, authorization, policy). 002 is about what a caller may reach; 003 is about where the caller's identity comes from, and 002 depends on it.
   - `005` and `006` (score 0.37; classifier, clinician, triage, evaluation, level). 005 changes the classifier; 006 builds the evaluation that 005's release depends on.
3. **G2, the 18 assumptions.** Each spec ends with them. Fourteen are engineering choices with a stated default. Four need someone else:
   - `005` A1 to A3 and `006` A1 are clinical: whether raising a priority needs confirmation, the thresholds, who signs them. They need a clinician.
   - `008` A2, how long audit records are kept, needs whoever answers for compliance.
4. **The tier of N1 and N2.** Critical is an agent's proposal from Phase 1.
5. **Whether the reference should move into the healthcare repository.** See decision 43.

### Made by the agent in this batch, each reversible

Numbering continues from the Phase 3e report.

| # | Decision | Why | To reverse |
|---|---|---|---|
| 36 | `roles.yml` lists the owner for all eleven roles, and single-approver exceptions are allowed | Charter D3 | Edit `examples/healthq/project/.specify/agentic/roles.yml` and `kit.yml` |
| 37 | The 20 components Phase 1 could not classify are treated as `restricted` | Otherwise a change to them would not ask Security and Compliance | Classify them in `convert_map.py` or in the map |
| 38 | Where Phase 1 cited a description, not a file, the file was looked up in the clone: 19 components and 26 publish or subscribe edges. None had to be downgraded to "assumed" | The kit requires a derived fact to cite a file that exists | `convert_map.py` |
| 39 | C2 is one spec in this batch. Its breakdown into a programme with a child per service is Phase 6, as the phase plan says | A programme needs its children to exist | Add `programme:` to the spec's front matter and write the children |
| 40 | The order between specs that share a component: 001, 003, 004, 007, 008; 006 then 005; 002 after all of them | The kit requires an order. C4 depends on C1 and C3 (the reference brief). Nothing waits on 002, which is analysis only | `depends_on.specs` in each spec |
| 41 | 005 covers what finding N5 says (negation, and unmatched input treated as non-urgent) | The corrected C5 statement already includes both | Take FR-004 and FR-005 out of 005; N5 then gets them in the High batch |
| 42 | The reference does not use living capability specs, deltas, intake records or outcomes (slice 0.5) | Phase 5 predates that slice. Using it needs an adoption pass that describes HealthQ's current behaviour | Run `product init` in the project and write adoption deltas |
| 43 | The reference lives in this repository, with an overlay script for the checks that read source | Charter D1 | With the owner's approval: put `.specify/`, `system-map/` and `specs/` on a feature branch of the healthcare repository and open a draft pull request. That is the only way a gate here can be passed as the kit prescribes, by a review |
| 44 | The enforcement adapter is GitHub, pointed at the healthcare repository | That is where approvals will come from | `kit.yml`: `enforcement` |

On decision 44, a finding for the owner: **the kit reports that the agent runs under the same GitHub account as the only approver.** While that is so, an approval "by imatiqul" could have been made by an agent, and GitHub will not let the author of a pull request approve it. Before Phase 7, agents need an identity of their own (a GitHub App or a second account) for anything they push or open.

## 7. Not verified, and not done

- **No agent team was used.** One agent wrote the specs. The Spec Author, Orchestrator and Independent Verifier roles are exercised in Phase 7.
- **Nothing ran in the healthcare repository's pipeline,** and no file was written to that repository.
- **No kit decision record exists** for any gate of the reference. G0 was approved in chat. A record needs a pull-request review.
- **The system map's owners, tiers and classifications are still Phase 1 proposals.** They are confirmed when a plan is reviewed (G3). The 26 naming differences from discovery are not reconciled.
- **No adoption baseline** has been drafted for the gaps in section 5.
- **The other three batches:** 6 High, 5 Medium and the remaining 8 additional findings (3 High, 1 Medium, 4 Low). Not started.

## 8. What happens after the owner decides

- G1 and G2 approved: the dispositions and the answers are recorded in the specs in the owner's words, the batch is committed, and the High batch is drafted. Phase 6 (plans, tasks, data-change plans for 007 and 008, the programme breakdown of 002) starts when all four batches are through, or sooner for C4 alone if the owner prefers.
- Anything rejected or changed: the spec is amended and its brief regenerated before it is shown again.

## 9. The owner's decision, 2026-11-22, and what followed

At 12:35 Central time the owner answered:

> 1. G1: yes
> 2. G2: approve
> 3. Move the reference into the healthcare repo? yes

| Decision | Recorded in | What the agent read into it |
|---|---|---|
| G1 approved for all eight specs | Each spec's header; the charter's decision log; the README | Nothing beyond the words |
| The two similar pairs are `distinct` | `origin.yml` of 002, 003, 005 and 006, decided by the owner as Product Owner | The owner did not use the word. He approved both specs of each pair after being told `distinct` would be recorded. CK-DUPLICATE passes now |
| G2 approved | "Decided at G2" in each spec: 14 assumptions accepted; 4 left as conditions for a clinician to settle at G3 (005 A1 to A3, 006 A1) | He wrote "approve". Treating the four clinical items as conditions, and not as settled, is the agent's reading and the more cautious one. How long audit records are kept (008 A2) is outside the spec and still undecided |
| N1 and N2 are Critical | Approved with their specs | |
| The reference moves into the healthcare repository | Charter D1, amended, and its decision log | See what follows |

None of these is a kit decision record. That needs a pull-request review, and the end of this section says why one cannot be made yet.

### The reference in the healthcare repository

- Branch `sdd/reference-governance`, one commit, `c4ebd13`, on top of `6e0879d2`. It adds 53 files and changes none: the constitution, the kit's settings, roles, the constitution map, the audit log, the system map, the eight specs with their impact reports and briefs, a CODEOWNERS file, and a short README under `.specify/agentic/`.
- It was built in the owner's local repository without checking anything out: his working tree, index and current branch were not touched. The content was compared, file by file, with `examples/healthq/export.py`'s output.
- **It is not pushed.** This session can read the healthcare repository and is refused pushes to it. The branch is on the owner's machine for him to push and open as a draft pull request; the description is in `examples/healthq/phase-5/pull-request.md`.
- Two files of `examples/healthq/project` were left out on purpose, because they would say something untrue there: the marker that Spec Kit is initialised, and the workflow that runs the kit's checks. Spec Kit and the kit are not installed in the healthcare repository.

The kit run on that tree: 87 checks pass, 15 fail, 2 could not run. Against section 5, CK-DUPLICATE now passes, CK-UPSTREAM-PIN cannot run (Spec Kit is not initialised there), and CK-CRED can now read the repository's settings and fails:

- the account this session presents as, the owner's, has admin rights on the repository;
- the default branch does not require a pull-request review, so that account can change it alone;
- that same account is the only approver in `roles.yml`.

What has to be true before a gate can be passed there by a review, as the kit prescribes:

1. The branch is pushed and a draft pull request is open.
2. Agents push and open pull requests under an identity that is not the owner's. GitHub does not let the author of a pull request approve it, and an approval by the account agents also use proves nothing.
3. `main` is protected: a pull request and a review are required (`docs/admin-setup.md`).
4. Spec Kit and the kit are installed there, with the checks workflow. That is a further change to the healthcare repository and needs the owner's approval of its own.
