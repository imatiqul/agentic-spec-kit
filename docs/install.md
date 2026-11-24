# Install

Needs: Spec Kit 1.4.3 (`specify --version`), Python 3.10 or later with PyYAML (3.11 or later if agents use a Codex `.codex/config.toml`), git. For real approvals: a GitHub repository and the `gh` CLI.

## 1. Install into a Spec Kit project
```bash
# from the root of a project already set up with `specify init`
bash path/to/agentic-spec-kit/scripts/install.sh . standard     # or lite, or: regulated hipaa
```
```powershell
path\to\agentic-spec-kit\scripts\install.ps1 -Project . -Profile standard      # add -Pack hipaa for regulated
```
Call the script through `bash`, as written. The PowerShell script has never been run. The script runs ordinary `specify` commands: the `agentic` extension, an optional domain pack, the `agentic-team` extension, the profile preset, the `agentic-gate` step and three workflows (`agentic-sdd`, `agentic-sdd-team`, `agentic-sdd-sequential`).

For Standard and Regulated the script also installs `agentic-system` (the system map and impact analysis), `agentic-quality` (quality packs), `agentic-product` (intake, living specs, duplicates) and `agentic-connect` (trackers, pipelines, notifications). Lite installs none of the four. After installing, draft the map with `agentic.py map discover --write`, give every node an owner, tier and classification, and save it as `system-map/map.yml`. Until that file exists the map checks report "not run".

With a coding agent, the skill `agentic-spec-kit-install` in this repository's `.claude/skills/` does this section and the next two with you. Claude Code and GitHub Copilot both read that folder.

Bundles are in `bundles/` but cannot be installed yet. Spec Kit 1.4.3 resolves a bundle's components only through catalogs, and this kit has not published one.

## 2. Configure
```bash
python .specify/extensions/agentic/scripts/agentic.py init --profile standard --repository owner/name
```
```bash
python .specify/extensions/agentic/scripts/agentic.py team init --runtimes claude,copilot,sequential   # name the runtimes you use
```
`team init` copies the agent specs for your profile into `.specify/agentic/agents/` and renders the runtime files. See `docs/adapters/agent-runtime.md` for what each runtime enforces.

Spec Kit puts the kit's commands where the project's coding agent reads them: `.claude/skills/` for Claude Code, `.github/skills/` for GitHub Copilot. Start with `/speckit.agentic.guide`, which says where a change stands and which command to run next.

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
Exit codes: 0 pass, 1 a check failed, 2 a check could not run. In Lite, "could not run" is a warning. A command whose output is piped into a program that stops reading early, such as `head`, ends with 141.

## 4. Adopting an existing codebase
```bash
python .specify/extensions/agentic/scripts/agentic.py suppressions              # what is suppressed today
python .specify/extensions/agentic/scripts/agentic.py suppressions --baseline   # a draft baseline to review
```
Fill in an owner and expiry for each group, have it approved in a review, and save it as `.specify/agentic/waivers/baseline.yml`. After that each group's count may only go down.

## 5. Working a spec
| Step | Command |
|---|---|
| Find out where a change stands and what comes next | `/speckit.agentic.guide`, in your coding agent |
| See what a gate needs and the line to paste | `agentic.py gate --spec <id> --gate G3` |
| A human submits the review in the pull request, with that line on a line of its own | (in GitHub, not by an agent) |
| Mirror the review into a decision record | `agentic.py record --spec <id> --gate G3 --decision approve --commit <sha> --approval <user>:<role>:pull/<n>#review-<id>` |
| Build the trace manifest | `agentic.py trace --write` |
| Run the whole lifecycle with gates | `specify workflow run agentic-sdd -i spec="..."` |

## 6. Seeing where things stand
| You want | Command |
|---|---|
| Who is needed next, at which gate | `agentic.py report gates` |
| Open exceptions and when they end | `agentic.py report waivers` |
| Requirement to test, per spec | `agentic.py report trace --spec <id>` |
| Flow and agent measures, each with its source | `agentic.py report metrics` |
| What agents cost, by spec and gate | `agentic.py report spend` |
| Everything, as files and one page | `agentic.py report all --out reports --html` |
| The reviewer's one page for a gate | `agentic.py brief --spec <id> --gate G3 --write` |
| The evidence pack for a release | `agentic.py audit-pack --spec <id> --write` |
| Why a line of code exists | `agentic.py why <file>:<line>` |

What each role does with these is in `docs/guide/roles.md`. What the kit does not do is in `docs/limits.md`.

## Lite in one page
Lite needs three gates (G1 spec, G3 plan, G5 implementation), one approver each, and requirements linked to tasks. You edit two files: `roles.yml` and CODEOWNERS. The constitution map, the trace manifest, domain packs, drift detection and the evidence-hash line are not required.
