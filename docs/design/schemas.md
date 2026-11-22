# Schemas

- **Phase and date:** Phase 2 (design), 2026-11-21
- **Requirement IDs covered:** GOV-1 to GOV-16, TRC-1 to TRC-7, MAP-1 to MAP-9, CHG-1 to CHG-3, AGT-1, AGT-3
- **Assumptions:** YAML for files people edit, JSON for files the kit generates
- **Unverified:** the examples below parse as YAML or JSON (checked by script); no code consumes them yet

All examples use invented values. Field names are the contract; JSON Schema files are produced in Phase 3 from these.

## kit.yml (GOV-13)
```yaml
schema: agentic-kit/1
profile: regulated            # lite | standard | regulated
domain_packs: [hipaa]
enforcement:
  adapter: github
  default_branch: main
upstream:
  speckit: "1.4.3"
gates:
  single_approver_exception: allowed   # allowed | forbidden
  require_evidence_hash: true          # false is permitted in lite only
waivers:
  max_days: 90
  critical_max_days: 30
```

## roles.yml (GOV-1 to GOV-3)
Read from the base branch only.
```yaml
schema: agentic-roles/1
people:
  - id: example-user          # account name in the enforcement channel
    roles: [product-owner, solutions-architect, security-compliance]
  - id: second-user
    roles: [qa, backend]
roles:
  product-owner: {title: Product Owner}
  solutions-architect: {title: Solutions Architect}
  backend: {title: Backend}
  frontend: {title: Frontend}
  ai-engineer: {title: AI Engineer}
  data-owner: {title: Data Owner}
  platform: {title: Platform}
  qa: {title: QA}
  security-compliance: {title: Security & Compliance}
  devops-sre: {title: DevOps/SRE}
  engineering-manager: {title: Engineering Manager}
```

## constitution.map.yml (GOV-11)
```yaml
schema: agentic-constitution-map/1
principles:
  - id: P-1
    title: Authentication fails closed
    enforcement: machine
    checks: [arch-test:no-anonymous-fallback]
  - id: P-7
    title: A human reviews every clinical decision path
    enforcement: human
    judged_at: G3
```

## Spec front matter (GOV-9, MAP-8, TRC-1)
Added to upstream's `spec.md` by the preset.
```yaml
---
spec: 004-audit-identity
tier_declared: critical
owner_role: backend
principles: [P-5]
touches: [lib-infrastructure, phi-audit-logs]
depends_on:
  nodes: [entra-id]
  specs: [001-fail-closed-auth]
lane: standard
---
```

## Gate decision record (GOV-5, GOV-6, TRC-18 proposed)
Written by the kit after a valid review exists. One file per gate.
```yaml
schema: agentic-decision/1
spec: 004-audit-identity
gate: G3
decision: approve-with-conditions      # approve | reject | approve-with-conditions
conditions:
  - Add a migration rollback test before G5
commit: 9c1e4f0a7b2d
evidence:
  hash: sha256:5b0c1d2e3f405162738495a6b7c8d9e0f1a2b3c4d5e6f708192a3b4c5d6e7f80
  files: [specs/004-audit-identity/plan.md, specs/004-audit-identity/impact.md]
approvals:
  - reviewer: example-user
    role: solutions-architect
    review_ref: "pull/12#review-3"
    at: 2026-12-01T15:04:00Z
single_approver_exception: true
audit_head: sha256:aa11bb22cc33dd44ee55ff66007788990011223344556677889900aabbccddee
```

## Waiver (GOV-15, GOV-16) and baseline (GOV-21 proposed)
```yaml
schema: agentic-waiver/1
id: W-014
rule: ck:no-skipped-tests          # a check id or a principle id
scope:
  paths: ["frontend/e2e-cloud/**"]
  pattern: "test.skip("
reason: Live smoke tests skip when the staging service is down
compensating_control: Nightly job fails if more than two services are skipped
owner: qa
expires: 2027-01-31
approved_by: {reviewer: example-user, review_ref: "pull/9#review-1"}
```
```yaml
schema: agentic-baseline/1
approved_by: {reviewer: example-user, review_ref: "pull/3#review-1"}
groups:
  - rule: ck:no-ci-escapes
    count: 40
    owner: devops-sre
    reason: Existing escapes at adoption
    expires: 2027-03-31
```
`CK-WAIVER` fails when a group's live count exceeds its recorded count, or when it has expired.

## Trace manifest (TRC-1 to TRC-4) — generated
```json
{
  "format": "agentic-trace/1",
  "spec": "004-audit-identity",
  "gate": {"ok": false, "failures": ["AC-003: gap"]},
  "rows": [
    {"principle": "P-5", "requirement": "FR-001", "criterion": "AC-001",
     "tasks": ["T004"], "tests": ["AuditIdentityTests.AC_001_user_from_token"],
     "state": "proven", "nodes": ["lib-infrastructure"]},
    {"principle": "P-5", "requirement": "FR-002", "criterion": "AC-003",
     "tasks": [], "tests": [], "state": "gap", "nodes": ["phi-audit-logs"]}
  ]
}
```
States: `proven`, `tracked-debt`, `waived`, `gap`.

## Audit log entry (TRC-5 to TRC-7)
One JSON object per line in the file; wrapped here for reading.
```json
{"seq": 41, "at": "2026-12-01T15:05:10Z",
 "actor": {"type": "agent", "id": "impact-analyst", "on_behalf_of": "solutions-architect"},
 "action": "impact.write", "spec": "004-audit-identity", "commit": "9c1e4f0a7b2d",
 "inputs": ["specs/004-audit-identity/spec.md"], "outputs": ["specs/004-audit-identity/impact.md"],
 "prev": "sha256:0f0e0d0c0b0a09080706050403020100ffeeddccbbaa99887766554433221100",
 "hash": "sha256:aa11bb22cc33dd44ee55ff66007788990011223344556677889900aabbccddee"}
```
`actor.type` is `human`, `agent` or `kit`.

## System map (MAP-1 to MAP-7)
```yaml
schema: agentic-map/1
nodes:
  - id: lib-infrastructure
    type: shared-library
    owner: platform
    tier: critical
    classification: none
    repo: .
    origin: derived
    evidence: src/Infrastructure/Infrastructure.csproj
  - id: phi-audit-logs
    type: schema-object
    owner: security-compliance
    tier: critical
    classification: restricted
    origin: derived
    evidence: src/Infrastructure/Persistence/AuditDbContext.cs
edges:
  - {from: identity-service, rel: writes, to: phi-audit-logs, origin: derived,
     evidence: src/Identity/Program.cs}
index:
  - {paths: ["src/Infrastructure/**"], node: lib-infrastructure}
federated:
  - {repo: example-org/other-app, ref: 4f2a9c1, path: system-map}
```
Node types and edge types are the lists in MAP-2 and MAP-3. `classification` values come from the active domain pack.

## Impact report front matter (MAP-10 to MAP-12) — generated
```yaml
spec: 004-audit-identity
touches: [lib-infrastructure, phi-audit-logs]
affected:
  - {node: identity-service, distance: 1, via: builds-with, owner: backend}
  - {node: identity-db, distance: 1, via: owns, owner: data-owner}
tier_computed: critical
required_approvers:
  G3: [solutions-architect, platform, security-compliance, data-owner]
  G5: [platform, qa, security-compliance]
packs_triggered: [data-store, shared-component]
```

## Data-change plan (CHG-1 to CHG-5)
`specs/<spec>/data-change-plan.md`: front matter plus required headings, checked by `CK-DATA-PLAN` and `CK-DATA-CLASS`.
```yaml
stores: [identity-db]
classification: breaking          # additive | backward-compatible | breaking | destructive
migrations: [src/Identity/Migrations/20261201_AuditTenant.cs]
changes: [{kind: change-embedding-model}]   # engines whose changes are not files (vector stores)
restore_evidence: specs/004-audit-identity/evidence/restore.txt   # destructive changes only
```
Headings for every engine: `Classification`, `Rollback or roll-forward`, `Compatibility during rollout`, `Tenant isolation`, `Retention and deletion`, `Field classification and encryption`, `Readers and writers` (must name every reader and writer in the map).
Relational engines add `Forward migration`, `Backfill`, `Index and query impact`. Vector stores add `Collection and vector changes`, `Re-embedding plan`, `Search index rebuild`. Document stores add `Document shape versioning`, `Index and partition-key changes`. Caches add `Cache key and expiry changes`.
A breaking change adds `Expand, migrate, contract`; a destructive one adds `Restore test`.

## Rollout order (CHG-18)
`specs/<spec>/rollout.yml`, required when a spec touches more than one deployable node.
```yaml
schema: agentic-rollout/1
deploy: [{node: identity-db, phase: expand}, identity-service, {node: identity-db, phase: contract}]
rollback: [identity-service, identity-db]
flags: [audit-tenant-field]
compatibility_window: Two releases
```

## Run records (CHG-4, CHG-8, CHG-11) — written by CI
`specs/<spec>/evidence/migration-run.yml`
```yaml
schema: agentic-migration-run/1
store: identity-db
engine: postgresql
engine_version: "16.4"
result: pass
model_drift: none
applied:
  - {path: src/Identity/Migrations/20261201_AuditTenant.cs, sha256: 5d41402abc4b2a76b9719d911017c592a3f1e0b7c6d5e4f30918273645566778}
```
`specs/<spec>/evidence/consumer-runs.yml`
```yaml
schema: agentic-runs/1
runs:
  - {kind: contract, provider: contract-identity-api, consumer: portal-web, result: pass,
     subject: "sha256:9b74c9897bac770ffc029102a200c5de0f1e2d3c4b5a69788796a5b4c3d2e1f0"}
  - {kind: build, provider: lib-infrastructure, consumer: identity-service, result: pass,
     subject: "sha256:1f3870be274f6c49b3e31a0c6728957f0a1b2c3d4e5f60718293a4b5c6d7e8f9"}
```
`subject` is a hash of the contract file, or of every file of the shared component. A record whose subject no longer matches does not count.

## System-map fields used by the change packs
```yaml
- {id: identity-db, type: data-store, engine: postgresql, engine_version: "16", migrations: ["src/Identity/Migrations/*"],
   shared: true, writers: [identity-service, audit-export]}
- {id: contract-identity-api, type: api-contract, path: contracts/identity.yaml, drift: {generated: build/identity.generated.json},
   deprecations: [{element: "GET /v1/users", sunset: 2027-06-30, migration: "Use GET /v2/users"}]}
- {id: lib-infrastructure, type: shared-library, version_file: src/Infrastructure/Infrastructure.csproj}
- id: model-provider
  type: external-service
  agreement: {status: in-place}          # in-place | pending | not-required; never the document
  dependency: {contract: ..., version: ..., auth: ..., data: ..., availability: ..., timeout: ..., retry: ...,
               circuit_breaker: ..., user_failure: ..., test_double: ...}
```
Edges to a contract carry the consumer's test: `{from: portal-web, rel: calls, to: contract-identity-api, contract_test: tests/contract/identity.test.ts}`.
Spec front matter adds `breaking: [<node>]` and `changes: {<node>: fix | feature | breaking}`. `kit.yml` adds `supply_chain: {licences: {deny: [...], allow: [...], allow_unknown: false}}` and `synthetic_data: {paths: [...], allow: [...], patterns: {...}}`.

## Agent spec (AGT-1)
```yaml
schema: agentic-agent/1
id: impact-analyst
supports_role: solutions-architect
charter: Compute blast radius, required reviewers and tier for one spec.
inputs: [specs/*/spec.md, specs/*/plan.md, system-map/**]
outputs: [specs/*/impact.md]
tools: [read, search, run:agentic_kit]
write_paths: [specs/*/impact.md]
never:
  - Edit the spec or plan it analyses
  - Approve, merge, publish or deploy
model_class: standard
```

## Work item (AGT-3)
`.specify/agentic/work/<spec>/<item>.yml`. Written only by kit commands.
```yaml
schema: agentic-work/1
id: T017
spec: 004-audit-identity
title: Move the audit middleware after authentication
state: in-review        # ready | in-progress | in-review | rework | blocked | done
owner_agent: backend-implementer
reviewer_agent: independent-verifier
paths: [src/Infrastructure/Middleware/*]
depends_on: [T016]
rework_rounds: 1
base: 9c1e4f0a7b2d       # the commit the item was claimed at
worktree: ../repo.worktrees/004-audit-identity-T017   # only when it is worked in an isolated copy
history:
  - {state: ready, by: orchestrator, at: "2026-11-21T09:00:00Z"}
  - {state: in-progress, by: backend-implementer, at: "2026-11-21T09:05:00Z"}
  - {state: in-review, by: backend-implementer, at: "2026-11-21T09:40:00Z"}
handoff:
  done: Moved audit middleware after authentication in nine services
  evidence: [specs/004-audit-identity/evidence/T017-test-run.txt]
  open_questions: []
  files: [src/Infrastructure/Middleware/AuditMiddleware.cs]   # recorded by the kit from the diff
findings:
  - {round: 1, by: independent-verifier, text: The tenant id is read before authentication runs}
```
Legal moves: ready → in-progress; in-progress → in-review; in-review → done or rework; rework → in-review; any working state → blocked; blocked → ready, in-progress, in-review or done. Nothing leaves done.

## Escalation (AGT-6)
`.specify/agentic/work/<spec>/escalations/<item>.yml`, written when a reviewer returns an item a third time.
```yaml
schema: agentic-escalation/1
spec: 004-audit-identity
item: T017
reason: rework-limit
accountable_role: backend
author: {agent: backend-implementer, position: The middleware order is now correct}
reviewer: {agent: independent-verifier, position: The tenant id is still read before authentication}
status: open            # a person in roles.yml sets it to resolved
resolution: {decided_by: sam, decision: The reviewer is right, review_ref: "pull/12#review-88"}
```

## Run (AGT-7)
`.specify/agentic/runs/<spec>/<run>.yml`
```yaml
schema: agentic-run/1
id: r1
spec: 004-audit-identity
mode: parallel
budget: {steps: 200, minutes: 240}
steps: 37
started: "2026-11-21T09:00:00Z"
last: "2026-11-21T10:12:00Z"
state: running          # running | stopped | completed
stop_reason: null       # budget-steps | budget-minutes | completed | ...
report: null            # written when the run stops
```

## Golden-task results (AGT-13)
`.specify/agentic/golden/results.yml`: for each mode, the driver (`scripted` or `agent`), each task with the gates it stopped at and what was observed, each seeded defect with who caught it and how, and a hash of the agent specs the run used.

## Slices 0.5 and 0.6 (added 2026-11-22)

| File | Schema | Written by | Holds |
|---|---|---|---|
| `.specify/agentic/intake/<id>.yml` | `agentic-intake/1` | `connect fetch`, `intake add` | `source {platform, key, url, revision, fetched}`, `title`, `body`, `hash`, `status`, `via`, and when closed `disposition {decision, target, reason, decided_by}`; `latest` and `acknowledged` when the source changed |
| `specs/<spec>/origin.yml` | `agentic-origin/1` | `product specify`; people add decisions | `intake: [ids]`, `candidates: [{target, suggested_by}]` added by agents or people, `dispositions: [{target, decision, reason, decided_by}]` |
| `specs/<spec>/deltas/<capability>.md` | front matter plus `## ADDED / MODIFIED / REMOVED / RENAMED Requirements` | Agent drafts, a person approves at the first gate | Requirement blocks (`### Requirement:`), each with `Verifies: FR-…` and `#### Scenario:` blocks |
| `.specify/agentic/product/capabilities/<id>/spec.md` | generated | `product merge` only | The living spec: purpose, requirements, scenarios, and the changes each requirement came from |
| `.specify/agentic/product/index.yml` | `agentic-product-index/1` | `product init`, `product merge` | `exempt: [specs older than adoption]`, `order: [merges applied]` |
| `.specify/agentic/product/merges/<id>.yml` | `agentic-merge/1` | `product merge` | `merged_on`, `deltas {path: sha256}`, `result` per capability; for adoption, `approved_by` |
| `.specify/agentic/product/glossary.yml` | `agentic-glossary/1` | People | `terms: [{term, definition, avoid}]` |
| `specs/<spec>/outcomes.yml`, `outcomes-review.yml` | `agentic-outcomes/1` | Agent drafts; a Product Owner reviews | `outcomes: [{id, hypothesis, metric, baseline, target, source, review_by}]`; `reviews: [{outcome, result, measured, evidence, reviewed_by, follow_up}]` |
| `specs/<spec>/SEALED.yml` | `agentic-seal/1` | `product archive` | `sealed_on`, `files {path: sha256}` |
| `.specify/agentic/connect.yml` | `agentic-connect/1` | People | `sources`, `notify {channels, routes, templates, links, deadline_days}`, `pipeline_secrets`. Secrets by variable name only |
| `.specify/agentic/context/<spec>/<item>.md` | `agentic-context/1` | `work claim`, `team context --write` | Front matter `sources {path: sha256}`, `trimmed`; then the pack |
| `.specify/agentic/tools.yml` | `agentic-tools/1` | People | `mcp_servers: [{name, command, args | url, reviewed_by, reason}]` |

Settings added to `kit.yml`: `intake.screen`, `intake.owner_roles`, `intake.dedupe.threshold`, `requirements.style | weak_words | allow_words | limits`, `product.merge_days | archive_days | outcomes.from_tier`, `team.context.max_chars`, `team.tools.files`.

