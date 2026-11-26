# The conversation behind a change

- **Phase and date:** Phase 12 (features), proposal 3 of the Phase 12 review; 2026-11-26
- **Requirement IDs covered:** CNV-1 to CNV-14, new with this document. One check is added, `CK-CONVERSATION`. It is registered under INT-2 and INT-7, the two requirements of `docs/prompts/spec/17-product-truth.md` that it carries further: the as-built requirement map is made from the IDs in that folder, and the CNV IDs are not there
- **Assumptions:**
  1. The owner said on 2026-11-26 to build the features of the Phase 12 review. This is its proposal 3.
  2. Each tracker answers as its published reference says. The three requests for comments were read on 2026-11-26: GitHub's and Azure DevOps's from their reference pages, Jira's from Atlassian's OpenAPI document, because its reference page could not be read without a browser.
  3. The page of a change, which calls `CHANGESET_HOOKS`, is built by another feature of this phase. Only the list of hooks is in this branch.
- **Unverified:** no adapter has read its live service: every comment in the tests is a recorded response. Nothing here has run on Windows. The section for a change's page was tried by calling its function; it has not been seen on a page.

## Why

The kit keeps the request that started a change. `.specify/agentic/intake/<id>.yml` holds where the request came from, its text and a hash of that text, and `specs/<spec>/origin.yml` ties a spec to it. The discussion is not kept. The tracker adapters read an item's comments only to find the kit's own marker. So what was agreed in a thread is recorded nowhere, and nobody notices when the thread moves on after the spec was written.

## What it does

| ID | Requirement |
|---|---|
| CNV-1 | `origin.yml` may hold `conversation`: `summary` (a few lines of prose written for the change: what was asked, by whom, what was agreed, what was left open), `links`, `people` (ids or names as given), `captured_on`, `captured_by` and `confirmed_by`. `product conversation --spec <spec>` prints what is recorded. With `--summary` and `--captured-by` it builds the block anew, with `--link` and `--person` as often as needed, and prints it; with `--write` it writes it, and keeps what else `origin.yml` holds. `links` are the links given and the thread links on the intake records that `origin.yml` lists. `captured_on` is the day of the run. A spec that does not exist or is sealed is not written to. |
| CNV-2 | The summary and each name under `people` go through the screen that the text of an incoming request goes through: the built-in patterns and those of `intake.screen` in `kit.yml`. What the screen finds is replaced by `[removed: <kind>]` and counted, and the command reports the counts. It is never written. |
| CNV-3 | A link is an `http` or `https` address. One that is not, one that carries a user name or a password, and one in which the screen finds something is refused: the command says which link and what kind of value, does not repeat the address, writes nothing and ends with 2. The card-number pattern is not used on a link: an address often holds a long number that is none. |
| CNV-4 | `confirmed_by` is empty until `--confirmed-by <person>` is given, and the person has to be listed in `roles.yml`. Given alone, it is set on the block that is there. A new summary empties it, unless the same command gives it. The command says that the kit cannot tell who typed it, and that `origin.yml` is part of the evidence of the first gate. Nothing else in the kit sets it. |
| CNV-5 | `intake add --thread <url>` puts a link on an intake record, under `threads`. With `--title` that is the record the command adds or refreshes. Without `--title` it is the record that `--platform` and `--key` name: its text, hash and status stay as they are, and a record that does not exist ends the command with 2. CNV-3 holds for the address. A later fetch keeps `threads`. |
| CNV-6 | For each item of a Jira, Azure DevOps or GitHub source, `connect fetch` reads the item's comments and stores `discussion: {comments, hash, fetched}` on the intake record: the count, a hash over the ids, the authors and the screened texts of the comments ("What is kept, and where", below), and the day. A GitHub Projects item that is an issue is read through the issue. Nothing else of a comment is stored. A draft project item, a ClickUp task and a document get no `discussion`. |
| CNV-7 | A note that the kit posted on the item itself is left out of the count and of the hash. It is known by its form: it begins with `agentic-spec-kit: ` and ends with `(ref agentic:<key>)`. |
| CNV-8 | Comments are read 100 at a time, and at most 2,000 of one item. Where the last page that may be read is full, the digest covers what was read and carries `partial: true`, and `CK-CONVERSATION` says so in a note. A request for comments that fails stops the fetch, as a failed request for items does. The comments of an item are read before anything of its record is written, so that record stays as it was. |
| CNV-9 | A later fetch that finds the same hash changes nothing. One that finds another hash on a record nobody has acted on (status `new`) replaces the digest. On any other record it leaves `comments`, `hash` and `fetched` as they are and sets `discussion.latest: {comments, hash, fetched}` beside them, as `latest` is set for an item whose text changed. Each row that `fetch` returns says which: `discussion` is `new`, `unchanged`, `updated` or `moved`, and null where the source has no comments to read. The text output names each record whose discussion moved and counts them, and `intake list` marks them. `--dry-run` reads the comments, writes nothing, and says what a fetch would do. |
| CNV-10 | `CK-CONVERSATION` fails for a record whose `discussion.latest.hash` differs from `discussion.hash`, until `discussion.acknowledged` holds that hash, an `action` (`amend` or `ignore`), a reason, and under `decided_by` a person who holds the Product Owner role: the rule `CK-INTAKE-DRIFT` has for `acknowledged`. A record with status `new` or `rejected` is left alone. No command of the kit writes `acknowledged`: a person does. |
| CNV-11 | `CK-CONVERSATION` also fails when what is kept is not what CNV-1 to CNV-6 write: a `conversation` with no summary, or that does not say who wrote the summary and on which day; a summary or a name in which the screen finds something; a link or a thread link that CNV-3 refuses; a `confirmed_by` that names nobody in `roles.yml`; a `discussion` that is not a count and a hash. |
| CNV-12 | The brief for a spec's first gate (G1, or G4 where the fast lane folds G1 into it) has a section "The conversation behind it", of at most seven lines: whether a person has confirmed the summary, who wrote it and when, its first lines, the links and the people. A `conversation` that has links and no `confirmed_by` is not a failure. The brief says that no person has confirmed the summary, and `CK-CONVERSATION` adds a note for as long as the first gate is open. Where no summary is recorded and a linked intake record has comments or a thread link, the section is one line that says so. Where nothing is recorded there is no section. |
| CNV-13 | `CHANGESET_HOOKS` gets a section "The conversation behind it" for a change's page: the confirmation, who wrote the summary and when, the whole summary, the links and the people; and for each linked intake record its thread links, the count and the day of its digest, whether the discussion moved, and who acknowledged that. Where nothing is recorded the section says so. |
| CNV-14 | The self-test holds one fixture that `CK-CONVERSATION` passes and one that it fails. The sample project has a digest on its intake record and a confirmed summary. In the broken one the discussion moved after the spec was written, and nobody acknowledged it. |

## What is kept, and where

In `specs/<spec>/origin.yml`, written by `product conversation`:

```yaml
conversation:
  summary: |-
    pat asked for a greeting that uses the person's name. sam agreed to take the name from the account.
    Left open: what to say when the account has no name.
  links:
  - https://example.atlassian.net/browse/DEMO-1
  people:
  - pat
  - sam
  captured_on: '2026-11-26'
  captured_by: spec-author
  confirmed_by: ''
```

On the intake record: `threads` by `intake add --thread`, `discussion` by `connect fetch`, and `acknowledged` by a person.

```yaml
threads:
- https://chat.example.com/archives/C1/p1764150000000100
discussion:
  comments: 2
  hash: sha256:…
  fetched: '2026-11-21'
  latest: {comments: 3, hash: sha256:…, fetched: '2026-11-26'}
  acknowledged:
    hash: sha256:…            # the hash under `latest`
    action: ignore            # or amend
    reason: The new comment thanks the team and asks for nothing
    decided_by: {reviewer: alice, role: product-owner}
```

**The hash.** Each comment gives one line: a JSON list of three strings, with no space between them and with every character outside ASCII written as a `\u` escape. They are the comment's id; its author, as the tracker names the account (GitHub: the login; Jira: the account id; Azure DevOps: the identity's id); and the sha256 of the comment's text after the screen. The text is the comment as plain text, with CRLF read as LF, and with the white space at the end of each line and the empty lines at both ends dropped. The lines are sorted and joined by line feeds, and the line `agentic-discussion/1` is put in front. The hash is the sha256 of that. So the order in which a tracker returns comments does not matter, and a comment that was edited or deleted changes the hash, as a new one does.

**The requests**, one more for each item and one more for every 100 comments:

| Tracker | Request |
|---|---|
| Jira Cloud | `GET {base_url}/rest/api/3/issue/{key}/comment?startAt=N&maxResults=100` |
| Azure DevOps | `GET https://dev.azure.com/{org}/{project}/_apis/wit/workItems/{id}/comments?$top=100&api-version=7.1-preview.4`, then with `&continuationToken=…` |
| GitHub | `GET /repos/{repo}/issues/{n}/comments?per_page=100&page=N` |

## Acceptance criteria

- **AC-001** (verifies CNV-1): Given a spec whose `origin.yml` lists one intake record that has a thread link, When `product conversation` runs with a summary, a link, two people and `--captured-by`, Then without `--write` no file changes; with `--write`, `origin.yml` holds the six fields, the given link and the thread link are under `links`, `confirmed_by` is empty, and what the file held before is still there; and the command with no other option prints the summary. For a spec that is sealed nothing is written and the command ends with 2.
- **AC-002** (verifies CNV-2): Given a summary that holds a national id and a password, a name that holds a record number, and a pattern of the project's own in `kit.yml`, When the block is written, Then each value is replaced by `[removed: <kind>]`, the command prints the counts, and no file of the project holds any of the values.
- **AC-003** (verifies CNV-3): Given a link with a token in its query, one with a user name and a password, and one that is no `http` or `https` address, When the command runs with any of them, Then it ends with 2, `origin.yml` is unchanged, and the output does not hold the token or the password. Given a link with a long number that passes the card test, Then the link is kept as it was given.
- **AC-004** (verifies CNV-4): Given a recorded summary, When `--confirmed-by` names someone who is not in `roles.yml`, Then nothing is written and the command ends with 2. When it names a listed person, Then `confirmed_by` is that person, and the output says that the kit cannot tell who typed the command. When a new summary is then written, Then `confirmed_by` is empty again.
- **AC-005** (verifies CNV-5): When `intake add --title … --thread <url>` runs, Then the new record lists the link. Given a record that was fetched and specified, When `intake add --platform jira --key DEMO-1 --thread <url>` runs, Then the link is added and the record's text, hash and status are what they were. A record that does not exist, and a link that CNV-3 refuses, end the command with 2. Given a record that nobody has acted on, When a fetch brings new text for it, Then its thread link is still there.
- **AC-006** (verifies CNV-6, CNV-7): Given recorded responses of Jira, of Azure DevOps and of GitHub that each hold one item, two comments by people and one note of the kit, When `fetch` runs, Then the record holds `discussion` with `comments: 2`, the day, and the hash that the formula above gives for the two comments, worked out in the test; and the requests are the ones in the table above.
- **AC-007** (verifies CNV-6): Given a GitHub project with an issue and a draft, When `fetch` runs, Then the issue's record has a digest that was read through the issue, and the draft's record has no `discussion`. Given a ClickUp source and a document source, Then no comment is asked for and no record has a `discussion`.
- **AC-008** (verifies CNV-8): Given more comments than one page holds, When `fetch` runs, Then each tracker is asked for the next page and the count is the whole number. Given a limit of one page and a page that is full, Then the digest carries `partial: true` and `CK-CONVERSATION` passes with a note that names the record. Given a request for comments that fails, Then `fetch` ends with 2 and the item's record is byte for byte what it was.
- **AC-009** (verifies CNV-9): Given a record with a digest, When a second fetch finds the same comments, Then the row says `unchanged` and the file does not change. Given one more comment on a record with status `new`, Then the digest is replaced and there is no `latest`. Given one more comment on a record that was specified, Then `discussion.latest` holds the new count and hash, the first count and hash are still there, the row says `moved`, the output of `connect fetch` names the record, and `intake list` marks it. With `--dry-run` the row says `moved` and the file does not change.
- **AC-010** (verifies CNV-10): Given a specified record whose discussion moved, When `CK-CONVERSATION` runs, Then it fails and names the record and both counts. When `acknowledged` names another hash, gives no reason, or is decided by someone who is not a Product Owner, Then it still fails. When a Product Owner's acknowledgement names the hash under `latest`, Then it passes; and when the discussion moves again, it fails again. A rejected record whose discussion moved does not fail it.
- **AC-011** (verifies CNV-11): Given an `origin.yml` edited by hand so that the summary holds a password, or `confirmed_by` names an agent, or a link carries a token, or `captured_by` is missing; or an intake record with a thread link that carries a token, or with a `discussion` that has no hash, When `CK-CONVERSATION` runs, Then it fails and says which.
- **AC-012** (verifies CNV-12): Given a spec at its first gate whose `conversation` has a link and no `confirmed_by`, When the brief for G1 is built, Then it holds the section, the summary and the words that no person has confirmed it, and it is no longer than a page; `CK-CONVERSATION` passes with a note that names the spec; and the brief for G3 has no such section. When a listed person has confirmed, Then the brief names that person and the note is gone. Given a spec with no `conversation` whose intake record has comments, Then the section is the one line. Given a spec with neither, Then the brief has no such section.
- **AC-013** (verifies CNV-13): Given the sample project after its discussion moved, When the function registered in `CHANGESET_HOOKS` is called for the spec, Then it gives one section "The conversation behind it" that holds the summary, who confirmed it, the links, the people, both counts of the digest and that nobody has acknowledged the move. Given a spec with nothing recorded, Then the section says that no conversation is recorded.
- **AC-014** (verifies CNV-6, CNV-9): Given the fetches of AC-006 and a later fetch with one more comment, for all three trackers, with `connect fetch` run as a command, Then no file under the project holds the text of any comment or the name of any author, and neither does what the command printed.
- **AC-015** (verifies CNV-14): The fixtures of the product extension hold `CK-CONVERSATION`. On the sample project the check passes. On the broken one it fails, and the finding says that the discussion moved.
- **AC-016** (verifies CNV-6): The test of `fetch` in `tests/test_connect.py` passes with the request for comments added to its recorded responses and `discussion` added to the row it expects. Nothing else in that file changes.

## What it will not do

- Copy a thread into the repository. Of a comment it keeps nothing. Of a discussion it keeps a count and a hash, and of a conversation the few lines that someone wrote for the change.
- Read a chat system. A thread in Slack, Teams or mail is a link that a person gave, and the summary is written by whoever read the thread. The kit asks nothing of those services.
- Write the summary, or judge whether it is true to the thread. It shows who wrote it and whether a person has confirmed it.
- Confirm a summary or acknowledge a discussion that moved. Both are a person's to do. It cannot tell who typed `--confirmed-by`: the name is a line in `origin.yml`, which the review of the first gate covers.
- Say what changed in a discussion. A hash says that it is not what it was. A person reads the thread.
- Digest a ClickUp task, a document or a draft project item.
- Notice anything about an item that the source's query no longer returns. Such an item is not fetched again; that is so for its text today.
- Send a notification of its own. A failing `CK-CONVERSATION` is announced as any failing check is.
- Tell a note of the kit from a comment that a person wrote in the same form. Both are left out.
- Read more than 2,000 comments of one item.
- Keep a hash steady when the project changes its screen patterns: a comment that holds a value of the new kind then hashes differently, and the discussion counts as moved.

## Decisions made here that are the owner's to change

1. **A new check, `CK-CONVERSATION`, and not a wider `CK-INTAKE-DRIFT`.** The self-test keeps one broken fixture for each check, and a discussion that moved needs one of its own. The check also reads `origin.yml`, which `CK-INTAKE-DRIFT` does not. `CK-INTAKE-DRIFT` is unchanged. This branch then has 106 checks, where its base has 105.
2. The check is registered under INT-2 and INT-7, because the as-built map takes only the IDs of `docs/prompts/spec/`. Should the CNV requirements move into that folder, the check names them.
3. A summary that no person has confirmed is a note, in the brief and from the check. It does not fail.
4. Any person listed in `roles.yml` may be named under `confirmed_by`, not only a Product Owner: the one who was in the conversation knows best what was said. An acknowledgement takes a Product Owner, as it does for an item.
5. `--captured-by` has to be given with a summary. Nothing in the kit knows who is typing.
6. `origin.yml` is evidence of G1 and G2. So a summary that is written or confirmed after G1 was approved opens G1 again. The command says so when it writes.
7. The brief shows the section at the first gate only. It shows the first three or four lines of the summary; the whole of it is in `origin.yml`, which is evidence of the same gate.
8. The comments of every item are read at every fetch: one request more for each item. There is no setting that turns it off.
9. The author in the hash is the account as the tracker names it. On GitHub that is the login, so an account that is renamed changes the hash.
10. A link may be an `http` address. The card-number pattern is not used on links; every other pattern is, the project's own among them.
11. A row of `connect fetch --json` gains the key `discussion`.
12. The kit's own note is known by its form, not by the account that posted it. Finding out which account the pipeline's token belongs to would take one more request for each tracker.
