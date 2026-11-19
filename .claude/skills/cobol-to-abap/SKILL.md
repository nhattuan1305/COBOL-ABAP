---
name: cobol-to-abap
description: Method and reference for converting IBM i COBOL subroutines into ABAP Classic function modules - reading Shift-JIS sources, writing a behavior spec, COBOL-to-ABAP type and statement mapping, known traps (truncation vs rounding, MOD sign, c-to-n conversion, EBCDIC order, DBCS), spec template and output file layout. Use when analysing COBOL source, writing or reviewing a conversion spec, or generating ABAP from such a spec.
---

# COBOL → ABAP conversion method

Two steps, two agents, one contract:

```
input/<ID>/ ──► cobol-analyst ──► output/<ID>/spec.md ──► (human review) ──► abap-developer ──► output/<ID>/*.abap
```

The analyst never writes ABAP. The developer never reads COBOL to invent
behavior: if the spec is wrong or incomplete, it stops and reports.

## Files

- [reference/cobol-abap-mapping.md](reference/cobol-abap-mapping.md):
  type mapping, statement mapping, traps (**TRAP**) and items that need a
  human decision (**DECIDE**). Read the sections that match the statements
  found in the program.
- [templates/spec-template.md](templates/spec-template.md): exact structure
  of `output/<ID>/spec.md`.
- `examples/case-study-SCCS010/` (project root): a finished conversion
  (spec, FM, DDIC structure, test report). Match its level of detail.

## Output layout per program

```
output/<ID>/
  spec.md               analyst: behavior spec (template above)
  Z<copybook>.ddic.md   developer: SE11 structure definition (one per copybook)
  Z_<ID>.abap           developer: full FUNCTION ... ENDFUNCTION incl. interface comment
  ZTEST_<ID>.abap       developer: report that runs every spec test case and prints PASS/FAIL
  report.md             developer: lint result, docs checked, assumptions, dependencies
```

## Reading COBOL

- Sources of one program are in `input/<ID>/` (filled by
  `python scripts/collect_deps.py <ID>`).
- `python scripts/read_cobol.py --root input/<ID> <name>`: full source with
  line numbers. Add `--refs` for only COPY / CALL lines.
- Read every copybook of the LINKAGE SECTION / `USING`, and the copybooks of
  WORKING-STORAGE that hold logic (tables, constants).
- For called programs: read their copybook (interface) always; read their
  source only if the spec needs their behavior.
- Ignore columns 1-6 markers; `!DEL!` lines are deleted code.

## Finding edge cases

Trace the code by hand with concrete inputs. Minimum set:
blank / all spaces, minimum and maximum length, each invalid character class,
boundary values of every numeric limit, each `WHEN` branch, each error path.
Ask after each one: is the error flag ever reset? Does a loop keep running
after an error? What is left in output fields on error?

## Writing ABAP

- Follow `.claude/rules/abap-naming.md` and `.claude/rules/abap-coding.md`
  (they load automatically when editing `output/**/*.abap`).
- Before using a statement whose exact semantics matter (conversions,
  rounding, string functions, `CO`/`CA`, `SPLIT`, `FIND`), look it up:
  `mcp__sap-docs__search` (query in English, `abapFlavor: "standard"`,
  `includeSamples: false`) then `mcp__sap-docs__fetch` the best hit.
  Record the doc IDs in `report.md`.
- Lint: wrap the FM body in a test report with local `TYPES` for the DDIC
  structure and run `mcp__sap-abap__abap_lint` with `version: "Standard"`.
  0 errors required.
