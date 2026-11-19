# <ID>: <short English title> (<original title>)

Status: READY | NEEDS-DECISION
Analysed: <YYYY-MM-DD> by cobol-analyst

<!--
Reader: an ABAP developer who has never seen COBOL.
Sections 1-9: no COBOL syntax, no PIC clauses, no COBOL line numbers.
Use the ABAP names from section 2 and 5 everywhere.
All COBOL details and proofs go to Appendix A.
-->

## 1. Summary

<2-4 short sentences: what the FM does, from which input to which output.>

Example: `<input>` → `<output>`.

| Item | Value |
|---|---|
| Function module | `Z_<ID>` (function group `Z_<GRP>`) |
| Parameter | `CHANGING cs_<copybook> TYPE z<copybook>` (by reference) |
| Calls other FMs | none / `Z_<ID2>` (exists? yes/no) |
| Database / files | none / `<table>` read / write |
| State between calls | none (fresh local data every call) / `<fields kept>` |

## 2. Interface: structure `Z<copybook>`

| Field | Type | In / Out | Meaning | Example |
|---|---|---|---|---|
| `<FIELD_NAME>` | CHAR 20 | in | <meaning, allowed values> | `'-1,234.56'` |

Result codes:

| `<RTN_FIELD>` | Meaning | Other outputs |
|---|---|---|
| `OK` | <meaning> | <what is filled> |
| `NG` | <meaning> | <value left in output fields> |

## 3. Rules

The business rules in a form that can be coded directly: decision tables,
allowed patterns, formulas. One rule per row. Plain words.

| Situation / character | OK when | Error (`NG`) when |
|---|---|---|
| <...> | <...> | <...> |

## 4. Processing steps

ABAP-like pseudo-code with the names of sections 2 and 5. Short and in
execution order. Each step says what to do on error.

```
1. <init outputs>
2. <check parameters>  -> error: RETURN
3. LOOP / DO over ...:
     CASE ...
4. ...
```

## 5. Local variables

| ABAP variable | Type | Purpose |
|---|---|---|
| `ldf_<name>` / `ldf_flg_<name>` / `lds_<name>` / `ldt_<name>` | `abap_bool` | <purpose> |

## 6. Behavior to keep

Results that look odd but are what the old system does. ABAP must give the
same result. Each one has a test case in section 9.

| # | Input | Result | Why, in one sentence | Looks intended? |
|---|---|---|---|---|
| Q1 | <input> | <result> | <plain reason> | yes / probably not |

## 7. ABAP implementation notes

Concrete instructions for the developer: which ABAP construct to use where
the obvious one would give a different result, what is allowed (e.g. early
`RETURN`), what must not be done. Write "none" if nothing applies.

- <note>

## 8. Open questions

| # | Question | Assumption used | BLOCKING? |
|---|---|---|---|
| OQ1 | <question> | <assumption> | yes / no |

## 9. Test cases

One column per input and output field so the table can be copied into the
test report. Defaults for omitted inputs: <defaults>.

| # | `<IN_FIELD_1>` | `<IN_FIELD_2>` | → `<OUT_FIELD>` | → `<RTN_FIELD>` | Covers |
|---|---|---|---|---|---|
| T1 | `'...'` | `13` | 1234 | `OK` | rule / Q# |

---

## Appendix A. COBOL traceability (for reviewers)

### A.1 Steps → COBOL

| Step (section 4) | COBOL section / paragraph | Lines |
|---|---|---|
| 1 | `<SECTION>` | L<a>-<b> |

### A.2 Fields → COBOL

| ABAP name | COBOL field | PIC / initial value |
|---|---|---|
| `<FIELD_NAME>` / `ldf_<name>` | `<COBOL-FIELD>` | `X(20)` |

### A.3 Source facts and proofs

Facts the developer does not need but a reviewer may check: `IS INITIAL`,
error flag never reset (why early `RETURN` is safe), uninitialised fields,
unused copybooks, traps from `reference/cobol-abap-mapping.md` and why they
do or do not apply. Cite lines.

- <fact> (L<n>)
