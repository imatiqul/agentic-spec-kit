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
  - {node: identity-service, distance: 1, via: builds-with lib-infrastructure, owner: backend}
  - {node: identity-db, distance: 1, via: is owned by identity-service, owner: data-owner}
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

## Slice 0.4 additions (added 2026-11-22)

### Agent step (AGT-17)
One entry in `.specify/agentic/audit/<spec>.jsonl` per step, written only by `orchestrate step`. The action is `agent.<action>`.
```json
{"action": "agent.step", "actor": {"type": "agent", "id": "backend-implementer"}, "spec": "004-audit-identity", "run": "r1",
 "inputs": ["specs/004-audit-identity/tasks.md"], "input_hashes": {"specs/004-audit-identity/tasks.md": "sha256:…"},
 "outputs": [], "agents_hash": "sha256:…", "model": {"name": "…", "version": "…"},
 "tools": ["Read", "Edit"], "tools_source": "declared", "cost": 0.25, "seconds": 41.0, "gate": "G5"}
```
| Field | Filled by | Note |
|---|---|---|
| `agents_hash`, `input_hashes` | The kit | An input that does not exist is recorded as `missing` |
| `tools`, `tools_source` | The kit, or the runtime | `reported` when the runtime passed `--tools`; otherwise `declared`, copied from the agent spec |
| `seconds` | The runtime, or the kit | When not reported, the time since the run's last step |
| `model`, `cost` | The runtime only | The kit cannot see either. CK-RUN-RECORD fails a step that leaves one out; nothing can prove what was reported |
| `gate` | The orchestrator | The gate the work is heading for; `report spend` groups by it |

The run record (`runs/<spec>/<run>.yml`) gains `cost`, the sum of its steps, and `budget.cost`. A run past its cost budget stops with `stop_reason: budget-cost`.

### Golden baseline (AGT-14)
`.specify/agentic/golden/baseline.yml`, written by `golden baseline --accepted-by <person>:<role>:pull/<n>#review-<id> --write`.
```yaml
schema: agentic-golden-baseline/1
agents_hash: "sha256:…"        # the agent specs the results were produced with
routing_hash: "sha256:…"       # the routing policy at that time
accepted_by: {reviewer: bob, role: engineering-manager, review_ref: "pull/7#review-31"}
results:
  parallel:
    tasks: {T001: true}         # completed
    defects: {D1: true}         # caught
    injections: {in-a-file: true, in-an-issue: true, in-tool-output: true}   # reported and not acted on
```
The kit checks that the reviewer is a person in `roles.yml` and that the reference is well formed. It does not look the review up. What protects the baseline is that it is read from the base branch once it is there, that agents may not write `golden/*`, and that CODEOWNERS covers `.specify/`.

Golden results (`golden/results.yml`) gain, per run, `injections: [{id, channel, acted, reported, evidence}]`, and at the top `routing_hash` when the golden tasks were run for a project that has a routing policy (`agentic.py --root <project> golden run --fixture <fixture> --out <project>/.specify/agentic/golden/results.yml`).

### Evidence pack (TRC-16)
`agentic.py audit-pack --spec <spec> --write` writes `specs/<spec>/release/audit-pack.json`; `--out <dir>` writes the whole pack as files, with `MANIFEST.json` and a `README.md`. `--from <date> --to <date>` takes every spec released in the range.
```yaml
schema: agentic-audit-pack/1
statement: This pack supports an audit. It does not certify compliance with any law, regulation or standard.
generated_on: "2026-11-22"
kit: {version, upstream, profile, domain_packs}
scope: {specs: [...]}                      # and from / to when a range was asked for
controls:                                  # from each active domain pack's `controls: [{section, reference, asks}]`
  - {pack, reference, section, asks, specs: {<spec>: {present, sha256, where}}}
approvals: [{spec, gate, decision, commit, evidence_hash, approvals: [{reviewer, role, review_ref}], conditions, lane}]
waivers: [...]                             # active waivers, and the adoption baseline by rule and count
exceptions: [...]                          # single-approver decisions and emergency changes
checks: {CK-…: pass | fail | not run | skipped}
audit_log: intact                          # or "NOT INTACT: …"
sources: {<repository path>: sha256}
files: {<path inside the pack>: sha256}     # in MANIFEST.json only
delivery: {<spec>: <ledger>}              # since 2026-11-26: the commits, branches and pull requests of each spec, as found that day
```

### Report views (TRC-15)
`agentic.py report <view>`; `report all --out <dir>` writes every view, and `--html` adds one self-contained page. Views are generated; nothing reads them back.

| View | From | Registered by |
|---|---|---|
| `gates`, `waivers`, `trace`, `metrics` | Decision records, waivers, the trace manifest, the audit log | core |
| `changesets` | One line for each change: its open gate, its tier and its pull requests (added 2026-11-26) | core |
| `map` | The system map, as a diagram and a table | system |
| `debt` | The technical-debt register: discovery findings, waivers, drift | quality |
| `spend` | Agent steps | team |
| `capabilities` | The living specs | product |

A metric is a row `{metric, value, source}`. Extensions add rows through `METRIC_HOOKS`. A measure with no data is left out, not shown as zero.

### Settings added to `kit.yml`
| Setting | Meaning | Default |
|---|---|---|
| `team.routing.<class>: {model, version}` | The model each class of agent may run on | none; required at Regulated |
| `team.spend.per_spec` | Limit on recorded agent cost for one spec | none |
| `team.budget.cost` | Limit on recorded cost for one run | none |
| `team.memory.files` | More instruction files to lint | none |
| `team.memory.forbid: [{pattern, why}]` | More things an instruction file may not grant | none |
| `team.memory.allow_missing` | Paths an instruction file may name although they do not exist | none |
| `team.tools.files` | More MCP configuration files to read | none |
| `metric_claims.scan` | Files CK-METRIC-PROVENANCE reads for figures, as path patterns. In prose a figure is a percentage on a line that names a measure; in any other file it is also a number given to a name that says what it measures (`accuracy = 0.94`) | `[README.md]` |
| `metric_claims.allow` | Regular expressions; a line that matches one is not read for figures | none |

## Phase 12 additions (added 2026-11-26)

Each of these is described in full in its own document under `docs/design/`. What follows is where each file is and what holds it to its form.

### Decision log (DEC-1)
`specs/<spec>/decision-log.yml`, written by `agentic.py decision` and by a hand-off's questions; a person may edit it. It is part of the evidence of G5 where a spec has one. `CK-DECISION-LOG` holds it to this form.
```yaml
schema: agentic-decision-log/1
entries:
  - id: D-001                    # D- and three digits or more
    title: <the question>
    state: decided               # proposed | open | decided | superseded
    outcome: <what was decided>  # needed when decided; refused while proposed or open
    why: <the reason>
    owner: <person id>           # needed when decided; a person in roles.yml
    decided_on: 2026-11-26       # needed when decided
    proposed_by: <agent or person id>
    affects: [FR-001, T003, "node:<map node id>", "adr:<file>"]
    source: <a link>
    superseded_by: D-002         # needed when superseded; another entry of this log
```
Audit actions: `decision-log.add`, `decision-log.decide`, `decision-log.supersede`, each with `entry`, `state` and `outputs`. The actor is `{type: kit, id: decision}`, or the agent where a hand-off made the proposal.

### The conversation behind a change (CNV-1, CNV-5, CNV-6)
`specs/<spec>/origin.yml` gains `conversation`, written by `agentic.py product conversation`. An intake record gains `threads`, written by `intake add --thread`, and `discussion`, written by `connect fetch`; a person writes `acknowledged`. `CK-CONVERSATION` holds all of it to this form.
```yaml
# in origin.yml
conversation: {summary, links: [<url>], people: [<id or name>], captured_on, captured_by, confirmed_by}
# on an intake record
threads: [<url>]
discussion:
  comments: 2
  hash: "sha256:…"               # label agentic-discussion/1: over each comment's id, author and the sha256 of its screened text
  fetched: "2026-11-21"
  partial: true                  # only where the item has more comments than the kit reads
  latest: {comments, hash, fetched}                                             # set when the discussion moved after someone acted on the record
  acknowledged: {hash, action: amend | ignore, reason, decided_by: {reviewer, role}}   # a Product Owner's
```
Of a comment neither the text nor the author is written anywhere.

### The page of a change (CHS-7, CHS-8) — generated
`agentic.py changeset --spec <spec> --json` prints `{spec, title, about, sections: [{heading, lines, data}]}`. `--write` keeps the page as `specs/<spec>/changeset.md`, whose first line marks it as generated. It is never gate evidence, and nothing reads it back. The ledger of a change, `delivery.ledger(ctx, spec)`, is `{spec, git, note, default_branch, found, cut, commits, branches, more_branches, adapter, pulls, unread}`; the evidence pack keeps it under `delivery`.

### The file adapter's stand-in file
`.specify/agentic/_adapter/reviews.json` is for tests and the demo, and proves nothing about what GitHub holds. Two things may now be in it.
```json
{"changes": {"pull/7": {"authors": [], "reviews": [], "state": "open", "head": "", "base": "", "merge_commit": "", "url": "", "commits": []}},
 "repositories": {"<owner>/<name>": {"default": "<commit id>", "commits": {"<commit id>": {"<path>": "<text of the file>"}}}}}
```
`state` is `open`, `closed` or `merged`; with none, an entry that names a merge commit is merged and any other is open (DLV-3). `repositories` is what another repository holds at a commit, for a programme's child there (PRG-11).

### Search (SRC-3, SRC-11)
A hit is `{path, line, text, node, tier, group}`: the text is 200 characters at most, and `group` is `touched`, `near` or `rest`. `agentic.py search --json` prints `{hits, total, limit, cut, tracked, groups, touched, near, notes}`. The search reads `nodes[].id` and `tier`, `edges[].from` and `to`, and `index[].paths` and `node` of `system-map/map.yml`, and `touches` of a spec. It writes no file.

### A programme's child in another repository (PRG-8)
In a parent's front matter a child is `{spec, repo, ref}`. `repo` is `.` for this repository and is left out then; for another it is `<owner>/<name>` on the host of this project's enforcement adapter, and `ref` is a commit id of seven to forty characters. `CK-PROGRAMME` asks for the commit id and takes any text for `repo`; the page reads only a child that is named in this form.

### The MCP server
It adds no file and no schema, and it writes nothing. A person lists it in `.specify/agentic/tools.yml` as `{name: agentic-spec-kit, command: python, args: [".specify/extensions/agentic-mcp/scripts/agentic_mcp.py", "--root", "."], reviewed_by, reason}`, with the same `command` and `args` in the client's own file. The JSON inside a tool's result is described in `mcp-server.md` (MCP-9 to MCP-17) and is not promised as a schema.
