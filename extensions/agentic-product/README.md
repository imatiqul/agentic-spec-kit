# agentic-product

Product truth for agentic-spec-kit (slice 0.5). Needs `agentic`. Uses `agentic-system` when it is installed.

Spec-driven projects collect a folder per feature. After a year nobody can say, from the specs, what the system does today, and agents read stale folders as if they were current. This extension keeps one living spec per capability and makes every change state its effect on it.

## How it works

| Step | What happens | Who |
|---|---|---|
| A requirement arrives | It becomes an intake record: source, screened text, hash | An adapter, or `intake add` |
| A spec is drafted | Likely duplicates are listed; wording is linted; a delta says what behaviour is added, modified or removed | Agent drafts |
| Gate G1 | The reviewer approves the spec, the delta, the duplicate decisions and the expected outcome as one piece of evidence | Product Owner |
| Release | `product merge` applies the delta to the living spec | Tool, never by hand |
| After release | `product archive` seals the change folder; the outcome is reviewed on its date | Tool; Product Owner |

## Checks

| Check | Fails when |
|---|---|
| CK-INTAKE-RECORD | A record's text was edited, holds personal data or a credential, or was closed without a reason and a Product Owner |
| CK-INTAKE-DRIFT | The work item changed at its source after someone acted on it, and nobody decided what that means |
| CK-REQ-QUALITY | A requirement still to be approved is vague, double, untestable or has an open question |
| CK-SPEC-SIZE | A spec still to be approved is too large to review |
| CK-GLOSSARY | A spec uses a synonym where a term was agreed |
| CK-DUPLICATE | A likely duplicate has no decision from a Product Owner before the first gate |
| CK-DELTA-VALID | A delta does not apply to the living spec, or cannot be tested |
| CK-CAPABILITY-COVERAGE | A change does not say how behaviour changes, or touches a component no capability describes |
| CK-LIVING-SPEC | A living spec differs from the replay of its merged deltas |
| CK-DELTA-MERGED | A released change was never merged |
| CK-SPEC-COLLISION | Two changes in flight alter the same requirement with no order between them |
| CK-ARCHIVE | A merged change is not sealed, or a sealed change was edited |
| CK-OUTCOME | A change states no expected result, or nobody looked after release |

## Commands

```
agentic.py product init [--write]
agentic.py intake add --title "..." [--body "..."]      |  intake list
agentic.py product specify --intake <id> --spec <spec> --write
agentic.py product duplicates --spec <spec> | --intake <id> | --title "..."
agentic.py product lint
agentic.py product delta --spec <spec> --capability <id> --write
agentic.py product merge --spec <spec> --write           |  product merge --adoption --approved-by <reviewer:role:pull/n#review-id> --write
agentic.py product archive --spec <spec> --write
agentic.py product catalog
agentic.py why <path>[:line]
```

## Limits you should know

- **Duplicate detection matches shared words, not meaning.** "Say hello" and "greet" score as unrelated. Agents and people add those candidates by hand; the kit then insists each one is decided.
- **The lint is a list of patterns.** It catches "should", "quickly" and two obligations in one sentence. It does not know whether a requirement is right.
- **Sealing does not delete anything.** Finished change folders stay in the repository; the kit keeps them unchanged and out of agent context packs.
- **Adopting on an existing system** starts with deltas under `.specify/agentic/product/adoption/` that describe what the system does today, merged once with a named Product Owner's approval. Coverage then grows with each change that touches an undescribed component.
