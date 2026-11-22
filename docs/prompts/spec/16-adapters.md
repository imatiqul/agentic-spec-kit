# Adapters — platform and technology bindings

The only spec file where products and vendors are named. Each adapter binds neutral
rules to one platform and states what it cannot enforce. Adding a platform means
adding an adapter, not editing the rules.

Every adapter documents: rules it binds, setup an administrator must do, what stays
convention-only, and its own passing and failing fixtures (TRC-17).

## Upstream
- ADP-1 [0.1] github/spec-kit at the pinned tag (charter D6). Delivery shape is
  extension + preset + bundle on unmodified upstream unless the upstream audit proves a core
  change is unavoidable. Upstream and community components are attributed.
- ADP-2 [0.1] Community extensions are dependencies only after their source has
  been read and the review recorded (charter D7).

## Enforcement channel (binds GOV-6, GOV-7, GOV-8)
- ADP-3 [0.1] GitHub first: pull request reviews, CODEOWNERS and branch protection
  are the trust anchor. The adapter documents required repository settings and
  reports when they are absent.
- ADP-4 [later] The interface must allow GitLab and Azure DevOps adapters without
  changing governance rules.

## Data engines (binds CHG-1 to CHG-5)
- ADP-5 [0.2] PostgreSQL.
- ADP-6 [0.2] Qdrant, the vector store the reference system uses, as the first
  non-relational engine.
- ADP-7 [0.2] A written guide for adding an engine adapter.

## Contract formats (binds CHG-6 to CHG-9)
- ADP-8 [0.2] OpenAPI and GraphQL first; gRPC and AsyncAPI where the reference
  system or the fixture uses them.

## Discovery sources (binds MAP-5)
- ADP-9 [0.2] .NET solutions and project references, package manifests, ORM
  contexts and migrations, front-end module federation configs, infrastructure as
  code, and CI workflows. Only what the reference system and the fixture need.

## Agent runtimes (binds AGT-1, AGT-8, AGT-10)
- ADP-10 [0.3] Claude Code subagents.
- ADP-11 [0.3] GitHub Copilot custom agents.
- ADP-12 [0.3] Sequential single-agent mode, available on any supported agent.
- ADP-13 [0.3] Each runtime adapter states which allow-lists it enforces natively
  and which fall back to the post-run diff check.

## Domain packs (binds GOV-13 Regulated, TRC-16)
- ADP-14 [0.1] HIPAA: mandatory spec sections mapped to specific Security Rule
  safeguards; classified data means protected health information; the agreement in
  CHG-14 is a business associate agreement. The pack states that it is an
  engineering aid, not legal advice or a compliance certification.
- ADP-15 [0.1] A written guide for adding a domain pack.

## Work trackers (binds TRC-15)
- ADP-16 [0.4] GitHub Issues and Projects, and Azure DevOps Boards. The repo stays
  the source of truth; trackers are views. Superseded by ADP-18.

## Outbound connections (binds PIP-3, PIP-4, NTF-6)
- ADP-17 [0.6] One transport carries everything that leaves the repository: https
  only, a short bounded retry, and replaceable in tests by a recorded script. No
  adapter test opens a network connection.

## Requirement sources (binds INT-1, NTF-4)
- ADP-18 [0.6] Azure DevOps Boards, Jira Cloud, ClickUp, GitHub Issues and Projects,
  and documents on disk (Markdown, text, HTML, CSV, JSON). An exported or pasted
  Claude artifact comes in as a document. Each adapter fetches work items and posts
  one note on a work item, once.

## Notification channels (binds NTF-4)
- ADP-19 [0.6] Slack incoming webhooks, Microsoft Teams Workflows webhooks with an
  Adaptive Card, and SMTP email.

## CI/CD systems (binds PIP-1, PIP-5)
- ADP-20 [0.6] GitHub Actions, Azure Pipelines and GitLab CI, each with a template
  that says how the platform keeps secrets from a proposed change, and a written
  contract for any other system. Reading approvals stays bound to ADP-3 until
  ADP-4 is built.

## Agent tool configurations (binds AGT-20)
- ADP-21 [0.4] The MCP server configuration files of Claude Code, Cursor, VS Code,
  Gemini CLI, Kiro and Codex.
