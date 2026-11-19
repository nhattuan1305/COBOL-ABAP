# Case study: SCCS010 (numeric item digit check)

A finished conversion, kept as the reference for style and level of detail.
Agents read it; people can read it to see what "done" looks like.

> The COBOL source in `input/` belongs to the customer project it came from.
> Remove `input/` before sharing this kit outside that project team.

## What it is

COBOL subroutine (355 lines) that validates a quantity string like
`-1,234.56` and converts it to a number. Converted to FM `Z_SCCS010` with
structure `ZSCCS01R`.

## Files

```
input/SCCS010/SCCS010.txt          COBOL source (Shift-JIS)
input/SCCS010/SCCS01R.txt          interface copybook
input/SCCS010/CVTCOMMON.txt        converter work area (not used by the logic)
output/SCCS010/spec.md             step 1: behavior spec (cobol-analyst)
output/SCCS010/cases.json          step 2: spec section 9 as machine-readable cases (cobol-tester)
output/SCCS010/cobol-test.md       step 2: result of running the original COBOL: 32 PASS
output/SCCS010/ZSCCS01R.ddic.md    step 3: SE11 structure
output/SCCS010/Z_SCCS010.abap      step 3: function module
output/SCCS010/ZTEST_SCCS010.abap  step 3: test report, 31 cases
output/SCCS010/report.md           step 3: lint, docs checked, desk check
```

Re-run the analysis on it with:

```
python scripts/read_cobol.py --root examples/case-study-SCCS010/input/SCCS010 SCCS010
```

## Lessons

- **The spec is where the value is.** Tracing inputs by hand found 7
  behaviors that are not in any design document: a blank string returns
  `OK` with 0, `1,23` is accepted as 123, `- 5` is accepted as -5, a lone `.`
  or `-` returns `OK`. A literal "clean" rewrite would have changed all of
  them.
- **Early `RETURN` is only safe after proving the error flag is never
  reset.** Here it was checked by reading the code and by comparing both
  versions on 300,000 random inputs.
- **Build the number as text, then convert once.** Digit-by-digit
  arithmetic would add rounding questions; `<13 digits>.<5 digits>` into a
  DEC 18,5 field has none.
- **A test report beats SE37** for 31 cases, and SE37 may strip leading
  blanks from input.

## Effort

Fill in after the SAP side (SE11, SE37, run `ZTEST_SCCS010`) is done:

| Step | Manual estimate | With AI (actual) |
|---|---|---|
| Read COBOL + spec | | |
| ABAP + test report | | |
| SAP objects + test run | | |
