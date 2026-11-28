# A programme's release waits for its children

- **Phase and date:** Phase 12, after the live test on HealthQCopilot; 2026-11-28 (UTC)
- **Upstream and reference:** github/spec-kit `v1.4.3`; `docs/design/programme-view.md` (PRG-1 to PRG-12); MAP-14 and `CK-PROGRAMME`
- **Requirement IDs covered:** PRR-1 to PRR-8, new with this document. They add one check, `CK-PROGRAMME-RELEASE`, and make `CK-PROGRAMME` fail where it stopped (PRR-8). No gate is added, and no rule about who approves changes: the check judges a parent's release record against the records of its children
- **Assumptions:**
  1. The Phase 12 report lists, as decision 6 that is the owner's to change: "A parent's gate does not wait for its children. The view of a programme adds no rule. The other way is a check that holds a parent's release until each child has passed its own." On 2026-11-28 the owner said to take the other way.
  2. A spec's release is its gate G7. Programmes are checked in Standard and Regulated, where `CK-PROGRAMME` runs, and both profiles ask for G7.
  3. A child in another repository is judged by that repository's own checks. The parent reads its records only as the pinned commit holds them (PRG-5). That repository's `CK-GATE-RECORD` holds the order of its gates, so of such a child the parent asks only that its last gate is approved there.
- **Unverified:** nothing here has read another repository on GitHub. The three reading methods of the adapters (PRG-11) have met only answers written by hand. Whether a pipeline's own token may read the other repository depends on that repository; see PRR-4

## Why

A programme spec plans a change across several specs, here or in other repositories: a parent, its children, a shared contract, and a rollout order. Until now the parent's page showed where each child stands, and nothing held the parent: its release could be approved while a child had not passed its own gates. The owner asked for the parent's release to wait.

## Requirements

| ID | Requirement |
|---|---|
| PRR-1 | A new check, `CK-PROGRAMME-RELEASE`, in the profiles that run `CK-PROGRAMME`. For each spec whose front matter has `programme` and whose G7 has a decision record that approves it, every child has to have passed its own gates. A parent whose G7 has no approving record is not looked at: the check holds the release and nothing before it. |
| PRR-2 | A child in this repository has passed when every gate it needs, in this project's profile and on its own lane, has a decision record that approves it. The finding names the child and each gate that has none, with what is recorded for it. A child whose spec folder does not exist has not passed, and nor has an entry under `children` that names no spec. |
| PRR-3 | A child in another repository has passed when, at the commit the parent pins it to, it has a decision record that approves its last gate: G7 where that repository's `kit.yml` names Standard or Regulated, G5 where it names Lite. The record names the child and that gate. The check reads that repository through the enforcement adapter's `commit_at` and `file_at`, as the parent's page does (PRG-5, PRG-11), and takes from there the profile and the decision, each only where it is one of the kit's own words (PRG-7). |
| PRR-4 | Where a child in another repository cannot be read (the repository, the commit, its `kit.yml` or its record), the release has not been shown to wait for it: the check fails, and the finding says what could not be read. So does a child that is not pinned to a commit, whose repository is not named as `owner/name`, or whose name is not the plain name of a folder; the adapter is not asked about those. For a child it is asked about, the adapter is asked at most three things: the commit, `.specify/agentic/kit.yml` and `.specify/agentic/decisions/<child>/<gate>.yml` at that commit. |
| PRR-5 | A decision record that rejects a gate does not pass it. One that approves with conditions does. |
| PRR-6 | The check has the self-test's two fixtures: the sample passes, and with the sample's spec made a parent whose G7 is approved and whose child does not exist, it fails. |
| PRR-7 | `docs/design/programme-view.md` and the Phase 12 report say that decision 6 is taken the other way: the parent's release waits; the view itself still adds no rule. `docs/limits.md` says that the check reads another repository with the pipeline's own credential, which a private repository may refuse, and that the release then stays held. |
| PRR-8 | `CK-PROGRAMME` fails, and does not stop, where the `programme` entry is not a mapping, where `children` or `rollout` is not a list, where the shared contract is not a name, and on an entry under `children` that is not a mapping with the key `spec`. Before this, such an entry stopped the whole `check` run with a Python error. |

## Acceptance criteria

- **AC-001** (verifies PRR-1): Given a parent with two children in this repository, both with every gate approved, and the parent's G7 approved, Then `CK-PROGRAMME-RELEASE` passes. Given the parent's G7 not recorded, and a child with no record at all, Then it passes too.
- **AC-002** (verifies PRR-2, PRR-5): Given the parent's G7 approved and a child whose G5 is rejected and whose G6 and G7 have no record, Then the check fails, names the child and those three gates. Given a child whose folder does not exist, Then it fails and says so. Given a child whose G7 approves with conditions and every other gate approves, Then that child has passed.
- **AC-003** (verifies PRR-3): Given a child in another repository whose pinned commit holds `kit.yml` with the Standard profile and an approving record for G7, Then it has passed. Given the same commit with no G7 record, Then the check fails and names the repository, the commit and G7. Given a Lite repository and an approving record for G5, Then it has passed.
- **AC-004** (verifies PRR-4): Given another repository that cannot be read, and a commit it does not hold, Then the check fails and says so with the reason. Given a child pinned to a branch name, a repository not named as `owner/name`, and a child's name that is a path, Then the check fails without asking the adapter. Then for a readable child the adapter was asked for the commit, `kit.yml` and the one record, and nothing else.
- **AC-005** (verifies PRR-6): Then the self-test passes on the sample and fails on the fixture, and `CK-SELFTEST` finds fixtures for the new check.
- **AC-006** (verifies PRR-7): Then the three documents say what PRR-7 says.
- **AC-007** (verifies PRR-8): Given a `programme` entry that is a word, a `children` entry that is a word, a child entry that is a word, a `rollout` that is a number and a contract that is a list, Then `CK-PROGRAMME` fails each and names what is wrong, and `CK-PROGRAMME-RELEASE` neither stops nor passes a release over them.

## What this does not do

- It does not hold any gate before the parent's release.
- It does not judge the reviews behind a child's records in another repository. That repository's own checks do.
- It does not move a child's pin. Moving it is a person's decision, as PRG-6 says.

## Sources

1. `docs/phase-reports/phase-12-features.md` of this repository, "Decisions that are the owner's to change", decision 6.
2. `docs/design/programme-view.md` of this repository, PRG-5, PRG-7 and PRG-11.
