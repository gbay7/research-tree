# Research Tree: data model

One page (a claude.ai artifact with a database) serves any number of projects. The data lives in the artifact's
database as documents under collections. Claude writes them as the work goes; the owner reads them from any device
and can change a status, write a note, or add an idea from the page.

All ids: ASCII letters, digits and hyphens only (the page uses them in `#` links). Dates: `YYYY-MM-DD`.
Text fields are Markdown (paragraphs, lists, **bold**, `code`, links, small tables). Use plain words: the owner
reads the tree months later, often on a phone.

## `projects/<projectId>`

| field | type | meaning |
|---|---|---|
| `title` | string | the project's name, a few words |
| `question` | string | the overall research question, 1-2 sentences |
| `summary` | string (md) | where the project stands now, a short paragraph |
| `current` | nodeId | the node we are on now ("you are here") |
| `created` | date | |
| `updated` | date | |
| `order` | number | position in the project list |

## `nodes/<nodeId>` (nodeId = `<projectId>--<slug>`)

| field | type | meaning |
|---|---|---|
| `project` | projectId | |
| `parent` | nodeId or null | null only for the project's single root |
| `order` | number | position among its siblings (chronological by default); unique among siblings |
| `kind` | `goal` / `line` / `experiment` / `option` | see below |
| `status` | see below | depends on the kind |
| `title` | string | short, plain words, at most ~70 characters; a code name may follow in parentheses, e.g. "Baseline on the held-out set (baseline-ho)" |
| `date` | date | when it was run (experiment) or proposed (option) |
| `asked` | string (md) | the question it answers, or why it was done or proposed, 1-3 sentences |
| `did` | string (md) | what was done: setup, the decision rule if one was fixed beforehand. Empty for an option |
| `found` | string (md) | findings, with the key numbers. Empty for an option |
| `verdict` | string | one line: the outcome in plain words |
| `next` | string (md) | for an option: what it would take (cost, data, hardware, ...). For a dropped option: why it was dropped |
| `proposed_by` | `user` / `claude` / `both` / `unknown` | whose idea it was |
| `proposed_in` | nodeId or null | the node after which it was suggested (usually the parent) |
| `terms` | termId[] | glossary terms this node uses |
| `links` | {label, ref}[] | `ref` is a URL (https://...) or a plain reference such as a commit, a file path or a document name |
| `user_note` | string | written by the owner from the page; Claude never writes it |
| `updated` | ISO timestamp | |

Kinds and statuses:

- `goal`: the project's root, one per project. Status `active` / `paused` / `closed`.
- `line`: a research direction that groups experiments. Status `active` / `paused` / `closed`.
- `experiment`: something that was carried out (a run, a test, an analysis, a build, a write-up). Status:
  `planned` (decided, not run), `running`, `passed`, `failed`, `mixed` (part passed), `done` (no pass/fail test),
  `stopped` (abandoned before or during the run).
- `option`: something suggested that was NOT carried out (or not yet). Status: `open` (still possible: we may
  return to it), `dropped` (decided against; say why in `next`), `superseded` (overtaken by something else).
  When an option is taken it becomes an `experiment` (same node: kind and status change, the history stays).

Use only these kinds and statuses: the page draws each one with its own shape and colour, and anything else shows
up as unknown.

## `terms/<termId>` (termId = `<projectId>--<slug>`)

| field | type | meaning |
|---|---|---|
| `project` | projectId | |
| `term` | string | the word as used, e.g. "baseline" |
| `aliases` | string[] | other spellings to recognise in text |
| `short` | string | one line, plain words |
| `definition` | string (md) | 2-5 sentences |
| `node` | nodeId or null | where it first appeared |

The page underlines a term wherever it appears in node text and shows its definition on click.

## What the page itself writes

The owner can, from the page:

- change a node's `status` (and `updated`);
- write `user_note` on any node;
- add an idea under a node: a new `option` node with id `<projectId>--idea-<milliseconds>`, status `open`,
  `proposed_by: "user"`, the idea in `title` and `asked`, `next` empty.

So between sessions, statuses may have changed and new ideas may be waiting. Read them before proposing anything.

## `meta/guide`

`{title, text, updated}`: this data model plus the working rules, written into every tree so that a session
without this skill can be pointed at the tree and still keep it correctly (`scripts/guide_doc.py` builds it).
The page ignores the `meta` collection.

## File form (for seeding or importing)

`<projectId>.json`: `{"projects": [{"id": ..., ...}], "nodes": [{"id": ..., ...}], "terms": [{"id": ..., ...}]}`,
the same fields as above plus `id`. `scripts/validate.py` checks such a file, and `scripts/to_batches.py` turns it
into database writes (each entry becomes `<collection>/<id>`). `assets/example.json` is a complete example with
two small projects.
