# Traceability and audit — what is recorded

## Traceability
- TRC-1 [0.1] Stable IDs link principle → requirement → acceptance criterion →
  task → test → change request → evidence.
- TRC-2 [0.2] Requirements also link to the system-map nodes they touch.
- TRC-3 [0.1] A check fails when any link is missing or orphaned in either
  direction.
- TRC-4 [0.1] A traceability matrix is generated, never hand-written.

## Audit log
- TRC-5 [0.1] Append-only record of kit command runs and gate decisions: who, role,
  what, commit, time. Hash-chained so edits are detectable.
- TRC-6 [0.3] Agent runs are logged too: which agent, on whose behalf, inputs and
  outputs by path.
- TRC-7 [0.1] The log states its own limit: it does not capture actions taken
  outside kit commands.

## Drift
- TRC-8 [0.1] Spec drift: after merge, detect code that no longer matches its
  approved spec.
- TRC-9 [0.2] Map drift and contract drift are detected the same way
  (see MAP-6, CHG-9).
- TRC-10 [0.1] Drift is reported as a finding; it is never auto-fixed without a spec.

## Metrics
- TRC-11 [0.1] Lead time per gate and rework rate, computed from the audit log.
- TRC-12 [0.4] Escaped defects, computed from the incident loop (QLT-22).
- TRC-13 [0.4] Agent versus human effort and time-to-decision per gate, computed
  from run records (AGT-17).
- TRC-14 [0.1] A metric with no data source is not shown.

## Reporting
- TRC-15 [0.4] Views generated from the log and the map: gate board, waiver
  register, system-map diagram, traceability matrix, metrics.
- TRC-16 [0.4] Auditor evidence pack: for a release or date range, export the
  control mapping from the active domain pack, evidence per control, approvals,
  waivers and exceptions, with hashes. It states that it supports an audit and does
  not certify compliance.

## Self-tests
- TRC-17 [0.1] Every check ships with a passing fixture and a deliberately broken
  fixture, and CI proves the broken one fails.
