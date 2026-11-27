# Install

Needs: Spec Kit 1.4.3 (`specify --version`), Python 3.10 or later with PyYAML (3.11 or later if agents use a Codex `.codex/config.toml`), git. For real approvals: a GitHub repository and the `gh` CLI.

## Before you start
A project needs three things first. They are yours to do; the install does none of them.

```bash
uv tool install specify-cli==1.4.3              # Spec Kit, at the release this kit is pinned to
specify init my-project --integration claude    # or copilot; this makes the .specify/ folder
cd my-project && git init -b main               # `specify init` on its own leaves a folder that is not a git repository
```

- Without the version, `uv tool install specify-cli` installs upstream's newest release. On 2026-11-25 that was 1.4.5. The install runs on it, and `doctor` then fails `CK-UPSTREAM-PIN`. Beyond the install and the self-test, the kit has not been tried on 1.4.5.
- The kit's commands are run as `python .specify/extensions/agentic/scripts/agentic.py`. So `python` has to exist, with PyYAML, wherever you or your coding agent run them. The virtual environment from the README's "Try it" will do, or any other. Debian and Ubuntu refuse `pip install` into the system's own Python.
- `specify init --integration claude` looks for the Claude Code program, and stops with "Agent Detection Error" where it is not installed. Install Claude Code first, or add `--ignore-agent-tools` and install it later. With `--integration copilot` it asked for no program when that was tried, on Linux, on 2026-11-26.
- The first line was run on Linux on 2026-11-25. On Windows, what sections 1 to 3 below describe runs in the kit's own pipeline since 2026-11-26, through both install scripts and with the Lite profile, on a runner hosted by GitHub with Spec Kit installed by `pip`. No person is on record as having followed this document on a Windows machine of their own.

## 1. Install into a Spec Kit project
```bash
# from the root of a project already set up with `specify init`
bash path/to/agentic-spec-kit/scripts/install.sh . standard     # or lite, or: regulated hipaa
```
```powershell
path\to\agentic-spec-kit\scripts\install.ps1 -Project . -Profile standard      # add -Pack hipaa for regulated
```
Call the script through `bash`, as written. The PowerShell script first ran on 2026-11-26, on a Windows runner in the kit's own pipeline, and only with the Lite profile: with `standard`, with `regulated` and with `-Pack` it has never been run. The script runs ordinary `specify` commands: the `agentic` extension, an optional domain pack, the `agentic-team` extension, the profile preset, the `agentic-gate` step and three workflows (`agentic-sdd`, `agentic-sdd-team`, `agentic-sdd-sequential`).

For Standard and Regulated the script also installs `agentic-system` (the system map and impact analysis), `agentic-quality` (quality packs), `agentic-product` (intake, living specs, duplicates) and `agentic-connect` (trackers, pipelines, notifications). Lite installs none of the four. After installing, draft the map with `agentic.py map discover --write`, give every node an owner, tier and classification, and save it as `system-map/map.yml`. Until that file exists the map checks report "not run".

With a coding agent, the skill `agentic-spec-kit-install` in this repository's `.claude/skills/` does this section and the next two with you. Claude Code and GitHub Copilot both read that folder.

**Before you commit `.specify/`**, look at three things the install leaves there. Seen on 2026-11-26, when the kit was installed into a repository with a pipeline for the first time.

- Python compiles the kit's code where it runs, into `__pycache__` folders. Since 2026-11-27 the install scripts write `.specify/extensions/.gitignore`, which keeps those under `.specify/extensions/` out of git. An ignore file that is already there is left alone. The `agentic-gate` step under `.specify/workflows/steps/` is compiled too, and nothing ignores that folder: Spec Kit's own `.specify/.gitignore` does not, and `specify init --here --force` writes that file again over what you added.
- Spec Kit leaves two empty lock files, `.specify/.step-install.lock` and `.specify/.workflow-install.lock`. They belong to the machine and not to the repository.
- Spec Kit writes the folder each workflow was installed from into `.specify/workflows/workflow-registry.json`, and the install script installs from a folder of yours. So that file holds a path of the machine that ran the install. In a public repository, change the path or leave the file out.

**A repository that Spec Kit never set up.** The script asks only whether `.specify/` exists. Where `specify init` has never run, it still copies the kit's code, and the kit's checks run from there, which is enough for a pipeline. No coding agent gets the kit's commands, and `CK-UPSTREAM-PIN` cannot run, because the file that names the Spec Kit version is written by `specify init`. Since 2026-11-27 the script ends with a note that says so.

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

To see a gate decided before you decide one: `python .specify/extensions/agentic/scripts/agentic.py demo`. It works in a throwaway project of its own, where a file plays GitHub, and writes nothing into yours.

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
| Write the reviewer's page | `agentic.py brief --spec <id> --gate G3 --write` |
| Commit and push the evidence, the brief included, and open a pull request | (git and GitHub) |
| See what a gate needs and the line to paste | `agentic.py gate --spec <id> --gate G3` |
| A human submits the review in the pull request, with that line on a line of its own | (in GitHub, not by an agent) |
| Mirror the review into a decision record | `agentic.py record --spec <id> --gate G3 --change pull/<n>` |
| Build the trace manifest | `agentic.py trace --write` |
| Run the whole lifecycle with gates | `specify workflow run agentic-sdd -i spec="..."` |

Keep that order. The line that `gate` prints is a hash of the evidence files as they are on disk, the brief among them. A reviewer sees only what was pushed. A decision record that names a commit without the brief fails `CK-GATE-RECORD`. `gate` lists the evidence files that are not committed yet.

`record --change` reads the pull request's reviews and takes the decision, the commit, the reviewer and the role from the review that carries the line. It writes nothing when no review carries it. The long form still exists: `--decision approve --commit <sha> --approval <user>:<role>:pull/<n>#review-<id>`.

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
| One change, whole: origin, gates, versions, tasks, branches and pull requests, and what is open | `agentic.py changeset --spec <id>` |
| One line for each change | `agentic.py report changesets` |
| What was decided inside a change, and what is still open | `agentic.py decision list --spec <id>` |
| What is recorded of the conversation behind a change | `agentic.py product conversation --spec <id>` |
| Where a text is in the code, by component | `agentic.py search "<text>" --spec <id>` |

What each role does with these is in `docs/guide/roles.md`. What the kit does not do is in `docs/limits.md`.

The last five were added on 2026-11-26 and are in the README under "One change, seen whole". A coding agent can ask for most of this through MCP as well: the optional extension `extensions/agentic-mcp` is a read-only server, and its README says how a person adds it.

**If you are the only person.** GitHub does not let the author of a pull request approve it, so with one account you cannot pass a gate on a pull request you opened. `agentic.py init --profile <profile> --open-pr-workflow` also writes `.github/workflows/agentic-open-pull-request.yml`, which opens the pull request as the workflow's own account, so that you may review it. Read the header of that file first. It needs the repository setting "Allow GitHub Actions to create and approve pull requests", and that setting also lets a workflow approve a pull request. The kit's gate never counts such an approval; a branch rule that only counts approvals may. `gates.single_approver_exception` has to be `allowed`, and each record then says that the exception was used. As of 2026-11-26 this workflow has not run on GitHub.

## Lite in one page
Lite needs three gates (G1 spec, G3 plan, G5 implementation), one approver each, and requirements linked to tasks. You edit two files: `roles.yml` and CODEOWNERS. The constitution map, the trace manifest, domain packs, drift detection and the evidence-hash line are not required.
