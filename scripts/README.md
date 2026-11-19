# scripts

Helper scripts. Run them from the kit folder (the folder that holds
`config.json`). Claude's agents use them too.

| Script | What it does |
|---|---|
| `collect_deps.py` | Finds a COBOL program and every file it needs (COPY + CALL, all levels) in the received sources and copies them to `input/<ID>/` |
| `read_cobol.py` | Prints a source file as UTF-8 with line numbers (sources are usually Shift-JIS) |
| `run_cobol.py` | Compiles and runs a pure-logic COBOL subroutine with GnuCOBOL and checks test cases (section 4) |

Requirements: Python 3.10 or newer (`python --version`). No extra packages.
`run_cobol.py` also needs GnuCOBOL (section 4.1).

---

## 1. Set the source path (once per machine)

The received sources stay where they are; the scripts only read them. Tell
the scripts where they are in `config.json` at the kit root:

```json
{
  "source_dirs": [
    "C:/Users/<you>/Desktop/受領ソース"
  ]
}
```

- Use `/` or `\\` in paths (JSON needs `\\` for a backslash).
- Several folders are allowed. They are searched together.
- A relative path is read from the kit folder, e.g. `"sources"` means
  `<kit>/sources`.
- `--src <folder>` on the command line overrides `config.json` for one run.

Check it:

```
python scripts/collect_deps.py SCCS010 --dry-run
```

The first line shows how many files were indexed and from where:

```
Indexed 24970 files from: C:\Users\<you>\Desktop\受領ソース
```

---

## 2. collect_deps.py: build `input/<ID>/`

```
python scripts/collect_deps.py <ID> [<ID> ...] [options]
```

| Option | Meaning |
|---|---|
| `--dry-run` | Show the file tree only, copy nothing. Use it first |
| `--depth N` | Follow only N levels (`--depth 1` = direct COPY / CALL only). Default: all |
| `--src DIR` | Source folder for this run, overrides `config.json`. Repeatable |
| `--out DIR` | Parent folder for the result. Default: `input/` |
| `--selftest` | Check the COPY / CALL parser and exit |

### Examples

```
python scripts/collect_deps.py SCCS010 --dry-run     # look first
python scripts/collect_deps.py SCCS010               # creates input/SCCS010/
python scripts/collect_deps.py SCCS010 SCCS020       # one folder per ID
python scripts/collect_deps.py SJFS010 --depth 1     # only what SJFS010 uses directly
```

### Output

```
===== SJFS010
PGM  SJFS010  ...\QPGMSRC\SJFS010.txt
    COPY CVTCOMMON  ...\QLBLSRC\QLBLSRC\CVTCOMMON.txt
    COPY SJFS01R  ...\QLBLSRC\QLBLSRC\SJFS01R.txt
    CALL SJFS020  ...\QPGMSRC\SJFS020.txt
        COPY SJFS02R  (already listed)
    CALL SCCS090  ...\QPGMSRC\SCCS090.txt
        COPY C060X060  ...
...
Files: 35   Not found: 0
Copied 35 files to <kit>\input\SJFS010
```

- `PGM` = the program you asked for, `COPY` = copybook, `CALL` = called
  program (COBOL or CL). Indentation = level.
- `(already listed)`: the same file was found earlier in this tree; it is
  copied once.
- `** NOT FOUND **`: no file with that name in the source folders. The
  analysis will list it as an open question.
- `dynamic CALL`: a `CALL <variable>` whose target is decided at run time.
  Check those lines by hand and add the files yourself.

### How it finds files

1. Indexes every file under the source folders by name (without extension).
   If a name exists twice, the copy in a folder starting with `_` (e.g. an
   earlier extract) is used last.
2. Reads the program (Shift-JIS) and collects names after `COPY`,
   `CALL 'NAME'` (COBOL) and `CALL PGM(LIB/NAME)` (CL). Comment lines, CL
   comments `/* */` and `!DEL!` lines are skipped.
3. Repeats step 2 for every file found, until nothing new appears.
4. Copies the files into `input/<ID>/`. Existing files with the same name
   are overwritten; other files in the folder are left alone.

The source folders are never changed.

---

## 3. read_cobol.py: read a source

```
python scripts/read_cobol.py --root input/<ID> <name> [<name> ...] [options]
```

| Option | Meaning |
|---|---|
| `--root DIR` | Folder to search. Default: `input/` |
| `--refs` | Print only the COPY / CALL lines |
| `--enc ENC` | Force the encoding (`cp932`, `utf-8`...). Default: UTF-8, else Shift-JIS (cp932) |

`<name>` is a member name (`SCCS010`) or a file path.

### Examples

```
python scripts/read_cobol.py --root input/SCCS010 SCCS010            # the program
python scripts/read_cobol.py --root input/SCCS010 SCCS01R CVTCOMMON  # copybooks
python scripts/read_cobol.py --root input/SCCS010 --refs SCCS010     # COPY / CALL only
```

Output starts with the file, line count and encoding used, then every line
with its number. These line numbers are the ones quoted in specs
(`L139-170`).

```
===== input\SCCS010\SCCS010.txt (355 lines, cp932)
  56 !ADD!      COPY CVTCOMMON.
  98            COPY  SCCS01R  SUPPRESS.
```

To read a file in an editor instead: VS Code → status bar encoding →
**Reopen with Encoding** → **Japanese (Shift JIS)**.

---

## 4. run_cobol.py: run the original COBOL

Runs a **pure-logic subroutine** (`PROCEDURE DIVISION USING ...`, no file /
table access) on test cases and compares the results with the expected
values. Used by the `cobol-tester` agent (`/cobol-test <ID>`).

### 4.1 Install GnuCOBOL (once per machine)

Windows, in PowerShell **Run as Administrator**:

```
choco install gnucobol -y
```

Then add its folder to `config.json` (the scripts set the GnuCOBOL
environment variables from it, like its `set_env.cmd`):

```json
{
  "source_dirs": ["C:/Users/<you>/Desktop/受領ソース"],
  "gnucobol_dir": "C:/ProgramData/chocolatey/lib/gnucobol/tools"
}
```

Without `gnucobol_dir`, `cobc` must already work in your shell.

### 4.2 Run

```
python scripts/run_cobol.py <ID>                    # input/<ID>/ + output/<ID>/cases.json
python scripts/run_cobol.py <ID> --stub SCCS560     # replace a called program by an empty stub
python scripts/run_cobol.py <ID> --input DIR --cases FILE --out DIR
python scripts/run_cobol.py --selftest
```

Exit code: `0` all PASS, `1` some FAIL, `2` setup / compile error.
Report: `output/<ID>/cobol-test.md`. Build files: `.work/<ID>/` (safe to delete).

### 4.3 cases.json

```json
{
  "defaults": {"INT_DNUM_DAT": 13, "DEC_DNUM_DAT": 5},
  "show": ["AFTR_CNVR_QTY"],
  "cases": [
    {"id": "T2", "in": {"BEFR_CNVR_QTY": "-1,234.56"},
     "expect": {"AFTR_CNVR_QTY": "-1234.56", "RTN_CD": "OK"}},
    {"id": "T32", "in": {"BEFR_CNVR_QTY": "1", "INT_DNUM_DAT": {"raw": "1 "}},
     "expect": {"RTN_CD": "NG"}},
    {"id": "P1", "in": {"BEFR_CNVR_QTY": "1,2345.6"}}
  ]
}
```

| Item | Meaning |
|---|---|
| `defaults` | inputs used by every case unless the case overrides them |
| `in` | inputs of the case; fields not given stay as after `INITIALIZE` (blank / zero) |
| `expect` | expected outputs; omit it for a probe (result is only shown) |
| `show` | extra fields to print for every case |
| field names | COBOL or ABAP style (`INT-DNUM-DAT` = `INT_DNUM_DAT`); arrays `NAME(2)`; ambiguous `NAME OF GROUP` |
| text values | strings, leading blanks kept; compared without trailing blanks |
| numeric values | numbers or numeric strings; compared by value |
| `{"raw": "..."}` | bytes moved as they are, to test invalid data in a DISPLAY numeric field |

Full example: `examples/case-study-SCCS010/output/SCCS010/cases.json`.

### 4.4 What the script does

1. Copies `input/<ID>/` to `.work/<ID>/` and removes IBM i-only syntax in
   the copy: `PROCESS` lines, `DATA-AREA IS ...` clauses. The originals are
   not changed.
2. Builds a driver program from the LINKAGE SECTION: reads each case, fills
   the parameters, `CALL`s the program, writes the outputs.
3. Compiles the driver with every COBOL program in `input/<ID>/`.
   Called programs that are not COBOL (CL programs such as `CCURDAT2`) become
   empty stubs.
4. Compiler options: `-std=ibm`, `-fdefaultbyte=0` (uninitialised storage =
   x'00', like IBM `STDINZHEX00`), `-fnot-reserved=SHIFT-OUT,SHIFT-IN,NEW`.

### 4.5 Limits

- Pure-logic subroutines only. Programs with file / table I/O compile but
  the report warns that results may be meaningless.
- Runs in ASCII, not EBCDIC: comparisons or sorting that mix letters and
  digits can differ from IBM i.
- `PIC N` / `PIC G` (full-width) parameters cannot be used as inputs or
  outputs yet. Other parameters of the same program still work.
- Stubbed programs do nothing; cases that depend on them are not reliable.
- `COPY ... REPLACING` inside the LINKAGE SECTION is not supported.

---

## Troubleshooting

| Message / symptom | Fix |
|---|---|
| `Cannot read source_dirs from ...config.json` | `config.json` missing or invalid JSON. Fix it or pass `--src` |
| `Source folder not found: ...` | Path in `config.json` is wrong on this machine |
| `NOT FOUND: <name>` (read_cobol) | Wrong `--root`, or run `collect_deps.py <ID>` first |
| `** NOT FOUND **` in the tree | File not in the received sources. Ask the customer for it |
| Japanese text shows as `�` | File is not Shift-JIS or UTF-8: try `--enc` |
| `python` not found | Install Python 3.10+, or use `py` instead of `python` on Windows |
| In Git Bash, `claude -p "/spec X"` turns `/spec` into a Windows path | Run `MSYS_NO_PATHCONV=1 claude ...`, or use PowerShell |
| `cobc not found` | Install GnuCOBOL and set `gnucobol_dir` (section 4.1) |
| `default.conf: No such file or directory` | `gnucobol_dir` missing or wrong: the GnuCOBOL environment is not set |
| `cobc failed: ... unexpected <WORD>, expecting Identifier` | `<WORD>` is reserved in GnuCOBOL but a data name on IBM i: add it to `NOT_RESERVED` in `run_cobol.py` |
| `cobc failed` on other IBM-only syntax | Add the pattern to `IBM_LINE` / `IBM_CLAUSE` in `run_cobol.py` |
| `field 'X' not found in the LINKAGE SECTION` | Wrong name in `cases.json`; check the interface copybook |
