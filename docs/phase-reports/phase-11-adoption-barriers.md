# Phase 11, steps 1 and 2: what stands in a new team's way, and what I propose

- **Phase and date:** Phase 11 (adoption), steps 1 and 2 of 3; 2026-11-25
- **Kit and upstream:** agentic-spec-kit `main` at `ec250b5`, in a fresh clone of the public repository. Spec Kit `v1.4.3` (the kit's pin) and `v1.4.5` (the newest upstream tag on this date)
- **Where it ran:** a Linux workspace, Ubuntu 24.04.5, in a new virtual environment made with Ubuntu's own Python 3.12.3 (PyYAML 6.0.4, pytest 9.2.0). No Windows and no macOS
- **Assumptions:**
  1. A new team starts at the README's "Start here" table and does what the documents say, in the order they say it.
  2. Where the documents hand a step to a coding agent, I did that step by hand from the installed command's instructions. No coding agent was run. Claude Code is installed in this workspace and I did not use it.
  3. Running the agents on local models is out of this work. The owner parked it on 2026-11-25.
  4. I call this work Phase 11. The phases document ends at 10; rename it if you prefer.
- **Unverified:** nothing here touched GitHub. No pull request, review, branch protection or pipeline was involved. What this report says about GitHub comes from reading the kit's code and GitHub's documentation, and each such finding is marked **read, not run**. Nothing was tried on Windows.
- **What was changed:** nothing. No file of the kit was edited, and nothing was committed or pushed. The four scratch projects are in the workspace and belong to no repository. One holds a decision record I wrote for a review that does not exist, to see what the kit does with it (finding 6). Another holds a stand-in review file I wrote for one of the sample's invented people (finding 8). Neither is an approval of anything.

Every command and its output is in `phase-11-adoption-walk-transcript.md`, next to this report. A number in square brackets, as in [05], is a section of that transcript.

**Updated the same evening, after the owner asked for the walk in Claude Code and GitHub Copilot as well.** Neither tool can run in my workspace. Claude Code is there as the engine of this session. Started on its own with a new, empty configuration it answers `Not logged in · Please run /login`, and I did not hand this session's own sign-in to a second copy. GitHub Copilot is not installed there, and I have no GitHub sign-in. Both are signed in on the owner's computer, so the runs are his to make. A run sheet with the setup, the prompts and how to save each session went to the owner. No coding agent has run anything yet; what the sessions show will be added here.

Two things I read in the installed files, to watch in those runs. The hook that Spec Kit writes for the kit's path guard calls `python3` before every tool call, and a Windows machine may have only `python`. And the documents write the commands with dots, as in `/speckit.agentic.guide`, while the install puts them on disk as skills with hyphens.

**Updated later that evening, after the owner said to continue.** Proposal 1 was built, as documents and two command files only; `docs/release-notes.md` says what changed. No other proposal was started: 2 and 4 wait for the owner's decisions, and the rest for his word. I had also offered to run the Copilot sessions in VS Code on the owner's screen. That offer was wrong: on his computer I may click in an IDE or a terminal, but not type there.

**Updated once more, early on 2026-11-26.** The owner said to continue again, and proposal 5 was built as well: `agentic.py demo`. Its spec, `docs/design/demo.md`, was committed before its code.

**And once more that night.** After a third "continue" the first half of proposal 6 was built: a test that walks the install with the real Spec Kit, and a workflow that runs the tests on a Windows runner. The workflow has not run. It starts when the owner pushes the branch.

**And after that.** On the owner's "next", two parts of proposal 4 were built, the two that change no rule: `record --change pull/<n>` finds the review itself, and `gate` lists evidence that is not committed. The spec is `docs/design/record-finds-review.md`. One thing differs from proposal 4 as written below: more than one review may carry the line, because a gate outside Lite needs a review for each role. The command refuses when those reviews are on different commits. What the gate board calls a decision nobody could verify, and what Lite does then, still wait for the owner.

**Then the owner merged, and Windows ran.** On 2026-11-26 the owner made the commit from the patch, pushed the branch and merged pull request #1. The push started the first run on Windows, and it failed, which is what the job was for: the self-test and the demo passed, 27 unit tests failed or ended in an error, and the golden tasks failed in parallel mode. There were three causes: Spec Kit looks for the coding agent's program, the evidence hash depended on line ends, and a closed pipe was not recognised in one case. `docs/design/windows-first-run.md` sets them out. The owner said to fix all three. They are changed in the code, and none of the changes has run on Windows. The second one is the one that matters to a team on Windows: as Git for Windows sets git up, no gate would have held.

**And Windows passed.** The owner pushed the branch with the three changes, and the second run of the job passed the same day: 574 unit tests passed and 2 were skipped, with the install walked through `install.ps1` and `install.sh`, and the self-test, the golden tasks and the demo passed. He merged it as pull request #2. The Windows job then moved into the kit's own test workflow, as its spec had said. What has still not happened is a person following the install on a Windows machine of their own.

## The short version

A newcomer on Linux who already has Spec Kit 1.4.3 gets from a fresh clone to an open gate, with its approval line printed, in a few minutes of commands. The path stops there. The first gate decision is a pull-request review on GitHub, and the kit has never read one.

Before that point a newcomer today meets two failures that are not theirs. Ubuntu's own Python refuses the README's first command. And the first `doctor` fails for anyone who installs upstream's newest Spec Kit, which is 1.4.5 as of today.

I propose eight things, ranked. The third, a first real gate on a live repository, matters most and needs you. The first two are small and come first because every newcomer meets them earlier.

## How far the path goes today

| Step | What happened | Time |
|---|---|---|
| Clone | `main` at `ec250b5` [01] | 2 s |
| README, "Try it" | Refused by Ubuntu's own Python [05]. In a virtual environment the self-test passes on 105 fixtures [07] and the tests give 536 passed, 2 skipped [08] | 21 s, then 3 min 45 s |
| The tour, five commands | Each prints what the README and the tour skill say it will [09] to [13] | under a second each |
| A new Spec Kit project, then the Lite install | One script, no error [15] [16] | 1 s, then 3 s |
| `init`, `team init` | Settings, a pipeline file, six agents rendered for three runtimes [17] [18] | under a second each |
| By hand: one person in `roles.yml`, CODEOWNERS, `git init` | `doctor`: 4 passed, 0 failed, 1 not run. `check`: 37 passed, 0 failed, 1 not run. `selftest`: 39 fixtures [21] to [24] | seconds |
| One small spec | The board shows G1 `open`, and `gate` prints the line to paste [25] [27] | under a second |
| The first gate decision | Not reached. It needs a pull request on GitHub and a review by a person | |

The one check that could not run throughout is `CK-CRED`. It asks GitHub about the token in use, and there was no repository behind `owner/name`.

## What a newcomer runs into

### 1. Ubuntu's own Python refuses the README's first command

"Try it" opens with `pip install pyyaml pytest`. Ubuntu 24.04's own Python answers `error: externally-managed-environment` [05]. This workspace keeps a second Python ahead of it on the path, where the same command passes [03], so I saw the refusal only by calling Ubuntu's Python by name.

The tour skill already tells an agent to make a virtual environment where pip refuses, and to use `python3` where `python` is missing. The README and `docs/install.md` say neither [50].

### 2. With upstream's newest Spec Kit, the first `doctor` fails

`docs/install.md` says "Needs: Spec Kit 1.4.3". No document in the repository gives the command that installs Spec Kit, at that version or any other [50]. Upstream has tagged twice since the pin: the commits behind `v1.4.3`, `v1.4.4` and `v1.4.5` are dated 19, 23 and 25 November [14] [51].

On 1.4.5 the install runs clean [38] and leaves the same 21 command folders as on 1.4.3 [48]. `init` then writes `speckit: "1.4.3"` into `kit.yml` whatever is installed, and `doctor` and `check` fail [39] [40]:

```text
FAIL     CK-UPSTREAM-PIN
         CK-UPSTREAM-PIN: Spec Kit 1.4.5 is installed but kit.yml pins 1.4.3 [.specify/init-options.json]
```

Beyond the install, those two commands and the self-test, nothing was tried on 1.4.5.

### 3. Nothing says how to get from an open gate to a pull request

`gate` prints the line and says that a person "submits an approving review containing this line" [27]. The documents do not say how the change gets in front of that person:

- `specify init` leaves a folder that is not a git repository [15], and no document says `git init` [50].
- No document says who opens the pull request, or from which account.
- The README, `docs/install.md`, `docs/admin-setup.md`, the two guides and the three skills never say how to give the coding agent an account of its own. They mention such an account only to say that its reviews are rejected [50].

### 4. An approver who runs `doctor` as themself gets a failure (read, not run on GitHub)

With the GitHub adapter the kit takes "the agent's account" to be whoever owns the token that `gh` is using (`adapters.py`, lines 107 to 111). On a developer's own machine that is the developer. If that developer is listed in `roles.yml`, `CK-ENFORCE-SETUP` fails, and when the checks run on that machine `CK-APPROVER` reports the same person's reviews as "the agent's or CI's own identity" (`checks_gov.py`, lines 241 to 245 and 559 to 568).

I ran the same check with the stand-in adapter, naming an approver as the agent's account [46]:

```text
FAIL     CK-ENFORCE-SETUP
         CK-ENFORCE-SETUP: the agent's own account (pat) is listed in roles.yml, so it could approve its own work [.specify/agentic/roles.yml]
```

The check is right: the kit cannot tell a person at a terminal from an agent holding that person's token. But `docs/install.md` tells a newcomer to list real people and then run `doctor`, and the person most likely to do both is one of those people.

### 5. One person with one account cannot pass a gate on GitHub (read, not run)

The checks accept a review only in the state `APPROVED` (`checks_gov.py`, lines 586 to 595). GitHub's documentation says: "Pull request authors cannot approve their own pull requests." The same page adds that a person cannot approve a pull request Copilot raised on an issue that person assigned to it.

So a developer who opens the pull request can never give the review the kit asks for, and `gates.single_approver_exception: allowed` does not change that. The exception covers a reviewer who is among the authors of the commits (`adapters.py`, lines 139 to 141; `checks_gov.py`, lines 599 to 603). That helps only when another account opened the pull request.

For a team of two or more this is how reviews already work. For the one developer who tries the kit before showing it to a team, it is a wall at the first gate. `doctor` gives no warning of it: with one person holding every role it notes "every approval is a single-approver exception" while `kit.yml` still says `forbidden` [22].

### 6. `record` takes five values by hand, and writes whatever it is given

```text
agentic.py record --spec <id> --gate G1 --decision approve --commit <sha> --approval <user>:<role>:pull/<n>#review-<id>
```

The review's number has to be found by hand. Lite does not install the connect extension, so `connect mirror` is not there to do it.

`record` does not look the review up. I gave it `pull/1#review-1` on a repository that does not exist, and it wrote the record [29] [33]. That is by design: the README calls the record a mirror, and three checks judge it. What follows in a Lite project where GitHub cannot be read is less obvious. The board [35]:

```text
| 001-greeting | approved | no evidence yet | later | solutions-architect |
```

And `check` [34]:

```text
NOT RUN  CK-APPROVER
NOT RUN  CK-CRED
NOT RUN  CK-GATE-MIRROR
35 passed, 0 failed, 3 not run
[exit 0, 2 s]
```

The board defines `approved` as "a recorded decision for the evidence as it stands now", and that is what it shows. A reader takes the word to mean that a person approved. In the project's pipeline `CK-APPROVER` would run and fail. On a machine with no working `gh` login, Lite turns "could not run" into a warning and the command ends with 0.

### 7. `gate` prints a hash for evidence that is not committed

After `brief --write` the brief is an untracked file. `gate` adds it to the evidence and prints a new line [32], with no word that the reviewer cannot see that file yet. A record that names the commit before the brief then fails `CK-GATE-RECORD` with "evidence file specs/001-greeting/briefs/G1.md does not exist" [31]. What works: write the brief, commit and push it, and only then ask for the review. The guide command names the brief and the `gate` command and nothing between them.

### 8. The tour stops before a gate closes

The tour's five commands write nothing, and the last thing they show is the line a person would paste. A newcomer never sees a gate close, or open again when the approved file changes. That is the kit's whole point.

It can be shown today, by hand, with the stand-in adapter in a throwaway copy of the sample: a handful of commands and a hand-written JSON file [41] to [45]. `CK-APPROVER`, `CK-GATE-MIRROR` and `CK-GATE-RECORD` pass, and the board moves G1 to `approved` and G2 to `open`. After one edit to the spec, `gate` says "approve recorded for DIFFERENT evidence (the files changed since)" and the board shows G1 `open` again.

### 9. There is no release, and no install without a clone

The repository has no tag [49]. The install script points Spec Kit at folders inside a clone (`--dev`), so a project depends on wherever that clone sits. `docs/install.md` says the bundles cannot be installed, because the kit has published no catalog. The command line calls itself 0.1.0, and the two extensions Lite installs call themselves 0.1.0 and 0.3.0 [49]. No document says how to move a project to a newer kit [50]. Spec Kit 1.4.3 can install an extension from a URL (`specify extension add --from`) or by name from a catalog. Neither was tried.

### 10. Nothing has been run on Windows

`docs/limits.md` already says so: neither install script has run there, and `scripts/install.ps1` has never run anywhere. This workspace has no PowerShell, so I read that script and did not run it.

### 11. Two small things

- In a Lite project with nobody listed, `doctor` asks for people at G0 as well as at G1, G3 and G5 [19]. The README says Lite has three gates, and the board shows three [25].
- "Try it" runs the kit's own 538 tests, 3 minutes 45 seconds, before the newcomer has seen the kit do anything [08]. The five tour commands need only PyYAML.

### Tried, and found in order

- `doctor` on the sample prints what the README quotes [09].
- The Lite install, on Spec Kit 1.4.3 and on 1.4.5 [16] [38].
- A first pull request that adds the kit to a repository whose default branch does not have it yet, simulated with two branches and no pull request: `check --base-ref main` gives 37 passed, 0 failed, 1 not run [47].
- A gate re-opens when its approved evidence changes [44] [45].

## What `docs/limits.md` already lists

These stand in a new team's way as much as anything above. None was tested here.

- No pull request, review or branch protection on a live GitHub repository has been read. It is the first line under "Never run".
- No coding agent has loaded the rendered agent files. Claude Code and GitHub Copilot have run one of the three skills, the tour, and none of the commands the install adds.
- None of the three pipeline files the kit ships has run in its CI system.
- The shipped pipelines skip `CK-DRIFT-SPEC` in every run, because they pass no list of changed files.
- No tracker, chat or mail adapter has met its live service.
- Approvals in GitLab merge requests and in Azure Repos are not read.
- Work that reaches the default branch without G5 and G6 is reported after the merge, not held back.

## Proposals, ranked

| # | Proposal | Size | Needs you |
|---|---|---|---|
| 1 | A quick start that works as written | Small | No |
| 2 | Spec Kit version: record what is installed, say what was tried | Small to medium | A decision |
| 3 | The first real gate, on a live repository | Medium, with an unknown tail | Yes |
| 4 | `record` finds the review, and the board says what was verified | Medium | A decision |
| 5 | A demo that closes a gate and re-opens it | Small | No |
| 6 | Windows | Unknown until it runs | A push and one run |
| 7 | A release that installs without a clone | Medium | Yes: publishing |
| 8 | The coding agents, on record | Your time; fixes unknown | Yes |

### 1. A quick start that works as written

- **What:** documents only. README "Try it": a virtual environment first, `python3` where `python` is missing, and the five tour commands ahead of the unit tests. `docs/install.md` and the install skill: the command that installs Spec Kit at a version the kit was tried on, `specify init`, `git init`, and the order "write the brief, commit, push, then ask for the review".
- **Who it helps:** everyone, in the first ten minutes.
- **Evidence:** findings 1, 2, 3, 7 and 11.
- **Size:** small. The test that compares command lines in the documents with the CLI covers the new lines.
- **Risks:** the Spec Kit install command names a tool the kit does not own. I would take it from upstream's README and say where it came from.
- **Will not:** change what any command does.

### 2. Spec Kit version: record what is installed, say what was tried

- **What:** `init` writes the installed Spec Kit version as the project's pin. The kit states the versions it has been tried on. `doctor` passes inside that set and says "not tried on this version" outside it. The kit's own pipeline runs the install on upstream's newest release as well as on 1.4.3.
- **Who it helps:** everyone who installs Spec Kit from now on.
- **Evidence:** finding 2. Upstream tagged twice in the six days after `v1.4.3`.
- **Size:** small to medium: `init`, one check with its two fixtures, one pipeline job.
- **Risks:** upstream can change behaviour in a patch release. The pipeline job is what would show it.
- **Will not:** follow upstream on its own, or promise that an untried version works.
- **Your decision:** you approved a single pinned release in Phase 0. Keep one exact version, and proposal 1's install command is the whole fix. Or accept a tried set.

### 3. The first real gate, on a live repository

- **What:** four parts. A guide, "Your first gate on GitHub": which accounts are needed (the people in `roles.yml`, a separate account for the coding agent that opens the pull request, the pipeline's own), the repository settings, and every step from a branch to a merged decision record, for one person and for a team. One real run of that guide on a test repository, with you as the reviewer. Fixes for what the run shows. The transcript in the repository, and "Never run" brought up to date.
- **Who it helps:** every team. Until one gate has closed on GitHub, the kit's central claim rests on recorded responses.
- **Evidence:** the first line of "Never run"; findings 3, 4 and 5.
- **Size:** medium, with an unknown tail. The GitHub adapter has only ever read recorded responses.
- **Risks:** the run may show defects that take longer than the guide. One to look for, read and not run: the decision record is committed after the review. If the repository dismisses approvals when new commits arrive, that review would then read as dismissed, where the checks ask for `APPROVED`.
- **Will not:** read GitLab or Azure Repos, or approve anything for you.
- **Needs from you:** a test repository; a second GitHub account or a GitHub App for the agent, which is yours to create; your review in the browser. I cannot push, and I do not approve.

### 4. `record` finds the review, and the board says what was verified

- **What:** `record --spec <id> --gate G1 --change pull/<n>` reads the pull request, finds the one review that carries the gate line for the evidence as it stands, and fills in the reviewer, the role, the commit and the review's number. It refuses when no review matches, or more than one. `gate` warns when an evidence file is not committed. The board shows a recorded decision whose review could not be read as `recorded, not verified`.
- **Who it helps:** whoever mirrors a review, at every gate, and everyone who reads the board.
- **Evidence:** findings 6 and 7.
- **Size:** medium: one command, two views, fixtures.
- **Risks:** it changes what two commands print, and the board's words are in the README's diagrams and in the tour.
- **Will not:** make `record` approve anything. It stays a mirror.
- **Your decision:** whether Lite should fail, not warn, when a decision record exists and its review could not be read. That changes a rule.

### 5. A demo that closes a gate and re-opens it

- **What:** `agentic.py demo` copies the sample into a temporary folder, plays one approval through the stand-in adapter, shows the board before and after, changes the approved spec and shows the gate open again. Every screen says that the stand-in proves nothing about who approved. The tour skill gets it as a last step.
- **Who it helps:** the developer or manager who gives the kit ten minutes before deciding whether it gets an hour.
- **Evidence:** finding 8.
- **Size:** small. The parts exist: the stand-in adapter and the sample project.
- **Risks:** someone takes the stand-in for the real thing. So it runs only on a temporary copy and refuses a project.
- **Will not:** prove identity, or write into any project.

### 6. Windows

- **What:** a Windows job in the kit's own pipeline: the unit tests, the self-test, the golden tasks, and `install.ps1` on a new project. Fixes for what fails. Then one run by hand in PowerShell on your machine.
- **Who it helps:** every team on Windows.
- **Evidence:** finding 10.
- **Size:** the job is small. What it finds is unknown.
- **Risks:** the first run may fail in many places. That would be the finding.
- **Will not:** say Windows works before the job passes.
- **Needs from you:** a push, so that the pipeline runs, and the one run by hand.

### 7. A release that installs without a clone

- **What:** a tagged pre-alpha release. Each extension, preset, step and workflow as a file Spec Kit can install from a URL, or a catalog so that the bundles install by name. One page on moving a project to a newer kit.
- **Who it helps:** teams that will not tie a project to somebody's working copy, and anyone who asks which version they have.
- **Evidence:** finding 9.
- **Size:** medium. How Spec Kit resolves a catalog has to be tried first.
- **Risks:** a release is public, and it is yours to publish. It needs one version number for the whole kit.
- **Will not:** enter a community catalog.

### 8. The coding agents, on record

- **What:** you run the install skill, the kit's commands in a project, and one stage with the agent team, in Claude Code and in GitHub Copilot, and keep the sessions. I read them and fix what they show.
- **Who it helps:** every team, since each will use one of the two.
- **Evidence:** the second and third lines of "Never run".
- **Size:** your time for the runs. The fixes are unknown.
- **Will not:** build anything new.
- **Where it stands:** on 2026-11-25 I tried Claude Code in my workspace. It is not signed in there, and GitHub Copilot is not installed. The run sheet is for your computer.

### Not proposed now

- Running the agents on local models: parked by you.
- Approvals from GitLab merge requests and Azure Repos: large, and better after one channel has been proven.

## What I need from you

1. The numbers of the proposals to build.
2. For proposal 2: one exact Spec Kit version, or a tried set.
3. For proposal 4: whether Lite fails or warns when a recorded review cannot be read.
4. For proposal 3, when you want it: a test repository and an account for the agent.

Nothing is built until you say which.

## Sources

- GitHub Docs, "Approving a pull request with required reviews", read 2026-11-25: https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/approving-a-pull-request-with-required-reviews
- The tags of `github/spec-kit` and the dates of their commits, read with git on 2026-11-25 [14] [51]
