---
name: convert
description: Full COBOL-to-ABAP pipeline for one or more COBOL members - cobol-analyst writes the spec, cobol-tester confirms it by running the COBOL (pure-logic programs), the user reviews it, then abap-developer generates the ABAP. Logs AI time to effort/effort-log.csv.
argument-hint: <COBOL-ID> [<COBOL-ID> ...]
disable-model-invocation: true
---

Convert these COBOL members, one after another: $ARGUMENTS

If no ID was given, list the folders in `input/` (one per program) and ask
which one.

For each ID whose folder `input/<ID>/` does not exist yet, run
`python scripts/collect_deps.py <ID> --dry-run`, show the file tree, and
after the user agrees run it again without `--dry-run`.

For each ID:

1. **Start time**: run
   `python -c "import datetime as d; print(f'{d.datetime.now():%Y-%m-%d %H:%M}')"`
   and keep the value.
2. **Spec**: launch the `cobol-analyst` subagent with the prompt
   `Analyse COBOL member <ID> and write output/<ID>/spec.md.`
3. **COBOL run**: if spec section 1 says "Database / files: none", launch
   the `cobol-tester` subagent with the prompt
   `Run COBOL <ID> against output/<ID>/spec.md section 9.`
   Otherwise note "not pure logic, COBOL run skipped".
4. **Review stop**: read `output/<ID>/spec.md`. Show the user, in their
   language: purpose (2 lines), interface fields, quirks, open questions,
   number of test cases, and the COBOL run result (PASS / FAIL, new quirks
   from probes). Then ask: "Spec OK? Answer the open questions or say go."
   Wait for the answer. Count this waiting time as human time: note the
   time you asked and the time the user answered.
5. If the user corrects the spec, update `output/<ID>/spec.md` (or relaunch
   `cobol-analyst` with the corrections), re-run step 3, then go back to
   step 4.
6. **ABAP**: launch the `abap-developer` subagent with the prompt
   `Generate ABAP for <ID> from output/<ID>/spec.md.` plus the user's
   answers to open questions, if any.
7. **End time** (same command as step 1).
8. **Log**: append one line to `effort/effort-log.csv` (create the file with
   its header if missing):
   `<ID>,<start>,<end>,<AI minutes = end - start - review wait>,,,"<short note>"`
   The two empty columns are for the user: manual estimate (h) and total
   actual time incl. SAP work and testing (h).
9. **Report** to the user: files in `output/<ID>/`, lint result, open
   points from `report.md`, and the next manual steps (SE11 structure,
   SE37 FM, run `ZTEST_<ID>`).
