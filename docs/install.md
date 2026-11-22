# Install (slice 0.1)

Needs: Spec Kit 1.4.3 (`specify --version`), Python 3.10 or later with PyYAML, git. For real approvals: a GitHub repository and the `gh` CLI.

## 1. Install into a Spec Kit project
```bash
# from the root of a project already set up with `specify init`
path/to/agentic-spec-kit/scripts/install.sh . standard          # or lite, or: regulated hipaa
```
```powershell
path\to\agentic-spec-kit\scripts\install.ps1 -Project . -Profile standard      # add -Pack hipaa for regulated
```
The script runs five ordinary `specify` commands: the `agentic` extension, an optional domain pack, the profile preset, the `agentic-gate` step and the `agentic-sdd` workflow.

Bundles are in `bundles/` but cannot be installed yet. Spec Kit 1.4.3 resolves a bundle's components only through catalogs, and this kit has not published one.

## 2. Configure
```bash
python .specify/extensions/agentic/scripts/agentic.py init --profile standard --repository owner/name
```
Then, by hand:
1. List real people and their roles in `.specify/agentic/roles.yml`. Use account names from the enforcement channel. Never list an agent or CI account.
2. Add a CODEOWNERS file that covers `.specify/`.
3. For Standard and Regulated, give each principle in your constitution an id (`P-1`, `P-2`, …) and map it in `.specify/agentic/constitution.map.yml`.
4. Follow `docs/admin-setup.md` for the repository settings.

## 3. Check
```bash
python .specify/extensions/agentic/scripts/agentic.py doctor     # can approvals be trusted here?
python .specify/extensions/agentic/scripts/agentic.py check      # every check for the active profile
python .specify/extensions/agentic/scripts/agentic.py selftest   # prove each check fails on a broken fixture
```
Exit codes: 0 pass, 1 a check failed, 2 a check could not run. In Lite, "could not run" is a warning.

## 4. Adopting an existing codebase
```bash
python .specify/extensions/agentic/scripts/agentic.py suppressions              # what is suppressed today
python .specify/extensions/agentic/scripts/agentic.py suppressions --baseline   # a draft baseline to review
```
Fill in an owner and expiry for each group, have it approved in a review, and save it as `.specify/agentic/waivers/baseline.yml`. After that each group's count may only go down.

## 5. Working a spec
| Step | Command |
|---|---|
| See what a gate needs and the line to paste | `agentic.py gate --spec <id> --gate G3` |
| A human submits the review in the pull request | (in GitHub, not by an agent) |
| Mirror the review into a decision record | `agentic.py record --spec <id> --gate G3 --decision approve --commit <sha> --approval <user>:<role>:pull/<n>#review-<id>` |
| Build the trace manifest | `agentic.py trace --write` |
| Run the whole lifecycle with gates | `specify workflow run agentic-sdd -i spec="..."` |

## Lite in one page
Lite needs three gates (G1 spec, G3 plan, G5 implementation), one approver each, and requirements linked to tasks. You edit two files: `roles.yml` and CODEOWNERS. The constitution map, the trace manifest, domain packs, drift detection and the evidence-hash line are not required.
