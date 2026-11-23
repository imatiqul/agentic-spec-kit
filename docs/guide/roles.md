# Role guide: what each person does, and where

- **Phase and date:** closing documents, 2026-11-22
- **Requirement IDs covered:** GOV-1 to GOV-8, GOV-17 to GOV-20, INT-4, INT-6, PRD-15, PRD-16, AGT-14
- **Assumptions:** the default approvers; a project may change them in `kit.yml` under `gates.approvers`
- **Unverified:** the approval path has not been run against a live GitHub repository

## How a gate is passed

1. An agent, or the pipeline, writes the reviewer's page: `specs/<spec>/briefs/<gate>.md`. It is one page: what changed since the last review, the behaviour change, similar work, impact, risks, open waivers, and what a verifier disputed.
2. You open the pull request and read that page, then as much of the evidence as you need.
3. You submit a review. To approve, the review contains the line the gate command prints, for example:
   `gate G3 approve sha256:…`
   The hash binds your decision to exactly what you reviewed. To send it back, request changes with `reject` in place of `approve`.
4. The decision is mirrored into a record in the repository, by the pipeline or by the record command. The checks then read your review itself to confirm who you are, which role you hold, and that you did not author the change.

**What never counts as a decision:** a reply in chat, a comment on a work item, an email, a statement by an agent, or an approval of evidence that has since changed.

## Who approves what

These are the defaults (`DEFAULT_APPROVERS` in the core extension). At Standard and Regulated a gate needs every role listed for it; at Lite it needs any one of them.

| Gate | What is approved | Roles |
|---|---|---|
| G0 | The constitution | Product Owner, Solutions Architect, Security and Compliance |
| G1 | The spec | Product Owner |
| G2 | The clarified spec | Product Owner, Solutions Architect |
| G3 | The plan | Solutions Architect, and the roles the change's impact adds (below) |
| G4 | The tasks | Engineering Manager, QA |
| G5 | The implementation evidence | QA, and the roles the change's impact adds (below) |
| G6 | The independent verification | QA |
| G7 | The release | DevOps / SRE, Product Owner |

G4 comes before work on the tasks starts. G5 and G6 come before the change is merged: the checks on the default branch fail while a spec's work is there without them.

### Roles the kit adds from what a change touches (Standard and Regulated)

| When the change | These roles join | At |
|---|---|---|
| Touches a component, or one that is one step away from it on the system map | The owner of each such component | G3 |
| Touches a component | The owner of each touched component | G5 |
| Touches or is one step from a data store | Data Owner | G3; G5 when the store itself is touched |
| Touches or is one step from a shared component | Platform | G3; G5 when the component itself is touched |
| Touches or is one step from something that holds protected data | Security and Compliance | G3; G5 when it is touched itself |

Nobody chooses these. The impact report lists them, and the gate command prints them.

### What each role is looking at

| Role | Looking at | Also yours |
|---|---|---|
| Product Owner | Whether this is the right thing to build, how behaviour changes, whether it repeats existing work, the result it expects | Deciding each duplicate candidate; closing an intake record without a spec; accepting the first living specs on an existing system; recording what an outcome review measured |
| Solutions Architect | Whether the plan fits the system: what it touches, what it reaches, data and contract changes, rollout order | |
| Engineering Manager | Whether the work is cut into tasks with owners, paths and an order that can run | May approve an emergency change |
| QA | Whether every criterion is traced to a passing test, and what the independent verifier found | |
| Security and Compliance | Whether the principles can be enforced; protected data in the blast radius | Approving a waiver marked critical; may approve an emergency change |
| DevOps / SRE | Readiness to run it: rollout, rollback, alerts, the software bill of materials, the evidence pack | May approve an emergency change |
| Backend, Frontend, AI Engineer, Platform | The impact report: your component is in the blast radius | Owning the components the system map gives you |
| Data Owner | The data-change plan, the classification of each migration, the restore test for a destructive one | |

Three things need a named person from `roles.yml` and no particular role:
- **Resolving an escalation.** After two rework rounds a work item is blocked and an escalation is written with both positions. It names the role accountable for the item. A person records the decision in that file; no agent may.
- **Accepting the golden-task baseline.** The baseline names the person and the review in which they accepted it.
- **Approving an ordinary waiver.** The waiver names its owner, its expiry and the review that approved it.

An emergency change needs one approval from DevOps / SRE, the Engineering Manager or Security and Compliance (`lanes.emergency.roles` in `kit.yml` changes the list).

## How much of this applies to you

| Profile | Gates |
|---|---|
| Lite | G1, G3, G5 |
| Standard, Regulated | G1 to G7 |
| Fast lane (computed, never chosen) | A change that touches only Low-tier components and triggers no change pack has one review, at G4, by everyone G1 to G4 would have asked |
| Emergency | The fix goes in with one named person's review; a retrospective spec is due within the number of days `kit.yml` sets (`lanes.emergency.days`), and the default branch fails after that |

## If you hold more than one role, or wrote the change yourself

One person may hold several roles, and one review by that person counts for each role they hold that the gate needs.

A person may not approve a change they authored. A project with too few people can allow it (`gates.single_approver_exception: allowed` in `kit.yml`; the default is `forbidden`). The decision record must then say so, and the evidence pack lists every such decision as an exception.

## Where to look

| You want to know | Look at |
|---|---|
| What is waiting for me | `agentic.py report gates`, or the notification you were sent |
| What exactly I am approving | `agentic.py gate --spec <spec> --gate <gate>` |
| Why a line of code exists and who approved it | `agentic.py why <file>:<line>` |
| What the system does today | `agentic.py product catalog` and the living specs it lists |
| Which exceptions are open and when they end | `agentic.py report waivers` |
| How the team is doing | `agentic.py report metrics` |
