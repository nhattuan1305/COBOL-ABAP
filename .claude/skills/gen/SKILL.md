---
name: gen
description: Step 2 only - generate ABAP (FM, DDIC structure, test report) from an existing output/<ID>/spec.md with the abap-developer agent.
argument-hint: <COBOL-ID> [<COBOL-ID> ...] [answers to open questions]
disable-model-invocation: true
---

Generate ABAP from the reviewed spec for: $ARGUMENTS

Words that are not COBOL IDs in the arguments are answers to open questions
or extra instructions: pass them on to the agent.

For each ID:

1. Check that `output/<ID>/spec.md` exists. If not, tell the user to run
   `/spec <ID>` first and stop.
2. If its `Status:` is `NEEDS-DECISION` and the arguments do not answer the
   BLOCKING questions, list those questions and stop.
3. Launch the `abap-developer` subagent with the prompt
   `Generate ABAP for <ID> from output/<ID>/spec.md.` plus the extra
   instructions.
4. Report to the user: files in `output/<ID>/`, lint result, open points
   from `report.md`, next manual steps (SE11 structure, SE37 FM, run
   `ZTEST_<ID>`).
