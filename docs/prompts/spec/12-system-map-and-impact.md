# System map and impact — what exists and what a change reaches

## System map
- MAP-1 [0.2] A versioned, technology-neutral map in the repo is the one source of
  truth for what exists and what depends on what.
- MAP-2 [0.2] Node types: application or service; frontend; data store (relational,
  document, key-value, cache, search index, vector store, object storage,
  warehouse, event store); schema object (table, collection, index, with field-level
  classification where it matters); API contract; event, topic or queue; shared
  library or package; shared UI component or design system; shared pipeline or
  infrastructure module; infrastructure resource; external application or
  third-party service; identity provider; AI model, prompt, tool or retrieval
  index; feature flag; secret reference (name only).
- MAP-3 [0.2] Edge types: calls, reads, writes, owns, publishes, subscribes,
  builds-with, deploys-with, authenticates-via. Every edge names consumer and
  provider.
- MAP-4 [0.2] Every node carries owner role, risk tier, data classification,
  environment notes and source repo. A node with no owner fails.
- MAP-5 [0.2] Discovery derives nodes and edges from the codebase and marks each as
  derived (citing the file that proves it) or assumed. A human confirms the map at
  a gate.
- MAP-6 [0.2] Discovery re-runs in CI and reports drift between map and code.
- MAP-7 [0.2] A map may federate maps from other repos by pinned reference, so a
  provider sees consumers that live elsewhere.

## Declaring a change
- MAP-8 [0.2] Every spec and plan declares `touches` and `depends_on`.
- MAP-9 [0.2] A check compares the declaration with the files a change actually
  modifies and fails on undeclared touches.

## Impact analysis
- MAP-10 [0.2] From the map, compute the blast radius: direct and transitive
  consumers, shared data, contracts and deployments affected.
- MAP-11 [0.2] The impact report is part of the G3 and G5 evidence bundles.
- MAP-12 [0.2] Impact drives governance: the owner of each affected node becomes a
  required reviewer; the tier is raised (GOV-10); classified data adds Security &
  Compliance.

## Across specs and repos
- MAP-13 [0.2] Detect in-flight specs that touch the same node; order them by
  declared dependency; block a gate when a spec it depends on has not passed the
  gate it needs.
- MAP-14 [0.2] A change spanning several applications or repos is a programme spec:
  a parent, child specs per repo, a shared contract agreed first, and a rollout
  order.

## Brownfield
- MAP-15 [0.2] From an existing codebase, produce a draft map, draft specs for
  current behaviour, and a findings backlog. Every finding cites evidence.
- MAP-16 [0.4] A technical-debt register is fed by discovery, waivers and drift
  reports, ordered by tier and blast radius.
