---
name: spec
description: Step 1 only - analyse a COBOL member with the cobol-analyst agent and write output/<ID>/spec.md, then summarise it for review.
argument-hint: <COBOL-ID> [<COBOL-ID> ...]
disable-model-invocation: true
---

Analyse these COBOL members, one after another: $ARGUMENTS

If no ID was given, list the folders in `input/` (one per program) and ask
which one.

For each ID whose folder `input/<ID>/` does not exist yet, run
`python scripts/collect_deps.py <ID> --dry-run`, show the file tree, and
after the user agrees run it again without `--dry-run`.

For each ID:

1. Launch the `cobol-analyst` subagent with the prompt
   `Analyse COBOL member <ID> and write output/<ID>/spec.md.`
2. Read `output/<ID>/spec.md` and show the user, in their language:
   status, purpose (2 lines), interface fields, quirks, open questions,
   number of test cases.
3. Remind the user: review the spec, then run `/gen <ID>`.
