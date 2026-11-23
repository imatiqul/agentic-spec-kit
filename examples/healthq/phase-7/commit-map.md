# Commit ids: where the change was written, and on the owner's machine

- **Phase and date:** Phase 7, 2026-11-22
- **Upstream and reference:** spec-kit `v1.4.3`; healthcare repository `imatiqul/azure-ai-cloud-healthcare`, `main` at `8d04df3`
- **Requirement IDs exercised:** TRC-19, AGT-10
- **Assumptions:** none now. The owner pushed the branches as they were and merged them with merge commits on 2026-11-22 (pull requests #73 to #75), so the ids in the right-hand column are the ids in the history of `main`
- **Unverified:** the three branch tips were checked to be in the history of `main` at `d78ffe7`; the fifteen commits between them were not looked up one by one

The change was written in a workspace, under placeholder names. On the owner's machine each commit was made again with the same files, the same message and the same author date, under the name and address of his own latest commit in that repository (`1b74f48`), with two attribution lines added to the message. A commit's id depends on who made it, so each has a new one.

The records made in the workspace name commits by the old id: the four work items (`base:`), the security review, the verification report and `evidence/trace-lines.md`, 20 mentions of five ids in all. They were not edited, because the reviews and the evidence are what a gate decision is bound to. This table is how to read them.

The files are the same on both sides. `rebuild_from_bundle.py` stops unless the tree of each branch is the one it was told to expect:

| Branch | Tree | Tip here |
|---|---|---|
| `sdd/reference-plans` | `991a4df1b7bb25e39b80c6a017842eac6f2abbc3` | `89a4fc9` |
| `sdd/004-audit-identity` | `ea7f15ebee1ff05bc4cbea680e0cdc7fbeb77815` | `1e8d054` |
| `sdd/showcase-proposals` | `0ed88cf7397a4c8ac41f4e0671fd6b3e7069fe74` | `a44c57c` |

| Branch | In the records | On the owner's machine | Commit |
|---|---|---|---|
| `sdd/reference-plans` | `769efd4` | `89a4fc9` | Governance update: constitution v2, the corrected system map, specs 009-025, plans, the agent team |
| `sdd/004-audit-identity` | `373793a` | `f97face` | T001: the audit record names the subject of the authenticated identity |
| | `3d5e82a` | `5d156f3` | T002: the audit middleware runs directly after authentication in the nine services |
| | `5b5ee5c` | `03f987d` | T003: tests for who the audit record names, in the middleware and in a request pipeline |
| | `03c9f5b` | `1ae91cd` | T004: a test that fails the build when a service registers the audit middleware out of order |
| | `d5902a2` | `e6cb69a` | T001, rework 1: the subject comes from an authenticated identity; the log lines name the user |
| | `91b9c32` | `d3995e0` | T003, rework 1: tests for the event, the log lines, a 403 and two identities |
| | `91c3a7b` | `3ea0240` | T004, rework 1: the order check reads one list and looks at what stands in front of the audit |
| | `30241ac` | `0a575ea` | 004: the security review and the independent verification, first round |
| | `0feddc2` | `70e58fc` | 004: the plan's documents corrected after the two reviews |
| | `15bf0f9` | `eb596e3` | 004: work items, the run and the audit log so far |
| | `857f340` | `31bc6c7` | 004: the two reviews, second round: the three reworked items are accepted |
| | `ed3cbe0` | `879ed44` | 004: what is left after the second round, and three sentences that said more than the code does |
| | `dbef918` | `538a9c4` | Map: the nine services write the audit event stream; found while tracing the C4 change |
| | `bc5fdb4` | `7ab7b43` | 004: the trace from each changed line, the briefs for G3 to G7, release drafts, and the amendment proposed to the owner |
| | `6b37cdd` | `2b448d1` | 004: the work records and the run, closed |
| | `12ff77d` | `1e8d054` | The governance folder's README counts what is beside it |
| `sdd/showcase-proposals` | `7d763f7` | `a44c57c` | Showcase proposals: an adoption baseline, the threat model and authorization matrix for C2, and the files the kit reads for unsourced figures |

What was checked on a rehearsal copy before the owner's repository was touched: the kit's checks give the same result on the recreated branch as on the original (80 pass, 23 fail, 1 not run, no line different once ids are set aside), and `agentic.py why` on a changed line finds the same work item, task, criteria and principle.
