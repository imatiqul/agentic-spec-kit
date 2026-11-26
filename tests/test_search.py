"""The search that knows the system map (SRC-1 to SRC-14, docs/design/search.md).

Each test is named after the acceptance criterion it proves. Most work on a copy of fixtures/multi-app in a
throwaway git repository, prepared as tests/test_team.py prepares its own. No model is involved, and nothing
here reaches a network. Run: python -m pytest tests/test_search.py -q
"""
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "extensions" / "agentic" / "scripts"
sys.path.insert(0, str(CORE))

from agentic_kit import core, demo, search  # noqa: E402
from agentic_kit.__main__ import _captured, main  # noqa: E402

core.load_plugins(CORE)

from agentic_kit_system import mapmodel  # noqa: E402
from agentic_kit_team import golden  # noqa: E402

FIXTURE = ROOT / "fixtures" / "multi-app"
REFERENCE = ROOT / "examples" / "healthq" / "project"
DOCUMENT = ROOT / "docs" / "design" / "search.md"
SPEC, DB_SPEC, ORDERS_SPEC = "040-search", "041-search-db", "042-search-orders"   # each touches one node: the shared library, the database, the orders service
FIXTURE_SPEC = "001-money-format"                        # the fixture's own spec; it touches the shared library too
LIB, BILLING, ORDERS = "packages/shared-lib/src/index.js", "services/billing/src/index.js", "services/orders/src/index.js"
SIX = [(LIB, 2), (LIB, 5), (BILLING, 2), (BILLING, 7), (ORDERS, 2), (ORDERS, 7)]   # where the fixture says formatMoney
CALLS = [(LIB, 2), (BILLING, 7), (ORDERS, 7)]            # where it defines or calls the function
FIELDS = {"path", "line", "text", "node", "tier", "group"}


def git(root, *args):
    done = subprocess.run(["git", "-C", str(root), "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                           "-c", "commit.gpgsign=false", *args], capture_output=True)
    assert done.returncode == 0, done.stderr.decode(errors="replace")
    return done.stdout.decode("utf-8", errors="replace").strip()


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def spec_md(spec, touches):
    return (f"---\nspec: {spec}\ntier_declared: high\nowner_role: backend\nprinciples: [P-1]\ntouches: [{touches}]\n---\n"
            "# Feature Specification: something to search with\n\n- **FR-001**: it works\n")


@pytest.fixture()
def shop(tmp_path):
    """A copy of the fixture as a git repository, with three specs of its own, committed."""
    root = tmp_path / "shop"
    golden.prepare(FIXTURE, root)
    for spec, touches in ((SPEC, "shop-shared-lib"), (DB_SPEC, "shop-db"), (ORDERS_SPEC, "shop-orders")):
        write(root, f"specs/{spec}/spec.md", spec_md(spec, touches))
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "three specs")
    return root


def plain_copy(root):
    """The fixture as it is in the kit's repository, its own spec included. Not a git repository."""
    shutil.copytree(FIXTURE, root)
    return root


def ctx(root):
    src = core.Source(root)
    return core.Context(src, src)


def find(root, text, **options):
    return search.search(ctx(root), text, **options)


def kit(root, *words):
    return _captured(["--root", str(root), *words])


def places(hits):
    return [(hit["path"], hit["line"]) for hit in hits]


def link(target, at):
    """A symbolic link, where the system lets this account make one."""
    try:
        os.symlink(target, at)
    except (OSError, NotImplementedError):
        return False
    return True


def test_AC_001_a_fixed_string_is_found_as_it_is_written_and_a_long_line_is_cut(shop):
    text = "(cents / 100).toFixed(2)"
    assert find(shop, text) == [{"path": LIB, "line": 3, "text": "return (cents / 100).toFixed(2);", "node": "shop-shared-lib",
                                 "tier": "medium", "group": "rest"}]
    code, out = kit(shop, "search", text)
    assert code == 0
    assert out.splitlines()[0] == f"{LIB}:3: return (cents / 100).toFixed(2);  [shop-shared-lib, medium]"
    assert find(shop, text, regex=True) == [], "as a pattern the brackets are a group and each dot is any character"
    assert kit(shop, "search", text, "--regex")[0] == 1

    write(shop, "docs/long.md", "\t  needle-AC-001 \x1b[2Jafter an escape sequence " + "x" * 400 + "  \n")
    git(shop, "add", "docs/long.md")
    hit, = find(shop, "needle-AC-001")
    assert set(hit) == FIELDS and (hit["node"], hit["tier"]) == ("", "")
    assert len(hit["text"]) == search.WIDTH == 200
    assert hit["text"].startswith("needle-AC-001  [2Jafter an escape sequence xxx"), "no white space in front, and a space for the escape character"
    assert kit(shop, "search", "needle-AC-001")[1].splitlines()[0] == f"docs/long.md:1: {hit['text']}"
    (shop / "docs" / "windows.md").write_bytes(b"first line\r\ncarriage-AC-001 at the end of a line\r\n")
    git(shop, "add", "docs/windows.md")
    assert b"\r\n" in (shop / "docs" / "windows.md").read_bytes(), "git changed the line ends, so nothing was tried"
    assert [hit["text"] for hit in find(shop, "carriage-AC-001")] == ["carriage-AC-001 at the end of a line"]


def test_AC_002_a_regular_expression_and_a_search_that_ignores_case(shop):
    pattern = r"format(Money|Date)\("
    assert places(find(shop, pattern, regex=True)) == CALLS
    assert find(shop, pattern) == [], "without --regex the pattern is a text, and no line holds it"
    code, out = kit(shop, "search", "--regex", pattern)
    assert code == 0 and out.rstrip().endswith("3 hits in the files git tracks, all shown.")
    assert places(find(shop, r"FORMATMONEY\(", regex=True, ignore_case=True)) == CALLS

    assert kit(shop, "search", "shared by every service")[0] == 1
    code, out = kit(shop, "search", "shared by every service", "--ignore-case")
    assert code == 0
    assert out.splitlines()[0].startswith(f"{LIB}:1: // Shared by every service.")

    lines = [b"using System;", b"", b"class App {", b"    decimal price = 5;  // costs $5", b"}"]
    for folder, line_end in (("unix", b"\n"), ("windows", b"\r\n")):   # one file, as git writes it on either system
        (shop / folder).mkdir()
        (shop / folder / "App.cs").write_bytes(b"".join(line + line_end for line in lines))
    (shop / "unix" / "open.txt").write_bytes(b"one\n\nthree, and no line end after it")
    (shop / "unix" / "empty.txt").write_bytes(b"")
    git(shop, "add", "unix", "windows")
    for pattern, found in (("System;$", [1]), ("^$", [2]), (r"\{$", [3]), (r"costs \$5$", [4]), ("[$]5$", [4]), (r"^\}$|^class", [3, 5]),
                           ("[[:space:]]App[^$]+$", [3]), (r"\$5", [4])):
        hits = find(shop, pattern, regex=True, limit=0)
        on = {folder: [hit["line"] for hit in hits if hit["path"] == f"{folder}/App.cs"] for folder in ("unix", "windows")}
        assert on == {"unix": found, "windows": found}, f"{pattern} matches the same lines whether they end in LF or in CRLF"
    empty = find(shop, "^$", regex=True, limit=0)   # git also gives what follows a file's last line end; that is not a line
    assert [hit["line"] for hit in empty if hit["path"].startswith("unix/")] == [2, 2], "one in App.cs and one in open.txt: lines that are there"
    assert empty.total == len(empty) == len(find(shop, "^[[:space:]]*$", regex=True, limit=0))
    for given, made in ((";$", ";\r?$"), (r"\$5$", "\\$5\r?$"), ("[$]5", "[$]5"), ("a$|b$", "a\r?$|b\r?$"), ("[]$]x$", "[]$]x\r?$"), ("[^]$]", "[^]$]"),
                        ("[[:alpha:]$]$", "[[:alpha:]$]\r?$"), ("[a$", "[a$"), ("a\\", "a\\"), (r"\\$", "\\\\\r?$"), ("plain", "plain")):
        assert search.end_of_line(given) == made, given
    code, out = kit(shop, "search", "--regex", "(System;$")
    assert (code, out) == (2, "git did not take the pattern: fatal: -e option, '(System;$': Unmatched ( or \\(\n"), "the pattern as it was given"


def test_AC_003_a_text_that_starts_with_a_dash_is_found_like_any_other(shop):
    write(shop, "scripts/build.sh", "#!/bin/sh\nnpm ci --ignore-scripts\ngrep -e pattern file\n")
    git(shop, "add", "scripts/build.sh")
    assert places(find(shop, "--ignore-scripts")) == [("scripts/build.sh", 2)]
    code, out = kit(shop, "search", "--", "--ignore-scripts")
    assert code == 0
    assert out.splitlines()[0] == "scripts/build.sh:2: npm ci --ignore-scripts"
    assert places(find(shop, "-e pattern")) == [("scripts/build.sh", 3)]
    assert ("scripts/build.sh", 3) in places(find(shop, "-e", limit=0)), "git took -e for the text, and not for its own option"
    code, out = kit(shop, "search", "--json", "--", "-e")
    assert code == 0 and ("scripts/build.sh", 3) in places(json.loads(out)["hits"])
    assert places(find(shop, "-+ignore-[a-z]+$", regex=True)) == [("scripts/build.sh", 2)]


def test_AC_004_hits_in_what_the_spec_touches_come_first_then_one_edge_away_then_the_rest(shop):
    hits = find(shop, "shared-lib", spec=SPEC, limit=0)
    by = {group: [hit for hit in hits if hit["group"] == group] for group in search.GROUPS}
    assert [hit["group"] for hit in hits] == [group for group in search.GROUPS for _ in by[group]], "the three groups, in their order"
    assert all(by.values()), "each group has a hit, so the order is tried"
    assert {(hit["node"], hit["tier"]) for hit in by["touched"]} == {("shop-shared-lib", "medium")}
    assert {(hit["node"], hit["tier"]) for hit in by["near"]} == {("shop-billing", "high"), ("shop-orders", "high")}
    assert not {hit["node"] for hit in by["rest"]} & {"shop-shared-lib", "shop-billing", "shop-orders"}
    assert any(hit["node"] == "" for hit in by["rest"]), "a file no node owns is among the rest"
    for part in by.values():
        assert places(part) == sorted(places(part)), "by path and line inside a group"
    assert (hits.touched, hits.near) == (["shop-shared-lib"], ["shop-billing", "shop-orders"])
    assert hits.groups == {group: len(part) for group, part in by.items()}

    code, out = kit(shop, "search", "shared-lib", "--spec", SPEC, "--limit", "0")
    rows = out.splitlines()
    heads = [f"In the nodes {SPEC} touches (shop-shared-lib):", "One edge away (shop-billing, shop-orders):", "The rest:"]
    at = [rows.index(head) for head in heads]
    assert code == 0 and at[0] == 0 and at == sorted(at)
    assert rows[1].startswith("packages/shared-lib/package.json:1: ") and rows[1].endswith("  [shop-shared-lib, medium]")
    assert rows[at[1] + 1].startswith("services/billing/package.json:2: ") and rows[at[1] + 1].endswith("  [shop-billing, high]")
    assert [row for row in rows if not row] == ["", "", ""], "an empty line before the second and third heading and before the last line"

    other = find(shop, "shared-lib", spec=DB_SPEC, limit=0)
    assert sorted(places(other)) == sorted(places(hits)), "the same hits, in another order"
    assert (other.touched, other.near) == (["shop-db"], ["shop-billing", "shop-orders"])
    assert other.groups["touched"] == 0 and other[0]["group"] == "near"
    assert {hit["node"] for hit in other if hit["group"] == "near"} == {"shop-billing", "shop-orders"}
    assert {hit["group"] for hit in other if hit["node"] == "shop-shared-lib"} == {"rest"}

    away = find(shop, "formatMoney", spec=ORDERS_SPEC)   # the orders service is where these edges start, not where they end
    assert away.near == ["contract-payments-openapi", "payments-provider", "shop-db", "shop-shared-lib"]
    assert [(hit["path"], hit["group"]) for hit in away] == [(ORDERS, "touched")] * 2 + [(LIB, "near")] * 2 + [(BILLING, "rest")] * 2

    plain = find(shop, "shared-lib", limit=0)
    assert places(plain) == sorted(places(hits)) and {hit["group"] for hit in plain} == {"rest"}
    assert "touches" not in kit(shop, "search", "shared-lib")[1].splitlines()[0], "no heading without --spec"
    many = search.Hits([hits[0]], total=1, touched=[f"node-{n}" for n in range(8)], near=["shop-db"])
    assert search.plain(many, SPEC)[0] == f"In the nodes {SPEC} touches (node-0, node-1, node-2, node-3, node-4, node-5 and 2 more):"


def test_AC_005_node_keeps_the_search_to_the_files_of_one_node(shop):
    everything = find(shop, "formatMoney")
    only = find(shop, "formatMoney", node="shop-orders")
    assert places(only) == [(ORDERS, 2), (ORDERS, 7)]
    assert list(only) == [hit for hit in everything if hit["node"] == "shop-orders"]
    code, out = kit(shop, "search", "formatMoney", "--node", "shop-orders")
    rows = out.splitlines()
    assert code == 0 and len(rows) == 4 and all(row.startswith("services/orders/") for row in rows[:2])
    assert rows[-1] == "2 hits in the files git tracks, all shown."
    both = find(shop, "formatMoney", node="shop-orders", spec=SPEC)
    assert places(both) == places(only) and {hit["group"] for hit in both} == {"near"}


def test_AC_006_kind_splits_the_hits_into_code_specs_and_records(shop):
    found = {kind: find(shop, "backend", kind=kind, limit=0) for kind in search.KINDS}
    assert all(found.values()), "the text is in code, in a spec and in a record, so each kind is tried"
    assert all(hit["path"].startswith("specs/") for hit in found["specs"])
    assert all(hit["path"].startswith(".specify/") for hit in found["records"])
    assert not any(hit["path"].startswith(("specs/", ".specify/")) for hit in found["code"])
    assert "system-map/map.yml" in {hit["path"] for hit in found["code"]}
    together = places(found["code"]) + places(found["specs"]) + places(found["records"])
    assert sorted(together) == places(found["all"]) and len(set(together)) == len(together)
    assert places(find(shop, "backend", limit=0)) == places(found["all"]), "left out, the kind is all"
    code, out = kit(shop, "search", "backend", "--kind", "specs")
    assert code == 0 and [row.split(":")[0] for row in out.splitlines()[:-2]] == [hit["path"] for hit in found["specs"]]
    assert kit(shop, "search", "backend", "--kind", "documents")[0] == 2
    with pytest.raises(core.KitError, match="kind must be one of all, code, specs, records"):
        find(shop, "backend", kind="documents")


def test_AC_007_the_last_line_counts_the_hits_and_says_whether_the_limit_cut_them(shop):
    code, out = kit(shop, "search", "formatMoney")
    rows = out.splitlines()
    assert code == 0 and len(rows) == 8, "six hits, an empty line and the last line"
    assert rows[-1] == "6 hits in the files git tracks, all shown."

    code, out = kit(shop, "search", "formatMoney", "--limit", "2")
    assert code == 0
    assert out.splitlines() == [*rows[:2], "", "6 hits in the files git tracks; the limit of 2 cut 4 of them."]
    assert kit(shop, "search", "formatMoney", "--limit", "0")[1].splitlines() == rows

    cut = find(shop, "formatMoney", limit=2)
    assert places(cut) == SIX[:2] and (cut.total, cut.limit, cut.cut) == (6, 2, True)
    whole = find(shop, "formatMoney")
    assert places(whole) == SIX and (whole.total, whole.limit, whole.cut) == (6, 50, False)
    assert places(find(shop, "formatMoney", limit=3, spec=DB_SPEC)) == SIX[2:5], "the limit keeps the first in the order of the groups"
    assert places(find(shop, "formatMoney", limit=None)) == SIX

    write(shop, "docs/many.md", "".join(f"needle-AC-007 number {n}\n" for n in range(1, 61)))
    git(shop, "add", "docs/many.md")
    rows = kit(shop, "search", "needle-AC-007")[1].splitlines()
    assert len(rows) == 52 and rows[49].startswith("docs/many.md:50: ")
    assert rows[-1] == "60 hits in the files git tracks; the limit of 50 cut 10 of them."
    assert kit(shop, "search", "number 60")[1].splitlines()[-1] == "1 hit in the files git tracks, all shown."
    code, out = kit(shop, "search", "formatMoney", "--limit", "-1")
    assert code == 2 and "the limit is 0 for every hit" in out


def test_AC_008_a_folder_that_is_not_a_git_repository_is_read_file_by_file_and_the_output_says_so(tmp_path):
    root = plain_copy(tmp_path / "exported")
    write(root, "node_modules/pkg/index.js", "formatMoney in a dependency\n")
    (root / "scan.bin").write_bytes(b"\0\1 formatMoney in a binary file\n")
    (root / "windows.txt").write_bytes(b"first line\r\nformatMoney with CRLF  \r\n")
    (tmp_path / "outside.txt").write_text("formatMoney outside the folder\n", encoding="utf-8")
    link(tmp_path / "outside.txt", root / "link.txt")
    assert not search._git_answers(root), "the temporary folder is inside a git repository, so nothing was tried"

    hits = find(root, "formatMoney", spec=FIXTURE_SPEC)
    assert places(hits) == [*SIX, ("windows.txt", 2)]
    assert hits[-1]["text"] == "formatMoney with CRLF" and not hits.tracked
    assert [hit["group"] for hit in hits] == ["touched"] * 2 + ["near"] * 4 + ["rest"]
    assert hits[0]["node"] == "shop-shared-lib" and hits[0]["tier"] == "medium"
    assert places(find(root, "FORMATMONEY", ignore_case=True)) == sorted(places(hits))

    code, out = kit(root, "search", "formatMoney")
    rows = out.splitlines()
    assert code == 0
    assert rows[-2] == "This folder is not in a git repository. Every file was read, also what git would leave out as untracked or ignored."
    assert rows[-1] == "7 hits in the files of this folder, all shown."
    assert json.loads(kit(root, "search", "formatMoney", "--json")[1])["tracked"] is False

    found = find(root, r"format(Money|Date)\(", regex=True)
    assert places(found) == CALLS
    assert found.notes[-1].endswith("Python's `re` read the pattern, and it differs from git's in places.")
    assert places(find(root, "^$", regex=True, node="shop-db")) == [], "what follows a file's last line end is not a line"
    code, out = kit(root, "search", "--regex", "a[")
    assert code == 2 and out.startswith("Python's `re` did not take the pattern: ")
    assert kit(root, "search", "no such text anywhere")[1] == f"{rows[-2]}\nNo hits in the files of this folder.\n"


def test_AC_009_a_project_with_no_map_is_searched_and_its_hits_name_no_node(tmp_path):
    demo.build_project(tmp_path)   # the Lite project of the demo: no system map, and nothing but the core is needed
    demo._git(tmp_path, "init", "-q")
    demo._commit(tmp_path, "the demo's project")
    hits = find(tmp_path, "greeting")
    assert len(hits) >= 3 and demo.SPEC_FILE in {hit["path"] for hit in hits}
    assert all((hit["node"], hit["tier"], hit["group"]) == ("", "", "rest") for hit in hits)
    code, out = kit(tmp_path, "search", "greeting")
    without = out.splitlines()
    assert code == 0
    assert without[:len(hits)] == [f"{hit['path']}:{hit['line']}: {hit['text']}" for hit in hits], "no brackets at the end of a line"

    code, out = kit(tmp_path, "search", "greeting", "--spec", demo.SPEC)
    rows = out.splitlines()
    assert code == 0 and rows[:len(hits)] == without[:len(hits)], "the same lines in the same order, and no heading"
    assert rows[-2] == "There is no system map (system-map/map.yml), so the hits name no node, and the spec does not change their order."
    assert rows[-1] == without[-1] == f"{len(hits)} hits in the files git tracks, all shown."
    code, out = kit(tmp_path, "search", "greeting", "--node", "shop-orders")
    assert code == 2 and out == "there is no system map (system-map/map.yml), so there is no node shop-orders\n"


def test_AC_010_untracked_ignored_and_binary_files_and_links_are_not_searched(shop, tmp_path):
    write(shop, "docs/tracked.md", "needle-AC-010 in a tracked file\n")
    write(shop, "notes.txt", "needle-AC-010 in a file nobody has added\n")
    write(shop, ".gitignore", "node_modules/\n*.env\n")
    write(shop, "local.env", "TOKEN=needle-AC-010\n")
    write(shop, "node_modules/pkg/index.js", "needle-AC-010 in a dependency\n")
    (shop / "scan.bin").write_bytes(b"\0\1 needle-AC-010 in a binary file\n")
    (tmp_path / "outside.txt").write_text("needle-AC-010 outside the repository\n", encoding="utf-8")
    linked = link(tmp_path / "outside.txt", shop / "link.txt")
    git(shop, "add", "docs/tracked.md", ".gitignore", "scan.bin", *(["link.txt"] if linked else []))
    tracked = git(shop, "ls-files").splitlines()
    assert "scan.bin" in tracked and "notes.txt" not in tracked and "local.env" not in tracked
    assert places(find(shop, "needle-AC-010")) == [("docs/tracked.md", 1)]
    assert kit(shop, "search", "needle-AC-010")[1].splitlines()[-1] == "1 hit in the files git tracks, all shown."

    git(shop, "add", "notes.txt")   # added, and not committed
    assert places(find(shop, "needle-AC-010")) == [("docs/tracked.md", 1), ("notes.txt", 1)]


def test_AC_011_json_is_one_document_with_the_hits_and_what_the_last_line_says(shop):
    code, out = kit(shop, "search", "formatMoney", "--spec", SPEC, "--limit", "3", "--json")
    document = json.loads(out)
    found = find(shop, "formatMoney", spec=SPEC, limit=3)
    assert code == 0
    assert document["hits"] == list(found) and places(document["hits"]) == SIX[:3]
    assert all(set(hit) == FIELDS for hit in document["hits"])
    del document["hits"]
    assert document == {"total": 6, "limit": 3, "cut": True, "tracked": True, "groups": {"touched": 2, "near": 4, "rest": 0},
                        "touched": ["shop-shared-lib"], "near": ["shop-billing", "shop-orders"], "notes": []}
    assert json.loads(json.dumps(found)) == list(found), "what the function gives is a list like any other"

    code, out = kit(shop, "search", "no such text anywhere", "--json")
    assert code == 1
    assert json.loads(out) == {"hits": [], "total": 0, "limit": 50, "cut": False, "tracked": True,
                               "groups": {"touched": 0, "near": 0, "rest": 0}, "touched": [], "near": [], "notes": []}


def test_AC_012_the_command_ends_with_0_with_hits_1_with_none_and_2_when_it_cannot_search(shop, monkeypatch):
    assert kit(shop, "search", "formatMoney")[0] == 0
    assert kit(shop, "search", "no such text anywhere") == (1, "No hits in the files git tracks.\n")
    code, out = kit(shop, "search", "--regex", "a[")
    assert code == 2 and out.startswith("git did not take the pattern: ") and "a[" in out and len(out.splitlines()) == 1
    for words, said in ((("formatMoney", "--spec", "999-none"), "spec 999-none does not exist"),
                        (("formatMoney", "--node", "no-such-node"), "node no-such-node is not in the system map"),
                        (("",), "give the text to search for"),
                        (("two\nlines",), "the text holds a line break")):
        code, out = kit(shop, "search", *words)
        assert code == 2 and out.startswith(said) and len(out.splitlines()) == 1, words
    with pytest.raises(core.KitError, match="git did not take the pattern"):
        find(shop, "a[", regex=True)

    def program(*words):   # as a person runs it, so that the code is the program's own
        return subprocess.run([sys.executable, str(CORE / "agentic.py"), "--root", str(shop), "search", *words], capture_output=True, text=True)

    done = program("formatMoney")
    assert done.returncode == 0 and done.stdout.splitlines()[-1] == "6 hits in the files git tracks, all shown." and not done.stderr
    assert program("no such text anywhere").returncode == 1
    done = program("--regex", "a[")
    assert done.returncode == 2 and not done.stdout and done.stderr.startswith("git did not take the pattern: ")
    assert git(shop, "status", "--porcelain") == "", "a search writes nothing"

    def faulty(*_):
        raise RuntimeError("a fault of the kit's own")

    monkeypatch.setattr(search, "_tracked", faulty)
    code, out = kit(shop, "search", "formatMoney")
    assert code == 2 and "Traceback" in out and out.rstrip().endswith("RuntimeError: a fault of the kit's own"), "never 1: that would say no hits"


def test_AC_013_nothing_in_the_text_or_in_an_id_reaches_a_shell_an_option_of_git_or_a_path_outside(shop, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)   # where a shell would have run, had there been one
    texts = ["$(touch INJECTED)", "; touch INJECTED", "`touch INJECTED`", "| touch INJECTED", "--open-files-in-pager=touch INJECTED",
             "-Otouch INJECTED", "--no-index INJECTED"]
    write(shop, "docs/odd.md", "".join(f"{text}\n" for text in texts))
    git(shop, "add", "docs/odd.md")
    for number, text in enumerate(texts, 1):
        assert places(find(shop, text)) == [("docs/odd.md", number)], text
        assert kit(shop, "search", "--", text)[0] == 0, text
    assert places(find(shop, r"\$\(touch INJECTED\)$", regex=True)) == [("docs/odd.md", 1)]
    assert not [path for folder in (shop, tmp_path) for path in folder.rglob("INJECTED")]

    write(tmp_path, "outside/spec.md", spec_md("outside", "shop-db"))
    assert (shop / "specs" / ".." / ".." / "outside" / "spec.md").is_file(), "the path the id would make is a file, so reading it is tried"
    for words in (("--spec", "../../outside"), ("--spec", str(tmp_path / "outside")), ("--spec", ""), ("--spec", ".")):
        code, out = kit(shop, "search", "formatMoney", *words)
        assert (code, out) == (2, f"spec {words[1]} does not exist\n"), words
    code, out = kit(shop, "search", "formatMoney", "--node", "../../outside")
    assert (code, out) == (2, "node ../../outside is not in the system map\n")

    held = plain_copy(tmp_path / "held")
    (held / ".git").write_text("gitdir: /nowhere/that/exists\n", encoding="utf-8")   # a repository that git cannot read
    code, out = kit(held, "search", "formatMoney")
    assert code == 2 and out.startswith("there is a git repository here, and git did not read it (")
    assert "Nothing was searched" in out and LIB not in out


def test_AC_014_the_core_extension_alone_is_enough_and_prints_what_the_document_shows(tmp_path):
    root = plain_copy(tmp_path / "shop")
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "the fixture")
    words = ["search", "formatMoney", "--spec", FIXTURE_SPEC]
    only_core = ("import sys; sys.path.insert(0, sys.argv[1]); from agentic_kit.__main__ import main; "
                 "code = main(['--root', *sys.argv[2:]]); "
                 "assert not [m for m in sys.modules if m.startswith('agentic_kit_')], 'another extension was loaded'; sys.exit(code)")
    done = subprocess.run([sys.executable, "-c", only_core, str(CORE), str(root), *words], capture_output=True, text=True, cwd=tmp_path)
    assert done.returncode == 0, done.stdout[-600:] + done.stderr[-600:]
    rows = done.stdout.splitlines()
    owners = [row.rsplit("  [", 1)[-1] for row in rows if "  [" in row]
    assert owners == ["shop-shared-lib, medium]"] * 2 + ["shop-billing, high]"] * 2 + ["shop-orders, high]"] * 2

    shown = DOCUMENT.read_text(encoding="utf-8").split(f"$ agentic.py {' '.join(words)}\n", 1)[1].split("```", 1)[0]
    assert rows == shown.splitlines(), "the example in docs/design/search.md is what the command prints"


def test_AC_015_the_search_names_the_node_that_the_system_extension_names(shop):
    compared = owned = 0
    for root in (shop, REFERENCE):
        theirs, mine = mapmodel.load_map(ctx(root)), search.read_map(core.Source(root))
        paths = set(core.Source(root).files()) | {"README.md", "nowhere/at/all.txt", "services", ""}
        for entry in theirs.raw["index"]:
            for pattern in entry["paths"]:
                made = pattern.replace("**", "deep/er").replace("*", "file.x")
                paths |= {made, f"{made}/more.txt", f"x/{made}", made.rsplit("/", 1)[0], made.upper()}
        for path in sorted(paths):
            assert mine.owner(path) == (theirs.node_for(path) or ""), path
            compared += 1
            owned += bool(mine.owner(path))
        assert set(mine.nodes) == set(theirs.nodes) and mine.indexed == {entry["node"] for entry in theirs.raw["index"]}
        assert all(mine.tier(node) == str(entry.get("tier") or "") for node, entry in theirs.nodes.items())
    assert compared > 300 and owned > 100, "far fewer paths were compared than the two maps give"

    raw = {"index": [{"paths": ["src/*"], "node": "wide"}, {"paths": ["src/api/*", "src/web/*"], "node": "narrow"},
                     {"paths": ["src/a?i/*"], "node": "as-long-and-later"}, {"paths": ["docs/*"]}, {"paths": ["docs/api/*"], "node": "manual"}]}
    theirs, mine = mapmodel.SystemMap(raw), search.Map(raw)
    answers = {path: mine.owner(path) for path in ("src/api/x.py", "src/web/x.py", "src/x.py", "docs/a.md", "docs/api/a.md", "other.py")}
    assert answers == {path: theirs.node_for(path) or "" for path in answers}
    assert answers == {"src/api/x.py": "narrow", "src/web/x.py": "narrow", "src/x.py": "wide", "docs/a.md": "", "docs/api/a.md": "manual", "other.py": ""}


def test_AC_016_a_persons_own_git_settings_do_not_change_the_hits(tmp_path, monkeypatch):
    larger, inner = tmp_path / "larger", tmp_path / "inner"
    root = plain_copy(larger / "apps" / "shop")
    write(larger, "elsewhere/other.js", "formatMoney, elsewhere in the larger repository\n")
    write(inner, "lib.js", "formatMoney, in a repository of its own\n")
    for repository in (inner, larger):
        git(repository, "init", "-q")
        git(repository, "add", "-A")
        git(repository, "commit", "-q", "-m", "a project in a folder of a larger repository, and a repository to put inside it")
    git(root, "-c", "protocol.file.allow=always", "submodule", "--quiet", "add", inner.as_posix(), "vendor/inner")
    git(larger, "commit", "-q", "-m", "the other repository as a submodule of the project")
    before = find(root, "formatMoney", spec=FIXTURE_SPEC)
    assert places(before) == SIX, "paths start at the project's folder; what lies outside it, or in a submodule, is not searched"

    settings = tmp_path / "gitconfig"
    settings.write_bytes(b"[grep]\n\tcolumn = true\n\tfullName = true\n\tlineNumber = false\n\tpatternType = perl\n"
                         b"[color]\n\tui = always\n\tgrep = always\n[core]\n\tquotePath = true\n[submodule]\n\trecurse = true\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(settings))
    assert git(root, "config", "grep.fullName") == "true", "this git does not read GIT_CONFIG_GLOBAL, so nothing was tried"
    as_git_prints_it = git(root, "grep", "-F", "-e", "formatMoney")
    assert "apps/shop/" in as_git_prints_it and "\x1b[" in as_git_prints_it and "vendor/inner/" in as_git_prints_it, \
        "the settings do not change what git prints, so nothing was tried"

    after = find(root, "formatMoney", spec=FIXTURE_SPEC)
    assert list(after) == list(before) and after.groups == before.groups
    assert places(find(root, r"format(Money|Date)\(", regex=True)) == CALLS
    assert kit(root, "search", "formatMoney")[1].splitlines()[0] == f"{LIB}:2: function formatMoney(cents) {{  [shop-shared-lib, medium]"


def test_AC_017_a_path_is_given_as_it_is_whatever_characters_it_holds(shop):
    names = ["docs/gr\u00fc\u00dfe.md", "docs/two words.md"] + ([] if os.name == "nt" else ["docs/a:b.md"])   # no colon in a name on Windows
    for name in names:
        write(shop, name, "needle-AC-017\n")
    git(shop, "add", "docs")
    assert places(find(shop, "needle-AC-017")) == [(name, 1) for name in sorted(names)]
    assert kit(shop, "search", "needle-AC-017")[1].splitlines()[:len(names)] == [f"{name}:1: needle-AC-017" for name in sorted(names)]

    answer = (b"a.txt\x001\x00one\n" b"dir/two words:x.md\x0012\x00two: with a colon\n" b"odd\nname.txt\x003\x00three\n"
              b"nul.txt\x004\x00four\x00after the NUL\n" + "gr\u00fc\u00dfe.md\x005\x00f\u00fcnf\n".encode("utf-8") + b"last.txt\x0060\x00\n")
    whole = [("a.txt", 1, "one"), ("dir/two words:x.md", 12, "two: with a colon"), ("odd\nname.txt", 3, "three"),
             ("nul.txt", 4, "four\0after the NUL"), ("gr\u00fc\u00dfe.md", 5, "f\u00fcnf"), ("last.txt", 60, "")]
    for size in (1 << 16, *range(1, len(answer) + 2)):
        assert list(search._records(io.BytesIO(answer), size)) == whole, f"read {size} bytes at a time"
    assert list(search._records(io.BytesIO(b""))) == []
    for broken in (b"no separators at all\n", answer + b"cut.txt\x007"):
        with pytest.raises(core.KitError, match="could not be read"):
            list(search._records(io.BytesIO(broken)))
    found = search.Hits([{"path": "odd\nname.txt", "line": 3, "text": "three", "node": "", "tier": "", "group": "rest"}], total=1)
    assert search.plain(found)[0] == "odd?name.txt:3: three", "a name cannot start a line of its own in the output"


def test_AC_018_a_character_the_output_cannot_write_is_printed_as_a_question_mark(shop, monkeypatch):
    write(shop, "docs/words.md", "needle-AC-018 \u65e5\u672c\u8a9e and \u20ac\n")
    git(shop, "add", "docs/words.md")
    with pytest.raises(UnicodeEncodeError):   # what a plain print does with such a line
        print("\u65e5\u672c\u8a9e", file=io.TextIOWrapper(io.BytesIO(), encoding="cp1252"))
    written = io.BytesIO()
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(written, encoding="cp1252", newline="\n"))
    code = main(["--root", str(shop), "search", "needle-AC-018"])
    sys.stdout.flush()
    assert code == 0
    assert written.getvalue().decode("cp1252").splitlines() == ["docs/words.md:1: needle-AC-018 ??? and \u20ac", "",
                                                                "1 hit in the files git tracks, all shown."]

    own_rule = io.BytesIO()   # as PYTHONIOENCODING=cp1252:backslashreplace sets it
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(own_rule, encoding="cp1252", errors="backslashreplace", newline="\n"))
    code = main(["--root", str(shop), "search", "needle-AC-018"])
    sys.stdout.flush()
    assert code == 0
    assert own_rule.getvalue().decode("cp1252").splitlines()[0] == "docs/words.md:1: needle-AC-018 \\u65e5\\u672c\\u8a9e and \u20ac"


def test_AC_019_a_spec_or_a_node_that_cannot_order_or_own_anything_is_said_so(shop):
    write(shop, "specs/050-nothing/spec.md", spec_md("050-nothing", ""))
    write(shop, "specs/051-unknown/spec.md", spec_md("051-unknown", "shop-orders, shop-warehouse"))
    none = find(shop, "formatMoney", spec="050-nothing")
    assert places(none) == SIX and {hit["group"] for hit in none} == {"rest"}
    assert none.notes == ["050-nothing names no node under `touches`, so the hits are in one group."]
    rows = kit(shop, "search", "formatMoney", "--spec", "050-nothing")[1].splitlines()
    assert rows[0].startswith(f"{LIB}:2: ") and rows[-2] == none.notes[0], "no heading, and the sentence before the last line"

    some = find(shop, "formatMoney", spec="051-unknown")
    assert some.touched == ["shop-orders"] and some.notes == ["051-unknown touches shop-warehouse, which the system map does not have."]
    assert places(some)[:2] == [(ORDERS, 2), (ORDERS, 7)]

    code, out = kit(shop, "search", "provider", "--node", "payments-provider")   # a node of the map that has no files here
    assert code == 1
    assert out == "The map's index names no path for payments-provider, so no file belongs to it.\nNo hits in the files git tracks.\n"
