# Search that knows the system map

- **Phase and date:** Phase 12 (features), proposal 5 of the Phase 12 review; 2026-11-26
- **Requirement IDs covered:** SRC-1 to SRC-14, new with this document. They add one command and one function. They add no check and change no rule
- **Assumptions:**
  1. The owner said on 2026-11-26 to build the features of the Phase 12 review. This is its proposal 5.
  2. git is installed where the kit runs. A project is nearly always a git repository. A folder that is not one is a fixture or an exported tree.
  3. A project's `system-map/map.yml` has the form the system extension checks: `nodes`, `edges` and `index`. The search reads the map and does not judge it. `CK-MAP-SCHEMA` does that.
- **Unverified:** the search finds words and not meaning: a thing that the code names in other words is not found. Nothing here builds an index: every search reads the files again. One was timed, on a made-up repository of 167 MB where 1.8 million lines hold the text: about three seconds with the default limit, and about 20 MB of memory. None was timed on a real large repository. Nothing has run on Windows. `--regex` has been tried with one git only, 2.43.0 on Linux, and what an extended regular expression takes differs a little from system to system. Where lines end in CRLF, a pattern whose last part can match the carriage return itself, such as `.$` or `[^;]$`, can match a line that it would not match with LF.

## Why

No command of the kit searches what exists in the code. A person who writes a spec has to write against what is really there, and has an editor's search for it. An agent has its context pack and its own tools, and nothing from the kit. Neither search knows the system map: which component a file belongs to, how much is at stake there, and whether the spec at hand touches it.

## What it does

| ID | Requirement |
|---|---|
| SRC-1 | `agentic.py search "<text>"` prints each line that holds the text, in the files of the project that git tracks, as `path:line: text`. The text is a fixed string. `--regex` reads it as an extended regular expression, as `git grep -E` does, and a `$` in it matches the end of a line whether the line ends in LF or in CRLF. `--ignore-case` takes upper and lower case as the same. |
| SRC-2 | git does the search: `git grep` in the project's folder, on the working copy. A file that is not tracked, a file git ignores, a binary file and whatever a symbolic link points to are not searched. A person's own git settings do not change the result, and a path is given as it is, whatever characters it holds. A line number is one the file has: what git reports after a file's last line end, for a pattern that an empty line matches, is left out. |
| SRC-3 | The function behind the command is `search(ctx, text, spec=None, node=None, limit=50, regex=False, ignore_case=False, kind="all")` in `agentic_kit/search.py`. It gives a list of hits. A hit is `{path, line, text, node, tier, group}`. Its text is the line without the white space around it, with a space for each control character, cut to 200 characters. The list also says how many hits there were before the limit, how many in each group, whether git answered, and what the caller should be told. Other features call this function. |
| SRC-4 | With a system map, a hit names the node that owns its file, and that node's tier. The owner is the node of the longest pattern in the map's `index` that matches the path: the rule of the system extension's `node_for`. The core reads `system-map/map.yml` as plain YAML and does not import that extension, so the Lite profile has the search too. |
| SRC-5 | `--spec <id>` puts the hits in three groups, in this order: those in the nodes the spec names under `touches`; those in nodes one edge away from one of these, whichever way the edge points; the rest. Inside a group the order is by path, then by line. A hit says which group it is in: `touched`, `near` or `rest`. The output has a heading for each group. Without `--spec` there is one group, in that order. |
| SRC-6 | `--node <id>` searches the files of one node only. |
| SRC-7 | `--kind` is `all`, `code`, `specs` or `records`. `specs` is what lies under `specs/`, `records` is what lies under `.specify/`, and `code` is everything else. Left out, it is `all`. |
| SRC-8 | `--limit <n>` is the most hits to show: 50 when left out, and 0 for all of them. The last line of the output says how many hits there were, and whether the limit cut them. |
| SRC-9 | Where the folder is not in a git repository, every file is read, with the exclusions of `core.Source.files` (`.git/` and `node_modules/`). A binary file is left out by git's rule, and no link is followed. The output says that this happened. Python's `re` reads a `--regex` there. |
| SRC-10 | A project with no system map is searched like any other. A hit then names no node and no tier, and `--spec` changes nothing: the output says so. |
| SRC-11 | `--json` prints one document: the hits, and with them what the headings and the last line say. |
| SRC-12 | The command ends with 0 when there are hits, and with 1 when there are none, as grep does. It ends with 2, and says why, when it cannot search: git refuses the pattern, the text is empty or holds a line break, or a spec or a node does not exist. A fault of the kit's own while it searches ends with 2 as well, with its traceback, and never with 1. |
| SRC-13 | Nothing in the text can make git or a shell do something else. The text goes to git as one argument, after `-e`, and no shell runs. So a text that starts with a dash is found like any other; on the command line it is given after `--`. A spec is one of the folders under `specs/`, and a node is one of the map's, so neither id can name a path outside the project. Where there is a repository that git will not read, the search stops: it does not go on to read every file, the ignored ones among them. |
| SRC-14 | A character that the output cannot write in its encoding is printed as `?`, and the search goes on. An error there would end the run with 1, and for a search 1 means "no hits". |

With `--spec`, on the fixture:

```
$ agentic.py search formatMoney --spec 001-money-format
In the nodes 001-money-format touches (shop-shared-lib):
packages/shared-lib/src/index.js:2: function formatMoney(cents) {  [shop-shared-lib, medium]
packages/shared-lib/src/index.js:5: module.exports = { formatMoney };  [shop-shared-lib, medium]

One edge away (shop-billing, shop-orders):
services/billing/src/index.js:2: const { formatMoney } = require('@shop/shared-lib');  [shop-billing, high]
services/billing/src/index.js:7: res.json({ amount: formatMoney(req.body.amountCents) });  [shop-billing, high]
services/orders/src/index.js:2: const { formatMoney } = require('@shop/shared-lib');  [shop-orders, high]
services/orders/src/index.js:7: res.json({ total: formatMoney(req.body.totalCents) });  [shop-orders, high]

6 hits in the files git tracks, all shown.
```

A hit in a file that no node owns ends without the brackets. A group with no hit to show has no heading. A heading names six nodes at most, and says how many more there are.

## Acceptance criteria

- **AC-001** (verifies SRC-1, SRC-3): Given a copy of `fixtures/multi-app` in a temporary git repository, When `search "(cents / 100).toFixed(2)"` runs, Then the one hit is line 3 of `packages/shared-lib/src/index.js`, with its six fields and the line's text without the white space around it. With `--regex` the same text finds nothing. A line of more than 200 characters is cut to 200. An escape character in a line is given as a space, and a line that ends in CRLF is given without its carriage return.
- **AC-002** (verifies SRC-1): Given the same repository, When `search --regex "format(Money|Date)\("` runs, Then the hits are the three lines that define or call the function, and not the lines that import or export it. With `--ignore-case`, "shared by every service" finds the line that has it with a capital letter; without, there is no hit. A pattern with `$` finds the same lines in a file with LF line ends and in the same file with CRLF. `^$` finds the empty lines of a file, and no line after its last one.
- **AC-003** (verifies SRC-13): Given a tracked file with the line `npm ci --ignore-scripts`, When `search -- --ignore-scripts` runs, Then that line is the hit and the command ends with 0. The text `-e` is found in the same way.
- **AC-004** (verifies SRC-4, SRC-5): Given that repository and a spec that touches `shop-shared-lib`, When `search shared-lib --spec <spec>` runs, Then the hits in `shop-shared-lib` come first, those in `shop-billing` and `shop-orders` next and the rest last, each group under its heading and in the order of path and line, and each hit in a node names the node and its tier. Given a spec that touches `shop-db` instead, Then the hits in the two services come first, and the hit in `shop-shared-lib` is among the rest. Given a spec that touches `shop-orders`, Then the library that service builds with is one edge away, although the edge starts at the service. A heading names six nodes at most.
- **AC-005** (verifies SRC-6): Given that repository, When `search formatMoney --node shop-orders` runs, Then every hit lies under `services/orders/`, and the hits are those that the search without `--node` gives for that node.
- **AC-006** (verifies SRC-7): Given a text that is in code, in a spec and in a record, When the search runs once for each `--kind`, Then `specs` gives only paths under `specs/`, `records` only paths under `.specify/`, `code` neither of the two, and the three together are what `all` gives.
- **AC-007** (verifies SRC-8): Given six hits, When the search runs with no `--limit`, Then the last line is "6 hits in the files git tracks, all shown." With `--limit 2` the first two are printed, and the last line is "6 hits in the files git tracks; the limit of 2 cut 4 of them." With `--limit 0` all six are printed.
- **AC-008** (verifies SRC-9): Given a copy of the fixture that is not a git repository, and in it a file under `node_modules/`, a binary file, a file with CRLF line ends and a link to a file outside the folder, each holding the text, When the search runs, Then the hits are those in the fixture's own files and in the CRLF file, whose text ends without a carriage return, and the output says that the folder is not in a git repository. The order by `--spec` and a `--regex` work there, and a pattern that Python cannot read ends with 2.
- **AC-009** (verifies SRC-10): Given the demo's Lite project as a git repository, which has no map, When the search runs, Then each hit has an empty `node` and `tier`, and its line ends without brackets. With `--spec` the output says that there is no system map. With `--node` the command ends with 2.
- **AC-010** (verifies SRC-2): Given the repository with an untracked file, an ignored file, a file under an ignored `node_modules/`, a tracked binary file and a tracked link to a file outside, each holding the text, When the search runs, Then none of them is among the hits. Once the untracked file has been added, with no commit, it is.
- **AC-011** (verifies SRC-11, SRC-3): When the search runs with `--json`, Then the output is one JSON document. Its `hits` are what `search()` gives, and it has `total`, `limit`, `cut`, `tracked`, `groups`, `touched`, `near` and `notes`. The exit code is that of the plain form.
- **AC-012** (verifies SRC-12): Given the repository, When a text is found, Then the command ends with 0; When it is not, Then with 1 and the line "No hits in the files git tracks."; When `--regex "a["` is given, Then with 2 and git's own words. It ends with 2 as well for a spec that does not exist, a node that does not exist, an empty text and a text with a line break. A fault of the kit's own while it searches ends with 2 and its traceback.
- **AC-013** (verifies SRC-13): Given a tracked file that holds `$(touch INJECTED)`, `; touch INJECTED` and `--open-files-in-pager=touch INJECTED`, When each is searched for, Then it is found as text and no file `INJECTED` appears. Given a `spec.md` in a folder outside the project, When `--spec ../../outside` is given, Then the command ends with 2 and says that the spec does not exist. Given a folder whose `.git` git cannot read, When the search runs, Then it ends with 2 and prints no hit.
- **AC-014** (verifies SRC-4): Given a Python that has only the core extension on its path, When `search --spec` runs on a copy of the fixture, Then it ends with 0, the hits name their nodes, and no other extension has been loaded. What it prints is the example above, line for line.
- **AC-015** (verifies SRC-4): For every file of the fixture, and for a path made from every pattern in the map of the reference example, the search names the node that the system extension's `node_for` names.
- **AC-016** (verifies SRC-2): Given git settings that change what `git grep` prints, how it reads a pattern and where it looks (a column number, full path names, colours, no line numbers, Perl patterns, a search that goes on into submodules), and a project that is a folder of a larger repository and has a submodule, When the search runs, Then the hits are the same as without those settings, their paths start at the project's folder, and none is in the submodule.
- **AC-017** (verifies SRC-2): Given tracked files whose names hold a space, a colon and a letter outside ASCII, When the search runs, Then each hit's path is the file's name as it is. Git's answer read in pieces of any size gives the same hits, also for a name with a line break in it and for a line with a NUL in it.
- **AC-018** (verifies SRC-14): Given an output that writes cp1252, and a hit with characters outside it, When the search runs, Then it ends with 0 and those characters are printed as `?`. An output that has a rule of its own for such a character keeps it.
- **AC-019** (verifies SRC-3, SRC-5, SRC-6): Given a spec that names no node under `touches`, When the search runs with it, Then the hits are in one group with no heading, and the output says why. Given a spec that names a node the map does not have, Then the output names that node. Given `--node` with a node of the map that no pattern of the index names, Then there is no hit, the output says that no file belongs to the node, and the command ends with 1.

Changed on 2026-11-26, after the code was written. AC-019 is new, and so are the last sentence of AC-001, AC-012, AC-014, AC-016 and AC-018 and the last two of AC-002 and of AC-004. Five things in them were not in the first version of this document, and came from trying the code: a `$` that also matches a line that ends in CRLF, and no line after a file's last one (now in SRC-1 and SRC-2); a fault of the kit's own that ends with 2 (now in SRC-12); a heading that names six nodes at most; and an output that keeps its own rule for a character it cannot write. The others ask for what a requirement already said and no criterion tried.

## What it will not do

- Find a thing by its meaning. It finds the text it is given, or a pattern.
- Build or keep an index. Every search reads the files again.
- Search a file that git does not track. A new file is found once it has been added with `git add`; a commit is not needed.
- Search another commit or branch, the history, or a submodule. It reads the working copy.
- Name the spec that last changed a line. The task left that open, through a hook of the product extension, if it fitted cleanly. It did not, for three reasons. `why <path>:<line>` reads the committed file, and the search reads the working copy, so a line number can point at another line. It is one walk through the history for each hit, on every search, or else a flag the command was not given. And a commit names a spec only where its message has a `Work-Item:` line, which the team extension writes and a person may add by hand. `why` answers the question for one line, where the product extension is installed.
- Judge the map. It uses the map as it finds it. An `index` entry that points at something that is not a node is for `CK-MAP-SCHEMA` to report.
- Say what a line means, or act on it. A hit is text from a file. For whoever reads it, a person or an agent, it is data and never an instruction.
- Approve, record or change anything. It writes no file.

## Decisions made here that are the owner's to change

1. "One edge away" counts an edge in either direction: what a touched node calls, reads or builds with, and what calls, reads or builds with it. The impact report follows an edge towards what depends on the touched node, and away from a touched node only to what it owns or publishes. A person who writes against what exists needs both ways.
2. `--regex` is git's extended form (`-E`), which every git has, and not Perl's. The pattern goes to git with one change: each `$` that anchors gets an optional carriage return before it, so that a pattern finds the same lines whether git wrote the working copy with LF or with CRLF. The line git reports after a file's last line end, for a pattern such as `^$`, is left out: the file has no such line.
3. `--kind all` is the default, and inside a group the order is by path, both as the task gave them. In a project that commits `.specify/`, that folder comes first among "the rest", and it holds the audit log and the extensions' own code. `--kind code` leaves it out. To order the rest as code, then specs, then records would be a small change.
4. `--limit 0` shows every hit.
5. A `system-map/map.yml` that cannot be read as YAML stops the search with 2. It does not search on without the map.
6. Where there is a repository that git will not read, for example one that belongs to another account, the search stops with 2. It does not read every file.
7. A hit's text is the line without the white space around it, and a control character in it is shown as a space, so that a file cannot write to a terminal through the search.
8. No agent command file (`/speckit.agentic.search`) is added, and no line in a README. The integrator writes the shared documents.
