# Product truth — what was asked for and what the system does

Owns three things: how a requirement enters, how good its wording must be before a
person is asked to approve it, and how the repository keeps one current statement of
what the system does. Trackers and file formats are adapters (`16-adapters.md`).

## Intake
- INT-1 [0.5] Every incoming requirement becomes one record in the repository, in
  one neutral shape, whatever tool or document it came from. The record carries its
  source, a copy of the text and a hash of that text.
- INT-2 [0.5] Text is screened before it is written. A value that looks like a
  personal identifier or a credential is replaced, and the record says how many
  were. A record that still contains one fails.
- INT-3 [0.5] A record's text changes only by fetching it again, never by hand.
- INT-4 [0.5] A record ends as exactly one of: specified, duplicate, already
  delivered, rejected. A specified record and its spec point at each other. Closing
  a record without a spec takes a reason and a person who holds the Product Owner
  role.
- INT-5 [0.5] Each incoming requirement, and each spec whose wording is not yet
  approved, is compared with the living specs, every other spec and the open
  intake records. The comparison is repeatable and needs no network. It matches
  wording, not meaning; that limit is stated wherever its result is shown, and an
  agent or a person may add candidates it missed.
- INT-6 [0.5] A spec does not pass its first gate while a candidate has no decision.
  Only a person who holds the Product Owner role decides; an agent never does. The
  decisions are part of the first gate's evidence.
- INT-7 [0.5] When a source changes after someone acted on its record, the record
  keeps its text and notes the new revision. A check fails until a Product Owner
  records whether the spec is amended or the change ignored.

## Requirement quality
These rules apply while a spec's wording is still to be approved: before its first
gate, and again whenever the spec changes after that gate. Once a named person has
approved the wording they stay quiet.
- PRD-1 [0.5] Each requirement states one obligation, with MUST or SHALL.
- PRD-2 [0.5] A vague word with no measure beside it fails. The word list can be
  extended or relaxed per project.
- PRD-3 [0.5] Each requirement has at least one acceptance criterion a test can be
  written from, and no open question remains at the gate. A project may require a
  sentence pattern.
- PRD-4 [0.5] A spec has a size limit, so one person can review it. Larger work is
  split into specs that state their order.
- PRD-5 [0.5] A glossary holds the agreed term for each idea and the words to avoid.
  A spec uses the term. The glossary is read from the base branch.

## Living specs
- PRD-6 [0.5] One living spec per capability states what the system does today, as
  requirements with scenarios. It is the only description of current behaviour an
  agent is given.
- PRD-7 [0.5] A change never edits a living spec. It carries one delta per
  capability: requirements added, modified, removed or renamed. Each added or
  modified requirement is testable and names the spec requirements it carries;
  every requirement of the spec is carried by a delta. The delta is part of the
  first gate's evidence, so the approver approves the change in behaviour itself.
- PRD-8 [0.5] The kit merges a change's deltas when the change has passed every
  gate it needs. Never before, and never by hand.
- PRD-9 [0.5] A check rebuilds every living spec from the merged deltas, in order,
  and fails on any difference. A merged delta is history and cannot change. A
  released change is merged within a set number of days.
- PRD-10 [0.5] Every change states its effect on behaviour, or declares with a
  reason that it has none. A change that touches a component no capability
  describes must describe it, so coverage of an existing system grows with each
  change.
- PRD-11 [0.5] Two changes in flight that alter the same requirement state which
  goes first.
- PRD-12 [0.5] A merged change is sealed: its files are recorded one by one, and a
  later edit or addition fails. Records written after release are the exception.
- PRD-13 [0.5] A sealed change is never given to an agent as context.
- PRD-16 [0.5] On an existing system the first living specs come from adoption
  deltas that describe current behaviour, merged once with the recorded approval of
  a named Product Owner. Specs that existed before adoption are exempt; the list
  is read from the base branch, so a change cannot exempt itself.

## Outcomes
- PRD-14 [0.5] A change at Medium tier or above states, before its first gate, the
  result it expects: hypothesis, measure, baseline, target, where the number comes
  from, and the date to look. Or it says why there is none.
- PRD-15 [0.5] After release, on that date, a Product Owner records what was
  measured and the evidence. An outcome that was not met becomes a new intake
  record or a recorded decision to accept it.
