# Phase 3b, part 1 — System map and impact (slice 0.2)

- **Phase and date:** Phase 3b part 1, 2026-11-21
- **Pinned upstream:** github/spec-kit `v1.4.3`; installed and run against that version
- **Requirement IDs implemented:** MAP-1 to MAP-15, GOV-10, TRC-2, ADP-9 (18 of the 39 tagged `[0.2]`)
- **Not in this part:** CHG-1 to CHG-15, CHG-18, TRC-9 for contracts, ADP-5 to ADP-8 (the change packs; part 2)
- **Assumptions:** one map file, `system-map/map.yml`, instead of the three files sketched in the design
- **Unverified:** see section 5

## 1. What was built
| Unit | Path |
|---|---|
| System extension, 2 commands | `extensions/agentic-system/` |
| Map model, discovery, impact, 11 checks (about 700 lines) | `extensions/agentic-system/scripts/agentic_kit_system/` |
| Multi-app fixture (charter D8) | `fixtures/multi-app/` |
| Tests | `tests/test_system.py` (15 tests) |
| Extension points in the core | `ROLE_HOOKS`, `MANIFEST_HOOKS`, `CLI_HOOKS`, sample and fixture hooks in `agentic_kit/core.py` |

The core discovers sibling extensions at start-up, so installing `agentic-system` adds its checks and commands to the same CLI. The core still works alone.

### Checks added
`CK-MAP-SCHEMA`, `CK-MAP-OWNER`, `CK-MAP-EVIDENCE`, `CK-MAP-DRIFT`, `CK-MAP-FEDERATION`, `CK-TOUCH`, `CK-IMPACT`, `CK-TIER-RAISE`, `CK-CROSS-SPEC`, `CK-PROGRAMME`, `CK-FINDING-EVIDENCE`. They run in Standard and Regulated only.

### How a change now reaches the right people
1. The spec lists the nodes it changes under `touches`.
2. `impact` walks the map backwards from those nodes and writes `impact.md`: everything that depends on them, with distance and owner.
3. The owner of each touched node, and of each direct dependant, becomes a required approver. A data store adds the Data Owner; a shared component adds Platform; protected data adds Security & Compliance.
4. `CK-APPROVER` (slice 0.1) enforces that list at G3 and G5 through the same review mechanism as every other approval.
5. `CK-TIER-RAISE` fails a spec whose declared tier is below the highest tier it touches.

## 2. Evidence
```bash
python extensions/agentic/scripts/agentic.py selftest        # 29 fixtures
python -m pytest tests -q                                    # 51 tests
python extensions/agentic/scripts/agentic.py --root fixtures/multi-app map validate
python extensions/agentic/scripts/agentic.py --root fixtures/multi-app impact --spec 001-money-format
```
- **Self-tests:** 29 checks, each passing on the valid sample and failing on its broken variant.
- **Unit tests:** 51 pass (36 core, 15 system). The 36 core tests also pass with the system extension not loaded.
- **Real install:** a fresh Standard project through `scripts/install.sh`; the CLI then lists 29 checks and `map discover --write` drafts a map.

### On the multi-app fixture
| Scenario | Result |
|---|---|
| Discovery | Finds all 5 nodes and both library dependencies, each citing its file |
| Change to the shared library | Reaches both services at distance 1; G3 needs Solutions Architect, Backend and Platform; G5 needs QA and Platform |
| Change to the shared database | Reaches both writers; adds the Data Owner; triggers the data-store pack |
| A file under an undeclared node changes | `CK-TOUCH` fails and names the node |
| A new dependency appears in a `package.json` | `CK-MAP-DRIFT` fails |
| A service is deleted | `CK-MAP-DRIFT` fails |
| A dependent spec passes a gate before the spec it depends on | `CK-CROSS-SPEC` fails |

### On the real healthcare repo (read-only)
Discovery found **46 nodes and 86 edges** with no configuration: 11 services, 3 shared libraries, 8 frontends, 9 packages, 9 databases, 4 data stores and 1 message bus. The hand-built Phase 1 draft has 77 nodes and 168 edges. The 31 nodes discovery did not find are the kinds it has no adapter for: 15 event topics, 9 external services, 4 AI components, the audit table, the API contract (its file name does not say OpenAPI) and one FHIR server container. It also found no reads, writes, owns or publishes edges. Those stay hand-entered and marked assumed, as the design says.

## 3. Problems found by testing, and fixed
| Found by | Problem | Fix |
|---|---|---|
| Fixture run | Required approvers listed a role twice | De-duplicated |
| Combined test run | The sample's G3 evidence omitted `impact.md` once the system extension added it, so the gate command and the record disagreed | The sample uses the same evidence the gate command does |
| Combined test run | Two core tests assumed no other extension was loaded | Made independent of loaded extensions |
| Self-test | Two fixtures assumed the sample spec was still in flight | Fixtures corrected |

## 4. Deviations from the design
1. **One map file**, with `index` and `federated` inside it. Simpler to review; nothing depended on three files.
2. **Federated maps are checked from a committed snapshot.** The kit does not fetch other repositories. It checks that the reference is a commit and that the snapshot was taken at that commit.
3. **"In flight" means no approved G5.** `CK-TOUCH` uses the specs changed in the pull request, or failing that every spec without an approved G5.
4. **Brownfield (MAP-15) is half machine, half agent.** The kit drafts the map and checks that findings cite evidence. Drafting specs and findings from code is an agent task described in the `adopt` command, and its quality is not checked.

## 5. What I did not verify
- Everything listed as unverified in the Phase 3a report still applies: no live GitHub, no CI run, no Windows run, no agent in the loop.
- Discovery was run on two codebases only (the fixture and the healthcare repo). Other stacks will find less.
- `CK-TOUCH` against a real pull request diff. It was tested with explicit file lists; the `git diff` path is exercised only indirectly.
- The fixture's services are not runnable code and were never started.
- A fresh Standard project reports the map checks as "not run" until `system-map/map.yml` exists, which fails `check`. That is by design but has not been tried on a real adoption.

## 6. Decisions I need from you
1. Approve part 1, or say what to change.
2. **Discovery scope.** Add adapters now for the gaps the healthcare repo exposed (event topics from publish and subscribe calls, external services from SDK references), or leave them hand-entered until the healthcare example needs them in Phase 5. I recommend leaving them: both need stack-specific parsing, and the hand-built map already has them.
3. **Standard adoption friction.** Whether a project with no map yet should fail (current) or warn for a grace period. I recommend keeping the failure and letting the adoption baseline carry it, so there is one mechanism for "not there yet".

## 7. What part 2 needs from you
Approval of this part. Part 2 builds the change packs: data-change plans and migration classification, contract diff and consumer tests, shared-component versioning and the consumer matrix, external dependencies, and pinning.
