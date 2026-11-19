# COBOL → ABAP mapping reference

Use this when analysing COBOL (to spot behavior that ABAP would change) and
when writing ABAP (to reproduce it). Items marked **TRAP** silently give a
different result if translated literally. Items marked **DECIDE** cannot be
converted without a human decision: put them in the spec as open questions.

ABAP facts here were checked against the ABAP Keyword Documentation
(sap-docs: `ABENARITH_OPERATORS`, `ABENCONVERSION_TYPE_C`,
`ABENDEC_FLOATING_POINT_ROUND`). Re-check with `mcp__sap-docs__search` /
`fetch` when in doubt.

## Contents

1. Data types
2. Moves and conversions
3. Arithmetic
4. Conditions and comparisons
5. Control flow
6. String handling
7. Tables (OCCURS)
8. Program structure and calls
9. File, database and system I/O
10. IBM i specifics

---

## 1. Data types

| COBOL | DDIC built-in type | ABAP local type | Notes |
|---|---|---|---|
| `PIC X(n)` | CHAR n | `c LENGTH n` | |
| `PIC 9(n)` (DISPLAY, unsigned) | NUMC n | `n LENGTH n` | Use DEC / `p` if it is used in arithmetic with decimals or negatives |
| `PIC S9(n)V9(m)` DISPLAY / COMP-3 / PACKED-DECIMAL | DEC n+m, m decimals | `p LENGTH (n+m)/2+1 DECIMALS m` | |
| `PIC 9(n)V9(m)` unsigned | DEC n+m, m decimals | same | **TRAP**: COBOL drops the sign when a negative value is stored. Use `abs( )` |
| `PIC S9(1-4) COMP/BINARY/COMP-4` | INT2 | `int2` / `i` | **TRAP**: COBOL keeps only the PIC digits (9(4) max 9999) unless TRUNC(BIN) |
| `PIC S9(5-9) COMP` | INT4 | `i` | same trap |
| `PIC S9(10-18) COMP` | INT8 or DEC | `int8` / `p` | |
| `COMP-1` / `COMP-2` | FLTP | `f` | rare; check precision |
| `PIC N(n)` / `PIC G(n)` (DBCS) | CHAR n | `c LENGTH n` | Length counts characters in ABAP (Unicode) |
| Edited `PIC Z,ZZ9.99-` etc. | CHAR | `c` | Build with string template / `WRITE ... TO`. Reproduce the exact format |
| Level 88 condition | constant | `CONSTANTS lcf_...` | `SET x TO TRUE` → assign the 88 value; `IF x` → compare |
| `REDEFINES` | — | separate fields or offset access | **TRAP** when it overlays numeric on character (see §2) |
| `FILLER` | — | keep as a field only if positions matter | |

## 2. Moves and conversions

| COBOL | ABAP | Notes |
|---|---|---|
| `MOVE X TO Y` (both alphanumeric) | `y = x.` | Same: left-aligned, pad/truncate right |
| `MOVE num TO num` | `y = x.` | **TRAP**: COBOL truncates extra decimals and extra high-order digits silently. ABAP rounds decimals commercially and raises `CX_SY_CONVERSION_OVERFLOW` on too many integer digits. Reproduce with `round( ... mode = cl_abap_math=>round_down )` and `MOD 10 ** n` |
| `MOVE alnum TO numeric (9)` | — | **TRAP**: COBOL copies the bytes. ABAP `c`→`n` keeps only the digits, right-aligned, and drops other characters. ABAP `c`→`p` raises `CX_SY_CONVERSION_NO_NUMBER` for non-numbers and turns blanks into 0 |
| `MOVE numeric TO alnum (X)` | NUMC intermediate, or `\|{ x WIDTH = n ALIGN = RIGHT PAD = '0' }\|` | **TRAP**: COBOL gives the unsigned digits ('00123'). ABAP `p`→`c` gives a formatted number with a trailing sign |
| `MOVE group TO group` | field by field / `MOVE-CORRESPONDING` | COBOL group move = byte copy. ABAP is the same only for purely character-like structures |
| `MOVE SPACE / ZERO` | `CLEAR` or `= space` / `= 0` | `ZERO` to an X field = `'0'` repeated |
| `INITIALIZE` | `CLEAR` | INITIALIZE leaves FILLER untouched; CLEAR does not |
| `HIGH-VALUE` / `LOW-VALUE` | `cl_abap_char_utilities=>maxchar` / `minchar` | Often used as an end-of-file key in match logic. A boolean flag may be clearer |

## 3. Arithmetic

| COBOL | ABAP | Notes |
|---|---|---|
| `ADD a TO b`, `SUBTRACT`, `MULTIPLY` | `b = b + a.` | Truncation trap of §2 applies to the target |
| `COMPUTE x = expr` | `x = expr.` | **TRAP**: no `ROUNDED` = truncate. ABAP rounds. Use `round( val = expr dec = m mode = cl_abap_math=>round_down )` |
| `COMPUTE x ROUNDED = expr` | `x = expr.` | Both round half away from zero. OK |
| `DIVIDE a BY b GIVING q` | `q = a / b` + round_down | **TRAP**: ABAP division rounds commercially, COBOL truncates |
| `DIVIDE ... REMAINDER r` | `r = a - b * trunc( a / b )` | **TRAP**: ABAP `MOD` is always positive (-7 MOD 3 = 2). COBOL remainder keeps the dividend sign (-1) |
| `ON SIZE ERROR` | `TRY ... CATCH cx_sy_arithmetic_overflow cx_sy_conversion_overflow` | Without ON SIZE ERROR, COBOL truncates silently, ABAP dumps |
| Division by zero | `CATCH cx_sy_zerodivide` | ABAP: 0 / 0 = 0, x / 0 raises |
| Intermediate precision | — | Long expressions may round differently. Split them and note it in the spec |

## 4. Conditions and comparisons

| COBOL | ABAP | Notes |
|---|---|---|
| `IF x NUMERIC` (alphanumeric field) | `IF x CO '0123456789'.` | `CO` respects trailing blanks of both operands (ABENLOGEXP_STRINGS), so `'1 '` and an all-blank field are not numeric, as in COBOL |
| `IF x ALPHABETIC` | ``IF x CO `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz `.`` | COBOL ALPHABETIC accepts letters and space. Use a backquote string literal so the space counts |
| `IF x = SPACE` | `IF x IS INITIAL` / `= space` | |
| Alphanumeric comparison | same | Shorter operand padded with spaces in both |
| Numeric vs alphanumeric comparison | convert explicitly | **TRAP**: ABAP converts `c` to a number and may raise |
| `x > 'A'`, sorting, `THRU` ranges with mixed letters/digits | — | **TRAP**: IBM i uses EBCDIC: lower case < upper case < digits. Unicode/ASCII: digits < upper case < lower case. Only pure-digit or pure-letter ranges are safe |
| `EVALUATE x WHEN a WHEN b THRU c` | `CASE x. WHEN a. ...` / `IF x BETWEEN b AND c` | |
| `EVALUATE TRUE WHEN cond` | `IF ... ELSEIF ...` | |
| `EVALUATE ... ALSO ...` | nested `IF` | |

## 5. Control flow

| COBOL | ABAP | Notes |
|---|---|---|
| `PERFORM sec` | inline block or `PERFORM <id>_<sec>` | Keep a `" COBOL <sec> (Lx-y)` comment |
| `PERFORM sec n TIMES` | `DO n TIMES.` | |
| `PERFORM VARYING i FROM a BY b UNTIL cond` | `i = a. WHILE NOT cond. ... i = i + b. ENDWHILE.` | Condition is tested **before** each pass. **TRAP**: after the loop COBOL `i` = last value + b; `DO` + `sy-index` differs. Matters if `i` is used later |
| `... WITH TEST AFTER` | `DO. ... IF cond. EXIT. ENDIF. ENDDO.` | |
| `PERFORM a THRU b` | call each paragraph in order | Check for `GO TO` inside |
| `GO TO` | restructure (loop + `EXIT` / `CONTINUE`, or flags) | Describe the real flow in the spec first |
| `EXIT` (paragraph end) | nothing | `EXIT` in COBOL is a no-op label; ABAP `EXIT` leaves a loop. Do not copy it |
| `GOBACK` / `EXIT PROGRAM` | `RETURN.` | |
| `STOP RUN` in a subroutine | **DECIDE** | Ends the whole job in COBOL |

## 6. String handling

| COBOL | ABAP | Notes |
|---|---|---|
| `STRING a DELIMITED BY SIZE` | `CONCATENATE` / `&&` | |
| `STRING a DELIMITED BY SPACE` | take `a` up to the first space, then concatenate | Not the same as `CONDENSE` |
| `STRING ... WITH POINTER p` | track `p` explicitly | |
| `UNSTRING ... DELIMITED BY d INTO a b c` | `SPLIT ... AT d INTO a b c.` | **TRAP**: targets are padded/truncated to their length in COBOL; `TALLYING`, `COUNT IN`, `DELIMITER IN`, `ALL d` need explicit code |
| `INSPECT x TALLYING n FOR ALL 'a'` | `FIND ALL OCCURRENCES OF 'a' IN x MATCH COUNT n.` | COBOL adds to `n`, does not reset it |
| `INSPECT ... FOR LEADING` | loop over characters | |
| `INSPECT x REPLACING ALL 'a' BY 'b'` | `REPLACE ALL OCCURRENCES OF 'a' IN x WITH 'b'.` | Same length only |
| `INSPECT x CONVERTING 'abc' TO 'xyz'` | `TRANSLATE x USING 'axbycz'.` | |
| Reference modification `x(s:l)` | `x+off(l)` with `off = s - 1` | 1-based vs 0-based |
| `FUNCTION LENGTH / UPPER-CASE / NUMVAL` | `strlen( )` / `to_upper( )` / explicit conversion | `strlen` ignores trailing blanks of `c` |

## 7. Tables (OCCURS)

| COBOL | ABAP | Notes |
|---|---|---|
| `05 T PIC X OCCURS n` on a character field | offset access on a `c LENGTH n` field | Simple and close to COBOL (see case study) |
| `OCCURS n` of a group | internal table (`STANDARD TABLE`) or fixed rows | Index 1-based in both |
| `OCCURS ... DEPENDING ON cnt` | internal table, `lines( )` | |
| `SEARCH` | `READ TABLE ... WITH KEY` | Sequential from the current index in COBOL |
| `SEARCH ALL` | `READ TABLE ... BINARY SEARCH` or sorted table | Requires the same sort order (§4 EBCDIC trap) |
| Hard-coded value tables (`VALUE` + `REDEFINES ... OCCURS`) | constants in a `VALUE #( )` table, or a customizing table | **DECIDE** if the values may change in future |

## 8. Program structure and calls

| COBOL | ABAP | Notes |
|---|---|---|
| `PROGRAM-ID x IS INITIAL` | all WORKING-STORAGE as local `DATA` in the FM | Fresh values on every call |
| `PROGRAM-ID x` (not INITIAL) | fields that must survive between calls → global data in TOP include | The spec must list which fields rely on it |
| `LINKAGE SECTION` + `PROCEDURE DIVISION USING p` | FM interface `CHANGING cs_p TYPE z<p>` (by reference) | |
| `COPY member` | DDIC structure (interface) or local `TYPES` (work areas) | |
| `CALL 'X' USING p` | `CALL FUNCTION 'Z_X' CHANGING cs_p = lds_p.` | If X is not converted yet, still call it and list it as a dependency |
| `CALL` to a CL / system program | **DECIDE** | See §10 |
| `PROCESS ... STDINZHEX00` | — | **TRAP**: uninitialised WORKING-STORAGE holds x'00', not spaces/zeros. Check every field read before it is written |

## 9. File, database and system I/O

All **DECIDE**. The spec must describe what the program reads/writes; the
human chooses the ABAP form.

| COBOL | Possible ABAP forms |
|---|---|
| `SELECT f ASSIGN TO DATABASE-xxx` + `READ` / `WRITE` / `REWRITE` / `DELETE` / `START` | Z table + Open SQL, internal table parameters, or application server file (`OPEN DATASET`) |
| Sequential match of two sorted files | Internal tables sorted by key + loop with two indices |
| `EXEC SQL` | Open SQL |
| `DISPLAY` / console messages | Nothing in an FM, an output table parameter, or application log (BAL) |
| `ACCEPT ... FROM DATE / TIME` | `sy-datum` / `sy-uzeit` (watch 2-digit years) |
| Abend routine | `RAISE EXCEPTION` / classic exception / `MESSAGE ... TYPE 'X'` |

## 10. IBM i specifics

- **Shift-JIS export**: read with `scripts/read_cobol.py`. Line numbers in the
  spec are those printed by the script.
- **Change markers in columns 1-6** (`!ADD!`, `!UPD!`, `!DEL!`, `C020A`...):
  from migration or change tools. `!DEL!` lines are deleted code; ignore them.
- **DBCS in `PIC X`**: Japanese text in an alphanumeric field is wrapped in
  shift-out x'0E' / shift-in x'0F'. Byte lengths and positions differ from
  ABAP character positions. Logic that scans SO/SI or "full-width vs
  half-width" needs a new ABAP rule (character ranges). **DECIDE** + test.
- **Data areas (`DTAARA`)**: global system values. **DECIDE** (customizing
  table, TVARVC, constant).
- **CL programs** called with `CALL` (date, console, abend, job info): read
  their source in `input/<ID>/` and describe their effect; map per §9.
- **Date windows**: 2-digit years are often expanded with a pivot
  (e.g. `< 59` → 20xx). Keep the exact pivot.
