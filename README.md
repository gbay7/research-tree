# Research Tree

A Claude Code skill that keeps a research project's history as a living tree, on a page you can open from any
device.

Long research gets lost: after each experiment several next steps are suggested, one is followed deep, the others
are forgotten, and months later nobody remembers why a direction was dropped. The Research Tree records:

- every experiment: what it asked, what was done, what was found, and a one-line verdict;
- every option suggested along the way, and whether it was taken, dropped, overtaken, or is still open;
- a glossary of the project's terms;
- where the work stands now ("you are here") and a short summary.

The page is a claude.ai artifact with a small database. Claude writes to it as the work goes; you read it, change a
status, write a note or add an idea from the page. One page holds any number of projects.

## Install

In Claude Code:

```
/plugin marketplace add gbay7/research-tree
/plugin install research-tree@research-tree
```

or from a terminal:

```
claude plugin marketplace add gbay7/research-tree
claude plugin install research-tree@research-tree
```

Requires Claude Code signed in to claude.ai (the skill uses the Artifact and ArtifactData tools) and Python 3 for
the helper scripts.

## Use

Ask Claude to "start a research tree for this project", or to "add this experiment to the research tree". In a
project that already has a tree, the skill keeps it current after every experiment and every set of suggested next
steps, and reads your notes and ideas from the page at the start of a session.

A session without the skill can still use a tree: every tree holds a `meta/guide` document with the data model and
the working rules. Point the session at the tree's link and ask it to read that document first.

## Contents

- `skills/research-tree/SKILL.md`: the workflow.
- `skills/research-tree/assets/research-tree.html`: the page, published as is.
- `skills/research-tree/assets/example.json`: two small example projects.
- `skills/research-tree/references/`: the data model and the working rules.
- `skills/research-tree/scripts/`: `validate.py` (check a seed file or an exported tree), `to_batches.py` (import a
  whole history in batches), `guide_doc.py` (build a tree's `meta/guide` document).
