# Evidence pack: 004-audit-identity

**This pack supports an audit. It does not certify compliance with any law, regulation or standard.**

Generated on 2026-11-22 by agentic-spec-kit 0.1.0, profile regulated.

| Folder | Holds |
|---|---|
| `decisions/` | One record per gate decision: who approved, in which role, in which review, and the hash of what they reviewed |
| `evidence/` | The files each decision was made on, as they are in the repository today |
| `audit/` | The hash-chained audit log of each spec |
| `trace/` | Requirement to test, per spec |
| `waivers/` | Recorded exceptions that are active |
| `config/` | Roles and who holds them, the kit settings, the constitution |

`MANIFEST.json` lists every file here with its SHA-256, the control mapping of each active domain pack with the hash of the spec section that
answers each control, every approval, waiver and exception, and the result of every check on the day the pack was made.

Audit log: intact.
Checks: 76 passed, 22 failed, 1 not run, 5 not required by the profile.
