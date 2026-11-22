
## Traceability (agentic-spec-kit)

Every task that delivers behaviour ends with `Carries:` and the acceptance criteria it serves, for example:

- [ ] T012 [P] Reject requests with no tenant claim in src/api/auth.py. Carries: AC-003, AC-004

Rules the checks enforce:
- A task may only carry IDs that exist in `spec.md`.
- An acceptance criterion with no passing test must be carried by at least one open task, or it is a gap.
- Tests name the criterion they prove in their name, for example `test_AC_003_rejects_missing_tenant`.
