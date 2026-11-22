# Governance — who decides

Neutral rules. Platform bindings are in `16-adapters.md`.
Build only what upstream and the community do not already provide (charter D7).

## Roles
- GOV-1 [0.1] Every artifact, gate and system-map node has one accountable human
  role and one supporting agent.
- GOV-2 [0.1] Roles: Product Owner, Solutions Architect, Backend, Frontend, AI
  Engineer, Data Owner, Platform (shared components), QA, Security & Compliance,
  DevOps/SRE, Engineering Manager. Teams may rename or merge roles in config.
- GOV-3 [0.1] A roles file maps roles to people. One person may hold several roles;
  the kit reports every place where that removes separation of duties.

## Gates
- GOV-4 [0.1] Gates G0–G7: constitution, spec, clarify, plan, tasks + analysis,
  implementation, verification, release.
- GOV-5 [0.1] Each gate defines entry criteria, an evidence bundle, approving
  role(s), and a decision: approve, reject, or approve with conditions. The decision
  is tied to a commit.
- GOV-6 [0.1] A decision counts only if it arrives through a channel an agent
  cannot write to with its own credentials. The in-repo decision record mirrors
  that channel; a check fails when they disagree, or when the approver is the
  author or a non-human account.
- GOV-7 [0.1] The author of an artifact, human or agent, never approves it.
- GOV-8 [0.1] The kit states, per adapter, what is and is not enforced, and what an
  administrator must configure. Unenforced rules are labelled as convention.

## Risk tiers
- GOV-9 [0.1] Critical, High, Medium, Low. The tier sets required reviewers, test
  depth and evidence.
- GOV-10 [0.2] The tier of a spec is the highest tier of anything it touches,
  computed from the system map, not chosen by the author.

## Constitution
- GOV-11 [0.1] Each principle is either machine-checked (CI rule, architecture
  test, policy-as-code) or explicitly marked human-judged, with the gate where a
  human judges it.
- GOV-12 [0.4] Amendments are versioned and re-approved at G0, with a report of
  every approved spec the amendment invalidates.

## Profiles
- GOV-13 [0.1] A profile is declared once and every check reads it.
  - Lite: G1, G3, G5; one reviewer; traceability to requirement level.
  - Standard: all gates; impact analysis.
  - Regulated: Standard plus a domain pack, independent verification and the
    auditor evidence pack.
- GOV-14 [0.1] Lite must be adoptable without reading Standard or Regulated material.

## Waivers
- GOV-15 [0.1] Any suppressed rule (skipped test, ignored advisory, CI escape, lint
  disable, unmet principle) is a recorded waiver with owner, reason, scope,
  compensating control and expiry date. Unrecorded suppressions fail. Expired
  waivers fail.
- GOV-16 [0.1] Waivers on Critical-tier principles need Security & Compliance
  approval and are listed in every release evidence bundle.
- GOV-21 [0.1] Adoption baseline: when the kit is first applied to an existing
  codebase, existing suppressions may be recorded as one baseline, grouped by rule,
  each group with an owner, reason and expiry, approved once at a gate. New
  suppressions need individual waivers. The count in each group may only go down.

## Lanes
- GOV-17 [0.4] Fast lane: Low-tier changes may merge G1–G4 into one review. The
  lane is selected by impact analysis, never by the author.
- GOV-18 [0.4] Emergency lane: a production fix may proceed on one human approval,
  provided a retrospective spec and the skipped gates are completed within a
  configured number of days. A check fails the default branch after the deadline.
- GOV-19 [0.4] Spec amendments: a change to an approved spec re-opens only the
  gates its diff affects; the kit computes which.

## Human reviewer support
- GOV-20 [0.4] Every gate produces a one-page brief: what changed since the last
  review, impact, risks, open waivers, and anything a verifier disputed.
