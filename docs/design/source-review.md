# Source review of the three design references

- **Phase and date:** Phase 2 (design), 2026-11-21
- **Requirement IDs covered:** ADP-2
- **Assumptions:** the default branch head of each repo on 2026-11-21 is representative
- **Unverified:** no code from these projects was executed. I read the files listed; I did not read every file in any of the three. None is proposed as a hard dependency, so this is a design review, not a dependency audit.

Charter D7 applies: learn from these, optionally integrate, copy no code without attribution. No code has been copied.

## 1. spec-kit-ado
- **Repo and commit:** `praveenlavu/spec-kit-ado` at `75f9a84`, 2026-11-16. MIT.
- **Read:** `rules/hitl.md`, `rules/roles.md`, `extension.yml`, and in `src/ado/`: `approvals.py` (header, `excluded`, `guard`, `gate_hash`), `config.py` (`trusted`), `doctor.py` (approver rows).
- **Size:** about 13,700 lines of Python in 30 modules; 94 test files by path.

### What it does that matters here
| Mechanism | Where | Adopted as |
|---|---|---|
| Approver and role lists are read only from the target branch, never from the working tree or the pull request | `config.py` `trusted()`; `rules/hitl.md` | Rule 1 of "What counts as an approval": `roles.yml` read from the base branch |
| Identities that can never approve: the agent's token identity, the kit's own posting identities, the CI identity | `approvals.py` `excluded()` | Rule 2; `CK-APPROVER` |
| A comment is rejected if it was edited, posted on someone's behalf, or by a non-approver | `approvals.py` `guard()` | Dismissed, stale or wrong-commit reviews are rejected |
| An approval names a hash over the gate id, the story id and the exact bytes approved | `approvals.py` `gate_hash()` | Evidence hash in the review line and the decision record (proposed TRC-18) |
| Setup check fails when the agent's token is an approver or can bypass rules | `doctor.py`; `approvals.py` `bypass_bit()` | `CK-ENFORCE-SETUP`, `CK-CRED` |
| Human-only actions refuse to run without a terminal | `rules/hitl.md` | Not adopted. A terminal check is weaker than an identity check in a separate channel |
| States plainly that identity binding protects only while the agent cannot use an approver's credentials | `doctor.py` `ONE_HUMAN` | Stated in the architecture as the limit of the single-human case (charter D3) |

### Not adopted
- Its twelve workflow gates and the story-centred ledger are specific to Azure DevOps work items.
- Comment parsing with a command grammar. On GitHub a pull request review is a stronger primitive than a comment, so the kit uses review state plus one hash line.

### Verdict
Design reference. The enforcement adapter interface is shaped so an Azure DevOps adapter could reuse this project's approach, and could later wrap this project if its author agrees.

## 2. spec-gates
- **Repo and commit:** `schwichtgit/spec-gates` at `179e78e`, 2026-11-20. MIT.
- **Read:** `README.md`, `docs/how-it-works.md` (sections on boundaries and protected changes), `extension/extension.yml`, `extension/runtime/policy.schema.json`, `extension/constitution/manifest.yml`, the listing of `extension/runtime/`.
- **Size:** about 19,000 lines of shell and JavaScript; 19 test files by path.

### What it does that matters here
| Mechanism | Adopted as |
|---|---|
| One policy file; the same verify script runs at the agent, git and CI boundaries; a test asserts the boundaries agree | Section 3 of the architecture: one CLI entry point, three boundaries, CI authoritative |
| Policy is read from the staged copy and `HEAD`, not the working tree, so an unstaged edit cannot relax it | `kit.yml` and `roles.yml` are read from the base branch in CI |
| A change to a protected file needs `Protected-Change` and `Approved-By` commit trailers, and its docs call the trailer "an auditable declaration, not a credential" | Confirms the kit's choice: declarations are mirrored records; the credential is the review |
| The CI check re-examines every commit in the range | `CK-PATH-DIFF` and `CK-TOUCH` examine the whole pull request range |
| Constitution fragments carry machine-readable front matter | Informs `constitution.map.yml` |
| A slow gate may be skipped at the agent or git boundary but never in CI, and the report names what was skipped | The `not-run` rule in `checks.md` |

### Not adopted
- Conventional-commit and branding rules, auto-format hooks, and its starter constitution corpus. These are code-quality policy, outside this kit's scope.

### Compatibility
Its manifest requires Spec Kit `>=0.12.0` and its README says it was verified against v0.12.4. Whether it works on v1.4.3 is untested.

### Verdict
Optional integration. A project may run `spec-gates` for quality gates alongside this kit. Phase 3a should test the two installed together on v1.4.3 before the README recommends it.

## 3. specassay
- **Repo and commit:** `rdryfoos/specassay` at `fc89564`, 2026-10-11. MIT.
- **Read:** `README.md`, `PROMOTION-CONTRACT.md` (rules 1 to 12), `bundle.yml` and the extension manifest.
- **Size:** about 5,400 lines of code; 35 test files by path.

### What it does that matters here
| Rule in its contract | Adopted as |
|---|---|
| Mint IDs at intent; never renumber or reuse | Section 5 of the architecture |
| Tasks declare what they carry; tests name the acceptance criterion | `Carries:` on tasks; AC id in the test name or annotation |
| The acceptance criterion is the unit of "covered" | `CK-TRACE` fails only on a criterion in state `gap` |
| Named states instead of a false green: proven, tracked debt, backlog, gap | Trace manifest states: proven, tracked-debt, waived, gap |
| "Proven" requires a test that passed in this run, not one that merely exists | Same; `CK-TRACE` consumes test results, not names alone |
| The gate runs in CI because a local gate is only a courtesy | CI is authoritative |
| A portable trace manifest with a top-level gate result | `trace-manifest.json` |
| A self-report is not evidence; a capture method can misreport (for example a pipeline's exit status hiding a failure) | Checks regenerate and compare; the CLI returns its own exit code and is never piped in CI |
| Attribution is not authentication | The reason decision records are mirrors and reviews are the credential |

### Not adopted
- Its registry-in-the-PRD model. Upstream mints requirement IDs in `spec.md`, and the kit keeps that.
- `@covers` marks in source as a requirement. They are optional in the kit; the mandatory links are task and test.

### Verdict
Optional integration and the closest existing design for TRC-1 to TRC-4. The kit extends the chain upward to principles and gates and outward to system-map nodes, which this project does not do.

## 4. Attribution
`NOTICE.md` already lists all three as design references. If Phase 3 adapts any code, the file, source commit and licence are added there in the same change.
