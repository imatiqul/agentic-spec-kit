# Windows: a job that finds out, and the newcomer's walk as a test

- **Phase and date:** Phase 11 (adoption), proposal 6, first half; 2026-11-26
- **Requirement IDs covered:** WIN-1 to WIN-6, new with this document
- **Assumptions:**
  1. The owner's "continue" of 2026-11-26 is the go-ahead to build this half of the proposal as `docs/phase-reports/phase-11-adoption-barriers.md` describes it.
  2. A Windows runner hosted by GitHub stands for "Windows" until a person has run the same on a machine of their own.
- **Unverified:** everything here about Windows. No part of this has run there; the job is how that gets found out. The walk test ran on Linux.
- **Since then:** the job failed on its first run and passed on its second, both on 2026-11-26 (`docs/design/windows-first-run.md`). AC-003 is met, and WIN-6 was carried out the same day: the job moved into `tests.yml`, and `windows.yml` is gone. It is a job of its own there, not a row of the matrix as WIN-6 words it, because it installs Spec Kit and runs the demo, which the Linux jobs do not.

## Why

`docs/limits.md` says under "Never run": the install on Windows, by either script, and any command in PowerShell. Finding 10 of the report above says the same. Many teams work on Windows, and so does the owner.

## What it does

| ID | Requirement |
|---|---|
| WIN-1 | A test, `tests/test_install_walk.py`, does the install as a newcomer does it, with the real Spec Kit: `specify init`, the install script, `init`, `team init`, one person in `roles.yml`, `doctor`, `check`, `selftest`, and one spec taken to an open gate. |
| WIN-2 | The test uses the install script of the system it runs on: `install.ps1` through PowerShell on Windows, `install.sh` through bash elsewhere. Where the other shell exists as well, it tries that script too. |
| WIN-3 | The test is skipped, and says why, where `specify` is not installed. It reaches no network: the `gh` program is given no sign-in. |
| WIN-4 | A workflow, `.github/workflows/windows.yml`, runs on a Windows runner hosted by GitHub: the unit tests with the walk among them, the self-test, the golden tasks and the demo. Every step runs even when an earlier one failed, and one failed step fails the job. |
| WIN-5 | The workflow does not run on the default branch until it has passed once. It runs on every other branch that is pushed, and by hand. It has no secret and no write permission, and its actions are pinned to commits. |
| WIN-6 | When the job has passed, Windows joins the matrix of `tests.yml`, this workflow goes, and "Never run" is brought up to date. Until then no document says that the kit works on Windows. |

## How we will know

- **AC-001** (verifies WIN-1, WIN-2): Given Linux with Spec Kit 1.4.3, When the walk test runs, Then it passes with `install.sh`.
- **AC-002** (verifies WIN-3): Given a system with no `specify` program, When the tests run, Then the walk's tests are reported as skipped, with the reason.
- **AC-003** (verifies WIN-4, WIN-5): Given a pushed branch that holds the workflow, When GitHub runs it, Then there is one run on Windows, and `docs/limits.md` records its result, whatever it is.

AC-003 needs a push, which is the owner's. It is not met until he has made one.

## What it will not do

- Fix anything on Windows. Fixes come after the first run, from what it shows.
- Stand in for a person's own machine. One run by hand in PowerShell is still asked for.

## Decisions made here that are the owner's to change

1. The job stays off the default branch until it has passed once, so that a first failure does not turn `main` red.
2. Windows gets one Python version at first, 3.12.
3. The walk test runs wherever `specify` is installed. That includes the owner's machine, where a local test run will now install the kit into a temporary project.
4. The job takes Spec Kit from PyPI at the pinned release, `specify-cli==1.4.3`.
