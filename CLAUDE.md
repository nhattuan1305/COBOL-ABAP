# COBOL → ABAP conversion kit

This project converts COBOL subroutines/batches (typically IBM i / AS400 COBOL)
into ABAP Classic function modules, in separated steps:

1. `cobol-analyst` agent reads the COBOL source and writes a spec (`spec.md`).
2. `cobol-tester` agent runs the original COBOL locally (GnuCOBOL) on the
   spec's test cases, for pure-logic subroutines. The COBOL result is the
   reference when it disagrees with the spec.
3. `abap-developer` agent generates ABAP **only from that spec**, checking syntax
   against SAP documentation via the `sap-docs` MCP server.

The spec is the contract between the steps. A human reviews it before step 3.

## Project settings (edit these per project)

| Setting | Value |
|---|---|
| Target system | SAP S/4HANA, ABAP Classic (Standard ABAP, not ABAP Cloud / RAP) |
| Minimum ABAP release | 7.50 |
| Source platform | IBM i COBOL/400 (ILE COBOL), text export in Shift-JIS |
| Received-source folder | `source_dirs` in `config.json` (per machine, never hard-code it) |
| GnuCOBOL folder | `gnucobol_dir` in `config.json` (per machine; optional, only for `/cobol-test`) |
| Function group name | `Z_` + first 4 chars of the COBOL ID (SCCS010 → `Z_SCCS`) |
| Function module name | `Z_` + COBOL ID (SCCS010 → `Z_SCCS010`) |
| Parameter structure | `Z` + copybook name (SCCS01R → `ZSCCS01R`) |
| Test report name | `ZTEST_` + COBOL ID |
| Package | `$TMP` (until the project package is given) |
| Spec language | Vietnamese (keep Japanese/original terms in parentheses) |
| Code comment language | English |

Project-specific naming conventions from the customer go into
`.claude/rules/abap-naming.md`, section "Project-specific".

## Folders

- `input/<COBOL-ID>/` one folder per program: the program plus every file
  it COPYs or CALLs (all levels). Filled by `scripts/collect_deps.py`.
  Files are read-only.
- `output/<COBOL-ID>/` everything produced for one program:
  `spec.md`, `cases.json`, `cobol-test.md`, `<FM>.abap`, `<STRUCT>.ddic.md`,
  `ZTEST_<ID>.abap`, `report.md`.
- `.work/<COBOL-ID>/` build folder of `run_cobol.py` (prepared source copies,
  driver, executable). Safe to delete.
- `effort/effort-log.csv` time log per conversion.
- `examples/case-study-SCCS010/` a finished conversion to copy the style from.

## Commands

- `/convert <ID> [<ID>...]` full pipeline: spec → COBOL run → review stop → ABAP.
- `/spec <ID>` only analyze COBOL and write the spec.
- `/cobol-test <ID>` only run the original COBOL against the spec's test cases.
- `/gen <ID>` only generate ABAP from an existing `output/<ID>/spec.md`.

## Working rules

- Read COBOL with `python scripts/read_cobol.py --root input/<ID> <name>`.
  Never open Shift-JIS files with the Read tool: Japanese text comes back
  garbled.
- To create `input/<ID>/`, run `python scripts/collect_deps.py <ID> --dry-run`,
  then without `--dry-run`. It reads the folder set in `config.json`; that
  folder is read-only.
- Behavior must match COBOL exactly, including bugs and odd edge cases.
  Do not "improve" the logic. List suspicious behavior in the spec instead.
- When something cannot be decided from the source (file I/O, DB access,
  missing called program, unclear intent), write it as an open question in the
  spec. Do not invent behavior.
- Nothing in this kit writes to an SAP system. Creating objects in SAP is a
  manual step (SE11 / SE37 / SE38) or a separate, explicit request.
- Never delete or change existing SAP objects; only create new ones.

## Reply style

Reply to the user in the language they write in. Short sentences, result first.
