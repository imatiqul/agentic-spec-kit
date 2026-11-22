# agentic (slice 0.1 — Govern)

Human approval gates bound to identity and evidence, waivers, traceability and an audit log,
enforced by deterministic checks. Installs on unmodified Spec Kit 1.4.3.

```bash
specify extension add --dev path/to/agentic-spec-kit/extensions/agentic
python .specify/extensions/agentic/scripts/agentic.py init --profile standard --repository owner/name
python .specify/extensions/agentic/scripts/agentic.py doctor
python .specify/extensions/agentic/scripts/agentic.py check
```

Requires Python 3.11+ and PyYAML. See `docs/install.md` and `docs/admin-setup.md` in the repository.

Run `python .specify/extensions/agentic/scripts/agentic.py selftest` to see every check fail on its broken fixture.
