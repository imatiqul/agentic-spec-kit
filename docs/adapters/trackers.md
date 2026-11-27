# Requirement sources and notification channels

- **Phase and date:** slice 0.6, 2026-11-22
- **Requirement IDs covered:** ADP-17, ADP-18, ADP-19, INT-1, INT-2, NTF-2, NTF-4, NTF-5; and since 2026-11-26 CNV-6 to CNV-9 of `docs/design/conversation.md`
- **Assumptions:** each vendor's API behaves as its published reference says
- **Unverified:** the adapters for Jira, Azure DevOps and ClickUp, and every notification channel, have not been run against the live service. They are tested against recorded responses only (`tests/test_connect.py`). The GitHub adapter read a live repository for the first time on 2026-11-27; see "The first read of a live service". It has posted no note on a live issue

## What an adapter does

Three things, and nothing else:

1. **Fetch** work items and return them in one shape: key, title, body, link, revision, and optional type, priority, labels, state.
2. **Post one note** on a work item. The note carries a marker; the adapter looks for the marker before posting, so a note is never repeated.
3. **Read the comments** on one work item and return them in one shape: id, author, text. The adapters for Jira, Azure DevOps and GitHub do this; the others have nothing to read.

An adapter holds no state and writes nothing to the repository. `connect fetch` turns what it returns into intake records (`docs/design/schemas.md`), screening the text first. Of the comments it keeps a count and a hash on the record, and nothing else: no text and no author (`docs/design/conversation.md`).

## Endpoints used

Read from each vendor's reference on 2026-11-21 and 2026-11-22. If a vendor changes one, the recorded-response test for that adapter is the place to start.

| Platform | Fetch | Note | Authentication |
|---|---|---|---|
| Jira Cloud | `POST {base_url}/rest/api/3/search/jql` with `jql`, `fields`, `maxResults`, then `nextPageToken`. The older `/rest/api/3/search` has been removed. | `GET` then `POST {base_url}/rest/api/3/issue/{key}/comment`; the body is an Atlassian Document Format document | Basic, account email and API token |
| Azure DevOps Boards | `POST https://dev.azure.com/{org}/{project}/_apis/wit/wiql?api-version=7.1`, then `GET .../_apis/wit/workitems?ids=...&api-version=7.1` in groups of 200 | `GET .../_apis/wit/workItems/{id}/comments?api-version=7.1-preview.4`, `POST ...?api-version=7.0-preview.3` with `{"text": ...}` | Basic, empty user and a personal access token |
| ClickUp | `GET https://api.clickup.com/api/v2/list/{list}/task?page=N&include_closed=false` until `last_page` | `GET` then `POST https://api.clickup.com/api/v2/task/{id}/comment` with `comment_text` | `Authorization: <personal token>`, no `Bearer` prefix |
| GitHub Issues | `GET /repos/{repo}/issues?state=open&per_page=100&page=N&labels=...`; entries with `pull_request` are skipped | `GET` then `POST /repos/{repo}/issues/{n}/comments` | `Authorization: Bearer <token>` |
| GitHub Projects | `POST /graphql`, `projectV2(number:) { items { content { ... on Issue, ... on DraftIssue } } }` under `organization` or `user` | Issues as above. A draft item cannot take a comment and is skipped | as above |
| Documents | Files in the repository matching the configured paths: `.md`, `.txt`, `.html`, `.csv`, `.json` | None: a document has nowhere to post a note | None |
| Slack | n/a | `POST` to an incoming webhook with `text` and `blocks` | The webhook address is the secret |
| Teams | n/a | `POST` to a Workflows webhook with a `message` holding one Adaptive Card attachment. Office 365 connectors are being retired and are not used | The webhook address is the secret |
| Email | n/a | SMTP with STARTTLS, one plain-text message | Host, user and password are secrets |

## Comments read at fetch

Added on 2026-11-26, and read from each vendor on that day: GitHub's and Azure DevOps's from their reference pages, Jira's from Atlassian's OpenAPI document, because its reference page could not be read without a browser. One request more for each item, and one more for every 100 comments, up to 2,000 comments of one item.

| Platform | Request | How the next page is asked for |
|---|---|---|
| Jira Cloud | `GET {base_url}/rest/api/3/issue/{key}/comment?startAt=N&maxResults=100` | `startAt` moves on by what was returned, while a page is as full as the `maxResults` the answer states, or `total` says there is more |
| Azure DevOps Boards | `GET https://dev.azure.com/{org}/{project}/_apis/wit/workItems/{id}/comments?$top=100&api-version=7.1-preview.4` | `&continuationToken=…`, for as long as the answer gives one. A deleted comment is left out. The reference names a comment's id `id`, and its samples name it `commentId`; both are read |
| GitHub Issues, and Projects items that are issues | `GET /repos/{repo}/issues/{n}/comments?per_page=100&page=N` | The next `page`, while a page holds 100. A draft project item has no comments |

The note that the kit posts is among the comments it reads back. It is left out by its form: it begins with `agentic-spec-kit: ` and ends with `(ref agentic:<key>)`.

## Which token reads GitHub

From GitHub's documents, read on 2026-11-26 and 2026-11-27; the next section says what was tried. For the other trackers this document says how the adapter signs in, and not which rights the credential needs: that was not checked.

| Source | Token |
|---|---|
| A Project owned by a user account | A classic token with the scope `read:project`. A fine-grained token cannot read such a Project: GitHub lists that among the things fine-grained tokens cannot do |
| A Project owned by an organization | A classic token with `read:project`, or a fine-grained token with the organization's permission to read Projects |

A pipeline's own token (`github.token` in GitHub Actions) belongs to the repository it runs in and reads no Project. That is why a source names a secret of its own. `read:project` is for reading: to post a note on an issue a token needs more, and the kit posts none unless a channel of type `work-item` is configured.

The issue of the run below is in a public repository, which GitHub lets any token read. For a private repository the token also needs the right to read its issues; that was not tried.

## The first read of a live service

On 2026-11-27 `connect fetch` ran in GitHub Actions, in the intake job of `ci/github-actions.yml`, on the reference repository. Its one source named a label and a Project owned by a user account. It read one open issue with that label, the same issue as an item of the Project, and the issue's two comments, with a classic token that the repository's owner made for it; the kit never saw the token. The log says "1 item(s) from 1 source(s); 1 new". The intake record holds the title, the body, the link, and for the discussion a count of 2 and a hash. Not tried there: more than one page of anything, a draft item of a Project, a Project of an organization, a private repository, and a note posted on an issue.

## Safety rules built into the transport

- Only `https` leaves the repository (`http` is allowed to `localhost` for tests).
- A redirect is followed only to the scheme, host and port the request was sent to. Any other is not followed, so no header, and no credential in one, reaches an address the configuration did not name. The adapter then sees the redirect's own status as the answer. Before 2026-11-27 every redirect was followed, with every header.
- A busy service (429, 502, 503, 504) is retried at most three times.
- A Jira search stops on an empty page as well as on a missing page token, so a service that keeps returning a token cannot loop the pipeline.
- Error text is scrubbed of any secret the adapter read before it is printed.
- Documents must be inside the repository: an absolute path or `..` is refused.

## A Claude artifact as a requirement

No interface lets a pipeline read an artifact from a conversation. Export or paste it into a file under a configured `document` path. HTML is reduced to text and scripts and styles are dropped; the page title becomes the record's title.

## Adding a source

Subclass `Adapter` in `agentic_kit_connect/trackers.py`, implement `fetch` and `note`, and `discussion` where the platform has comments, add it to `ADAPTERS`, add its required fields to `NEEDS` and `AUTH` in `checks.py`, and add a recorded-response test that asserts the exact requests. Add the platform's endpoints to the table above with the date you read them.

## Existing community extensions

Spec Kit's community catalogue (v1.4.3) lists extensions for Jira, Azure DevOps, Linear and GitHub Projects. Their source was not read before these adapters were written, which the charter's reuse-first decision (D7) asks for. The intake record is the seam: any tool that writes a valid record can replace an adapter here. See the slice report for the decision this leaves with the owner.
