---
paths:
  - "output/**/*.abap"
  - "output/**/*.ddic.md"
  - "output/**/spec.md"
  - "examples/**/*.abap"
  - "examples/**/*.ddic.md"
  - "examples/**/spec.md"
---

# ABAP Classic naming convention (kit default)

Default convention of this kit. If the project has its own standard, edit this
file and the "Project settings" table in `CLAUDE.md` together.

---

## Repository objects

Patterns come from "Project settings" in `CLAUDE.md`. Defaults (`<ID>` = COBOL
member name, e.g. `SCCS010`; `<GRP>` = its first 4 chars, e.g. `SCCS`):

| Object | Name | Example |
|---|---|---|
| Function group | `Z_<GRP>` | `Z_SCCS` |
| Function module | `Z_<ID>` | `Z_SCCS010` |
| Parameter structure (from copybook) | `Z<copybook>` | `ZSCCS01R` |
| Function group includes (SAP generated) | `LZ_<GRP>TOP`, `LZ_<GRP>UXX`, `LZ_<GRP>F01` | `LZ_SCCSF01` |
| FORM inside a function group | `<id>_<cobol section>` (lower case) | `sccs010_check1` |
| Test report | `ZTEST_<ID>` | `ZTEST_SCCS010` |
| Data element / domain (only if the spec asks) | `Z<GRP>_<name>` | `ZSCCS_RTN_CD` |
| Any other new object | ask; do not invent a name | |

- All custom objects start with `Z` (or the project namespace `/<NS>/`).
- Max length 30 characters (function group 26). Names are upper case in SAP.
- Structure components: the COBOL field name with `-` replaced by `_`
  (`BEFR-CNVR-QTY` → `BEFR_CNVR_QTY`). Keep the original words so the
  mapping stays traceable. If longer than 30 chars, shorten and record the
  mapping in the spec.
- Built-in DDIC types (CHAR, NUMC, DEC, INT4...) are fine for structure
  components. No data elements / domains unless the spec asks for them.
- FORMs in one function group share one namespace. That is why the FORM name
  starts with the COBOL ID.

---

## ABAP variable naming (IPS standard)

Source: `IPS開発基準書 Ver4.0`, №05 "プログラム内の変数命名規則" and
"汎用モジュール パラメータID". The old ERP-style prefixes `lv_`, `ls_`,
`lt_`, `gv_`, `gs_`, `gt_`, `ty_`, `tt_`, `iv_`, `ev_`, `cv_` are **not used**.

### Declarations: 4-character prefix `<scope><kind><type>_`

- scope: `g` = global (TOP include / program top), `l` = local (FM / FORM)
- kind: `d` = DATA, `t` = TYPES, `c` = CONSTANTS, `r` = RANGES
- type: `f` = field (scalar), `s` = structure, `t` = internal table

| Declaration | Global | Local | Example |
|---|---|---|---|
| `DATA` field | `gdf_` | `ldf_` | `ldf_byte_before` |
| `DATA` structure | `gds_` | `lds_` | `lds_sccs01r` |
| `DATA` internal table | `gdt_` | `ldt_` | `ldt_case` |
| `TYPES` field / structure | `gtf_` / `gts_` | `ltf_` / `lts_` | `gts_case` |
| `TYPES` table type | `gtt_` | `ltt_` | `gtt_case` |
| `CONSTANTS` | `gcf_` | `lcf_` | `lcf_ok` |
| `RANGES` / range table | `grt_` | `lrt_` | `lrt_matnr` |
| `FIELD-SYMBOLS` | `<g_…>` | `<l_…>` | `<l_line>` |
| Report `PARAMETERS` / `SELECT-OPTIONS` | `p_` / `s_` | | `p_bukrs` |

Not covered by the standard; use these (common IPS practice / review list):

| Kind | Prefix | Example |
|---|---|---|
| Object reference | `lo_` / `go_` | `lo_alv` |
| Exception object (`CATCH ... INTO`) | `lx_` | `lx_error` |
| Flag / counter / index field | `ldf_flg_` / `ldf_cnt_` / `ldf_idx_` (`gdf_…` if global) | `ldf_flg_minus` |
| FORM parameter: USING (read) / CHANGING (write) | `pr_` / `pv_` | `pr_bukrs`, `pv_result` |

### Function module parameters `<dir><type>_`

| Direction | Field | Structure | Table parameter |
|---|---|---|---|
| IMPORTING | `if_` | `is_` | `ti_` (TABLES, input) |
| EXPORTING | `ef_` | `es_` | `te_` (TABLES, output) |
| CHANGING | `cf_` | `cs_` | |

Example: `CHANGING cs_sccs01r TYPE zsccs01r`.

### Rules

- Applies to every variable, including inline `DATA(...)` and loop targets.
- After the prefix, keep the full words of the COBOL field (`-` → `_`):
  `INT-DNUM-X` → `ldf_int_dnum_x`, not `ldf_int_x`. The standard
  shows 9 characters after the prefix, but IPS code commonly uses longer
  names; full COBOL words win for traceability (max 30 characters total).
- COBOL flags (`...-FLG`), counters (`...-CNT`) and indexes (`IX`, `...-IDX`)
  use the flag / counter / index prefix with the COBOL words after it:
  `MINUS-FLG` → `ldf_flg_minus`, `DELIMIT-CNT` → `ldf_cnt_delimit`,
  `INT-DNUM-CNT` → `ldf_cnt_int_dnum`, `IX` → `ldf_idx`.
- A COBOL flag `PIC X(03)` with values `'ON '` / `'NOT'` may become
  `abap_bool`. Say so in a comment at the declaration.
- Parameters defined by SAP standard interfaces keep their SAP names.
- Code in lower case, keywords upper case (pretty printer default).

---

## Project-specific

Add the customer's conventions here (titles, description language, numbering,
packages, transport names). Example from the case study project:

- Program title: `Zxxx9xx0：<function name>`.
- Table description: `<function name> <purpose>テーブル`.
- Structure description: `<function name> <purpose>構造`.
- When no ID is given, new objects are numbered starting with `9`.

---

## General

- Descriptions follow the pattern of each object type above.
- Change history lives in transports / git. Do not add a history block to the
  source header.
