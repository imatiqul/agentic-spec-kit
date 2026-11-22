# Phase 3a — Slice 0.1 (Govern)

- **Phase and date:** Phase 3a, 2026-11-21
- **Pinned upstream:** github/spec-kit `v1.4.3`; everything below was installed and run against that version
- **Requirement IDs implemented:** the 34 requirements tagged `[0.1]` (GOV-1 to GOV-9, GOV-11, GOV-13 to GOV-16, GOV-21, TRC-1, TRC-3 to TRC-5, TRC-7, TRC-8, TRC-10, TRC-11, TRC-14, TRC-17, TRC-18, QLT-1, QLT-2, QLT-12, ADP-1 to ADP-3, ADP-14, ADP-15)
- **Assumptions:** Python 3.10 or later and PyYAML are available where the kit runs
- **Unverified:** see section 6. The most important: nothing has run against a live GitHub repository, on Windows, or with a coding agent driving it.

## 1. What was built
| Unit | Path | Installed on real Spec Kit 1.4.3 |
|---|---|---|
| Core extension, 8 commands | `extensions/agentic/` | Yes, `specify extension add --dev` |
| Check CLI, 18 checks, about 1,850 lines of Python | `extensions/agentic/scripts/agentic_kit/` | Runs from the installed location |
| Gate step | `steps/agentic-gate/` | Yes, and exercised through the workflow engine |
| Lifecycle workflow | `workflows/agentic-sdd/` | Installs; only a one-gate test workflow was run |
| Profile presets ×3 | `presets/` | Lite and Regulated installed; the wrapped spec template renders correctly |
| HIPAA domain pack | `extensions/agentic-hipaa/` | Yes |
| Bundles ×3 | `bundles/` | Manifests only; see section 5 |
| Install scripts | `scripts/install.sh`, `install.ps1` | The bash script was run on a fresh project; the PowerShell one was not |
| CI workflow | `extensions/agentic/ci/agentic-checks.yml` | Not run |
| Guides | `docs/install.md`, `docs/admin-setup.md` | — |

## 2. Evidence
Commands to reproduce, from the repo root:
```bash
pip install pyyaml pytest
python extensions/agentic/scripts/agentic.py selftest
python -m pytest tests -q
```
- **Self-tests:** 18 checks, each run against a valid sample project (all pass) and against the same project with one thing broken (all 18 fail as intended).
- **Unit tests:** 36 pass.
- **Real install:** two scratch projects created with `specify init`, one Regulated with the HIPAA pack and one Lite through `scripts/install.sh`. On the Lite project, after listing one person and adding CODEOWNERS, `check` reports 17 passed, 0 failed.

### The gate cannot be passed without a valid human approval
Run through upstream's real workflow engine with a one-step workflow using `agentic-gate`:

| Attempt | Result |
|---|---|
| Resume with `--input verdict=approve`, the bypass that works on upstream's built-in gate | Stays paused |
| Write a decision record with no review behind it | Stays paused |
| A review exists but was written by the agent's own account | Stays paused |
| A listed human approves the exact evidence | Completes |
| The spec changes after approval, new run | Paused again: the approval was for different evidence |

The reviews in this test came from the file adapter, which simulates the enforcement channel. It shows the logic is right, not that GitHub enforces it.

## 3. Problems found by testing, and fixed
| Found by | Problem | Fix |
|---|---|---|
| Unit test | An all-digit commit SHA is read by YAML as a number; `0000000` was treated as "no commit" | Commit values are always read as text; a test covers it |
| Unit test | A baseline group whose suppressions had all been removed was never reported as lowerable | Groups are now iterated as well as live suppressions |
| Real install | `CK-WAIVER` flagged the kit's own installed code under `.specify/` | Installed tooling and dependencies are excluded by default; configurable |
| Real install | A fresh project failed `CK-METRIC-SOURCE` because the audit log did not exist yet | `init` writes the first audit entry |
| Real install | `CK-ROLES` printed one line per gate per missing role | One line per role, listing its gates |
| Gate test | My first run used a made-up commit; the gate correctly refused it | Test corrected. The refusal was the right behaviour |

## 4. Slice 0.1 acceptance (from `90-acceptance.md`)
| Criterion | Result | Evidence |
|---|---|---|
| A new engineer installs the kit on the pinned release from the README alone | Partly met | README points to `docs/install.md`; the bash script worked on a fresh project. Not tried by a person other than the author, and not on Windows |
| Lite is adopted in under an hour without reading Standard or Regulated material | Not measured | Lite needs one script, one `init`, and edits to two files; `docs/install.md` has a one-page Lite section. No one has timed it |
| Every gate shows its accountable role and approver | Met | `agentic.py gate` prints the roles; decision records name reviewer and role |
| A decision by an agent, by the author, or with no matching review is rejected | Met with the file adapter | Tests `test_agent_identity_cannot_approve`, `test_single_approver_exception_must_be_recorded`, `test_missing_review_is_reported`; the gate run above |
| Every principle in a sample constitution is machine-checked or human-judged | Met | `CK-CONSTITUTION` and its failing fixture |
| An unrecorded suppression fails; an expired waiver fails | Met | `CK-WAIVER` fixture; `test_expired_waiver_fails` |
| A missing or orphaned trace link fails | Met | `CK-TRACE` fixture; `test_orphans_are_reported` |
| An edited audit log entry is detected | Met | `CK-AUDIT-CHAIN` fixture; `test_deleted_audit_entry_is_detected` |
| Every check has a passing and a failing fixture, and CI shows the failing one fail | Met locally; CI not run | `selftest` output; `CK-SELFTEST` fails when a check has no fixture |
| The documentation lists what is not enforced | Met | `docs/admin-setup.md` |

## 5. Deviations from the Phase 2 design
1. **Fixtures are built in code**, not stored as `fixtures/<check>/pass` and `fail` folders. One valid sample project is generated and each failing fixture is that project with one mutation. This keeps about 36 near-identical folders out of the repo and guarantees the passing and failing cases differ in exactly one thing. `agentic.py selftest` shows each one.
2. **Bundles cannot be installed yet.** Spec Kit 1.4.3 resolves bundle components only through catalogs. `specify bundle validate` accepts the manifests' shape and reports the references as unresolved. The install scripts do what the bundles would. Publishing a catalog needs release archives at stable URLs, which waits on the repo going public (charter D2).
3. **`CK-ENFORCE-SETUP` does not inspect token permissions.** It compares the agent token's account with `roles.yml`. Checking what the token may do was moved to `CK-CRED` in slice 0.3, where it was already planned.
4. **No runtime-event hook yet.** The design allowed checks to run as an agent runtime event. Slice 0.1 ships hooks only (advisory) and relies on CI and the gate step. Events are better added with the agent team in 0.3.
5. **"A gate was passed without a record" is detected by artifact, not by history.** If `plan.md` exists, G1 (and G2) must be approved; if `tasks.md` exists, G3 must be. Code landing without G5 is not detectable until the system map exists (slice 0.2).

## 6. What I did not verify
- **Live GitHub.** The GitHub adapter is tested with recorded responses. No pull request review has been read from GitHub, and no branch protection has been inspected, because this session has no GitHub credentials.
- **CI.** `agentic-checks.yml` has not run on GitHub Actions. Its actions are pinned by tag with a note to pin by commit.
- **Windows.** Everything ran on Linux. The PowerShell install script and the CLI on Windows paths are untested.
- **A coding agent in the loop.** The eight commands are instructions for an agent; none was executed by one. The full `agentic-sdd` workflow was installed but not run end to end, because its other steps invoke an agent.
- **Copilot.** Only the Claude integration was used for `specify init`.
- **Time to adopt Lite**, as noted above.
- **The HIPAA mapping** was written from the Security Rule's technical safeguards as currently in force and has not been reviewed by a compliance professional. A proposed overhaul of the rule was still pending on this date.

## 7. Decisions I need from you
1. Approve slice 0.1, or say what to change.
2. Whether to run it against your real repository before Phase 3b. I recommend yes: turn on branch protection for `agentic-spec-kit`, open one pull request, approve it yourself with the pasted line, and run `check` with your own `gh` login. That is the one thing that turns "logic verified" into "enforcement verified", and it takes about fifteen minutes.
3. Whether fixtures-in-code (deviation 1) is acceptable, or you want folders on disk as designed.

## 8. What Phase 3b needs from you
Approval of this phase. Phase 3b builds slice 0.2: the system map, discovery, impact analysis and the change packs, plus the `fixtures/multi-app/` project.
