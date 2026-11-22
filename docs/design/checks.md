# Check catalogue

- **Phase and date:** Phase 2 (design), 2026-11-21
- **Requirement IDs covered:** see the "Enforces" column; full mapping in `requirement-map.md`
- **Assumptions:** every check runs from the repo root with no network, except the approval checks, which make one adapter call
- **Unverified:** none of these checks exists yet

Every check ships a passing and a failing fixture (TRC-17). "Runs" says where: **L** local command, **A** agent runtime event where supported, **CI** continuous integration. CI is authoritative. Checks for slice 0.4 are named in `requirement-map.md` and designed in Phase 9.

## Slice 0.1 — Govern
| Check | Fails when | Enforces | Runs | Failing fixture |
|---|---|---|---|---|
| CK-PROFILE | `kit.yml` is missing or invalid, or names an unknown profile or pack | GOV-13, GOV-14 | L, CI | `kit.yml` with `profile: strict` |
| CK-ROLES | `roles.yml` is invalid; a gate's required role has nobody; an artifact has no accountable role. Also prints the separation-of-duties report | GOV-1 to GOV-3 | L, CI | A gate role with no person |
| CK-UPSTREAM-PIN | Installed Spec Kit differs from the pinned version, or `NOTICE.md` lacks the pin | ADP-1 | L, CI | Pin `1.4.3`, installed `1.3.0` |
| CK-ENFORCE-SETUP | Branch protection, CODEOWNERS coverage or the agent token's permissions are wrong. Items that cannot be read are reported as not-checkable | GOV-8, ADP-3 | L (doctor), CI | CODEOWNERS missing `roles.yml` |
| CK-TIER | A spec has no declared tier or an unknown one | GOV-9 | L, CI | Spec without `tier_declared` |
| CK-CONSTITUTION | A principle names neither a check nor a judging gate; a named check does not exist | GOV-11 | L, CI | Principle with `enforcement: machine` and no checks |
| CK-GATE-RECORD | A gate was passed without a decision record; a record is malformed, names an unknown commit, or its evidence hash does not match the files at that commit | GOV-4, GOV-5, AGT-5 | L, CI | Record whose hash differs from its files |
| CK-APPROVER | The reviewer is not in base-branch `roles.yml`, lacks a required role, is the agent or CI identity, is not a human account, authored the artifacts without the exception being allowed, or the review is dismissed or on another commit | GOV-6, GOV-7, GOV-16; MAP-12 and CHG-12 once slice 0.2 is installed | CI | Review by the pull request author with exceptions forbidden |
| CK-GATE-MIRROR | A decision record has no matching review in the enforcement channel, or the two disagree | GOV-6 | CI | Record citing a review that does not exist |
| CK-WAIVER | A detected suppression has no waiver or baseline group; a waiver has expired or lacks a required field; a Critical waiver lacks its approval; a baseline group's live count exceeds its recorded count | GOV-15, GOV-16, QLT-12 | L, A, CI | A new `test.skip(` with no waiver |
| CK-TRACE | Any link principle → requirement → criterion → task → test is missing or orphaned; a criterion is in state `gap` | TRC-1, TRC-3; TRC-2 once slice 0.2 is installed | L, CI | Criterion with no test and no open task |
| CK-TRACE-GENERATED | The committed trace manifest differs from a fresh build | TRC-4 | CI | Hand-edited manifest |
| CK-AUDIT-CHAIN | A log entry's hash or previous-hash is wrong; sequence numbers skip; a decision record's `audit_head` is not in the log | TRC-5, TRC-6 | L, CI | One edited entry |
| CK-DRIFT-SPEC | After merge, a file under a spec's declared paths changed with no spec, or the trace manifest no longer builds clean | TRC-8 | CI (default branch) | Change to a traced file with no spec |
| CK-METRIC-SOURCE | A metric is displayed with no data source | TRC-11, TRC-14 | L, CI | Metric configured with no source |
| CK-VERIFY-INPUTS | The verifier's input manifest lists anything other than the artifact, spec, constitution and map, or the verifier's agent id equals the author's | QLT-1 | L, CI | Manifest that includes the author's notes |
| CK-DOMAIN-SECTIONS | A spec in a Regulated project lacks a section the active pack requires | ADP-14 | L, CI | HIPAA spec without the safeguards section |
| CK-SELFTEST | Any check lacks a passing or failing fixture, or its failing fixture passes | TRC-17 | CI | A check directory with one fixture |

## Slice 0.2 — System
| Check | Fails when | Enforces | Runs | Failing fixture |
|---|---|---|---|---|
| CK-MAP-SCHEMA | Map is invalid; unknown node or edge type; edge points at a missing node | MAP-1 to MAP-3 | L, CI | Edge to an unknown node |
| CK-MAP-OWNER | A node has no owner, tier or classification | MAP-4 | L, CI | Node without `owner` |
| CK-MAP-EVIDENCE | A node or edge marked derived cites a file that does not exist | MAP-5, ADP-9 | L, CI | Evidence path that was deleted |
| CK-MAP-DRIFT | Discovery finds nodes or edges not in the map, or the map has derived entries discovery no longer finds | MAP-6, TRC-9 | CI | New project reference not in the map |
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
| CK-AUTHOR-NEQ-VERIFIER | The same agent identity authored and reviewed or verified an artifact | AGT-9 | L, CI | Same id in both roles |
| CK-CRED | The token available to agents can approve, merge, bypass protection, publish or deploy | AGT-11 | L (doctor), CI | Token with admin permission |
| CK-GOLDEN | A golden task fails in parallel or sequential mode, or a seeded defect is not caught | AGT-8, AGT-13, ADP-12 | CI | Seeded missing tenant filter passes review |

## Order in CI
1. Profile, roles, upstream pin, self-test.
2. Map schema, owners, evidence (when slice 0.2 is installed).
3. Per changed spec: tier, trace, touch, impact, packs triggered.
4. Gate record, approver, mirror, waiver, audit chain.
5. On the default branch only: drift checks.

A check that cannot run reports `not-run` with the reason. At Standard and above `not-run` fails the job; at Lite it warns.

## Carried by the adoption baseline (added in Phase 3b, part 2)

Some change-pack rules hold for the whole codebase, and an existing codebase will not meet them on day one.
Their unmet items are reported under a rule id, so a waiver or the adoption baseline (GOV-21) can carry them
and the count can only fall. The owning check fails for anything beyond the baseline.

| Rule | Reported by | Meaning |
|---|---|---|
| `pin-action`, `pin-image`, `pin-package` | CK-PIN | An action not pinned to a commit; an image with no tag or a floating tag; a package requested as `*` or `latest`, or a manifest with no lockfile |
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
