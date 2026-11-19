---
paths:
  - "output/**/spec.md"
  - "examples/**/spec.md"
---

# Spec writing rules

## Reader

The reader is an ABAP developer who has never seen COBOL. After reading
sections 1-9 once, they must be able to write the FM without asking.

## Structure

- Follow `.claude/skills/cobol-to-abap/templates/spec-template.md` exactly:
  same sections, same order. Write "none" rather than deleting a section.
- Sections 1-9: no COBOL syntax (`MOVE`, `EVALUATE`, `PIC`, `OCCURS`), no
  COBOL field names, no line numbers, no `x'00'`. Everything COBOL goes to
  Appendix A, with line numbers as printed by `scripts/read_cobol.py`.
- Rules (section 3) as tables a developer can code from: one row per
  character / situation / formula.
- Processing steps (section 4) as short ABAP-like pseudo-code, not prose.
- Test cases (section 9): one column per input and output field, exact
  values, so they can be pasted into the test report.

## Names

- ABAP names in sections 2 and 5 follow `.claude/rules/abap-naming.md`
  (IPS standard): `ldf_` / `lds_` / `ldt_` + the full words of the COBOL
  field (`INT-DNUM-X` → `ldf_int_dnum_x`); flags / counters / indexes as
  `ldf_flg_` / `ldf_cnt_` / `ldf_idx_` (`INT-DNUM-CNT` → `ldf_cnt_int_dnum`).
  Never `lv_` / `ls_` / `lt_`.
- Use these ABAP names everywhere in sections 1-9. The developer copies them
  as they are.

## Language and style

- Language: "Spec language" in `CLAUDE.md`. Keep original Japanese terms in
  parentheses the first time only.
- Short sentences, one idea each. Result first, reason after.
- Plain words: "the first comma does not check the group before it", not
  "DELIMIT-FLG is NOT so DELIMIT-CNT is reset without validation".
- No proofs in sections 1-9. "Early RETURN is allowed" goes in section 7;
  why it is safe goes in Appendix A.3.

## Content

- Behavior, not syntax. Never smooth over a COBOL bug: list it in section 6.
- Edge cases come from tracing concrete inputs (blank, boundaries, invalid
  characters, max length, alignment). Each one gets a test case.
- `Status:` is `READY`, or `NEEDS-DECISION` when an open question is
  `BLOCKING`.
