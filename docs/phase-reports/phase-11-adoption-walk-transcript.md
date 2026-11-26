# Phase 11: transcript of the newcomer's walk

Every command of the walk, in the order it was run on 2026-11-25, with its exit code and seconds.
Long outputs are trimmed, and each trimmed place says how many lines were left out. Lines longer
than 190 characters are cut and end with `…`. Nothing else was changed.

The lines that begin `gh api repos/owner/name … failed` are this workspace's own answer for a repository
named `owner/name`, which does not exist. A newcomer would see GitHub's answer in their place.

## 01. A fresh clone of the public repository

```text
$ git clone https://github.com/imatiqul/agentic-spec-kit.git kit && git -C kit log --oneline -1 && git -C kit rev-parse HEAD
(in /home/claude/work/adopt)
Cloning into 'kit'...
ec250b5 The README links the video guide of 24 November, and says which commit it shows
ec250b5ef7d2f79a6592db960d9a89601df7bcdd
[exit 0, 2 s]
```

## 02. Which Python and pip this workspace puts first

```text
$ command -v python; echo "python: exit $?"; command -v python3; command -v pip; command -v pip3; cat /etc/os-release | head -2
(in /home/claude/work/adopt/kit)
/usr/local/bin/python
python: exit 0
/usr/local/bin/python3
/usr/local/bin/pip
/usr/local/bin/pip3
PRETTY_NAME="Ubuntu 24.04.5 LTS"
NAME="Ubuntu"
[exit 0, 0 s]
```

## 03. README, "Try it", first command, with the workspace's own Python

```text
$ pip install pyyaml pytest
(in /home/claude/work/adopt/kit)
Requirement already satisfied: pyyaml in /root/.local/lib/python3.13/site-packages (6.0.3)
Requirement already satisfied: pytest in /usr/local/lib/python3.13/site-packages (9.1.1)
[5 lines left out]
[exit 0, 2 s]
```

## 04. The same with /usr/bin/python3 (still the workspace's Python 3.13)

```text
$ /usr/bin/python3 --version; /usr/bin/python3 -m pip --version; /usr/bin/python3 -m pip install pyyaml pytest
(in /home/claude/work/adopt/kit)
Python 3.13.18
pip 26.2.1 from /usr/local/lib/python3.13/dist-packages/pip (python 3.13)
[7 lines left out]
[exit 0, 0 s]
```

## 05. The same with Ubuntu 24.04's own Python 3.12.3

```text
$ /usr/bin/python3.12 --version; /usr/bin/python3.12 -m pip --version; /usr/bin/python3.12 -m pip install pyyaml pytest
(in /home/claude/work/adopt/kit)
Python 3.12.3
pip 24.0 from /usr/lib/python3/dist-packages/pip (python 3.12)
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try apt install
    python3-xyz, where xyz is the package you are trying to
    install.
    
    If you wish to install a non-Debian-packaged Python package,
    create a virtual environment using python3 -m venv path/to/venv.
    Then use path/to/venv/bin/python and path/to/venv/bin/pip. Make
    sure you have python3-full installed.
    
    If you wish to install a non-Debian packaged Python application,
    it may be easiest to use pipx install xyz, which will manage a
    virtual environment for you. Make sure you have pipx installed.
    
    See /usr/share/doc/python3.12/README.venv for more information.

note: If you believe this is a mistake, please contact your Python installation or OS distribution provider. You can override this, at the risk of breaking your Python installation or OS, by …
hint: See PEP 668 for the detailed specification.
[exit 1, 1 s]
```

## 06. A new virtual environment with Ubuntu's Python 3.12.3

```text
$ /usr/bin/python3.12 -m venv /home/claude/work/adopt/venv312 && /home/claude/work/adopt/venv312/bin/python --version && /home/claude/work/adopt/venv312/bin/pip install pyyaml pytest 2>&1 |  …
(in /home/claude/work/adopt/kit)
Python 3.12.3
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.3/1.3 MB 14.1 MB/s eta 0:00:00
Installing collected packages: pyyaml, pygments, pluggy, packaging, iniconfig, pytest
Successfully installed iniconfig-2.3.1 packaging-26.4 pluggy-1.7.0 pygments-2.21.0 pytest-9.2.0 pyyaml-6.0.4
[exit 0, 5 s]
```

## 07. README, "Try it": the self-test

```text
$ python extensions/agentic/scripts/agentic.py selftest
(in /home/claude/work/adopt/kit)
ok   CK-A11Y              broken: a frontend change passed G5 with no accessibility check
       -> fail: CK-A11Y: G5 was approved for a frontend change without accessibility evidence (evidence/accessibility.yml) [.specify/agentic/decisions/001-demo/G5.yml
[207 lines left out]
       -> fail: CK-WORKITEM: 001-demo/T001 went from ready straight to done, which is not allowed [.specify/agentic/work/001-demo/T001.yml]

all self-tests behaved as expected (105 fixtures)
[exit 0, 21 s]
```

## 08. README, "Try it": the unit tests

```text
$ python -m pytest tests -q
(in /home/claude/work/adopt/kit)
[6 lines left out]
........................................................................ [ 93%]
..................................                                       [100%]
536 passed, 2 skipped in 225.01s (0:03:45)
[exit 0, 225 s]
```

## 09. The tour, step 1

```text
$ python extensions/agentic/scripts/agentic.py --root fixtures/multi-app doctor
(in /home/claude/work/adopt/kit)
ok       CK-PROFILE
ok       CK-ROLES
         note: separation of duties: pat holds 2 approving roles (product-owner, solutions-architect)
         note: separation of duties: sam holds 2 approving roles (engineering-manager, qa)
NOT RUN  CK-UPSTREAM-PIN
         .specify/init-options.json is missing, so the installed Spec Kit version is unknown
FAIL     CK-ENFORCE-SETUP
         CK-ENFORCE-SETUP: there is no CODEOWNERS file, so changes to roles, waivers and the constitution need no owner review
         CK-ENFORCE-SETUP: enforcement adapter: the file adapter is for tests only; no approval is bound to an identity
NOT RUN  CK-CRED
         the file adapter holds no description of the agent credential

2 passed, 1 failed, 2 not run

What this means:
  - The file adapter is configured. Approvals are NOT bound to any identity. Use it for tests only.
  - Until the items above are fixed, approver rules (GOV-6, GOV-7, GOV-16) are convention, not enforcement.
  - Identity binding protects only while the agent cannot use an approver's credentials.
[exit 1, 0 s]
```

## 10. The tour, step 2

```text
$ python extensions/agentic/scripts/agentic.py --root fixtures/multi-app check
(in /home/claude/work/adopt/kit)
[134 lines left out: `ok` lines and their notes]
NOT RUN  CK-AGENT-SPEC
         no agent specs in .specify/agentic/agents; run the team init command
FAIL     CK-CONSTITUTION
         CK-CONSTITUTION: constitution.map.yml is missing [.specify/agentic/constitution.map.yml]
NOT RUN  CK-CRED
         the file adapter holds no description of the agent credential
FAIL     CK-ENFORCE-SETUP
         CK-ENFORCE-SETUP: there is no CODEOWNERS file, so changes to roles, waivers and the constitution need no owner review
         CK-ENFORCE-SETUP: enforcement adapter: the file adapter is for tests only; no approval is bound to an identity
NOT RUN  CK-UPSTREAM-PIN
         .specify/init-options.json is missing, so the installed Spec Kit version is unknown
99 passed, 2 failed, 3 not run
[exit 1, 0 s]
```

## 11. The tour, step 3

```text
$ python extensions/agentic/scripts/agentic.py --root fixtures/multi-app report gates
(in /home/claude/work/adopt/kit)
# Gate board

`approved` means a recorded decision for the evidence as it stands now. `open` is the gate a person is needed at next.

| Spec | G1 | G2 | G3 | G4 | G5 | G6 | G7 | Approvers of the open gate |
|---|---|---|---|---|---|---|---|---|
| 001-money-format | open | later | later | later | later | later | later | product-owner |

[exit 0, 0 s]
```

## 12. The tour, step 4

```text
$ python extensions/agentic/scripts/agentic.py --root fixtures/multi-app gate --spec 001-money-format --gate G1
(in /home/claude/work/adopt/kit)
Gate G1 for 001-money-format: no decision recorded
Evidence:
  specs/001-money-format/spec.md
Roles that must approve: product-owner

To approve, a person holding the role submits an approving review containing this line:

  gate G1 approve sha256:da24c57a8647fc9f0529420dcecc621f2fc69b6de144dfa724527eba03440a0c

To reject, request changes with `reject` in place of `approve`.
[exit 0, 0 s]
```

## 13. The tour, step 5

```text
$ python extensions/agentic/scripts/agentic.py --root fixtures/multi-app impact --spec 001-money-format
(in /home/claude/work/adopt/kit)
---
spec: 001-money-format
touches:
- shop-shared-lib
affected:
- node: shop-billing
  distance: 1
  via: builds-with shop-shared-lib
  owner: backend
- node: shop-orders
  distance: 1
  via: builds-with shop-shared-lib
  owner: backend
tier_computed: medium
required_approvers:
  G3:
  - backend
  - platform
  G5:
  - platform
packs_triggered:
[19 lines left out: the same report as a table]
[exit 0, 0 s]
```

## 14. The newest release tags of github/spec-kit on 2026-11-25

```text
$ git ls-remote --tags --refs https://github.com/github/spec-kit | sed 's#.*refs/tags/##' | sort -V | tail -12
(in /home/claude/work/adopt)
v1.2.5
v1.2.6
v1.3.0
v1.3.1
v1.3.2
v1.3.3
v1.4.0
v1.4.1
v1.4.2
v1.4.3
v1.4.4
v1.4.5
[exit 0, 1 s]
```

## 15. A new project with Spec Kit 1.4.3

```text
$ specify init shop-demo --integration claude --non-interactive
(in /home/claude/work/adopt/proj)
[71 lines left out: banners and command lists]
[exit 0, 1 s]
```

## 16. docs/install.md, section 1: the Lite install

```text
$ bash /home/claude/work/adopt/kit/scripts/install.sh . lite
(in /home/claude/work/adopt/proj/shop-demo)
[54 lines left out: banners and command lists]
✓ Extension installed successfully!
✓ Extension installed successfully!
✓ Preset 'Agentic Spec Kit — Lite profile' v0.1.0 installed (priority 10)
✓ Step type 'Agentic Gate' (agentic-gate) installed
✓ Workflow 'Agentic SDD with human gates' (agentic-sdd) installed
✓ Workflow 'Agentic SDD with an agent team' (agentic-sdd-team) installed
✓ Workflow 'Agentic SDD, one agent playing each role in turn' 
Installed. Next:
  python .specify/extensions/agentic/scripts/agentic.py init --profile lite --repository <owner/name>
  python .specify/extensions/agentic/scripts/agentic.py team init --runtimes <claude,copilot,sequential>
  python .specify/extensions/agentic/scripts/agentic.py doctor
[exit 0, 3 s]
```

## 17. docs/install.md, section 2: init

```text
$ python .specify/extensions/agentic/scripts/agentic.py init --profile lite --repository owner/name
(in /home/claude/work/adopt/proj/shop-demo)
wrote .specify/agentic/kit.yml
wrote .specify/agentic/roles.yml
wrote .specify/agentic/constitution.map.yml
wrote .github/workflows/agentic-checks.yml
wrote .specify/agentic/audit/kit.jsonl
Next: list real people in roles.yml, add CODEOWNERS, then run `doctor`.
[exit 0, 0 s]
```

## 18. docs/install.md, section 2: team init

```text
$ python .specify/extensions/agentic/scripts/agentic.py team init --runtimes claude,copilot,sequential
(in /home/claude/work/adopt/proj/shop-demo)
wrote .specify/agentic/agents/ai-implementer.yml
wrote .specify/agentic/agents/backend-implementer.yml
wrote .specify/agentic/agents/frontend-implementer.yml
wrote .specify/agentic/agents/independent-verifier.yml
wrote .specify/agentic/agents/orchestrator.yml
wrote .specify/agentic/agents/spec-author.yml
rendered .claude/agents/ai-implementer.md
rendered .claude/agents/backend-implementer.md
rendered .claude/agents/frontend-implementer.md
rendered .claude/agents/independent-verifier.md
rendered .claude/agents/orchestrator.md
rendered .claude/agents/spec-author.md
rendered .github/agents/ai-implementer.agent.md
rendered .github/agents/backend-implementer.agent.md
rendered .github/agents/frontend-implementer.agent.md
rendered .github/agents/independent-verifier.agent.md
rendered .github/agents/orchestrator.agent.md
rendered .github/agents/spec-author.agent.md
rendered .specify/agentic/agents/rendered/sequential.md
Next: review the agent specs, add them to CODEOWNERS with the rest of .specify/, and run `doctor`.
[exit 0, 0 s]
```

## 19. doctor, before the steps done by hand

```text
$ python .specify/extensions/agentic/scripts/agentic.py doctor
(in /home/claude/work/adopt/proj/shop-demo)
ok       CK-PROFILE
FAIL     CK-ROLES
         CK-ROLES: gate G0 has nobody in any of: product-owner, solutions-architect, security-compliance [.specify/agentic/roles.yml]
         CK-ROLES: gate G1 has nobody in any of: product-owner [.specify/agentic/roles.yml]
         CK-ROLES: gate G3 has nobody in any of: solutions-architect [.specify/agentic/roles.yml]
         CK-ROLES: gate G5 has nobody in any of: qa [.specify/agentic/roles.yml]
ok       CK-UPSTREAM-PIN
ok       CK-ENFORCE-SETUP
         note: not enforced: there is no CODEOWNERS file, so changes to roles, waivers and the constitution need no owner review
         note: not checkable: branch protection: gh api repos/owner/name/branches/main/protection failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo t …
NOT RUN  CK-CRED
         gh api repos/owner/name failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo to request access. If add_repo answers that read access is already …

3 passed, 1 failed, 1 not run

What this means:
  - Identity binding protects only while the agent cannot use an approver's credentials.
[exit 1, 2 s]
```

## 20. check, before the steps done by hand

```text
$ python .specify/extensions/agentic/scripts/agentic.py check
(in /home/claude/work/adopt/proj/shop-demo)
[49 lines left out: plain `ok` lines and "skipped: not required by the lite profile" notes]
         note: Claude Code subagents: write paths are enforced by the pre-tool-use event script for file-writing tools; shell commands and everything else fall back to the diff check
         note: GitHub Copilot custom agents: write paths are not enforced by the runtime; the diff check after the run is the one that counts
         note: Sequential single-agent mode: write paths are enforced by the event script only where the integration supports events; the diff check after the run is the one that counts
NOT RUN  CK-CRED
         gh api repos/owner/name failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo to request access. If add_repo answers that read access is already …
         note: not enforced: there is no CODEOWNERS file, so changes to roles, waivers and the constitution need no owner review
         note: not checkable: branch protection: gh api repos/owner/name/branches/main/protection failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo t …
         note: no golden-task results in this repository (they are produced in the kit's own CI, or where kit.yml requires them)
         note: no golden-task results in this repository
         note: no golden-task results in this repository
         note: skipped the comparison with the change as a whole: no base ref or list of changed files was given
FAIL     CK-ROLES
         CK-ROLES: gate G0 has nobody in any of: product-owner, solutions-architect, security-compliance [.specify/agentic/roles.yml]
         CK-ROLES: gate G1 has nobody in any of: product-owner [.specify/agentic/roles.yml]
         CK-ROLES: gate G3 has nobody in any of: solutions-architect [.specify/agentic/roles.yml]
         CK-ROLES: gate G5 has nobody in any of: qa [.specify/agentic/roles.yml]

36 passed, 1 failed, 1 not run
[exit 1, 2 s]
```

## 21. By hand: one person in roles.yml, a CODEOWNERS file, git init, first commit

```text
$ git init -q -b main && git add -A && git -c user.name=newcomer -c user.email=newcomer@example.com commit -q -m 'A new Spec Kit project with agentic-spec-kit, Lite profile' && git log --one …
(in /home/claude/work/adopt/proj/shop-demo)
3628bd9 A new Spec Kit project with agentic-spec-kit, Lite profile
170
[exit 0, 0 s]
```

## 22. doctor, after the steps done by hand

```text
$ python .specify/extensions/agentic/scripts/agentic.py doctor
(in /home/claude/work/adopt/proj/shop-demo)
ok       CK-PROFILE
ok       CK-ROLES
         note: separation of duties: newcomer holds 3 approving roles (product-owner, qa, solutions-architect)
         note: separation of duties: one person holds every role; every approval is a single-approver exception
ok       CK-UPSTREAM-PIN
ok       CK-ENFORCE-SETUP
         note: not checkable: branch protection: gh api repos/owner/name/branches/main/protection failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo t …
NOT RUN  CK-CRED
         gh api repos/owner/name failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo to request access. If add_repo answers that read access is already …

4 passed, 0 failed, 1 not run

What this means:
  - Identity binding protects only while the agent cannot use an approver's credentials.
[exit 2, 1 s]
```

## 23. check, after the steps done by hand

```text
$ python .specify/extensions/agentic/scripts/agentic.py check
(in /home/claude/work/adopt/proj/shop-demo)
[50 lines left out: plain `ok` lines and "skipped: not required by the lite profile" notes]
         note: Claude Code subagents: write paths are enforced by the pre-tool-use event script for file-writing tools; shell commands and everything else fall back to the diff check
         note: GitHub Copilot custom agents: write paths are not enforced by the runtime; the diff check after the run is the one that counts
         note: Sequential single-agent mode: write paths are enforced by the event script only where the integration supports events; the diff check after the run is the one that counts
NOT RUN  CK-CRED
         gh api repos/owner/name failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo to request access. If add_repo answers that read access is already …
         note: not checkable: branch protection: gh api repos/owner/name/branches/main/protection failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo t …
         note: no golden-task results in this repository (they are produced in the kit's own CI, or where kit.yml requires them)
         note: no golden-task results in this repository
         note: no golden-task results in this repository
         note: skipped the comparison with the change as a whole: no base ref or list of changed files was given
         note: separation of duties: newcomer holds 3 approving roles (product-owner, qa, solutions-architect)
         note: separation of duties: one person holds every role; every approval is a single-approver exception

37 passed, 0 failed, 1 not run
[exit 0, 2 s]
```

## 24. selftest inside the project

```text
$ python .specify/extensions/agentic/scripts/agentic.py selftest
(in /home/claude/work/adopt/proj/shop-demo)
ok   CK-AGENT-MEMORY      broken: an instruction file tells agents they may push to main
       -> fail: CK-AGENT-MEMORY: line 5 allows pushing to the default branch, which the kit forbids an agent to do. Take it out, or say plainly that it is not allowed
[75 lines left out]
       -> fail: CK-WORKITEM: 001-demo/T001 went from ready straight to done, which is not allowed [.specify/agentic/work/001-demo/T001.yml]

all self-tests behaved as expected (39 fixtures)
[exit 0, 3 s]
```

## 25. One small spec written: the gate board

```text
$ python .specify/extensions/agentic/scripts/agentic.py report gates
(in /home/claude/work/adopt/proj/shop-demo)
# Gate board

`approved` means a recorded decision for the evidence as it stands now. `open` is the gate a person is needed at next.

| Spec | G1 | G3 | G5 | Approvers of the open gate |
|---|---|---|---|---|
| 001-greeting | open | later | later | product-owner |

[exit 0, 0 s]
```

## 26. The lane and its gates

```text
$ python .specify/extensions/agentic/scripts/agentic.py lane
(in /home/claude/work/adopt/proj/shop-demo)
001-greeting: standard lane; gates G1, G3, G5
[exit 0, 0 s]
```

## 27. What gate G1 needs

```text
$ python .specify/extensions/agentic/scripts/agentic.py gate --spec 001-greeting --gate G1
(in /home/claude/work/adopt/proj/shop-demo)
Gate G1 for 001-greeting: no decision recorded
Evidence:
  specs/001-greeting/spec.md
Roles that must approve: product-owner

To approve, a person holding the role submits an approving review containing this line:

  gate G1 approve sha256:84303bed108e0df61b0aaefa867b6c975dfc328cfc5b9a40c3be53d4ca8d5d7d

To reject, request changes with `reject` in place of `approve`.
[exit 0, 0 s]
```

## 28. The brief for G1 (written after the spec was committed)

```text
$ python .specify/extensions/agentic/scripts/agentic.py brief --spec 001-greeting --gate G1 --write
(in /home/claude/work/adopt/proj/shop-demo)
wrote specs/001-greeting/briefs/G1.md
[exit 0, 0 s]
```

## 29. record, for a review that does not exist (to see what the kit does)

```text
$ python .specify/extensions/agentic/scripts/agentic.py record --spec 001-greeting --gate G1 --decision approve --commit $(git rev-parse HEAD) --approval newcomer:product-owner:pull/1#review …
(in /home/claude/work/adopt/proj/shop-demo)
wrote .specify/agentic/decisions/001-greeting/G1.yml
This is a mirror. CK-APPROVER and CK-GATE-MIRROR decide whether the review behind it is valid.
[exit 0, 0 s]
```

## 30. The gate board after that record

```text
$ python .specify/extensions/agentic/scripts/agentic.py report gates
(in /home/claude/work/adopt/proj/shop-demo)
# Gate board

`approved` means a recorded decision for the evidence as it stands now. `open` is the gate a person is needed at next.

| Spec | G1 | G3 | G5 | Approvers of the open gate |
|---|---|---|---|---|
| 001-greeting | approved | no evidence yet | later | solutions-architect |

[exit 0, 0 s]
```

## 31. check after that record

```text
$ python .specify/extensions/agentic/scripts/agentic.py check
(in /home/claude/work/adopt/proj/shop-demo)
[47 lines left out: plain `ok` lines and "skipped: not required by the lite profile" notes]
         note: Claude Code subagents: write paths are enforced by the pre-tool-use event script for file-writing tools; shell commands and everything else fall back to the diff check
         note: GitHub Copilot custom agents: write paths are not enforced by the runtime; the diff check after the run is the one that counts
         note: Sequential single-agent mode: write paths are enforced by the event script only where the integration supports events; the diff check after the run is the one that counts
NOT RUN  CK-APPROVER
         gh api repos/owner/name/pulls/1/reviews failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo to request access. If add_repo answers that read a …
NOT RUN  CK-CRED
         gh api repos/owner/name failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo to request access. If add_repo answers that read access is already …
         note: not checkable: branch protection: gh api repos/owner/name/branches/main/protection failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo t …
NOT RUN  CK-GATE-MIRROR
         gh api repos/owner/name/pulls/1/reviews failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo to request access. If add_repo answers that read a …
FAIL     CK-GATE-RECORD
         CK-GATE-RECORD: evidence file specs/001-greeting/briefs/G1.md does not exist [.specify/agentic/decisions/001-greeting/G1.yml]
         note: no golden-task results in this repository (they are produced in the kit's own CI, or where kit.yml requires them)
         note: no golden-task results in this repository
         note: no golden-task results in this repository
         note: skipped the comparison with the change as a whole: no base ref or list of changed files was given
         note: separation of duties: newcomer holds 3 approving roles (product-owner, qa, solutions-architect)
         note: separation of duties: one person holds every role; every approval is a single-approver exception

34 passed, 1 failed, 3 not run
[exit 1, 2 s]
```

## 32. gate, while the brief is not committed

```text
$ python .specify/extensions/agentic/scripts/agentic.py gate --spec 001-greeting --gate G1
(in /home/claude/work/adopt/proj/shop-demo)
Gate G1 for 001-greeting: approve recorded
Evidence:
  specs/001-greeting/briefs/G1.md
  specs/001-greeting/spec.md
Roles that must approve: product-owner

To approve, a person holding the role submits an approving review containing this line:

  gate G1 approve sha256:de1a20663601eda10a616c0a072086b5dee7a2cd87ce6a113f5389dd922b354d

To reject, request changes with `reject` in place of `approve`.
[exit 0, 0 s]
```

## 33. The brief committed; the same record written again

```text
$ python .specify/extensions/agentic/scripts/agentic.py record --spec 001-greeting --gate G1 --decision approve --commit $(git rev-parse HEAD) --approval newcomer:product-owner:pull/1#review …
(in /home/claude/work/adopt/proj/shop-demo)
wrote .specify/agentic/decisions/001-greeting/G1.yml
This is a mirror. CK-APPROVER and CK-GATE-MIRROR decide whether the review behind it is valid.
[exit 0, 0 s]
```

## 34. check in Lite when GitHub cannot be read

```text
$ python .specify/extensions/agentic/scripts/agentic.py check
(in /home/claude/work/adopt/proj/shop-demo)
[48 lines left out: plain `ok` lines and "skipped: not required by the lite profile" notes]
         note: Claude Code subagents: write paths are enforced by the pre-tool-use event script for file-writing tools; shell commands and everything else fall back to the diff check
         note: GitHub Copilot custom agents: write paths are not enforced by the runtime; the diff check after the run is the one that counts
         note: Sequential single-agent mode: write paths are enforced by the event script only where the integration supports events; the diff check after the run is the one that counts
NOT RUN  CK-APPROVER
         gh api repos/owner/name/pulls/1/reviews failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo to request access. If add_repo answers that read a …
NOT RUN  CK-CRED
         gh api repos/owner/name failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo to request access. If add_repo answers that read access is already …
         note: not checkable: branch protection: gh api repos/owner/name/branches/main/protection failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo t …
NOT RUN  CK-GATE-MIRROR
         gh api repos/owner/name/pulls/1/reviews failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo to request access. If add_repo answers that read a …
         note: no golden-task results in this repository (they are produced in the kit's own CI, or where kit.yml requires them)
         note: no golden-task results in this repository
         note: no golden-task results in this repository
         note: skipped the comparison with the change as a whole: no base ref or list of changed files was given
         note: separation of duties: newcomer holds 3 approving roles (product-owner, qa, solutions-architect)
         note: separation of duties: one person holds every role; every approval is a single-approver exception

35 passed, 0 failed, 3 not run
[exit 0, 2 s]
```

## 35. The gate board in that state

```text
$ python .specify/extensions/agentic/scripts/agentic.py report gates
(in /home/claude/work/adopt/proj/shop-demo)
# Gate board

`approved` means a recorded decision for the evidence as it stands now. `open` is the gate a person is needed at next.

| Spec | G1 | G3 | G5 | Approvers of the open gate |
|---|---|---|---|---|
| 001-greeting | approved | no evidence yet | later | solutions-architect |

[exit 0, 0 s]
```

## 36. Spec Kit 1.4.5 in its own environment

```text
$ /usr/bin/python3.12 -m venv /home/claude/work/adopt/sk145 && /home/claude/work/adopt/sk145/bin/pip install -q 'git+https://github.com/github/spec-kit.git@v1.4.5' pyyaml 2>&1 | tail -3; /ho …
(in /home/claude/work/adopt)
specify 1.4.5
[exit 0, 20 s]
```

## 37. A new project with Spec Kit 1.4.5

```text
$ specify init shop-demo --integration claude --non-interactive
(in /home/claude/work/adopt/proj145)
[71 lines left out: banners and command lists]
[exit 0, 1 s]
```

## 38. The Lite install on Spec Kit 1.4.5

```text
$ bash /home/claude/work/adopt/kit/scripts/install.sh . lite
(in /home/claude/work/adopt/proj145/shop-demo)
[54 lines left out: banners and command lists]
✓ Extension installed successfully!
✓ Extension installed successfully!
✓ Preset 'Agentic Spec Kit — Lite profile' v0.1.0 installed (priority 10)
✓ Step type 'Agentic Gate' (agentic-gate) installed
✓ Workflow 'Agentic SDD with human gates' (agentic-sdd) installed
✓ Workflow 'Agentic SDD with an agent team' (agentic-sdd-team) installed
✓ Workflow 'Agentic SDD, one agent playing each role in turn' 
Installed. Next:
  python .specify/extensions/agentic/scripts/agentic.py init --profile lite --repository <owner/name>
  python .specify/extensions/agentic/scripts/agentic.py team init --runtimes <claude,copilot,sequential>
  python .specify/extensions/agentic/scripts/agentic.py doctor
[exit 0, 3 s]
```

## 39. doctor on Spec Kit 1.4.5

```text
$ python .specify/extensions/agentic/scripts/agentic.py doctor
(in /home/claude/work/adopt/proj145/shop-demo)
ok       CK-PROFILE
FAIL     CK-ROLES
         CK-ROLES: gate G0 has nobody in any of: product-owner, solutions-architect, security-compliance [.specify/agentic/roles.yml]
         CK-ROLES: gate G1 has nobody in any of: product-owner [.specify/agentic/roles.yml]
         CK-ROLES: gate G3 has nobody in any of: solutions-architect [.specify/agentic/roles.yml]
         CK-ROLES: gate G5 has nobody in any of: qa [.specify/agentic/roles.yml]
FAIL     CK-UPSTREAM-PIN
         CK-UPSTREAM-PIN: Spec Kit 1.4.5 is installed but kit.yml pins 1.4.3 [.specify/init-options.json]
ok       CK-ENFORCE-SETUP
         note: not enforced: there is no CODEOWNERS file, so changes to roles, waivers and the constitution need no owner review
         note: not checkable: branch protection: gh api repos/owner/name/branches/main/protection failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo t …
NOT RUN  CK-CRED
         gh api repos/owner/name failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo to request access. If add_repo answers that read access is already …

2 passed, 2 failed, 1 not run

What this means:
  - Identity binding protects only while the agent cannot use an approver's credentials.
[exit 1, 2 s]
```

## 40. check on Spec Kit 1.4.5

```text
$ python .specify/extensions/agentic/scripts/agentic.py check
(in /home/claude/work/adopt/proj145/shop-demo)
[48 lines left out: plain `ok` lines and "skipped: not required by the lite profile" notes]
         note: Claude Code subagents: write paths are enforced by the pre-tool-use event script for file-writing tools; shell commands and everything else fall back to the diff check
         note: GitHub Copilot custom agents: write paths are not enforced by the runtime; the diff check after the run is the one that counts
         note: Sequential single-agent mode: write paths are enforced by the event script only where the integration supports events; the diff check after the run is the one that counts
NOT RUN  CK-CRED
         gh api repos/owner/name failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo to request access. If add_repo answers that read access is already …
         note: not enforced: there is no CODEOWNERS file, so changes to roles, waivers and the constitution need no owner review
         note: not checkable: branch protection: gh api repos/owner/name/branches/main/protection failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo t …
         note: no golden-task results in this repository (they are produced in the kit's own CI, or where kit.yml requires them)
         note: no golden-task results in this repository
         note: no golden-task results in this repository
         note: skipped the comparison with the change as a whole: no base ref or list of changed files was given
FAIL     CK-ROLES
         CK-ROLES: gate G0 has nobody in any of: product-owner, solutions-architect, security-compliance [.specify/agentic/roles.yml]
         CK-ROLES: gate G1 has nobody in any of: product-owner [.specify/agentic/roles.yml]
         CK-ROLES: gate G3 has nobody in any of: solutions-architect [.specify/agentic/roles.yml]
         CK-ROLES: gate G5 has nobody in any of: qa [.specify/agentic/roles.yml]
FAIL     CK-UPSTREAM-PIN
         CK-UPSTREAM-PIN: Spec Kit 1.4.5 is installed but kit.yml pins 1.4.3 [.specify/init-options.json]

35 passed, 2 failed, 1 not run
[exit 1, 1 s]
```

## 41. Stand-in demo, in a throwaway copy of the sample: record one approval

```text
$ python /home/claude/work/adopt/kit/extensions/agentic/scripts/agentic.py --root . record --spec 001-money-format --gate G1 --decision approve --commit fe7ef2031305052953e239af2231376018d23 …
(in /home/claude/work/adopt/demo)
wrote .specify/agentic/decisions/001-money-format/G1.yml
This is a mirror. CK-APPROVER and CK-GATE-MIRROR decide whether the review behind it is valid.
[exit 0, 0 s]
```

## 42. Stand-in demo: the gate board

```text
$ python /home/claude/work/adopt/kit/extensions/agentic/scripts/agentic.py --root . report gates
(in /home/claude/work/adopt/demo)
# Gate board

`approved` means a recorded decision for the evidence as it stands now. `open` is the gate a person is needed at next.

| Spec | G1 | G2 | G3 | G4 | G5 | G6 | G7 | Approvers of the open gate |
|---|---|---|---|---|---|---|---|---|
| 001-money-format | approved | open | later | later | later | later | later | product-owner, solutions-architect |

[exit 0, 1 s]
```

## 43. Stand-in demo: check

```text
$ python /home/claude/work/adopt/kit/extensions/agentic/scripts/agentic.py --root . check
(in /home/claude/work/adopt/demo)
[130 lines left out: `ok` lines and their notes]
NOT RUN  CK-AGENT-SPEC
         no agent specs in .specify/agentic/agents; run the team init command
ok       CK-APPROVER
FAIL     CK-BRIEF
         CK-BRIEF: the evidence for G1 does not include the reviewer brief (specs/001-money-format/briefs/G1.md) [.specify/agentic/decisions/001-money-format/G1.yml]
FAIL     CK-CONSTITUTION
         CK-CONSTITUTION: constitution.map.yml is missing [.specify/agentic/constitution.map.yml]
NOT RUN  CK-CRED
         the file adapter holds no description of the agent credential
FAIL     CK-ENFORCE-SETUP
         CK-ENFORCE-SETUP: there is no CODEOWNERS file, so changes to roles, waivers and the constitution need no owner review
         CK-ENFORCE-SETUP: enforcement adapter: the file adapter is for tests only; no approval is bound to an identity
ok       CK-GATE-MIRROR
ok       CK-GATE-RECORD
NOT RUN  CK-UPSTREAM-PIN
         .specify/init-options.json is missing, so the installed Spec Kit version is unknown
98 passed, 3 failed, 3 not run
[exit 1, 0 s]
```

## 44. Stand-in demo: the approved spec is changed

```text
$ python /home/claude/work/adopt/kit/extensions/agentic/scripts/agentic.py --root . gate --spec 001-money-format --gate G1
(in /home/claude/work/adopt/demo)
Gate G1 for 001-money-format: approve recorded for DIFFERENT evidence (the files changed since)
Evidence:
  specs/001-money-format/spec.md
Roles that must approve: product-owner

To approve, a person holding the role submits an approving review containing this line:

  gate G1 approve sha256:312c71cfc91eba1227b646b3c7cbca8ca7da52f0f293f37a1db25ce2af0995d9

To reject, request changes with `reject` in place of `approve`.
[exit 0, 0 s]
```

## 45. Stand-in demo: the gate board after the change

```text
$ python /home/claude/work/adopt/kit/extensions/agentic/scripts/agentic.py --root . report gates
(in /home/claude/work/adopt/demo)
# Gate board

`approved` means a recorded decision for the evidence as it stands now. `open` is the gate a person is needed at next.

| Spec | G1 | G2 | G3 | G4 | G5 | G6 | G7 | Approvers of the open gate |
|---|---|---|---|---|---|---|---|---|
| 001-money-format | open | later | later | later | later | later | later | product-owner |

[exit 0, 1 s]
```

## 46. doctor when the agent's account is also an approver (stand-in adapter)

```text
$ python /home/claude/work/adopt/kit/extensions/agentic/scripts/agentic.py --root . doctor
(in /home/claude/work/adopt/demo)
ok       CK-PROFILE
ok       CK-ROLES
         note: separation of duties: pat holds 2 approving roles (product-owner, solutions-architect)
         note: separation of duties: sam holds 2 approving roles (engineering-manager, qa)
NOT RUN  CK-UPSTREAM-PIN
         .specify/init-options.json is missing, so the installed Spec Kit version is unknown
FAIL     CK-ENFORCE-SETUP
         CK-ENFORCE-SETUP: there is no CODEOWNERS file, so changes to roles, waivers and the constitution need no owner review
         CK-ENFORCE-SETUP: the agent's own account (pat) is listed in roles.yml, so it could approve its own work [.specify/agentic/roles.yml]
         CK-ENFORCE-SETUP: enforcement adapter: the file adapter is for tests only; no approval is bound to an identity
NOT RUN  CK-CRED
         the file adapter holds no description of the agent credential

2 passed, 1 failed, 2 not run

What this means:
  - The file adapter is configured. Approvals are NOT bound to any identity. Use it for tests only.
  - Until the items above are fixed, approver rules (GOV-6, GOV-7, GOV-16) are convention, not enforcement.
  - Identity binding protects only while the agent cannot use an approver's credentials.
[exit 1, 0 s]
```

## 47. The first pull request of an adopting team, simulated with two branches

```text
$ python .specify/extensions/agentic/scripts/agentic.py check --base-ref main
(in /home/claude/work/adopt/boot)
[50 lines left out: plain `ok` lines and "skipped: not required by the lite profile" notes]
         note: Claude Code subagents: write paths are enforced by the pre-tool-use event script for file-writing tools; shell commands and everything else fall back to the diff check
         note: Sequential single-agent mode: write paths are enforced by the event script only where the integration supports events; the diff check after the run is the one that counts
NOT RUN  CK-CRED
         gh api repos/owner/name failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo to request access. If add_repo answers that read access is already …
         note: not checkable: branch protection: gh api repos/owner/name/branches/main/protection failed: gh: GitHub access to this repository is not enabled for this session. Use add_repo t …
         note: no golden-task results in this repository (they are produced in the kit's own CI, or where kit.yml requires them)
         note: no golden-task results in this repository
         note: no golden-task results in this repository
         note: no spec in flight is being worked through work items
         note: separation of duties: newcomer holds 3 approving roles (product-owner, qa, solutions-architect)
         note: separation of duties: one person holds every role; every approval is a single-approver exception

37 passed, 0 failed, 1 not run
[exit 0, 1 s]
```

## 48. The command folders after the install, on Spec Kit 1.4.3 and on 1.4.5

```text
$ diff <(ls proj/shop-demo/.claude/skills) <(ls proj145/shop-demo/.claude/skills) && echo 'the same command folders on 1.4.3 and 1.4.5:' $(ls proj145/shop-demo/.claude/skills | wc -l)
(in /home/claude/work/adopt)
the same command folders on 1.4.3 and 1.4.5: 21
[exit 0, 0 s]
```

## 49. The kit's tags and version numbers

```text
$ echo "tags in the kit's repository: $(git -C kit tag | wc -l)"; python kit/extensions/agentic/scripts/agentic.py --help | grep -m1 'agentic-spec-kit'; grep -hE '^\s+version:' kit/extension …
(in /home/claude/work/adopt)
tags in the kit's repository: 0
agentic-spec-kit 0.1.0
  version: "0.1.0"
  version: "0.3.0"
      version: ">=0.1.0"
[exit 0, 0 s]
```

## 50. Which newcomer documents mention each subject (nothing after a subject means none does)

```text
$ cd kit && for w in 'uv tool' 'uvx' 'pipx' 'git init' 'venv' 'virtual environment' 'python3' 'machine user' 'GitHub App' 'bot account' 'own account' 'second account' 'fine-grained' 'upgrade …
(in /home/claude/work/adopt)
uv tool                
uvx                    
pipx                   
git init               
venv                   
virtual environment    .claude/skills/agentic-spec-kit-try/SKILL.md 
python3                .claude/skills/agentic-spec-kit-try/SKILL.md .claude/skills/agentic-spec-kit-install/SKILL.md 
machine user           
GitHub App             
bot account            
own account            README.md 
second account         
fine-grained           
upgrade                
stale                  
dismiss                
[exit 0, 0 s]
```

## 51. The dates of the commits behind upstream's three newest tags

```text
$ git fetch -q --depth 1 https://github.com/github/spec-kit tag v1.4.3 tag v1.4.4 tag v1.4.5 2>&1 | tail -2; for t in v1.4.3 v1.4.4 v1.4.5; do echo "$t $(git log -1 --format=%cI $t^{commit}) …
(in /home/claude/work/adopt/upstream-tags)
v1.4.3 2026-11-19T14:20:20+00:00
v1.4.4 2026-11-23T18:07:15+00:00
v1.4.5 2026-11-25T17:43:26+00:00
[exit 0, 2 s]
```
