# Quality packs — how deep the checking goes

Depth is set by risk tier (GOV-9) and profile (GOV-13). Regulated-domain specifics
are adapters (`16-adapters.md`).

## Independent verification
- QLT-1 [0.1] A verifier that did not author the artifact checks it against the
  spec, the constitution and, from slice 0.2, the system map. It receives only
  those inputs, never the author's working context.
- QLT-2 [0.1] The kit states that this is procedural isolation, not a technical
  guarantee.

## Security
- QLT-3 [0.4] Threat model per spec at Standard and above, each threat linked to a
  mitigation requirement and a test.
- QLT-4 [0.4] Abuse cases are written as acceptance criteria.
- QLT-5 [0.4] G5 evidence includes secret scan, dependency scan, static analysis
  and, where an endpoint changes, an authorization test matrix (role × tenant ×
  resource).

## Privacy
- QLT-6 [0.4] A privacy impact for any spec touching classified data: purpose,
  minimum fields, lineage from the map, retention, access paths, who can see what.

## Test depth
- QLT-7 [0.4] A test strategy table per tier: unit, integration, contract,
  migration, end-to-end, performance, resilience, accessibility, and which are
  mandatory at which tier.
- QLT-8 [0.4] Critical tier adds mutation testing on changed code with a threshold,
  negative and boundary tests for every acceptance criterion, and a resilience test
  per external dependency relied on.
- QLT-9 [0.4] Brownfield: characterization tests exist and pass before code the
  spec touches is changed.
- QLT-10 [0.4] Test data comes from synthetic generators in the repo; a check
  rejects fixtures that look like real personal data.
- QLT-11 [0.4] Frontend changes are checked for accessibility to a stated level and
  for design-system conformance.
- QLT-12 [0.1] Skipped and flaky tests are waivers (GOV-15).

## AI systems
Applies when the map contains model, prompt, tool or retrieval-index nodes.
- QLT-13 [0.4] Those nodes are versioned; changing one is a spec change with the
  same gates.
- QLT-14 [0.4] Evaluation is a gate: a versioned golden set with documented
  provenance and domain sign-off; thresholds set in the spec; regression against
  the last released baseline blocks G6.
- QLT-15 [0.4] The evaluation must exercise the production code path, and a check
  proves it does.
- QLT-16 [0.4] Critical AI behaviour has a safety case: claim, evidence, residual
  risk, human-in-the-loop control, and who accepted it.
- QLT-17 [0.4] Retrieved content is kept separate from instructions and from
  classifier input; index provenance and refresh are recorded; prompt-injection and
  data-leak tests are in the suite.
- QLT-18 [0.4] Runtime: latency and cost budgets per feature, fallback when the
  model is unavailable, logging that excludes classified data, and a kill switch.
- QLT-19 [0.4] No fabricated metrics: any figure shown to users or in reports
  traces to a recorded evaluation or telemetry source.

## Operability
- QLT-20 [0.4] The G7 bundle includes operational readiness: service objectives
  touched, telemetry added, alerts, dashboards, runbook changes.

## Feedback loops
- QLT-21 [0.4] Architecture decision records link to specs and map nodes; a
  superseded record flags the specs that relied on it.
- QLT-22 [0.4] Incident to spec: a postmortem creates a finding linked to the spec,
  the gate that should have caught it, and a proposed constitution or check change.
