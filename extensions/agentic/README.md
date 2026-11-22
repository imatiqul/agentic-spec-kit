# agentic (slice 0.1 — Govern)

Human approval gates bound to identity and evidence, waivers, traceability and an audit log,
enforced by deterministic checks. Installs on unmodified Spec Kit 1.4.3.

```bash
specify extension add --dev path/to/agentic-spec-kit/extensions/agentic
python .specify/extensions/agentic/scripts/agentic.py init --profile standard --repository owner/name
python .specify/extensions/agentic/scripts/agentic.py doctor
python .specify/extensions/agentic/scripts/agentic.py check
```

Requires Python 3.10 or later and PyYAML (3.11 or later to read a Codex `.codex/config.toml`). See `docs/install.md` and `docs/admin-setup.md` in the repository.

Run `python .specify/extensions/agentic/scripts/agentic.py selftest` to see every check fail on its broken fixture.

## Added in slice 0.4

```bash
A="python .specify/extensions/agentic/scripts/agentic.py"
$A lane --spec <spec>                         # which lane the spec is on, and why; nobody chooses it
$A brief --spec <spec> --gate G3 --write      # the reviewer's one page; also starts the clock for time-to-decision
$A report list                                # gates, waivers, trace, metrics, and whatever the other extensions add
$A report gates                               # who is needed next
$A report all --out reports --html            # every view as files, and one page
$A audit-pack --spec <spec> --write           # the evidence pack a release is approved with (Regulated)
$A audit-pack --from 2026-10-01 --to 2026-12-31 --out pack   # every release in a range, as files with hashes
```

The evidence pack supports an audit. It does not certify compliance with any law, regulation or standard, and it says so on its first line.
