# What the first Windows run showed, and three fixes

- **Phase and date:** Phase 11 (adoption), proposal 6, second half: fixes for what the first run showed; 2026-11-26
- **Requirement IDs covered:** WIN-7 to WIN-12. They continue the numbering of `docs/design/windows-job.md`
- **Assumptions:**
  1. The owner's "fix those three causes" of 2026-11-26 is the go-ahead for all three, the second among them. He had been told that the second changes how the evidence hash reads a file.
  2. Git on the runner has `core.autocrlf` set to `true`, as Git for Windows sets it when it is installed. The run's log does not print the setting. It is inferred: Linux gives the same sixteen failures with that setting and with Python made to write CRLF, and none of them without.
- **Unverified:** none of these fixes has run on Windows. The next run of the Windows job is what shows whether they hold. Both install scripts are still untried there: the walk stopped before it reached them.
- **Since then:** the second run, 45881901293 on the push of `3f18fec` on 2026-11-26, passed, with the walk through both install scripts. AC-001 and the closed-pipe test of 2026-11-23 are met on a Windows runner hosted by GitHub.

## What the run showed

Run 45873112791 of `.github/workflows/windows.yml`, on the push of `2eb9243`, 2026-11-26: Windows Server 2025, Python 3.12.10, git 2.56.1, Spec Kit 1.4.3.

| Step | Result |
|---|---|
| Unit tests | Failed: 542 passed, 7 failed, 20 errors, 2 skipped, in 12 minutes 45 seconds |
| Self-test | Passed, on 105 fixtures |
| Golden tasks | Failed: all ten lines passed in sequential mode; in parallel mode the four tasks failed at G5 |
| Demo | Passed, and printed the same evidence hash as on Linux |

The 27 come from three causes.

1. **Ten errors: Spec Kit looks for the coding agent's program.** `specify init shop --integration claude` ends with "Agent Detection Error: claude not found" where Claude Code is not installed, and the runner has none. So the walk stopped at its first command, for both install scripts. A newcomer without Claude Code meets the same on any system; Linux with the program taken off the path gives the same error.
2. **Six failures and ten errors: the evidence hash depends on line ends.** Each says "the evidence hash does not match the evidence files at the decision's commit". With `core.autocrlf` on, git keeps LF in a commit and writes CRLF to the working copy, and Python on Windows writes CRLF for text unless told otherwise. So the same file is one byte string on disk and another in the commit. `gate` hashes the first and `CK-GATE-RECORD` the second. On Windows as Git for Windows sets it up, no gate would hold. The same reaches every other place where the kit keeps a hash of a file.
3. **One failure: a reader that has gone.** `agentic.py list` into a closed pipe ended with a traceback. Windows reports the failed write as "invalid argument", and the code took that for a closed pipe only when a flush then failed as well. Here the flush must have passed, since the error was raised again. The likely reason, read from how Python buffers and not seen on Windows: `list` prints about 17,000 bytes, a write larger than the buffer goes straight to the pipe, and what fails that way leaves nothing behind to flush.

## What will change

| ID | Requirement |
|---|---|
| WIN-7 | The walk test tells Spec Kit not to look for the coding agent's program (`--ignore-agent-tools`). It tests the kit's install, not whether Claude Code is installed. `docs/install.md` says what `specify init` does when that program is missing. On Windows the walk runs `install.sh` with the bash that comes with Git, where it finds one: `bash` on the path there can be the launcher of the Linux subsystem. Whether that matters is not known; no run has got that far. |
| WIN-8 | A file of the repository reads the same whatever its line ends: wherever the kit hashes or compares one, CRLF counts as LF. A file that git takes for binary, one with a NUL byte in its first 8000 bytes, is read as it is. |
| WIN-9 | A hash over files that hold no CRLF is what it was before. |
| WIN-10 | In a project whose git writes CRLF to the working copy and keeps LF in the commit, `gate`, `record` and the three checks agree, and the golden tasks complete in parallel mode. |
| WIN-11 | On Windows a write that fails because its reader has gone ends the run with 141 and no traceback, also when the write left nothing in the buffer. Another error with the same number is raised as before. |
| WIN-12 | `docs/limits.md` records the result of the first run, and says that the fixes have not run on Windows. |

## How we will know

- **AC-001** (verifies WIN-7): Given a machine with Spec Kit and without the Claude Code program, When the walk test runs, Then `specify init` passes and the walk goes on to the install. Shown on Linux by hand, with the program taken off the path; on Windows by the next run of the job.
- **AC-002** (verifies WIN-8, WIN-10): Given a project whose git has `core.autocrlf` on and whose spec was written with CRLF, When the brief is committed, a review carries the line and `record --change` mirrors it, Then `CK-GATE-RECORD`, `CK-APPROVER` and `CK-GATE-MIRROR` pass.
- **AC-003** (verifies WIN-8): The same text with LF and with CRLF gives one evidence hash. Two files with a NUL byte that differ only in their line ends give two.
- **AC-004** (verifies WIN-9): For files with no CRLF the evidence hash equals what the formula of `agentic-evidence/1` gives over their bytes.
- **AC-005** (verifies WIN-10): Given `core.autocrlf` on for every repository git makes, When a golden task runs in parallel mode, Then it completes and no check fails.
- **AC-006** (verifies WIN-11): Given a stream whose flush passes while nothing is buffered and whose next write fails, the run counts as one whose reader has gone, on Windows only. Given an intact stream, or an error that names a file, it does not.
- **AC-007** (verifies WIN-12): `docs/limits.md` names the run, its result and the three causes, and says what has still not run on Windows.

AC-001 in full, and the test of 2026-11-23 for a closed pipe, need Windows. They are met only when the job has run again.

## What it will not do

- Make either install script work on Windows. Nobody knows yet whether they do: the walk has not reached them.
- Change what a project's git does with line ends, or add a `.gitattributes` file to a project.
- Normalise anything but CRLF. A lone CR is left as it is.
- Put Windows into the matrix of `tests.yml`. That waits for a run that passes (WIN-6).

## Decisions made here that are the owner's to change

1. **CRLF counts as LF wherever the kit hashes or compares a file.** An approval then covers a text file whatever its line ends. The other way is to leave the hash as it is and have every project turn git's conversion off, for everyone who works on it on Windows. A project that instead tells git to normalise line ends would still break a gate whenever an editor saved a file with CRLF, until that file was committed and checked out again.
2. Binary is what git takes for binary: a NUL byte in the first 8000 bytes. Such a file is hashed as it is.
3. The hash keeps its label, `agentic-evidence/1`. For files with no CRLF nothing changes. A hash made earlier over a file that does hold CRLF no longer matches. The kit's own tests and its reference example hold no such hash: they pass unchanged, the two tests that read the healthcare repository among them.
4. The walk test does not check for the coding agent's program. A person who installs the kit for Claude Code still needs Claude Code; the test is about the kit's part.
5. On Windows the check for a closed pipe may write one empty line to standard output before another error's traceback. That is the price of telling the two apart.
