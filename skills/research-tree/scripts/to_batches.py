#!/usr/bin/env python3
"""Turn a seed file into ArtifactData batch writes, for creating or importing a whole project at once.

Usage: python3 to_batches.py seed.json OUT_DIR

Writes one JSON file per document under OUT_DIR/docs/<collection>/<id>.json (the document's fields, without `id`)
and the batches under OUT_DIR/batch-01.json, batch-02.json, ...: each a list of at most 50 write entries
{"op": "set", "collection", "doc_id", "file_path"} to pass as `writes` to ArtifactData's `batch` action, in order.
Terms go first, then nodes (parents before children), then projects, so a project never points at a missing node.

These are creations: an entry for a document that already exists in the tree is refused without `if_version`.
To change existing documents, read them and write with `update` and `if_version` instead.
Validate the seed first (validate.py).
"""
import json
import os
import sys

BATCH = 50


def depth(nid, nodes):
    d, seen = 0, set()
    while nodes.get(nid, {}).get("parent") and nid not in seen:
        seen.add(nid)
        nid = nodes[nid]["parent"]
        d += 1
    return d


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    seed, out = argv[1], os.path.abspath(argv[2])
    data = json.load(open(seed, encoding="utf-8"))
    nodes = {n["id"]: n for n in data.get("nodes", [])}
    ordered = ([("terms", t) for t in data.get("terms", [])]
               + [("nodes", n) for n in sorted(nodes.values(), key=lambda n: (depth(n["id"], nodes), n["id"]))]
               + [("projects", p) for p in data.get("projects", [])])
    writes = []
    for coll, doc in ordered:
        doc = dict(doc)
        did = doc.pop("id")
        path = os.path.join(out, "docs", coll, did + ".json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(doc, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        writes.append({"op": "set", "collection": coll, "doc_id": did, "file_path": path})
    n = 0
    for n, i in enumerate(range(0, len(writes), BATCH), 1):
        json.dump(writes[i:i + BATCH], open(os.path.join(out, f"batch-{n:02d}.json"), "w"), indent=1)
    print(f"{len(writes)} documents in {n} batch(es) under {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
