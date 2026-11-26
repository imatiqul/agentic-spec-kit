# A programme seen from its parent

- **Phase and date:** Phase 12 (features), proposal 7 of the report `phase-12-changeset-gap-analysis`, as step 2 of that phase reshaped it; 2026-11-26
- **Requirement IDs covered:** PRG-1 to PRG-12, new with this document. They add no check, no gate and no approval, and they change how no check judges. `CK-PROGRAMME` is as it was
- **Assumptions:**
  1. The owner said on 2026-11-26 to build the features of that report. Step 2 found that the kit already has programme specs (MAP-14, `CK-PROGRAMME`), and that what is missing is the view: a parent cannot see where its children stand. This document is that view and nothing more.
  2. A child in another repository is named as `owner/name`, on the same host and with the same sign-in as this project's own enforcement adapter. Until now no document of the kit said how such a child is named, and `CK-PROGRAMME` accepts any text there.
  3. GitHub answers as its REST reference says, read on 2026-11-26: "Get a commit", and "Get repository content" for a file and for a folder.
- **Unverified:** nothing here has read GitHub. What the GitHub adapter makes of an answer is tried only on answers written by hand from that reference. Nothing here has run on Windows. No project is known that has a child in another repository: the one programme in the reference example keeps all eight children in its own.

## Why

A programme spec is a parent with one child spec for each application or repository, a shared contract and a rollout order. `CK-PROGRAMME` checks that the parent names them. Nothing shows the parent's owner where the children stand. For a child in the same repository that takes one command for each child. For a child in another repository the kit reads nothing at all: the parent holds a commit id, and what that commit says about the child is for a person to look up.

The page of a change (`docs/design/changeset.md`) has a place for this. Other extensions add sections to it through a hook.

## What it does

| ID | Requirement |
|---|---|
| PRG-1 | The system extension adds one section to the page of a change, through `core.CHANGESET_HOOKS`. For a spec whose front matter has `programme`, the section is **The children of this programme**. For a spec whose front matter names a `parent`, it is **Part of a programme**. For any other spec the hook adds nothing, so that spec's page is what it was. |
| PRG-2 | **The children of this programme** names the shared contract and has one entry for each child, in the rollout order. A child that the rollout order leaves out comes after the others and is marked so. An entry that is not a mapping, or names no spec, gets a line that says so. |
| PRG-3 | A child in the same repository shows its title, its declared tier, and where it stands on the gate board: the gate that is open, or that every gate it needs is approved. A child whose folder does not exist is named as missing. |
| PRG-4 | A child in the same repository also shows its pull requests: those that hold one of its five newest commits, with the state of each. Where it has more commits the entry says how many were not asked about, and that the child's own page asks about them. Where the enforcement adapter cannot be read, the entry says that the pull requests could not be read, and why. |
| PRG-5 | A child in another repository shows the repository and the commit it is pinned to. From that commit, read through the enforcement adapter, it shows the child's declared tier and each gate that has a decision record there, with the decision. It says that these are records as that commit holds them, and that only the checks of the child's own repository judge the reviews behind them. |
| PRG-6 | For a child in another repository the entry says whether the pin is behind: whether the child's spec folder or its decision records are, at the head of that repository's default branch, something else than at the pinned commit. Where they are, it says which of the two changed, and that the parent's pin is for a person to move. |
| PRG-7 | Nothing but fixed words is copied from another repository onto the page: no title, no name of a person, no condition, no text of a review. A tier is shown only when it is one of the kit's four, a gate only when it is one of the kit's seven, and a decision only when it is one of the kit's three: `approve`, `approve-with-conditions` or `reject`. Anything else is shown as "not readable". So a file in another repository can put no instruction and no private text on this page. |
| PRG-8 | A child whose repository is not named as `owner/name`, or whose pin is not a commit id, is not asked about: the entry says what is wrong. A child's name that is not a plain folder name is refused in the same way. Nothing a spec's front matter holds can make the adapter ask for a path outside `specs/<child>/` and `.specify/agentic/decisions/<child>/` of the named repository. |
| PRG-9 | Where another repository, or the pinned commit in it, cannot be read, the entry says so with the reason, and the other entries are still shown. The command still ends with 0. A child that the pinned commit does not hold is named as missing there. |
| PRG-10 | **Part of a programme** names the parent with its title, the shared contract, this child's place in the rollout order and how many children there are. Where the parent's folder does not exist, or the parent does not list this spec, the section says so. |
| PRG-11 | Both enforcement adapters get three methods that only read. `commit_at(repo, ref)` gives the full id of a commit, and raises where the repository or the commit cannot be read. `file_at(repo, ref, path)` gives the text of a file at that commit, or nothing where the commit holds no such file. `folder_at(repo, ref, path)` gives the names in a folder at that commit, each with the id git has for it, or nothing where the commit holds no such folder; with an empty `ref` it reads the head of the default branch. The GitHub adapter asks `repos/{repo}/commits/{ref}` and `repos/{repo}/contents/{path}?ref={ref}` through the helper its other calls go through. The file adapter reads its stand-in file, under `repositories`. |
| PRG-12 | The section only reads. It writes no file, records nothing, fetches nothing with git, and asks the adapter through `pulls` and the three methods of PRG-11 alone. For a spec that is no parent and no child, the adapter is not asked at all. |

What the parent's page gains, for a programme with one child in each place:

```
## The children of this programme
Shared contract: `shop-orders-api`. 2 children, in the rollout order.
1. `002-orders-total` (this repository): A total on every order. Tier high. Open gate: G3. Pull requests: pull/12 (merged), pull/15 (open).
2. `004-billing-total` in `acme/billing`, pinned to `3f18fec`: tier high; recorded there at that commit: G1 approve, G2 approve-with-conditions. The pin is behind: the child's spec folder has changed on the default branch since. Moving the pin is a person's decision.

What is shown of another repository are its records as the pinned commit holds them. Only that repository's own checks judge the reviews behind them.
```

The stand-in file of the file adapter, for the tests and the demo:

```json
{"repositories": {"acme/billing": {"default": "<commit id>", "commits": {"<commit id>": {"<path>": "<text of the file>"}}}}}
```

## Acceptance criteria

The project in each criterion is a small Standard project made by the test, with a system map that has a contract node, a parent spec and two child specs, where a file plays GitHub.

- **AC-001** (verifies PRG-1): Given a spec that is no parent and no child, When its page is built, Then it has no section of this feature, and the adapter was not asked. Given the parent, Then the page has **The children of this programme** after the core sections; given a child, **Part of a programme**.
- **AC-002** (verifies PRG-2, PRG-3): Given a parent with two children in its own repository, one with G1 approved and one with no decision, Then the entries stand in the rollout order, each with its title, its tier and its open gate, and the section names the shared contract. Given a child that the rollout order leaves out, Then it comes last and is marked. Given a child whose folder does not exist, an entry that names no spec, and an entry that is a plain word, Then each has a line that says what is wrong.
- **AC-003** (verifies PRG-4): Given a child with seven commits and a stand-in file in which one pull request holds its newest commit and another its oldest, Then the entry names the first pull request with its state and not the second, and says that two commits were not asked about. Given a stand-in file that cannot be parsed, Then the entry says that the pull requests could not be read, and the page is still built.
- **AC-004** (verifies PRG-5, PRG-11): Given a child in `acme/billing` pinned to a commit that holds the child's spec with the tier `high` and decision records for G1 and G2, Then the entry names the repository, the pin cut to seven characters, the tier and the two gates with their decisions, and the section ends with the sentence about records and checks.
- **AC-005** (verifies PRG-6): Given the same child where the default branch's head holds the spec folder as the pin does, Then the entry says that the pin is current. Given a head whose spec folder differs, and given a head with one more decision record, Then the entry says that the pin is behind and which of the two changed.
- **AC-006** (verifies PRG-7): Given a pinned commit whose spec has a title and an owner that hold an instruction and a name, a tier that is no tier, a record for a gate `G9`, and a record whose decision is a sentence, Then none of those texts is on the page: the tier and the decision read "not readable", and the gate `G9` is not listed.
- **AC-007** (verifies PRG-8): Given a child whose repository is a web address, one whose pin is a branch name, and one whose name is `../../outside`, Then each entry says what is wrong, and the adapter was asked about none of them.
- **AC-008** (verifies PRG-9): Given a child in a repository the stand-in file does not hold, and one pinned to a commit it does not hold, Then each entry says that it could not be read, with the reason, the entry of a readable child beside them is whole, and the command ends with 0. Given a pinned commit that holds no folder for the child, Then the entry says that the commit does not hold it.
- **AC-009** (verifies PRG-10): Given a child of the programme, Then **Part of a programme** names the parent with its title, the contract, and "2 of 3". Given a spec that names a parent which does not list it, and one that names a parent with no folder, Then the section says so.
- **AC-010** (verifies PRG-11): Given answers written by hand in the form of GitHub's reference, When the GitHub adapter's three methods are called, Then `commit_at` gives the full id; `file_at` decodes the text of a file, also one with characters outside ASCII; `folder_at` gives each name with its id; a path that GitHub answers with "Not Found" gives nothing; and any other failure of the helper is raised. The requests are the two of PRG-11.
- **AC-011** (verifies PRG-12): Given the project as a git repository with everything committed, When the page of the parent and of a child is built, as text and as JSON, Then every ref, the state of the working copy and the bytes of the stand-in file are what they were.
- **AC-012** (verifies PRG-1): With only the core extension loaded, the page of a parent is built without this section, and with no error.

## What it will not do

- Judge a child. It shows the gate board's word for a child in the same repository, and for a child in another repository the records that a commit holds. Whether a review behind such a record would pass is for the checks of that repository.
- Hold a parent's gate until its children have passed theirs. Whether a programme may be released before each child is, is a rule, and this document adds none. It is listed below as a decision for the owner.
- Move a pin, or say that a pin must be moved. It says that the pin is behind.
- Show the pull requests of a child in another repository. The pin is one commit; what leads to it is on that repository's own page.
- Tell an unreadable repository from one that does not exist. GitHub answers both in the same words.
- Read a child on another host, or with another sign-in, than this project's enforcement adapter has.
- Read a file of more than one megabyte, or a folder with more than 1,000 names, in another repository. GitHub sends no content for the first and lists no more names for the second. A spec or a record that large reads as one that could not be read.
- Read more than one level. A child that is itself a parent is shown as a child, and its own page shows its children.
- Fail a spec whose child names its repository in another form. `CK-PROGRAMME` accepts any text there today, and it is not changed.
- Show on the page that is kept with `--write` anything else than on the printed one. A page kept in a public repository then holds the tier and the gate decisions of a child in a private one, where the sign-in could read it. No title and no name is among them (PRG-7).

## Decisions made here that are the owner's to change

1. **A view, and no rule.** A parent's gate does not wait for its children. The other way would be a check that fails a parent whose release gate is approved while a child has not passed its own.
2. **A child in another repository is named `owner/name`.** A web address or another host is not read.
3. **Only fixed words cross from another repository** (PRG-7). So the parent's page does not show such a child's title. The other way shows more and lets a file in another repository write on this page.
4. **"Behind" compares content, not history**: the ids git has for the child's two folders, at the pin and at the head of the default branch. A pin on a side branch whose folders differ from the default branch reads as behind as well.
5. **Five commits of each child in the same repository are asked about**, where the child's own page asks about fifty. With GitHub each commit is one request, and a programme may have many children.
6. **A child in another repository costs up to fourteen requests** each time the parent's page is built: one for the commit, three folders at the pin and two at the head, the spec, and up to seven records. Nothing is kept between two runs.
7. **The file adapter's stand-in file gains the key `repositories`.** What it held before is read as before.
