---
spec: 025-event-contracts
finding: N9
tier_declared: high
owner_role: solutions-architect
principles: [P-20]
touches: [topic-triage.completed, topic-escalation.required]
depends_on:
  nodes: [pubsub]
  specs: []
---
# Feature Specification: Every event topic has a publisher and a name that can be read from the source

- **Phase and date:** Phase 5, batch 4, 2026-11-22. Draft, waiting at gates G1 and G2
- **Upstream and reference:** spec-kit `v1.4.3`; healthcare repository at commit `6e0879d2`
- **Requirement IDs exercised:** GOV-9, MAP-8, TRC-1, PRD-1 to PRD-3
- **Assumptions:** A1 and A2 under "Questions for G2". The tier follows the components
- **Unverified:** nothing was built or run; the evidence is from reading files in Phase 1 and file listings on 2026-11-22

## Finding
N9, found in Phase 1. Two topics, `triage.completed` and `escalation.required`, have subscribers and no publisher that could be derived. Of the publish calls, 27 name their topic by something other than a literal, so event contracts cannot be checked from the source.
Evidence: The system map: `topic-triage.completed`, `topic-escalation.required`.

## User Stories
- As an architect, I want to know who publishes each event, so that a subscriber is not waiting for something nobody sends.
- As a developer, I want a topic's name to be one constant, so that a typing mistake is a build error and not a silent loss.

## Requirements
- **FR-001**: Every topic on the system map MUST have at least one publisher on the map.
- **FR-002**: A publish call MUST name its topic by a constant from the shared event catalogue.
- **FR-003**: The build MUST fail when a publish or subscribe call uses a topic that is not in the catalogue.
- **FR-004**: Each of the two topics named in the finding MUST gain a publisher or lose its subscribers.

## Acceptance Criteria
- **AC-001** (verifies FR-001): Given the system map after the change, When the topics are listed with their publishers, Then none has an empty list.
- **AC-002** (verifies FR-002): Given the source after the change, When the architecture test lists publish calls, Then each names a constant from the catalogue.
- **AC-003** (verifies FR-003): Given a change that publishes to a topic name typed inline, When the build runs, Then it fails and names the call.
- **AC-004** (verifies FR-004): Given the two topics, When the map and the source are read after the change, Then each has a publisher in both, or no subscriber in either.

## Non-Functional Requirements
- **NFR-001**: The catalogue is in a shared library, so publishers and subscribers read the same constant.

## Risks
- A subscriber with no publisher may be dead code, or may show that a publisher was lost. Which it is has to be found before anything is removed.
- The 27 calls are spread over several services, so the change is wide and shallow.

## Out of Scope
- Versions and consumer tests for the events, which the kit lists as gaps of their own.

## Questions for G2
- A1 (assumed): the plan decides, topic by topic, whether the missing publisher is added or the subscribers are removed, with the Solutions Architect.
- A2 (assumed): the shared event catalogue goes in the existing domain library.

## PHI Involved
Events can carry PHI. This spec changes how topics are named and who publishes them, not their content.

## Access Control
Not applicable: this spec changes nothing here.

## Audit Controls
Not applicable: this spec changes nothing here.

## Integrity
Not applicable: this spec changes nothing here.

## Authentication
Not applicable: this spec changes nothing here.

## Transmission Security
Not applicable: this spec changes nothing here.

## Minimum Necessary
Not applicable: this spec changes nothing here.
