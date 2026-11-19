# SCCS010 → Z_SCCS010: developer report

## Files

| File | Content |
|---|---|
| `ZSCCS01R.ddic.md` | SE11 structure (5 components, built-in types) |
| `Z_SCCS010.abap` | Function module, function group `Z_SCCS` |
| `ZTEST_SCCS010.abap` | Test report, 31 cases from spec section 9 |

## Lint (abaplint, version Standard)

- `Z_SCCS010` (wrapped as FORM): 0 syntax errors. Only naming-style
  findings: `local_variable_names` (abaplint default `^L._`, IPS uses
  `ldf_`) and `types_naming` on the local copy of `ZSCCS01R`. Both ignored
  per `abap-coding.md`.
- `ZTEST_SCCS010`: 0 syntax errors. Only `types_naming` on `gts_case` /
  `gtt_case` (IPS prefixes) and the local structure copy (ignored).

## SAP documentation checked (sap-docs)

| Doc ID | Why |
|---|---|
| `ABENLOGEXP_STRINGS` | `CN` / `CA` respect trailing blanks for type `c`: a blank or half-blank digit count is not numeric, same as COBOL `NUMERIC` |
| `ABENCONVERSION_TYPE_C` | `c` → `p` accepts `0000000001234.56000`; only digits beyond the target decimals are rounded (none here) |
| `ABENARITH_OPERATORS` | No division or `MOD` used, so no rounding / sign trap |

## Desk check

- All 11 quirks (spec Q1-Q11) traced through the ABAP: same result.
- All 31 expected results of `ZTEST_SCCS010` re-checked against the COBOL
  simulation: 0 mismatches.
- Extra check outside SAP: a Python port of this FM was compared with a
  line-by-line Python simulation of the COBOL on 300,000 random inputs
  (digits, `-`, `.`, `,`, space, letter; random digit limits). 0 differences.
  This proves the early `RETURN` is equivalent; it does not replace running
  `ZTEST_SCCS010` in SAP.

## Assumptions and open points

- Spec OQ1: quirks Q1-Q5, Q8, Q9 kept as in COBOL (accepts blank, `1,23`,
  `- 5`, right-aligned `1,234,`...).
- SE37 single test may drop leading blanks from the input field. Use
  `ZTEST_SCCS010` for cases with leading blanks (T5).
- No dependencies on other FMs.
