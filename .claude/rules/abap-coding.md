---
paths:
  - "output/**/*.abap"
  - "examples/**/*.abap"
---

# ABAP coding rules for converted code

## Target

- ABAP Classic (Standard ABAP) for the release in `CLAUDE.md`. No RAP, no
  ABAP Cloud-only APIs. Syntax up to that release is fine (inline
  declarations, string templates, `NEW`, `VALUE`). If unsure whether a
  statement exists in the release, check `abap_feature_matrix` (sap-docs).
- One COBOL subroutine = one function module. Interface mirrors
  `PROCEDURE DIVISION USING <copybook>`: a single
  `CHANGING cs_<copybook> TYPE z<copybook>` passed by reference
  ("Pass Value" off), unless the spec says otherwise.
- Return codes keep the exact COBOL values (`'OK'`, `'NG'`, `'00'`...).

## Faithfulness

- Same result as COBOL for every input, including quirks listed in the spec.
  Never fix a COBOL bug silently.
- Every COBOL SECTION/paragraph is traceable: put a comment like
  `" COBOL CHECK2-PROC (L174-311)` above the matching block.
- Early `RETURN` is allowed only when the spec confirms the COBOL error flag
  is never reset afterwards.
- `PROGRAM-ID ... IS INITIAL` → all WORKING-STORAGE as local `DATA` in the FM.
  Without `IS INITIAL`, values survive between calls → global data in the TOP
  include; the spec must say which fields rely on that.
- Numeric moves and `COMPUTE` without `ROUNDED` truncate in COBOL; ABAP
  rounds. Reproduce truncation explicitly (see
  `.claude/skills/cobol-to-abap/reference/cobol-abap-mapping.md`).

## Function module rules

- No `MESSAGE`, `WRITE`, screen or popup inside the FM. No `COMMIT WORK`
  unless the spec requires it.
- Calls to other converted subroutines use `CALL FUNCTION 'Z_<ID>'` even if
  that FM does not exist yet; list it in the output report.
- Header comment: COBOL ID, English title, one-line summary, spec path.
  No change-history block.
- Comments in English and 7-bit ASCII only (no Japanese, no `§`): keep
  original Japanese titles in the spec. Comments explain *why* or the COBOL
  origin, not *what*.

## Before handing over

- Lint with `abap_lint` (sap-abap MCP, `version: "Standard"`) through a
  wrapper report that defines the DDIC structure as local `TYPES`.
  Result must be 0 errors. Report remaining warnings.
- Ignore abaplint naming-style findings (`types_naming`, `local_variable_names`
  and similar) that ask for `TY_`, `lv_`... instead of the IPS prefixes, and
  `types_naming` on the local copy of the DDIC structure in the wrapper:
  `.claude/rules/abap-naming.md` (IPS) wins over abaplint's default style.
