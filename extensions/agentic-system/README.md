# agentic-system (slice 0.2, part 1 — system map and impact)

Adds a system map, discovery, impact analysis and eleven checks to the `agentic` extension.
Requires `agentic` to be installed first.

```bash
specify extension add --dev path/to/agentic-spec-kit/extensions/agentic-system
python .specify/extensions/agentic/scripts/agentic.py map discover --write   # drafts system-map/map.draft.yml
python .specify/extensions/agentic/scripts/agentic.py map validate
python .specify/extensions/agentic/scripts/agentic.py impact --spec <spec> --write
```

Discovery adapters in this slice: .NET projects, Node workspaces, Docker Compose, .NET Aspire app hosts and
contract files. It does not find events, external services or AI components; add those by hand as `assumed`.
The change packs for data stores, contracts and shared components arrive in part 2.
