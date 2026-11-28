# Check catalogue

- **Phase and date:** Phase 2 (design), 2026-11-21
- **Requirement IDs covered:** see the "Enforces" column; full mapping in `requirement-map.md`
- **Assumptions:** every check runs from the repo root with no network, except the approval checks, which make one adapter call
- **Unverified:** none of these checks existed when this catalogue was written. As of 2026-11-22 all 105 exist, each with a passing and a failing fixture (`agentic.py selftest`); what has and has not been run is in the phase reports. Phase 12 added two on 2026-11-26, listed at the end of this file, which makes 107

Every check ships a passing and a failing fixture (TRC-17). "Runs" says where: **L** local command, **A** agent runtime event where supported, **CI** continuous integration. CI is authoritative. Checks for slices 0.4 to 0.6 were built after this catalogue was written and are listed at the end of this file.

## Slice 0.1 — Govern
| Check | Fails when | Enforces | Runs | Failing fixture |
|---|---|---|---|---|
| CK-PROFILE | `kit.yml` is missing or invalid, or names an unknown profile or pack | GOV-13, GOV-14 | L, CI | `kit.yml` with `profile: strict` |
| CK-ROLES | `roles.yml` is invalid; a gate's required role has nobody; an artifact has no accountable role. Also prints the separation-of-duties report | GOV-1 to GOV-3 | L, CI | A gate role with no person |
| CK-UPSTREAM-PIN | Installed Spec Kit differs from the pinned version, or `NOTICE.md` lacks the pin | ADP-1 | L, CI | Pin `1.4.3`, installed `1.3.0` |
| CK-ENFORCE-SETUP | The rules of the default branch (rulesets and branch protection, LIV-1 to LIV-3), CODEOWNERS coverage or the agent token's permissions are wrong. Items that cannot be read are reported as not-checkable | GOV-8, ADP-3 | L (doctor), CI | CODEOWNERS missing `roles.yml` |
| CK-TIER | A spec has no declared tier or an unknown one | GOV-9 | L, CI | Spec without `tier_declared` |
| CK-CONSTITUTION | A principle names neither a check nor a judging gate; a named check does not exist | GOV-11 | L, CI | Principle with `enforcement: machine` and no checks |
| CK-GATE-RECORD | A gate was passed without a decision record: a plan, a task list or work on the tasks is ahead of a gate, or work is on the default branch and its implementation or verification gate has no approving record (see "What CK-GATE-RECORD asks for", below); a record is malformed, names an unknown commit, or its evidence hash does not match the files at that commit | GOV-4, GOV-5, AGT-5 | L, CI | Record whose hash differs from its files |
| CK-APPROVER | The reviewer is not in base-branch `roles.yml`, lacks a required role, is the agent or CI identity, is not a human account, authored the artifacts without the exception being allowed, or the review is dismissed or on another commit | GOV-6, GOV-7, GOV-16; MAP-12 and CHG-12 once slice 0.2 is installed | CI | Review by the pull request author with exceptions forbidden |
| CK-GATE-MIRROR | A decision record has no matching review in the enforcement channel, or the two disagree | GOV-6 | CI | Record citing a review that does not exist |
| CK-WAIVER | A detected suppression has no waiver or baseline group; a waiver has expired or lacks a required field; a Critical waiver lacks its approval; a baseline group's live count exceeds its recorded count | GOV-15, GOV-16, QLT-12 | L, A, CI | A new `test.skip(` with no waiver |
| CK-TRACE | Any link principle → requirement → criterion → task → test is missing or orphaned; a criterion is in state `gap` | TRC-1, TRC-3; TRC-2 once slice 0.2 is installed | L, CI | Criterion with no test and no open task |
| CK-TRACE-GENERATED | The committed trace manifest differs from a fresh build | TRC-4 | CI | Hand-edited manifest |
| CK-AUDIT-CHAIN | A log entry's hash or previous-hash is wrong; sequence numbers skip; a decision record's `audit_head` is not in the log | TRC-5, TRC-6 | L, CI | One edited entry |
| CK-DRIFT-SPEC | After merge, a file under a spec's declared paths changed with no spec, or the trace manifest no longer builds clean | TRC-8 | CI (default branch) | Change to a traced file with no spec |
| CK-METRIC-SOURCE | A metric is displayed with no data source | TRC-11, TRC-14 | L, CI | Metric configured with no source |
| CK-VERIFY-INPUTS | The verifier's input manifest lists anything other than the artifact, spec, constitution and map, or the verifier's agent id equals the author's. The artifact is the paths the spec names, the paths its task list names, and the files of the components it says it touches; a verifier may also read the files of the components the spec says it depends on. The work records, notes and other verification files are never allowed, and since 2026-11-26 neither is the generated page of the change, `specs/<spec>/changeset.md`, which repeats the work records | QLT-1 | L, CI | Manifest that includes the author's notes |
| CK-DOMAIN-SECTIONS | A spec in a Regulated project lacks a section the active pack requires | ADP-14 | L, CI | HIPAA spec without the safeguards section |
| CK-SELFTEST | Any check lacks a passing or failing fixture, or its failing fixture passes | TRC-17 | CI | A check directory with one fixture |

## Slice 0.2 — System
| Check | Fails when | Enforces | Runs | Failing fixture |
|---|---|---|---|---|
| CK-MAP-SCHEMA | Map is invalid; unknown node or edge type; edge points at a missing node | MAP-1 to MAP-3 | L, CI | Edge to an unknown node |
| CK-MAP-OWNER | A node has no owner, tier or classification | MAP-4 | L, CI | Node without `owner` |
| CK-MAP-EVIDENCE | A node or edge marked derived cites a file that does not exist | MAP-5, ADP-9 | L, CI | Evidence path that was deleted |
| CK-MAP-DRIFT | Discovery finds nodes or edges not in the map, or the map has derived entries discovery no longer finds | MAP-6, TRC-9 | CI | New project reference, or a new event topic or publisher, not in the map |
| CK-MAP-FEDERATION | A federated map reference is not pinned or cannot be read | MAP-7 | L, CI | Reference to a branch name |
| CK-TOUCH | A change modifies files indexed to a node the spec does not declare in `touches` | MAP-8, MAP-9 | L, A, CI | Edit to a file under an undeclared node |
| CK-IMPACT | `impact.md` is missing or stale against the map and spec; a required approver from it is absent at the gate | MAP-10 to MAP-12 | L, CI | Impact report older than the spec |
| CK-TIER-RAISE | A spec's effective tier is lower than the highest tier it touches | GOV-10, MAP-12 | L, CI | Medium spec touching a Critical node |
| CK-CROSS-SPEC | Two in-flight specs touch the same node with no declared order; a spec passes a gate before a spec it depends on has passed the gate it needs | MAP-13 | L, CI | Two open specs on one table |
| CK-PROGRAMME | A parent spec's children are missing, unpinned, or lack the shared contract and rollout order | MAP-14 | L, CI | Child spec with no contract reference |
| CK-FINDING-EVIDENCE | A brownfield finding cites no evidence, or cites a path that does not exist | MAP-15 | L, CI | Finding with an empty evidence list |
| CK-DATA-PLAN | A spec touches a data-store node with no data-change plan, or a required heading is missing or empty | CHG-1, CHG-3, CHG-5, ADP-6 | L, CI | Plan without a rollback section |
| CK-DATA-CLASS | A migration the engine adapter classes as breaking or destructive lacks the matching plan content or the Data Owner approval | CHG-2 | CI | Column drop classed as additive |
| CK-MIGRATION-ENGINE | Migrations were not applied in CI on the production engine and major version, or were generated for another engine | CHG-4, ADP-5 | CI | Migration with another engine's column types |
| CK-MIGRATION-DRIFT | The model and the migrations disagree; a migration warning is suppressed | CHG-4 | CI | Suppressed pending-changes warning |
| CK-SHARED-STORE | A store has more than one writer in the map and is not flagged shared with every writer named | CHG-4 | L, CI | Two writers, no shared flag |
| CK-SYNTH-DATA | Seed or test data matches personal-data patterns | CHG-4 | L, CI | Fixture with a realistic identifier |
| CK-CONTRACT-VERSION | A contract node has no version, or changed without a version change | CHG-6 | L, CI | Changed contract, same version |
| CK-CONTRACT-BREAK | The contract adapter reports a breaking change that the spec does not declare | CHG-7, ADP-8 | CI | Removed field, not declared |
| CK-CONTRACT-CONSUMER | A consumer in the map has no contract test, or it did not run | CHG-8 | CI | Consumer with no test |
| CK-DEPRECATION | A deprecation has no date or migration path | CHG-9 | L, CI | Deprecated endpoint with no date |
| CK-CONTRACT-DRIFT | The committed contract differs from the one generated from code | CHG-9, TRC-9 | CI | Endpoint in code, absent from the contract |
| CK-SHARED-SEMVER | A shared component changed without a version change consistent with the kind of change | CHG-10 | CI | Breaking change with a patch bump |
| CK-CONSUMER-MATRIX | A shared component changed and a consumer's build and tests did not run | CHG-11 | CI | Matrix missing one consumer |
| CK-EXTERNAL-DEP | An external node lacks a required field, or the domain pack requires an agreement status that is absent | CHG-13, CHG-14 | L, CI | External service with no timeout policy |
| CK-SBOM | A release has no bill of materials, or a licence is incompatible | CHG-15 | CI | Dependency with a disallowed licence |
| CK-PIN | A dependency, action or image is referenced by a floating tag | CHG-15 | L, CI | Image tagged `latest` |
| CK-ROLLOUT | A plan touching more than one deployable node lacks deploy and rollback order, or the order contradicts map edges | CHG-18 | L, CI | Consumer deployed before its provider's new contract |

## Slice 0.3 — Team
| Check | Fails when | Enforces | Runs | Failing fixture |
|---|---|---|---|---|
| CK-AGENT-SPEC | An agent spec is invalid, lacks a `never` list, or the rendered runtime files differ from a fresh render | AGT-1, AGT-2, ADP-10, ADP-11 | L, CI | Hand-edited rendered agent file |
| CK-WORKITEM | A work item is invalid, makes an illegal state transition, or is done without handoff evidence | AGT-3 | L, CI | `ready` straight to `done` |
| CK-PATH-LOCK | Two in-progress work items claim overlapping paths; a migration, contract or shared component has two writers | AGT-4 | L, CI | Two items on one migration folder |
| CK-PATH-DIFF | An agent's commits touch paths outside its work item or its agent spec | AGT-10 | A, CI | Implementer editing a spec file |
| CK-REWORK-LIMIT | A work item exceeds two rework rounds without an escalation record | AGT-6 | L, CI | Three rounds, no escalation |
| CK-BUDGET | A run exceeds its step or time budget without stopping | AGT-7 | L | Run log past its limit |
| CK-AUTHOR-NEQ-VERIFIER | The same agent identity authored and reviewed or verified an artifact, or a work item was returned or accepted by a reviewer its record does not name | AGT-9 | L, CI | Same id in both roles |
| CK-CRED | The token available to agents can approve, merge, bypass protection, publish or deploy. In a pipeline that is the pipeline's own token, which has no user: in GitHub Actions it is judged as `github-actions[bot]` (LIV-4) | AGT-11 | L (doctor), CI | Token with admin permission |
| CK-GOLDEN | A golden task fails in parallel or sequential mode, or a seeded defect is not caught | AGT-8, AGT-13, ADP-12 | CI | Seeded missing tenant filter passes review |

## Order in CI
1. Profile, roles, upstream pin, self-test.
2. Map schema, owners, evidence (when slice 0.2 is installed).
3. Per changed spec: tier, trace, touch, impact, packs triggered.
4. Gate record, approver, mirror, waiver, audit chain.
5. On the default branch only: drift checks, and the part of the gate record check that asks merged work for G5 and G6.

A check that cannot run reports `not-run` with the reason. At Standard and above `not-run` fails the job; at Lite it warns.

## What CK-GATE-RECORD asks for, and on which branch (added after the slices)

The gates are in order (GOV-4): G1 spec, G2 clarify, G3 plan, G4 tasks and analysis, G5 implementation, G6 verification, G7 release.
The check asks for an approving decision record once something is in the tree that should have come after the gate.

| What is in the tree | Gates asked for | Where |
|---|---|---|
| `plan.md` | G1, G2 | Every branch |
| `tasks.md` | G3 | Every branch |
| Work on the tasks | Every gate before G5: G4, and G1 to G3 where no plan or task list already asks | Every branch |
| Work on the tasks | G5 and G6 | The default branch only |

Only gates the spec needs are asked for: Lite has G1, G3 and G5, and the fast lane folds G1 to G3 into G4. Each missing gate is one
finding, which names the spec and the gate and says what was found. G7 is not asked for: a release may be decided after the merge.

**What shows work on the tasks.** In the core, a task ticked off in `tasks.md`. With the team extension also a work item that is done
or was handed off, unless its work is still in an isolated working copy, and a commit since `--base-ref` that names one of the spec's
work items in a `Work-Item:` trailer. Files that changed are not used: two specs may claim the same file.

**Which branch it is.** The default branch is the one `kit.yml` names (`enforcement.default_branch`; `main` when it names none).
The check takes the first answer it can get.

1. The caller says: `check --branch <name or full ref>`, and the same on `connect run` and `connect notify`. `main` and
   `refs/heads/main` are the default branch. `spec/004`, `refs/pull/7/merge` and anything else are not. This is for the places
   git cannot answer for. Nothing depends on remembering it: the pipeline files the kit ships do not pass it.
2. Git says, and only where the project root is the top of its own repository. A project kept in a folder of another repository
   would be given that repository's branch and commits. The reference example in this repository is such a folder. The shipped
   pipeline files make a full clone of the project's repository, so git answers there.
   - It is the default branch when that branch is checked out, or a commit with no branch that the default branch contains,
     which is what most pipelines check out.
   - It is not when what is checked out has commits the default branch does not have, and is compared with a branch
     (`--base-ref origin/main`), with a commit of the default branch, or with nothing. That is a change proposed to a branch.
3. Otherwise the check cannot tell. It adds a note that names the specs and gates it did not ask for and says why. It does not
   fail, and it does not pass in silence. The cases:
   - the root is not a repository of its own, or no branch has the name `kit.yml` gives;
   - another branch is checked out at a commit the default branch already holds: a branch just started, or the default branch
     under another name;
   - what is checked out is compared with a bare commit that the default branch does not hold. A push to the default branch is
     checked that way, against the commit before it. So this is the default branch under another name or beside an
     out-of-date copy, or it is a feature branch compared with its own past.

On what it knows to be a feature branch or a pull request, the check says nothing about G5 and G6. Work in progress is legitimate there.

**An emergency.** While an emergency record is open, the spec it names as its retrospective is not asked for G5 and G6 on the default
branch (GOV-18). CK-EMERGENCY-DEADLINE holds that spec to its date.

What this rule does not see is in `docs/limits.md`, under "Found by using it on a real change, and not fixed".

## Carried by the adoption baseline (added in Phase 3b, part 2)

Some change-pack rules hold for the whole codebase, and an existing codebase will not meet them on day one.
Their unmet items are reported under a rule id, so a waiver or the adoption baseline (GOV-21) can carry them
and the count can only fall. The owning check fails for anything beyond the baseline.

| Rule | Reported by | Meaning |
|---|---|---|
| `pin-action`, `pin-image`, `pin-package` | CK-PIN | An action not pinned to a commit; an image with no tag or a floating tag (`latest` and the like, or a tag that ends in `-latest`); a package requested as `*` or `latest`, or a manifest with no lockfile. Images are read from workflow, Compose and Kubernetes files, container files, and the `AddContainer` calls of a .NET Aspire application host |
| `pin-digest` | CK-PIN | Regulated only: an image with a tag but no digest |
| `store-engine-unknown` | CK-MIGRATION-ENGINE | The map does not state a store's engine and version |
| `migration-foreign-engine` | CK-MIGRATION-ENGINE | A migration carries another engine's types or annotations |
| `migration-warning-suppress` | CK-MIGRATION-DRIFT | The ORM's pending-model-changes warning is ignored in code |
| `unversioned-contract` | CK-CONTRACT-VERSION | A contract with no version |
| `contract-untested` | CK-CONTRACT-CONSUMER | A consumer in the map with no contract test |
| `contract-drift-undeclared` | CK-CONTRACT-DRIFT | A contract that does not say how drift from the code is detected |
| `unversioned-shared` | CK-SHARED-SEMVER | A shared component with no semantic version |
| `external-dep-incomplete` | CK-EXTERNAL-DEP | An external dependency record with fields missing |

Not carried, always a failure: a changed contract with the same version, an undeclared breaking change, a
missing or stale run record, a classification lower than the migration, a missing agreement status for
protected data, a denied licence, and a rollout order the map contradicts.

## Slice 0.5 — Truth (built after this catalogue was written)
| Check | Fails when | Enforces |
|---|---|---|
| CK-INTAKE-RECORD | An intake record is malformed, its text does not match its hash, it holds personal data or a credential, or it was closed without a reason and a Product Owner | INT-1 to INT-4 |
| CK-INTAKE-DRIFT | A work item changed at its source after someone acted on it and nobody decided what that means | INT-7 |
| CK-DUPLICATE | A spec still to be approved resembles existing work and a candidate has no decision from a Product Owner, or was decided to be a duplicate | INT-5, INT-6 |
| CK-REQ-QUALITY | A requirement still to be approved has no MUST or SHALL, has two, uses a vague word with no number, has no criterion, or has an open question | PRD-1 to PRD-3 |
| CK-SPEC-SIZE | A spec still to be approved is over the size limit | PRD-4 |
| CK-GLOSSARY | A spec still to be approved uses a word the glossary says to avoid; or the glossary contradicts itself | PRD-5 |
| CK-DELTA-VALID | A delta does not apply to the living spec, a requirement in it cannot be tested, or a requirement of the spec is carried by no delta | PRD-7 |
| CK-CAPABILITY-COVERAGE | A change says nothing about behaviour, or touches a component no capability describes | PRD-10 |
| CK-LIVING-SPEC | A living spec differs from the replay of its merged deltas; a delta changed after merge; a change was merged before release; an adoption merge names no Product Owner | PRD-8, PRD-9, PRD-16 |
| CK-DELTA-MERGED | A released change is not merged within `product.merge_days` | PRD-9 |
| CK-SPEC-COLLISION | Two changes in flight alter the same requirement and neither lists the other under `after:` | PRD-11 |
| CK-ARCHIVE | A merged change is not sealed within `product.archive_days`, or a sealed file changed or was added | PRD-12 |
| CK-OUTCOME | A Medium-tier or higher change states no expected result, or its review date passed with no review | PRD-14, PRD-15 |

## Slice 0.6 — Connected
| Check | Fails when | Enforces |
|---|---|---|
| CK-CONNECT-CONFIG | `connect.yml` holds a secret, uses a non-https address, misses a field a platform needs, or routes to a channel or event that does not exist | ADP-17 to ADP-19, PIP-3 |
| CK-NOTIFY-CONTENT | A notification template uses a field outside the fixed set, or the configuration asks for text or evidence to be included | NTF-2, NTF-3 |
| CK-PIPELINE-SECRETS | A pipeline file holds a secret; a workflow a proposed change can alter names a tracker or notification secret; an agent step has one in scope | PIP-3, PIP-5 |

## Slice 0.4 — Depth (built after this catalogue was written)

The three tables below are printed from the check registry, so the "Requires" column is each check's own
one-line statement of what must hold. A check fails when that statement is false. 34 checks.

### In the core extension: lanes, the reviewer's page and the evidence pack
| Check | Requires | Enforces | Profiles |
|---|---|---|---|
| CK-LANE | A spec is on the fast lane only when impact analysis puts it there | GOV-17 | Standard, Regulated |
| CK-EMERGENCY-DEADLINE | An emergency change has one valid human approval and its retrospective is done by the deadline | GOV-18 | all |
| CK-AMENDMENT | A change to something approved re-opens the gates that approved it | GOV-12, GOV-19 | Standard, Regulated |
| CK-BRIEF | Every gate decision was made with a current one-page brief in its evidence | GOV-20 | Standard, Regulated |
| CK-AUDIT-PACK | A release was approved with its evidence pack in front of the approver, and the pack still matches the repository | TRC-16 | Regulated |

Detail the summaries leave out:
- CK-AUDIT-PACK looks only at a spec whose G7 is approved. The pack must have been made by the kit, be listed in the G7 evidence, and its hashes must still match the spec's own files and decision records. Roles, settings, waivers and the audit log go on changing after a release; the pack holds them as they were and a later change to them is not a failure.
- CK-BRIEF needs the brief that was current when the decision was made. Writing a brief also appends `gate.ready` to the audit log, which is where the time-to-decision measure starts. Writing a brief that is the same as the one on disk changes nothing and appends nothing.

### In the team extension: what an agent is given, what it used and what it cost
| Check | Requires | Enforces | Profiles |
|---|---|---|---|
| CK-CONTEXT | An agent at work has a context pack the kit built, and the pack still matches the repository | AGT-19 | Standard, Regulated |
| CK-TOOL-ALLOWLIST | Every MCP server configured for an agent is on the allowlist, unchanged, and pinned to a version | AGT-20 | Standard, Regulated |
| CK-RUN-RECORD | Every agent step records the model and version, the agent spec hash, its inputs by hash, tools, cost and duration | AGT-17 | Standard, Regulated |
| CK-ROUTING | Each agent runs on the model the routing policy names for it, and spend stays within the budget | AGT-16 | Standard, Regulated |
| CK-GOLDEN-BASELINE | A change to the agent specs or the routing policy does not make the golden tasks worse than the accepted baseline | AGT-14 | all |
| CK-INJECTION | Instructions planted in a file, an issue and a tool's output were reported and not acted on | AGT-15 | all |
| CK-AGENT-MEMORY | Agent instruction files are under version control and review, grant nothing the kit forbids, and point at files that exist | AGT-18 | Standard, Regulated |

Detail the summaries leave out:
- CK-CONTEXT fails when an agent is at work with no context pack, the pack was edited by hand, a source changed since it was built, or it draws on a sealed change. Since 2026-11-26 it looks for the pack's mark where the pack's own text begins, after the list of sources: it used to look in the first 1,200 characters, and a pack with ten sources had its mark past them and was taken for an edited one. Since that day a pack is also stale when the spec's decision log comes to hold an entry that touches its task.
- CK-TOOL-ALLOWLIST fails when an MCP server is configured that is not on the allowlist, is launched differently from what was reviewed, is not pinned, or holds a stored credential; or a setting trusts every server. The allowlist is read from the base branch. Where the base branch has none yet, the one a change brings counts only for servers the base branch already configures in the same way: a server and the allowlist that approves it cannot arrive together (REV-5). For `npx`, `bunx` and `pnpx` a pinned version has three numbers; `@1` and `@1.2` are ranges (REV-6).
- CK-RUN-RECORD reads the `agent.<action>` entries of the audit log. A step whose tools were not reported by the runtime is recorded as `declared`, taken from the agent spec, and says so.
- CK-ROUTING requires a routing policy at Regulated only. Where a policy exists at Standard it is enforced. Model and cost are what the runtime reported (see `docs/limits.md`).
- CK-GOLDEN-BASELINE compares the last golden results with a baseline a named person in `roles.yml` accepted through a review. Once a baseline is on the base branch it is read from there, so a change cannot lower the bar it is judged by. A task, seeded defect or planted instruction that was good in the baseline and is not now fails the check; a new one that fails does not, until it is in a baseline. Where the project has a routing policy, the results must also have been produced under the policy the change proposes: a change of model with results from before it fails, as a change to an agent spec already does under CK-GOLDEN.
- CK-INJECTION needs each of the three planted instructions (in a repository file, in an issue's text, in a tool's output) to be reported at hand-off and not acted on. "Acted on" means the file the planted text asks for was created, or `roles.yml` was changed.
- CK-AGENT-MEMORY reads `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`, `.windsurfrules`, `.github/copilot-instructions.md`, `.github/instructions/*.md`, `.cursor/rules/*`, `.kiro/steering/*.md`, `.claude/CLAUDE.md`, `.specify/memory/*.md` other than the constitution, and the files named in `team.memory.files`. A line that grants something the kit forbids fails unless the same line negates it.

### In the quality extension: packs that switch on from a spec's tier and what it touches
| Check | Requires | Enforces | Profiles |
|---|---|---|---|
| CK-A11Y | A frontend change was checked for accessibility to a stated level and for design-system conformance | QLT-11 | Standard, Regulated |
| CK-ADR | Decision records link to specs and map nodes, and a superseded record flags the specs that relied on it | QLT-21 | Standard, Regulated |
| CK-AI-EVAL | A change to an AI component has a signed-off golden set, thresholds, and no regression against the last release | QLT-14 | Standard, Regulated |
| CK-AI-PROD-PATH | The evaluation calls the production code, not a copy of it | QLT-15 | Standard, Regulated |
| CK-AI-RETRIEVAL | Each retrieval index records its sources, its refresh, how retrieved text is kept apart, and its attack tests | QLT-17 | Standard, Regulated |
| CK-AI-RUNTIME | Each model has latency and cost budgets, a fallback, logging that leaves out protected data, and a kill switch | QLT-18 | Standard, Regulated |
| CK-AI-SAFETY-CASE | Critical AI behaviour has a safety case that a named person accepted | QLT-16 | Standard, Regulated |
| CK-AI-VERSION | Every model, prompt, tool and retrieval index is versioned, and a change to one changes its version | QLT-13 | Standard, Regulated |
| CK-CHARACTERIZATION | Code that already existed is pinned down by characterization tests before a spec changes it | QLT-9 | Standard, Regulated |
| CK-ENV-PARITY | The environment parity matrix is kept, and every difference between environments is reported | CHG-17 | Standard, Regulated |
| CK-FLAG | Every feature flag has an owner, a default and a removal date that has not passed | CHG-20 | Standard, Regulated |
| CK-INCIDENT-LOOP | Each postmortem names the spec, the gate that should have caught it, a finding and a proposed change | QLT-22, TRC-12 | Standard, Regulated |
| CK-INFRA-CHANGE | An infrastructure change states its impact, passes policy checks and fits a stated budget | CHG-16 | Standard, Regulated |
| CK-METRIC-PROVENANCE | Every figure shown to users or in reports traces to a recorded evaluation or telemetry source. It reads the files `metric_claims.scan` names: percentages in prose, and in code or data also a number given to a name that says what it measures | QLT-19 | Standard, Regulated |
| CK-OPS-READINESS | A release states its operational readiness: objectives, telemetry, alerts, dashboards, runbooks | QLT-20 | Standard, Regulated |
| CK-POST-RELEASE | Criteria that can only be checked in production are checked after release, and the result closes the trace. A check dated after today, or before the release, fails (REV-7) | CHG-21 | Standard, Regulated |
| CK-PRIVACY-IMPACT | A spec that touches protected data states purpose, minimum fields, lineage, retention and access | QLT-6 | Standard, Regulated |
| CK-PROGRESSIVE | A high-risk change is rolled out in stages with signals that halt it and a rollback trigger | CHG-19 | Standard, Regulated |
| CK-SECURITY-EVIDENCE | G5 was approved with secret, dependency and static scans, and an authorization matrix where an endpoint changed | QLT-5 | Standard, Regulated |
| CK-TEST-DATA | Seed and test data come from synthetic generators kept in the repository | QLT-10 | Standard, Regulated |
| CK-TEST-STRATEGY | Each spec plans the test kinds its tier requires, and shows them at G5 | QLT-7, QLT-8 | Standard, Regulated |
| CK-THREAT-MODEL | Each planned spec has a threat model whose threats link to a requirement and an abuse-case test | QLT-3, QLT-4 | Standard, Regulated |

None of these checks runs a scanner, an evaluation or an accessibility tool. Each requires the record that one ran, bound by hash to the files it ran on (`docs/limits.md`).

Detail the summaries leave out:
- CK-PROGRESSIVE asks a Critical change for a rollback rehearsal in two steps. While the spec is planned, the rollout must say how the rollback will be rehearsed (`rollback_rehearsal.plan`): a rollback cannot be rehearsed before the change is built. Once G7 is approved, the rehearsal must have a date and evidence that exists.
- CK-TEST-STRATEGY asks a Critical change for a resilience test per external system it relies on. Those are the external systems its touched components call, and the ones the spec lists under `depends_on`. For one a touched component calls and the change has nothing to do with, the strategy may say so: `{not_relied_on: <reason>}`. That is not accepted for a system the spec itself lists, and a placeholder is not an answer.

## Phase 12, 2026-11-26 (built after this catalogue was written)

| Check | Fails when | Enforces | Profiles |
|---|---|---|---|
| CK-DECISION-LOG | A spec's decision log is not a log, an entry has no title, an id of another form, an id used twice or an unknown state; a decided entry lacks its outcome, its day or an owner whom `roles.yml` lists as a person; an entry that is not decided carries an outcome; a superseded entry names no other entry; `affects` names a requirement or a task the spec does not have; or G5 is approved while an entry is still open or proposed, or without the log among its evidence. A spec with no log passes | GOV-5, TRC-18 | all |
| CK-CONVERSATION | A discussion moved after someone acted on its intake record and no Product Owner acknowledged it; or what is kept of a conversation holds what the screen removes, lacks its summary, its writer or its day, has a link that carries a credential, or names a confirmer whom `roles.yml` does not list | INT-2, INT-7 | Standard, Regulated |

The two are registered under requirement IDs of `docs/prompts/spec/`, because the as-built map is made from the IDs in that folder. Their own requirements are DEC-10 to DEC-14 in `decision-log.md` and CNV-10 and CNV-11 in `conversation.md`. No other feature of Phase 12 adds a check: the page of a change, the search, the MCP server, the view of a programme and the workflow that opens a pull request judge nothing.

## After Phase 12, 2026-11-28

| Check | Fails when | Enforces | Profiles |
|---|---|---|---|
| CK-PROGRAMME-RELEASE | A parent's G7 is approved while a child has not passed its own gates: in this repository, a gate the child needs has no approving record; in another repository, the pinned commit holds no approving record of the last gate that repository's profile asks for, or cannot be read | MAP-14, GOV-4 | Standard, Regulated |

It is registered under requirement IDs of `docs/prompts/spec/`, for the reason given above. Its own requirements are PRR-1 to PRR-8 in `programme-release.md`. PRR-8 also changed `CK-PROGRAMME`, which now fails, where it stopped, on a `programme` entry of the wrong shape.
