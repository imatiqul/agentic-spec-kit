## Spec-driven governance reference: constitution, system map, first eight specs

This pull request adds governance files only. **No source file changes.** It is a draft so that the files can be reviewed here.

They were written with [agentic-spec-kit](https://github.com/imatiqul/agentic-spec-kit), on github/spec-kit `v1.4.3`, from a review of this repository at `6e0879d2`.

| Path | What it is |
|---|---|
| `.specify/memory/constitution.md` | Constitution 1.0.0: 25 principles, each checked by a machine or judged by a named role |
| `.specify/agentic/` | Kit settings (Regulated profile, HIPAA pack), roles, constitution map, audit log, and a README |
| `system-map/map.yml` | 77 components and 168 dependencies. Owners, tiers and classifications are proposals until a plan is reviewed |
| `specs/001` to `specs/008` | One spec for each Critical finding: fail-closed authentication, endpoint authorization and scoping, identity from the token, audit attribution, triage validation, the evaluation's production path, a complete audit export, an append-only audit log |
| `.github/CODEOWNERS` | Owner review for the governance files |

### State

- The owner approved the constitution (gate G0) and the eight specs (gates G1 and G2) in conversation on 2026-11-22. At G2, four clinical questions were left as conditions for a clinician to settle when the plans are reviewed.
- No gate has been passed by a pull-request review, so the kit holds no decision record yet.
- Spec Kit and the kit's extensions are not installed here, and no workflow runs the checks. From a checkout of agentic-spec-kit: `python <agentic-spec-kit>/extensions/agentic/scripts/agentic.py --root . check`

### Before this can be more than a draft

- Agents need a GitHub identity that is not the maintainer's. GitHub does not let the author of a pull request approve it.
- `main` needs branch protection that requires a pull request and a review.
- Installing Spec Kit, the kit and the checks workflow is a separate change.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01A2CG7WvPeDnyLubfj4wQM5
