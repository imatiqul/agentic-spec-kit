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
- An agent's context for a task is rebuilt identically from the same repository, and
  a change to its sources while the task is in progress fails.
- A tool server that is not on the allowlist, is launched differently from what was
  reviewed, or floats on "latest" fails.

## Slice 0.5 — Truth
- A requirement that repeats one already in flight, or one the system already
  meets, is listed as a candidate, and the spec cannot pass its first gate until a
  Product Owner has decided it.
- Personal data and credentials in an incoming requirement are replaced before the
  record is written.
- A vague requirement, a requirement with two obligations and a spec too large to
  review each fail before the first gate, and none fails after a person approved
  the wording.
- A living spec edited by hand fails; so does a merge before release and an edit to
  a merged delta.
- After release, one command merges the change into the living specs, and the
  finished change is sealed and left out of agent context.
- From one line of code, one command names the request, the requirement, the
  capability and the approvers.

## Slice 0.6 — Connected
- Requirements are fetched from each supported tracker and from documents into the
  same record shape, with no adapter test using a network.
- One command runs the whole kit in a pipeline with no prompt.
- A notification contains no requirement text, in any channel.
- An event is announced once across repeated runs.
- A webhook address or token in a configuration or pipeline file fails.
- A pipeline that lets a proposed change, or an agent step, read a tracker or
  notification credential fails.
- A review is mirrored into a decision record only when it carries the gate's line
  for the current evidence and covers every required role.

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
