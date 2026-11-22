# Requirement sources and notification channels

- **Phase and date:** slice 0.6, 2026-11-22
- **Requirement IDs covered:** ADP-17, ADP-18, ADP-19, INT-1, INT-2, NTF-2, NTF-4, NTF-5
- **Assumptions:** each vendor's API behaves as its published reference says
- **Unverified:** no adapter has been run against the live service. Every one is tested against recorded responses only (`tests/test_connect.py`).

## What an adapter does

Two things, and nothing else:

1. **Fetch** work items and return them in one shape: key, title, body, link, revision, and optional type, priority, labels, state.
2. **Post one note** on a work item. The note carries a marker; the adapter looks for the marker before posting, so a note is never repeated.

An adapter holds no state and writes nothing to the repository. `connect fetch` turns what it returns into intake records (`docs/design/schemas.md`), screening the text first.

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

## Safety rules built into the transport

- Only `https` leaves the repository (`http` is allowed to `localhost` for tests).
- A busy service (429, 502, 503, 504) is retried at most three times.
- A Jira search stops on an empty page as well as on a missing page token, so a service that keeps returning a token cannot loop the pipeline.
- Error text is scrubbed of any secret the adapter read before it is printed.
- Documents must be inside the repository: an absolute path or `..` is refused.

## A Claude artifact as a requirement

No interface lets a pipeline read an artifact from a conversation. Export or paste it into a file under a configured `document` path. HTML is reduced to text and scripts and styles are dropped; the page title becomes the record's title.

## Adding a source

Subclass `Adapter` in `agentic_kit_connect/trackers.py`, implement `fetch` and `note`, add it to `ADAPTERS`, add its required fields to `NEEDS` and `AUTH` in `checks.py`, and add a recorded-response test that asserts the exact requests. Add the platform's endpoints to the table above with the date you read them.

## Existing community extensions

Spec Kit's community catalogue (v1.4.3) lists extensions for Jira, Azure DevOps, Linear and GitHub Projects. Their source was not read before these adapters were written, which the charter's reuse-first decision (D7) asks for. The intake record is the seam: any tool that writes a valid record can replace an adapter here. See the slice report for the decision this leaves with the owner.
