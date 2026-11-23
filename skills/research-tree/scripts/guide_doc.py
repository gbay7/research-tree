#!/usr/bin/env python3
"""Build the `meta/guide` document for a tree: the data model plus the working rules, with the tree's own link,
so that any session pointed at the tree can keep it correctly without this skill.

Usage: python3 guide_doc.py TREE_URL OUT.json
Then: ArtifactData set, collection "meta", doc_id "guide", file_path OUT.json (with if_version if it exists).
"""
import datetime
import json
import os
import sys


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    url, out = argv[1], argv[2]
    ref = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references")
    schema = open(os.path.join(ref, "schema.md"), encoding="utf-8").read()
    rules = open(os.path.join(ref, "working-rules.md"), encoding="utf-8").read().replace("{URL}", url)
    text = schema.rstrip() + "\n\n" + rules
    json.dump({"title": "How to use this tree (data model and working rules)", "text": text,
               "updated": datetime.date.today().isoformat()}, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"wrote {out} ({len(text)} characters)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
