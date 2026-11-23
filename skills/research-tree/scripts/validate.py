#!/usr/bin/env python3
"""Validate Research Tree data against references/schema.md.

Usage:
  python3 validate.py seed.json [more.json ...]   a seed file: {"projects": [...], "nodes": [...], "terms": [...]}
  python3 validate.py --dir EXPORT_DIR             documents exported from a tree's database with ArtifactData
                                                   (`out_dir`): EXPORT_DIR/{projects,nodes,terms}/<id>.json
Prints every problem found and exits 1 if there is any, 0 otherwise. Warnings (e.g. an email address in a text
field) are printed but do not fail the check.
"""
import glob
import json
import os
import re
import sys

ID_RE = re.compile(r"^[A-Za-z0-9-]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2})$")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")

KINDS = {
    "goal": {"active", "paused", "closed"},
    "line": {"active", "paused", "closed"},
    "experiment": {"planned", "running", "passed", "failed", "mixed", "done", "stopped"},
    "option": {"open", "dropped", "superseded"},
}
PROPOSERS = {"user", "claude", "both", "unknown"}
PROJECT_FIELDS = ["id", "title", "question", "summary", "current", "created", "updated", "order"]
NODE_FIELDS = ["id", "project", "parent", "order", "kind", "status", "title", "date", "asked", "did", "found",
               "verdict", "next", "proposed_by", "proposed_in", "terms", "links", "user_note", "updated"]
TERM_FIELDS = ["id", "project", "term", "aliases", "short", "definition", "node"]
TEXT_NODE = ["title", "asked", "did", "found", "verdict", "next", "user_note"]
TEXT_TERM = ["term", "short", "definition"]


def walk_strings(obj, path=""):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")


def validate(data, errors, warnings):
    def err(msg):
        errors.append(msg)

    for key in ("projects", "nodes", "terms"):
        if not isinstance(data.get(key), list):
            err(f"top level: '{key}' must be a list")
            return
    extra = set(data) - {"projects", "nodes", "terms"}
    if extra:
        err(f"top level: unexpected keys {sorted(extra)}")

    projects, nodes, terms = data["projects"], data["nodes"], data["terms"]
    all_ids = {}
    for coll, items in (("projects", projects), ("nodes", nodes), ("terms", terms)):
        for it in items:
            i = it.get("id")
            if not isinstance(i, str) or not ID_RE.match(i):
                err(f"{coll}: bad id {i!r}")
                continue
            if (coll, i) in all_ids:
                err(f"{coll}: duplicate id {i}")
            all_ids[(coll, i)] = it

    pids = {p["id"] for p in projects if isinstance(p.get("id"), str)}
    nids = {n["id"]: n for n in nodes if isinstance(n.get("id"), str)}
    tids = {t["id"]: t for t in terms if isinstance(t.get("id"), str)}

    # projects
    for p in projects:
        pid = p.get("id")
        for f in PROJECT_FIELDS:
            if f not in p:
                err(f"project {pid}: missing field '{f}'")
        for f in ("created", "updated"):
            if f in p and not (isinstance(p[f], str) and DATE_RE.match(p[f])):
                err(f"project {pid}: {f} must be YYYY-MM-DD, got {p[f]!r}")
        cur = p.get("current")
        if cur not in nids:
            err(f"project {pid}: current {cur!r} is not a node")
        elif nids[cur].get("project") != pid:
            err(f"project {pid}: current {cur} belongs to another project")
        if not isinstance(p.get("order"), (int, float)):
            err(f"project {pid}: order must be a number")

    # nodes
    for n in nodes:
        i = n.get("id", "?")
        for f in NODE_FIELDS:
            if f not in n:
                err(f"node {i}: missing field '{f}'")
        extra = set(n) - set(NODE_FIELDS)
        if extra:
            err(f"node {i}: unexpected fields {sorted(extra)}")
        proj = n.get("project")
        if proj not in pids:
            err(f"node {i}: project {proj!r} does not exist")
        elif isinstance(i, str) and not i.startswith(proj + "--"):
            err(f"node {i}: id must be '{proj}--<slug>'")
        kind, status = n.get("kind"), n.get("status")
        if kind not in KINDS:
            err(f"node {i}: bad kind {kind!r}")
        elif status not in KINDS[kind]:
            err(f"node {i}: status {status!r} not allowed for kind {kind}")
        par = n.get("parent")
        if par is not None:
            if par not in nids:
                err(f"node {i}: parent {par!r} does not exist")
            elif nids[par].get("project") != proj:
                err(f"node {i}: parent {par} is in another project")
        if (par is None) != (kind == "goal"):
            err(f"node {i}: parent must be null exactly for the goal (kind {kind}, parent {par!r})")
        pin = n.get("proposed_in")
        if pin is not None and pin not in nids:
            err(f"node {i}: proposed_in {pin!r} does not exist")
        if n.get("proposed_by") not in PROPOSERS:
            err(f"node {i}: bad proposed_by {n.get('proposed_by')!r}")
        d = n.get("date")
        if d is not None and not (isinstance(d, str) and DATE_RE.match(d)):
            err(f"node {i}: date must be YYYY-MM-DD or null, got {d!r}")
        u = n.get("updated")
        if not (isinstance(u, str) and TS_RE.match(u)):
            err(f"node {i}: updated must be an ISO timestamp, got {u!r}")
        if not isinstance(n.get("order"), (int, float)):
            err(f"node {i}: order must be a number")
        for f in TEXT_NODE:
            if f in n and not isinstance(n[f], str):
                err(f"node {i}: {f} must be a string")
        if not n.get("title"):
            err(f"node {i}: empty title")
        elif len(n["title"]) > 80:
            err(f"node {i}: title longer than 80 characters ({len(n['title'])})")
        if kind == "option":
            if n.get("did") or n.get("found"):
                err(f"node {i}: an option has empty did and found")
            if not n.get("next") and n.get("proposed_by") != "user":   # ideas added from the page have no 'next'
                err(f"node {i}: an option needs 'next'")
        if kind == "experiment":
            # what an experiment must say depends on how far it got
            need = {"planned": ("asked",), "running": ("asked", "did"), "stopped": ("asked", "verdict")}.get(
                status, ("asked", "did", "found", "verdict"))
            for f in need:
                if not n.get(f):
                    err(f"node {i}: a {status} experiment needs '{f}'")
        if not isinstance(n.get("terms"), list):
            err(f"node {i}: terms must be a list")
        else:
            for t in n["terms"]:
                if t not in tids:
                    err(f"node {i}: term {t!r} does not exist")
            if len(set(n["terms"])) != len(n["terms"]):
                err(f"node {i}: duplicate terms")
        if not isinstance(n.get("links"), list):
            err(f"node {i}: links must be a list")
        else:
            for l in n["links"]:
                if not (isinstance(l, dict) and set(l) == {"label", "ref"}
                        and all(isinstance(l[k], str) and l[k] for k in ("label", "ref"))):
                    err(f"node {i}: bad link {l!r}")

    # one root per project, no cycles, every node reaches its root
    for pid in pids:
        roots = [n["id"] for n in nodes if n.get("project") == pid and n.get("parent") is None]
        if len(roots) != 1:
            err(f"project {pid}: expected exactly one root, found {len(roots)}: {roots}")
    for i in nids:
        seen, cur = set(), i
        while cur is not None and cur in nids:
            if cur in seen:
                err(f"node {i}: parent chain has a cycle")
                break
            seen.add(cur)
            cur = nids[cur].get("parent")
    # sibling orders unique
    sib = {}
    for n in nodes:
        key = (n.get("project"), n.get("parent"), n.get("order"))
        if key in sib:
            err(f"node {n.get('id')}: same order as sibling {sib[key]}")
        sib[key] = n.get("id")

    # terms
    for t in terms:
        i = t.get("id", "?")
        for f in TERM_FIELDS:
            if f not in t:
                err(f"term {i}: missing field '{f}'")
        extra = set(t) - set(TERM_FIELDS)
        if extra:
            err(f"term {i}: unexpected fields {sorted(extra)}")
        proj = t.get("project")
        if proj not in pids:
            err(f"term {i}: project {proj!r} does not exist")
        elif isinstance(i, str) and not i.startswith(proj + "--"):
            err(f"term {i}: id must be '{proj}--<slug>'")
        if t.get("node") is not None and t["node"] not in nids:
            err(f"term {i}: node {t['node']!r} does not exist")
        if not isinstance(t.get("aliases"), list) or not all(isinstance(a, str) for a in t.get("aliases", [])):
            err(f"term {i}: aliases must be a list of strings")
        for f in TEXT_TERM:
            if not (isinstance(t.get(f), str) and t[f]):
                err(f"term {i}: {f} must be a non-empty string")

    # a tree may be shared: flag email addresses so nobody's address travels with it by accident
    for path, s in walk_strings(data):
        if EMAIL_RE.search(s):
            warnings.append(f"{path}: contains an email address")


def load_dir(root):
    """Documents saved by ArtifactData with out_dir: <root>/<collection>/<id>.json, each the document's fields."""
    data = {"projects": [], "nodes": [], "terms": []}
    for coll in data:
        for path in sorted(glob.glob(os.path.join(root, coll, "*.json"))):
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
            if isinstance(doc.get("data"), dict) and "id" in doc:      # tolerate an {id, data, ...} wrapper
                doc = doc["data"]
            data[coll].append({"id": os.path.splitext(os.path.basename(path))[0], **doc})
    return data


def main(argv):
    args = argv[1:]
    if not args:
        print(__doc__)
        return 2
    if args[0] == "--dir":
        sources = [(d, lambda d=d: load_dir(d)) for d in args[1:]]
    else:
        sources = [(p, lambda p=p: json.load(open(p, encoding="utf-8"))) for p in args]
    total = 0
    for name, load in sources:
        errors, warnings = [], []
        try:
            data = load()
        except (OSError, json.JSONDecodeError) as e:
            errors.append(f"cannot read: {e}")
        else:
            validate(data, errors, warnings)
        for w in warnings:
            print(f"{name}: warning: {w}")
        if errors:
            print(f"{name}: {len(errors)} problem(s)")
            for e in errors:
                print("  " + e)
        else:
            print(f"{name}: OK ({len(data['projects'])} project(s), {len(data['nodes'])} nodes, "
                  f"{len(data['terms'])} terms)")
        total += len(errors)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
