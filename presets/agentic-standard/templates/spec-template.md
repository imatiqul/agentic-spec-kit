---
spec: [###-feature-name]
tier_declared: [low | medium | high | critical]
owner_role: [a role from .specify/agentic/roles.yml]
principles: [P-#]            # principles from the constitution this spec serves
paths: []                     # code paths this spec owns, used for drift detection
---
{CORE_TEMPLATE}

## Acceptance Criteria *(mandatory — read by agentic-spec-kit)*

One line per criterion, each independently testable, each naming the requirement it verifies:

- **AC-001** (verifies FR-001): Given [state], When [action], Then [outcome].
- **AC-002** (verifies FR-001): Given [state], When [action], Then [outcome].

IDs are never renumbered or reused. Retire a criterion by striking it through, not by deleting it.
