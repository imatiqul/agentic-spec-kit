# Contract-format adapters (ADP-8)

**Assumptions.** A contract is a file in the repository, named by its system-map node (`path:` or the
node's `evidence`). Adapters read two versions of that file; they never call a running service.

Adapters live in `extensions/agentic-system/scripts/agentic_kit_system/contracts.py`.

| Method | Answers | Used by |
|---|---|---|
| `matches(path, text)` | Is this file mine? | all |
| `version(text)` | The contract's version | `CK-CONTRACT-VERSION` |
| `normal(text)` | A form that ignores comments and layout, to tell a real change from an edit | `CK-CONTRACT-VERSION`, `CK-CONTRACT-CONSUMER` |
| `breaking(old, new)` | Changes that can break a consumer | `CK-CONTRACT-BREAK`, `contract diff` |
| `deprecated(text)` | Deprecated elements, each with its removal date and migration path if stated | `CK-DEPRECATION` |
| `surface(text)` | The operations or fields offered | `CK-CONTRACT-DRIFT` |

## What the shipped adapters report as breaking

| Format | Reported | Not reported |
|---|---|---|
| OpenAPI 3 and Swagger 2 | Removed path, operation or response status; removed response content type; parameter or request property newly required; request body newly required; type change; removed response property; response property no longer guaranteed; request enum value removed | Semantic changes with the same shape; tightened `pattern`, `maxLength` or numeric bounds; header and security-scheme changes; `oneOf`/`anyOf`/`allOf` composition |
| GraphQL SDL | Removed type, field or enum value; field or argument type change (a field becoming non-null, or an input becoming nullable, is allowed); removed argument; new required argument or input field | Directive changes other than `@deprecated`; union and interface membership; schemas split with `extend` across files |

Version: OpenAPI uses `info.version`. GraphQL has no version field, so the adapter reads a header comment
`# version: 1.4.0`, or the map node's `version`.

Deprecations: OpenAPI uses `deprecated: true` with `x-sunset: <date>` and `x-migration: <text>`. GraphQL
uses `@deprecated(reason: "Removed 2027-01-01; use newField")`. Either can instead be recorded on the map
node under `deprecations: [{element, sunset, migration}]`.

gRPC and AsyncAPI have no adapter yet: neither the reference system nor the fixture uses them. A changed
`.proto` or AsyncAPI contract makes `CK-CONTRACT-BREAK` report "not run", which fails the run. It is never
reported as passed.

## Drift between the contract and the code (CHG-9, TRC-9)

Each contract node says how drift is caught:

```yaml
drift: {generated: build/openapi.generated.json}   # CI generates this from the code; the kit compares the two
drift: {mode: design-first}                         # the contract is the source; contract tests catch drift
```

With `generated`, CI must produce the file before the checks run. If it is absent the check is "not run".

## Adding a format

1. Write a class with the six methods above and add it to `ADAPTERS`.
2. Add tests: one breaking change per rule you claim, and one compatible change that must not be reported.
3. List what it reports and what it does not in the table above. Reviewers rely on the second column.
