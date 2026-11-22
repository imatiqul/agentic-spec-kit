# Connected delivery — running in a pipeline and telling people

Owns how the kit runs without a person at the keyboard and how people learn that
something needs them. CI systems, chat tools and mail are adapters
(`16-adapters.md`). Nothing here changes who decides (`10-governance.md`).

## Pipelines
- PIP-1 [0.6] One command runs every check with no prompt and no input, and exits 0
  for pass, 1 for fail, 2 for could not run. Any system that can run a command can
  run the kit.
- PIP-2 [0.6] The same command reports where every spec stands at each gate and
  what changed since the base, as text for people and as data for tools.
- PIP-3 [0.6] A pipeline file holds no secret. Secrets are named in configuration
  and supplied by the pipeline's secret store.
- PIP-4 [0.6] Connection settings are read from the base branch when the pipeline
  runs, so a change cannot send a credential to a new address.
- PIP-5 [0.6] No job that a proposed change can alter reads a tracker or
  notification credential. No step that runs an agent reads one either.
- PIP-6 [0.6] A pipeline may mirror reviews into decision records. A record is
  written only when the review carries the gate's line for the evidence as it
  stands, comes from a person, and every role the gate needs is covered. Mirroring
  creates no approval: the approval checks still judge the review itself.
- PIP-7 [0.6] Fetched requirements arrive as a proposed change for a Product Owner
  to review. The pipeline never writes them to the default branch.

## Notifications
- NTF-1 [0.6] An event is a fact read from the repository: a gate is ready (the
  checks pass and the next gate is undecided), a decision was recorded, a check
  failed, a change was released, a requirement arrived, a likely duplicate was
  found, a source changed, a date is close.
- NTF-2 [0.6] A notification carries identifiers, a status and a link. It never
  carries the text of a requirement, a spec or a piece of evidence.
- NTF-3 [0.6] A project may reword a notification using a fixed set of fields. A
  check fails any other field.
- NTF-4 [0.6] Routes say which events go to which channels. One channel is a note
  on the work item the spec came from.
- NTF-5 [0.6] An event is announced once. Its key is stable for the same state, a
  ledger remembers what was sent, and a work-item note carries a marker that is
  looked for before posting.
- NTF-6 [0.6] A notification never changes a gate, and a reply to one is not an
  approval. A delivery that fails is reported and does not fail the checks. No
  error message contains a secret.
