# Change packs — rules for changing a kind of thing

A pack applies when a spec touches a node of its kind (MAP-8). Packs are neutral;
engine, format and platform specifics are adapters (`16-adapters.md`).

## Data stores
- CHG-1 [0.2] A data-change plan is mandatory when a spec touches a data store.
- CHG-2 [0.2] Classify the change: additive, backward-compatible, breaking,
  destructive. Breaking changes go expand → migrate → contract across releases.
  Destructive changes need Data Owner approval and a tested restore.
- CHG-3 [0.2] The plan contains: forward migration; rollback or roll-forward
  strategy; backfill with volume and lock or time estimate; compatibility with the
  previous application version during rollout; index and query impact; tenant
  isolation; retention and deletion; field classification and encryption.
- CHG-4 [0.2] Checks: migrations are generated and tested on the same engine and
  major version as production; model-versus-migration drift fails; suppressed
  migration warnings fail; a store written by more than one service is flagged as
  shared with every writer named; seed and test data are synthetic.
- CHG-5 [0.2] Non-relational stores get the equivalent: document shape versioning,
  index and partition-key changes, cache key and expiry changes, vector re-embedding
  and search index rebuild plans.

## Contracts
- CHG-6 [0.2] Every API, event and schema contract is versioned.
- CHG-7 [0.2] Breaking-change detection runs on every change.
- CHG-8 [0.2] Consumer-driven contract tests run for each consumer in the map.
- CHG-9 [0.2] Deprecations carry a date and a named migration path; contract drift
  between the declared contract and the running code is reported.

## Shared components
- CHG-10 [0.2] Libraries, UI components, design tokens, pipeline templates and
  infrastructure modules use semantic versioning and a consumer registry taken from
  the map.
- CHG-11 [0.2] Gate evidence includes a breaking-change check and a consumer
  build-and-test matrix.
- CHG-12 [0.2] Approval: Platform plus the owner of each consumer whose build or
  tests change.

## Other applications and external services
- CHG-13 [0.2] Each dependency records: contract and version, authentication
  method, data exchanged and its classification, expected availability, timeout,
  retry and circuit-breaker behaviour, the failure the user sees, and a test double
  for CI.
- CHG-14 [0.2] Where the active domain pack requires a legal agreement for the data
  exchanged, record its status, not the document.

## Supply chain
- CHG-15 [0.2] Bill of materials per release, licence compatibility check, pinned
  versions and digests. Suppressed advisories are waivers (GOV-15).

## Infrastructure
- CHG-16 [0.4] Infrastructure changes get impact analysis, policy-as-code checks
  and a cost estimate against a stated budget.
- CHG-17 [0.4] An environment parity matrix (engine versions, flags, configuration)
  is maintained and drift is reported.

## Release
- CHG-18 [0.2] The plan states deploy order across affected nodes, flags,
  compatibility window and rollback order. The G7 bundle shows the order is safe.
- CHG-19 [0.4] Progressive delivery: stages, health signals that halt rollout,
  rollback trigger, and a rollback rehearsal for Critical changes.
- CHG-20 [0.4] Feature flags have an owner, a default and a removal date; expired
  flags fail.
- CHG-21 [0.4] After release, acceptance criteria that can be checked in production
  are checked, and the result closes the trace.
