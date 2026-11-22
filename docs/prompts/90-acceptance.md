# Acceptance — how we know it is done

Each line is checked with evidence (path, command, output). "Not run" is a failure
to report, not a pass.

## Slice 0.1 — Govern
- A new engineer installs the kit on the pinned upstream release from the README
  alone.
- The Lite profile is adopted in under an hour without reading Standard or
  Regulated material.
- Every gate shows its accountable role and approver.
- A gate decision recorded by an agent, by the author, or without a matching review
  in the enforcement channel is rejected by a check.
- Every principle in a sample constitution is machine-checked or marked
  human-judged.
- An unrecorded suppression fails; an expired waiver fails.
- A missing or orphaned trace link fails.
- An edited audit log entry is detected.
- Every check has a passing and a failing fixture, and CI shows the failing one fail.
- The documentation lists what is not enforced.

## Slice 0.2 — System
- Discovery produces a map of the fixture with every node owned and every derived
  fact citing a file.
- A change that modifies an undeclared node fails.
- A change to the fixture's shared library adds each consumer's owner as a reviewer
  and runs the consumer matrix.
- A breaking contract change is detected and blocks.
- A destructive data change without a data-change plan and Data Owner approval is
  blocked; a migration tested on a different engine than production fails.
- Two in-flight specs touching the same node are reported and ordered.
- A spec's tier rises to the highest tier it touches.

## Slice 0.3 — Team
- The minimum team of four completes a fixture task end to end, stopping at every
  gate.
- The same task completes in sequential mode with the same gates and evidence.
- Seeded defects (undeclared table touch, breaking contract change, missing tenant
  filter) are caught by the reviewer or verifier.
- An agent editing outside its declared paths is detected.
- A third rework round does not happen; the disagreement is escalated.
- No agent credential can approve, merge, publish or deploy; this is shown, not
  asserted.

## Slice 0.4 — Depth
- A Low-tier change takes the fast lane; an author cannot select it by hand.
- An emergency change with an overdue retrospective fails the default branch.
- An evaluation that does not call the production code path fails QLT-15.
- Planted instructions in fixture files, issues and tool output are reported and
  not acted on.
- A changed agent spec triggers the regression suite and a baseline comparison.
- The auditor pack for one release exports with hashes and its disclaimer.
- Lite profile effort is unchanged from slice 0.1.

## Reference example
- Every finding has a verification status with reproducible evidence.
- One spec exists per confirmed or corrected finding, each with touches, owner and
  reviewers.
- Any line of the C4 change traces back to a constitution principle and forward to
  every data store, contract, shared component and application it affects.
- Every C4 gate decision is a human review mirrored in the record, with
  single-approver exceptions stated.
- No suppression remains in the example without a dated, owned waiver.
- The C5/C6 evaluation design provably runs the production classifier.

## Overall
- Nothing is public, nothing was merged, no real data or secrets are in either repo.
- Every artifact carries the header from `01-working-rules.md`.
- Upstream and community components are attributed and their reviews recorded.
