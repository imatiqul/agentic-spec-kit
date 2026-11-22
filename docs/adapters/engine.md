# Adding a data-engine adapter (ADP-7)

**Assumptions.** You know the engine and its migration tooling. The kit never connects to a database: an
adapter reads files, and CI applies migrations on a throwaway instance.

An engine adapter lives in `extensions/agentic-system/scripts/agentic_kit_system/engines.py` and answers
three questions about a store whose map node says `engine: <id>`.

| Question | Function | Used by |
|---|---|---|
| Which sections must the data-change plan have? | `family`, which selects the headings | `CK-DATA-PLAN` |
| How risky is this migration? | `classify(path, text) -> [(class, reason)]` | `CK-DATA-CLASS`, `change classify` |
| Was this migration written for another engine? | `foreign(path, text) -> [marker]` | `CK-MIGRATION-ENGINE` |

For engines whose changes are not files (vector stores, caches), `declared` maps a change kind the plan
states (`changes: [{kind: change-embedding-model}]`) to a class.

## The four classes (CHG-2)

| Class | Meaning | What the plan must then contain |
|---|---|---|
| `additive` | Only new objects | The standard sections |
| `backward-compatible` | Existing objects change in a way the previous application version tolerates | The standard sections |
| `breaking` | The previous application version can fail | `Expand, migrate, contract`, across releases |
| `destructive` | Data is removed | `Restore test`, `restore_evidence`, and the Data Owner's approval at G3 |

Return `unrecognised` for anything you cannot classify. It is shown to the reviewer as "check by hand".
Never guess downward: an adapter that calls a column drop additive is worse than no adapter.

## Steps

1. Add the engine to `FAMILIES` (`relational`, `vector`, `document`, `cache`, `search`). That alone gives its plans the right headings.
2. Write `classify` and, where another engine's dialect is a realistic mistake, `foreign`. Register an `Engine` in `ENGINES`.
3. Add tests to `tests/test_change.py`: one statement per class, a commented-out destructive statement, and one foreign marker.
4. Say in the pull request what the adapter does not detect.

## What CI must do

`CK-MIGRATION-ENGINE` and `CK-MIGRATION-DRIFT` read `specs/<spec>/evidence/migration-run.yml`. A CI job
writes it after applying the migrations on the engine and major version the map states for the store:

```yaml
# Example job steps. Pin the image to a digest and the actions to commit SHAs in your repository.
services:
  db:
    image: postgres:16.4@sha256:<digest>
    env: {POSTGRES_PASSWORD: throwaway}      # a throwaway instance; never a real database
steps:
  - run: <apply every migration>             # e.g. dotnet ef database update
  - run: <compare the model with the migrations>   # e.g. dotnet ef migrations has-pending-model-changes
  - run: >
      python .specify/extensions/agentic/scripts/agentic.py run migration --spec "$SPEC"
      --engine-version 16.4 --result pass --model-drift none
```

The record stores a hash of each migration file. Editing a migration afterwards invalidates it.

## Shipped adapters

| Engine | Reads | Does not detect |
|---|---|---|
| `postgresql` | `.sql` files statement by statement, including inside `DO` blocks; EF Core migrations (`Up` only) | Data-dependent risk (table size, lock time); SQL built at run time; changes made outside migrations |
| `qdrant` | Changes declared in the plan; `delete_collection` and `recreate_collection` calls in listed files | Any other change made in code, such as a new vector size passed as a variable |
