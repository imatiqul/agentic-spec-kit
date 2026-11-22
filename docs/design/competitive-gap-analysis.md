# Where the kit stands against other spec-driven tools

- **Phase and date:** depth review, 2026-11-22
- **Requirement IDs covered:** none directly; this is the reasoning behind slices 0.5 and 0.6 and AGT-19, AGT-20
- **Assumptions:** the public descriptions cited below are accurate; none of these tools was installed or run for this review
- **Unverified:** every statement about another tool comes from its documentation or from a third-party article, not from use

## What the others do well

| Tool | Its strongest idea | Source |
|---|---|---|
| OpenSpec | One spec per capability is the statement of current behaviour. A change is a delta against it (added, modified, removed) and is merged when the change is archived. This suits existing systems | [OpenSpec concepts](https://openspec.dev/docs/core-concepts) |
| Kiro | Requirements in a fixed sentence pattern (EARS), and property-based tests derived from them, each traced to its requirement | [Kiro: correctness](https://kiro.dev/docs/specs/correctness/) |
| BMAD Method | A team of role-playing agents, with a product brief and an architecture before stories | [Comparison, TestMu](https://www.testmuai.com/blog/spec-driven-development-tools/) |
| Tessl | The spec, not the code, is the maintained artefact | [InfoWorld](https://infoworld.com/article/4171332/four-cutting-edge-tools-for-spec-driven-development.html) |
| Spec Kit | Works with about thirty coding agents, and has an extension system. Its community catalogue at v1.4.3 lists 203 extensions | [InfoWorld](https://infoworld.com/article/4171332/four-cutting-edge-tools-for-spec-driven-development.html); the catalogue in the pinned upstream clone |

## What practitioners say is still unsolved

An InfoQ article on adoption at enterprise scale lists the gaps: tools built for developers that shut out product people; one repository when a feature spans many; strategic and tactical documents sharing one folder; no link to existing backlogs; unclear collaboration; specs that drift from code; no clear path for existing systems; specs that turn into stale documentation; and a heavy review burden ([InfoQ](https://www.infoq.com/articles/enterprise-spec-driven-development)).

Two O'Reilly Radar pieces add that a change spec should not outlive the change, and that a spec itself needs review before an agent builds from it ([exit strategy](https://www.oreilly.com/radar/when-ai-writes-the-code-specifications-need-an-exit-strategy/), [right amount of spec](https://oreilly.com/radar/the-right-amount-of-spec-for-agentic-development)).

## The finding

Nearly every single idea exists somewhere as a separate tool or community extension: Jira sync, EARS linting, red-team review, drift checks, worktrees. What is missing is one system in which a gap in any of them fails the build, and in which a person's approval is bound to the exact evidence they saw.

So this kit should not try to win on the number of features. It should win on four properties:

1. **Nothing passes on trust.** Every rule is a check with a fixture that proves it fails.
2. **Approvals are real.** A named person, a pull-request review, a hash of what they reviewed.
3. **A change is a change to a system.** Data, contracts, shared components and other applications are in view before a line is written.
4. **Intent, change and proof are one chain.** From a request, to a requirement, to a behaviour delta, to a test, to the living spec, and back from any line of code.

## Where the kit stands

| What a best-in-class platform needs | State after this work |
|---|---|
| One current statement of what the system does | Built and tested: living capability specs, deltas, replay check (PRD-6 to PRD-9) |
| A change spec that does not outlive the change | Built and tested: merge on release, sealing, sealed changes kept out of agent context (PRD-12, PRD-13). Files are kept, not deleted |
| A start in the backlog tool, not in Git | Built, tested against recorded responses only: five sources (ADP-18) |
| Duplicate and already-delivered detection | Built and tested. It matches wording, not meaning; people and agents add what it misses (INT-5, INT-6) |
| Requirements an agent cannot misread | Built and tested: pattern lint, glossary, size limit (PRD-1 to PRD-5). Not built: tests generated from requirements, as Kiro does |
| Specs sized for review; a brief for the reviewer | Built and tested: size limit, one-page brief that leads with the behaviour change |
| Clear roles and real approvals | Built and tested offline. Never run against a live GitHub repository |
| System-wide impact | Built and tested for one repository. Maps from other repositories can be pinned and validated, and a programme spec can span repositories. Not built: folding those maps into impact analysis, so a blast radius stops at this repository's edge |
| Bounded agents | Built and tested: path guard, locks, budgets, context packs, tool allowlist, run records, routing, planted-instruction tests. The planted-instruction tests have run with a scripted stand-in only |
| Proof that code matches the spec | Built and tested: trace manifest, independent verifier inputs, evidence hashes. No agent has yet produced the evidence |
| Runs in any pipeline; tells people | Built; three pipeline files, none yet run by its CI system |
| A loop from production back to intent | Built and tested: outcome reviews, incident loop. Not built: escaped defects feeding new golden tasks |
| Measures of flow and of agent quality | Built and tested: gate board, waiver register, traceability matrix, system-map diagram, metrics, spend. A measure with no data is not shown |
| Evidence for an auditor | Built and tested: an evidence pack with hashes, the control mapping of each domain pack, approvals, waivers and exceptions. It certifies nothing |

## What would move it furthest now

Not another feature. In order:

1. One run on a live GitHub repository with branch protection, to prove the approval path.
2. One real agent run of a golden task, to prove the agent files, the guard and the context pack.
3. A review by the owner of the sixteen agent specs and the specs under `docs/prompts/spec/17` and `18`.
4. Then the unbuilt rows above, starting with impact analysis across repositories and tests generated from requirements.
