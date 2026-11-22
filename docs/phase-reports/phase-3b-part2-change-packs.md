# Phase 3b, part 2 — Change packs (slice 0.2)

- **Phase and date:** Phase 3b part 2, 2026-11-21
- **Pinned upstream:** github/spec-kit `v1.4.3`; installed and run against that version
- **Requirement IDs implemented:** CHG-1 to CHG-15, CHG-18, ADP-5 to ADP-8, and the contract half of TRC-9. With part 1, all 39 requirements tagged `[0.2]` now have code.
- **Approved inputs:** part 1 approved by the owner on 2026-11-21 with both recommendations: event topics and external services stay hand-entered until Phase 5; a project with no map keeps failing.
- **Assumptions:**
  1. The kit never applies a migration, generates a contract or builds a consumer. CI does, and records the result; the kit checks the record.
  2. "Changed" means different from the base: the base branch on a pull request, the previous commit on a push.
  3. Rules that hold for the whole codebase are carried by the adoption baseline when an existing codebase does not meet them yet. This stretches GOV-21 beyond suppressions; see decision 2.
- **Unverified:** see section 6

## 1. What was built

| Unit | Path |
|---|---|
| 17 change-pack checks | `extensions/agentic-system/scripts/agentic_kit_system/checks_change.py` |
| Engine adapters: PostgreSQL (SQL and EF Core migrations), Qdrant | `.../agentic_kit_system/engines.py` |
| Contract adapters: OpenAPI 3 / Swagger 2, GraphQL; semantic-version rules | `.../agentic_kit_system/contracts.py` |
| Commands `change plan`, `change classify`, `change check`, `contract diff`, `run contract`, `run build`, `run migration` | `.../agentic_kit_system/__init__.py` |
| Agent command `speckit.agentic-system.change` | `extensions/agentic-system/commands/change.md` |
| Guides (ADP-7, ADP-8) | `docs/adapters/engine.md`, `docs/adapters/contract-format.md` |
| Schemas for the new files and map fields | `docs/design/schemas.md` |
| Fixture extended: external service, contract test, shared store, lockfile | `fixtures/multi-app/` |
| Tests | `tests/test_change.py` (61 tests) |

About 1,600 lines of code in the three new modules.

### Checks added

| Check | Fails when |
|---|---|
| `CK-DATA-PLAN` | A spec touches a data store with no plan, a missing or empty section, or a reader or writer from the map left unnamed |
| `CK-DATA-CLASS` | A migration is riskier than the plan declares; a breaking change has no expand-migrate-contract section; a destructive one has no restore proof or was approved at G3 without the Data Owner; a changed migration is not listed |
| `CK-MIGRATION-ENGINE` | Written migrations have no CI run, the run was on another engine or major version, a migration changed after the run, or a migration carries another engine's types |
| `CK-MIGRATION-DRIFT` | The run reports model changes with no migration, or the ORM's pending-changes warning is ignored in code |
| `CK-SHARED-STORE` | A store has two or more writers and is not flagged shared with each writer named |
| `CK-SYNTH-DATA` | Seed or test data matches a personal-data pattern. The finding names the file, line and pattern; it never prints the value |
| `CK-CONTRACT-VERSION` | A contract has no version, or changed and kept its version |
| `CK-CONTRACT-BREAK` | A contract has a breaking change that no spec declares under `breaking:` |
| `CK-CONTRACT-CONSUMER` | A consumer has no contract test, or the test did not run against the changed contract |
| `CK-DEPRECATION` | A deprecated element has no removal date or no migration path |
| `CK-CONTRACT-DRIFT` | The committed contract and the copy generated from code offer different operations |
| `CK-SHARED-SEMVER` | A shared component changed with no version change, no stated kind of change, or a change smaller than the kind needs |
| `CK-CONSUMER-MATRIX` | A consumer of a changed shared component was not built and tested against it |
| `CK-EXTERNAL-DEP` | An external dependency record is incomplete, or protected data is exchanged with no agreement status |
| `CK-SBOM` | A release has no CycloneDX bill of materials, no licence policy, a denied licence, or components with no licence |
| `CK-PIN` | An action is not pinned to a commit, an image has no tag or a floating one, a package is requested as `*` or `latest`, or a manifest has no lockfile. Regulated also requires image digests |
| `CK-ROLLOUT` | A spec touching several deployable nodes states no deploy and rollback order, or the order contradicts the map |

### Three design points worth knowing

1. **Evidence is bound to content.** A run record stores a hash of the contract file, the component's files or the migration files. Edit the file after the run and the record stops counting. This is the same idea as the gate evidence hash (TRC-18).
2. **Settings come from the base.** The licence policy, profile and data-scan settings in `kit.yml` are read from the base branch, so a pull request cannot relax them for itself. The tests confirm an uncommitted edit changes nothing.
3. **"Not run" is not "passed".** A changed contract in a format with no adapter, or a missing generated copy, reports "not run", which fails the run.

## 2. Verification

| What | Result |
|---|---|
| Self-tests | 46 checks, each passing on the sample project and failing on its broken variant |
| Unit tests | 112 pass: 36 core, 15 system map, 61 change packs |
| Change-pack tests against a real git base | The 61 tests copy the fixture into a throwaway repository and compare the working tree with its last commit, as CI compares a pull request with its base |
| Multi-app fixture | All 17 change checks pass on the fixture as committed |
| Real install | Fresh Standard project through `scripts/install.sh` on spec-kit 1.4.3: three agent commands registered, self-test passes, and `CK-PIN` passes on the kit's own CI workflow |
| Owner's machine | In the Linux shell on the owner's machine (Python 3.10.12): self-test passes with 46 fixtures, and all 112 unit tests pass. pytest is not installed there, so the tests ran through a small stand-in for it kept outside the repository |

`CK-TOUCH` from part 1 is now also exercised against a real git diff, closing one item from part 1's unverified list.

### Read-only run against the healthcare repository

Run on an exported copy of commit `6e0879d`; the clone was not modified. No kit files were added to that repository.

| Finding | Result |
|---|---|
| EF Core migrations classified | 26 of 26, with no unrecognised operation: 20 additive, 3 backward-compatible, 3 breaking (two column alterations, one column rename) |
| Migrations with SQLite column types | 11 migration files. Phase 1 reported 24; that count included 13 designer and snapshot files, which the kit skips |
| Pending-model-changes warning ignored | 1 place: `src/HealthQCopilot.Infrastructure/Persistence/DatabaseExtensions.cs` |
| Unpinned references | 200 actions not pinned to a commit; 11 images with no tag or `latest` (10 in `infra/argocd/rollouts.yaml`); 23 images with a tag and no digest |
| Seed and test data files scanned | 0. The default patterns look for data files (`.json`, `.csv`, `.sql` and similar) in seed and fixture folders, and the repository has none there. Data seeded from C# code is not scanned |

These are inputs to the Phase 5 backlog. They would be carried by one adoption baseline, not fixed in one step.

## 3. Changes to slice 0.1 code

Part 2 needed three changes in the core, all covered by the existing 36 core tests:

1. `CK-WAIVER` was split into two functions so a sibling extension can report its own rules against the same waivers and baseline. Its behaviour is unchanged.
2. A new hook, `FINDER_HOOKS`, lets an extension add findings that waivers and the baseline can cover. The scan result is now computed once per run, not once per check.
3. The CI workflow template now pins `actions/checkout` to `11d5960` (v4.4.0) and `actions/setup-python` to `a26af69` (v5.6.0), read from the tags on GitHub today. Without this the kit's own workflow would fail the kit's own `CK-PIN`. The push job now compares with the previous commit, so contract and version changes are seen on the default branch too. The workflow has still never run on GitHub.

## 4. Deviations and limits

1. **gRPC and AsyncAPI have no adapter.** ADP-8 asks for them where the reference system or the fixture uses them; neither does.
2. **CHG-18's second sentence is not built.** "The G7 bundle shows the order is safe" needs the release bundle from slice 0.4. The order rule itself is enforced now.
3. **CHG-12 is met by part 1, slightly more strictly.** Platform and the owner of every direct consumer must approve, not only consumers whose build or tests change.
4. **Qdrant changes are mostly declared, not detected.** The plan states the change kind; the adapter detects only `delete_collection` and `recreate_collection` calls.
5. **Contract comparison is a conservative subset.** What each adapter reports and misses is tabled in `docs/adapters/contract-format.md`.
6. **Unrecognised migration statements are shown, not classified.** They appear as "check by hand" notes and do not fail the check.

## 5. Open risks

1. **A run record is a declaration, not proof.** Anything that can write to `specs/<spec>/evidence/` can write a passing record. The agent command forbids it, and the files are covered by the G5 evidence hash, but nothing ties a record to a CI identity until attestation arrives in slice 0.4. Until then, put `specs/*/evidence/` under code owners.
2. **Domain pack files are read from the pull request, not the base.** This dates from slice 0.1. A change could weaken a pack (drop a required section or the agreement rule) in the same pull request that benefits. Code owners on `.specify/` cover it today; see decision 3.
3. **A fresh Standard project reports 22 checks as "not run"** until it has a map. That is the approved behaviour, and it is noisy.

## 6. Unverified

- Everything from slices 0.1 and part 1 still applies: no live GitHub, no CI run, no Windows or PowerShell run, no coding agent in the loop.
- No migration was applied to any database. The PostgreSQL adapter was tested on SQL text and on the healthcare repository's migration files only.
- No real bill of materials was read; the tests use small hand-written CycloneDX files.
- The contract adapters were tested on the fixture's contract and on written examples, not on a large real API.
- The healthcare repository's API contract was not compared; its file is not yet a node in a kit map.
- The pinned action commits were read from GitHub's tag list; the workflow was not run with them.

## 7. Decisions for the owner

1. **Approve part 2**, or say what to change. Approval completes slice 0.2 and Phase 3b.
2. **Baseline scope.** I recommend accepting that the adoption baseline also carries the standing rules listed in `docs/design/checks.md` (unpinned references, unversioned contracts and components, untested consumers, incomplete dependency records, foreign-engine migrations), and widening GOV-21's wording from "existing suppressions" to "existing suppressions and unmet standing rules". The alternative is to make those rules hard failures, which blocks adoption on the healthcare repository until about 250 items are fixed.
3. **Read domain packs from the base branch.** I recommend yes: a small change in the core, in line with how `kit.yml` and `roles.yml` are already read. The alternative is to rely on code owners.
4. **Next step.** Phase 3c builds slice 0.3, the agent team. The live GitHub test of slices 0.1 and 0.2 is still open and can run before or after it; I recommend before, because slice 0.3 adds a third extension on top of an enforcement path that has never run for real.
