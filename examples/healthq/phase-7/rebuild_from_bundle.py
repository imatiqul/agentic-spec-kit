#!/usr/bin/env python3
"""Recreate branches from a git bundle under the repository owner's own identity.

    python3 rebuild_from_bundle.py <repository> <bundle> <plan.json> [--check] [--identity-of <commit>] [--map <file>]

The bundle holds commits made in a workspace under a placeholder identity. Each commit is recreated here with the
same tree, the same message and the same author date, authored and committed by the owner, with the attribution
trailers added. Nothing is checked out: the working tree and the index are not touched. Only objects and the named
branch refs are written. An existing branch is never moved.

The owner's identity is this repository's `user.name` and `user.email`. Where the repository has none configured,
`--identity-of <commit>` takes the author of a commit the owner already made in it.

`--map <file>` writes one line for each commit: the id it had in the workspace, the id it has here, its subject.
Records made in the workspace name commits by the first; the pushed history has the second.

plan.json: {"base": "<sha the first branch starts from>", "trailers": ["Co-Authored-By: ...", ...],
            "branches": [{"name": "sdd/x", "from": "base" | "<earlier branch name>", "tree": "<expected tree sha>"}]}
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

TMP = "refs/agentic/cloud/"


def git(repo, *args, env=None, text_in=None, ok=(0,)):
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env, input=text_in)
    if p.returncode not in ok:
        raise SystemExit(f"git {' '.join(args)} failed: {p.stderr.strip() or p.stdout.strip()}")
    return p.stdout.strip()


def with_trailers(message, trailers):
    body = message.rstrip("\n")
    missing = [t for t in trailers if t not in body]
    if not missing:
        return body + "\n"
    paragraphs = body.split("\n\n")
    last = paragraphs[-1].splitlines()
    block = len(paragraphs) > 1 and all(re.match(r"^[A-Za-z][A-Za-z-]*: \S", line) for line in last)
    return body + ("\n" if block else "\n\n") + "\n".join(missing) + "\n"


def option(argv, name):
    if name not in argv:
        return None, argv
    i = argv.index(name)
    if i + 1 >= len(argv):
        raise SystemExit(f"{name} needs a value")
    return argv[i + 1], argv[:i] + argv[i + 2:]


def identity(repo, of):
    if of:
        commit = git(repo, "rev-parse", "--verify", of + "^{commit}")
        name, email = git(repo, "log", "-1", "--format=%an%n%ae", commit).split("\n")[:2]
        return name, email, f"the author of {commit[:10]}"
    name = git(repo, "config", "user.name", ok=(0, 1))
    email = git(repo, "config", "user.email", ok=(0, 1))
    if not name or not email:
        raise SystemExit("this repository has no user.name or user.email configured; name a commit of the owner's with --identity-of")
    return name, email, "this repository's git configuration"


def main(argv):
    of, argv = option(argv, "--identity-of")
    map_path, argv = option(argv, "--map")
    check = "--check" in argv
    rest = [a for a in argv if a != "--check"]
    if len(rest) != 3:
        raise SystemExit(__doc__.strip().splitlines()[2].strip())
    repo, bundle, plan_path = rest
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    base = git(repo, "rev-parse", "--verify", plan["base"] + "^{commit}")
    name, email, source = identity(repo, of)
    for b in plan["branches"]:
        if git(repo, "rev-parse", "--verify", "-q", "refs/heads/" + b["name"], ok=(0, 1)):
            raise SystemExit(f"branch {b['name']} already exists here; it is not moved. Remove or rename it first")
    print(git(repo, "bundle", "verify", bundle).splitlines()[-1])
    if check:
        print(f"would recreate {len(plan['branches'])} branch(es) on {base[:10]} as {name}, from {source}")
        return 0
    git(repo, "fetch", "-q", bundle, "+refs/heads/*:" + TMP + "*")
    new_tip, cloud_tip, rows = {"base": base}, {"base": base}, []
    try:
        for b in plan["branches"]:
            cloud = git(repo, "rev-parse", TMP + b["name"])
            parent_new, parent_cloud = new_tip[b["from"]], cloud_tip[b["from"]]
            commits = git(repo, "rev-list", "--reverse", "--first-parent", f"{parent_cloud}..{cloud}").split()
            if not commits:
                raise SystemExit(f"{b['name']} has no commit beyond {b['from']}")
            for c in commits:
                parents = git(repo, "rev-list", "--parents", "-n", "1", c).split()[1:]
                if len(parents) != 1:
                    raise SystemExit(f"{c[:10]} is not a single-parent commit; this tool recreates straight lines only")
                tree = git(repo, "rev-parse", c + "^{tree}")
                message = with_trailers(git(repo, "log", "-1", "--format=%B", c), plan.get("trailers") or [])
                env = dict(os.environ, GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=email, GIT_COMMITTER_NAME=name,
                           GIT_COMMITTER_EMAIL=email, GIT_AUTHOR_DATE=git(repo, "log", "-1", "--format=%aI", c))
                parent_new = git(repo, "commit-tree", tree, "-p", parent_new, env=env, text_in=message)
                rows.append((b["name"], c, parent_new, message.splitlines()[0]))
                print(f"  {b['name']}: {c[:7]} -> {parent_new[:7]}  {message.splitlines()[0][:80]}")
            tree = git(repo, "rev-parse", parent_new + "^{tree}")
            if b.get("tree") and tree != b["tree"]:
                raise SystemExit(f"{b['name']}: the tree is {tree}, expected {b['tree']}; nothing was created for it")
            git(repo, "update-ref", "refs/heads/" + b["name"], parent_new, "")
            new_tip[b["name"]], cloud_tip[b["name"]] = parent_new, cloud
            print(f"{b['name']} -> {parent_new} (tree {tree}, {len(commits)} commit(s))")
    finally:
        for ref in git(repo, "for-each-ref", "--format=%(refname)", TMP).split():
            git(repo, "update-ref", "-d", ref)
    if map_path:
        lines = [f"{branch}\t{old}\t{new}\t{subject}" for branch, old, new, subject in rows]
        Path(map_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
