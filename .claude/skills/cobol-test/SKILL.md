---
name: cobol-test
description: Run the original COBOL subroutine locally (GnuCOBOL) against the test cases of output/<ID>/spec.md with the cobol-tester agent, and report differences.
argument-hint: <COBOL-ID> [<COBOL-ID> ...]
disable-model-invocation: true
---

Test these COBOL members against their specs, one after another: $ARGUMENTS

For each ID:

1. Check that `output/<ID>/spec.md` exists. If not, tell the user to run
   `/spec <ID>` first and stop.
2. Launch the `cobol-tester` subagent with the prompt
   `Run COBOL <ID> against output/<ID>/spec.md section 9.`
3. Report to the user, in their language: PASS / FAIL / probe counts, each
   FAIL with expected vs COBOL result and the likely cause, surprising probe
   results, and the report path `output/<ID>/cobol-test.md`.
4. If there are real FAILs or new quirks, ask whether to update the spec
   (section 6 and 9) before running `/gen <ID>`.
