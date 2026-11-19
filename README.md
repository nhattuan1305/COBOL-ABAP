# COBOL → ABAP conversion kit (Claude Code)

A Claude Code project that converts IBM i COBOL subroutines into ABAP Classic
function modules in reviewed steps:

```
COBOL source ─► /spec ─► spec.md ─► /cobol-test ─► you review ─► /gen ─► FM + DDIC structure + test report
             (cobol-analyst)      (cobol-tester:                (abap-developer + SAP docs MCP)
                                   runs the real COBOL)
```

`/convert` runs all steps with a review stop before the ABAP step.

## Requirements

- Claude Code (CLI, desktop or IDE extension).
- Python 3.10+ on PATH (`python --version`).
- Internet access for the MCP servers in `.mcp.json`:
  - `sap-docs`: ABAP keyword documentation search (used by `abap-developer`).
  - `sap-abap`: provides `abap_lint` (abaplint).
  Approve them when Claude Code asks on first start (`/mcp` shows status).
- Optional, for `/cobol-test`: GnuCOBOL (`choco install gnucobol -y` as
  Administrator) and `gnucobol_dir` in `config.json`. See
  [scripts/README.md](scripts/README.md) section 4.

No SAP connection is needed. Nothing in the kit writes to an SAP system.

## Usage guide

### A. One-time setup (per machine)

1. **Copy the kit folder** anywhere. Do not put customer sources inside it.
2. **Point it to the received sources** in `config.json` (relative paths
   start from the kit folder):
   ```json
   {
     "source_dirs": ["C:/path/to/received-sources"],
     "gnucobol_dir": "C:/ProgramData/chocolatey/lib/gnucobol/tools"
   }
   ```
   `gnucobol_dir` is only needed for `/cobol-test` (install: [scripts/README.md](scripts/README.md) section 4.1).
3. **Check the scripts** from a terminal in the kit folder:
   ```
   python scripts/collect_deps.py --selftest
   python scripts/run_cobol.py --selftest
   ```
4. **Project settings** (once per project, not per machine): the table in
   `CLAUDE.md` (object names, ABAP release, package, spec language) and the
   "Project-specific" part of `.claude/rules/abap-naming.md`.
5. **Open Claude Code** in the kit folder: `claude`.
   - Accept the workspace **trust** dialog. Without it the permissions in
     `.claude/settings.json` are ignored and every command asks.
   - Approve the MCP servers `sap-docs` and `sap-abap`, then type `/mcp`:
     both must be *connected*.

### B. Converting one program

Example: `SCCS010`. Start a timer now if you track effort by hand.

**Step 1. Collect the sources**

```
python scripts/collect_deps.py SCCS010 --dry-run    # look at the tree first
python scripts/collect_deps.py SCCS010              # copy into input/SCCS010/
```

Check the tree before copying:

| You see | Meaning | Action |
|---|---|---|
| `Not found: 0` | all files are there | go on |
| `** NOT FOUND **` | a COPY / CALL target is missing | ask the customer for it; the spec will list it as an open question |
| `dynamic CALL` | the program calls a name held in a variable | find the possible targets by hand and add their files |
| many files (e.g. 35 for `SJFS010`) | the program calls other programs | convert the called ones first (section C) |

`/convert` also runs this step for you if `input/<ID>/` does not exist.

**Step 2. Run the pipeline**

```
/convert SCCS010
```

Claude runs `cobol-analyst` (spec), then `cobol-tester` (runs the real
COBOL, pure-logic programs only), then **stops** and shows you a summary.
Prefer separate steps? Use `/spec SCCS010`, `/cobol-test SCCS010`,
`/gen SCCS010`.

**Step 3. Review the spec** (`output/SCCS010/spec.md`). This is the step
that matters most. Check:

- [ ] Section 1: the summary matches what the program is for (compare with
      the function list from the customer).
- [ ] Section 2: every parameter field, its type, in / out, allowed values.
- [ ] Section 3: the rules table. Pick 2-3 rules and check them against the
      COBOL (`python scripts/read_cobol.py --root input/SCCS010 SCCS010`;
      Appendix A.1 gives the lines).
- [ ] Section 4: pseudo-code uses IPS names (`ldf_`, `lds_`, `ldt_`...),
      never `lv_`.
- [ ] Section 6: each quirk. Decide: keep (default, same as old system) or
      ask the customer.
- [ ] Section 8: answer every open question. `BLOCKING` ones must be
      answered before ABAP.
- [ ] Section 9 + `output/SCCS010/cobol-test.md`: COBOL run result.

**Step 4. Act on the COBOL run** (`cobol-test.md`)

| Result | Meaning | Action |
|---|---|---|
| all PASS | the spec's expected results are what the COBOL really returns | go on |
| FAIL, "transcription" | the case was copied wrong into `cases.json` | ask Claude to fix `cases.json` and re-run `/cobol-test` |
| FAIL, "spec wrong" | the analysis was wrong; the COBOL is the reference | ask Claude to correct spec sections 3 / 6 / 9, then re-run `/cobol-test` |
| surprising probe | behavior the spec does not mention | ask Claude to add it to section 6 and a test case to section 9 |
| "not pure logic, not run" | the program reads files / tables | skip; review those parts by hand |
| stubs listed | called CL programs did nothing | results that depend on them are not proof |

**Step 5. Generate ABAP**: answer "go" in the `/convert` session (or run
`/gen SCCS010`, adding answers to open questions after the ID). Then read
`output/SCCS010/report.md`:

- lint: 0 syntax errors (naming-style findings about `lv_` / `TY_` are
  expected and ignored);
- "doubtful" points: things the developer agent found odd in the spec;
- missing FMs: called programs not converted yet.

**Step 6. Create the objects in SAP** (DEV, the package in `CLAUDE.md`)

1. SE11: structure from `Z<copybook>.ddic.md` (button **Predefined Type**),
   activate.
2. SE80: function group `Z_<GRP>` if it does not exist yet.
3. SE37: function module `Z_<ID>`. Tab *Changing*: the parameter from the
   `.abap` header, **Pass Value off**. Paste the code between `FUNCTION`
   and `ENDFUNCTION`, activate.
4. SE38: report `ZTEST_<ID>`, paste, activate, run (F8). Every line must
   say `PASS` and the last line `Failed: 0`.

A `FAIL` in SAP while `cobol-test.md` was all PASS means the ABAP differs
from the COBOL: give Claude the failing lines.

**Step 7. Log the effort**: `effort/effort-log.csv` already has the AI
minutes from `/convert`. Fill `manual_estimate_h` (how long without AI) and
`actual_total_h` (everything, including review and SAP work).

### C. Which programs first

1. **Pure-logic subroutines without calls** (e.g. `SCCS010`, `SCCS020`,
   `SCDS350`, `SCDS360`): fastest, fully testable with `/cobol-test`.
2. **Callers, bottom-up**: convert the called program before the caller
   (`SCCS010` before `SCCS710`), so the caller's ABAP can be tested.
3. **Programs with tables / hard-coded lists**: decide with the customer
   whether lists become constants or Z tables (spec open questions).
4. **Batch programs with files** (`SKDB...`): need a design decision (Z
   table, internal table, application server file) before ABAP.

### D. Common situations

| Situation | What to do |
|---|---|
| The spec is wrong or unclear | Say it in plain words in the session ("rule for `,` is wrong, see line 240"). Claude updates the spec; re-run `/cobol-test`, then `/gen` |
| You changed a rule / agent / template | Start a new `claude` session; rules and agents load at start |
| Several programs at once | `/convert SCCS010 SCCS020`: one after another, each with its own review stop |
| `run_cobol.py` cannot compile the COBOL | IBM-only syntax not handled yet: see Troubleshooting in [scripts/README.md](scripts/README.md) |
| Field names in the code are not IPS style | Rule `.claude/rules/abap-naming.md` applies; ask Claude to fix and check the rule was not edited |
| Claude asks permission for every script run | Accept the trust dialog, or add the script to `"allow"` in `.claude/settings.json` |

### E. Do / don't

- **Do** review the spec yourself. The agents are good at tracing code, not
  at knowing the business.
- **Do** keep odd COBOL behavior unless the customer decides otherwise;
  record the decision in spec section 8.
- **Don't** edit files in `input/`; re-run `collect_deps.py` instead.
- **Don't** fix the ABAP by hand without updating the spec: the next
  `/gen` would overwrite it.

## Commands

| Command | What it does |
|---|---|
| `/convert <ID> [<ID>...]` | spec → COBOL run → review stop → ABAP, logs AI time |
| `/spec <ID>` | writes `output/<ID>/spec.md` |
| `/cobol-test <ID>` | runs the original COBOL on the spec's test cases, writes `output/<ID>/cobol-test.md` |
| `/gen <ID> [answers]` | ABAP from a reviewed spec |

You can also talk normally: "re-check quirk Q3 in the SCCS010 spec",
"add a test case for a 20-digit input"...

## What is inside

```
CLAUDE.md                          project settings + working rules (always loaded)
config.json                        source_dirs + gnucobol_dir (per machine)
.mcp.json                          MCP servers (sap-docs, sap-abap)
.claude/settings.json              permissions: allow read script / docs / lint, deny delete
.claude/agents/
  cobol-analyst.md                 reads COBOL, writes the spec, never writes ABAP
  cobol-tester.md                  runs the original COBOL on the spec's test cases (GnuCOBOL)
  abap-developer.md                writes ABAP from the spec only, checks SAP docs, lints
.claude/skills/
  cobol-to-abap/                   method + COBOL→ABAP mapping + spec template (preloaded by the agents)
  convert/ spec/ cobol-test/ gen/  the slash commands
.claude/rules/
  abap-naming.md                   object and variable naming (loads for output/**/*.abap)
  abap-coding.md                   coding rules for converted code
  spec-writing.md                  spec rules (loads for output/**/spec.md)
scripts/read_cobol.py              prints Shift-JIS sources as UTF-8 with line numbers
scripts/collect_deps.py            finds all COPY / CALL dependencies of a program and copies them to input/<ID>/
scripts/run_cobol.py               compiles + runs a pure-logic COBOL subroutine on cases.json (GnuCOBOL)
.work/                             build folder of run_cobol.py (safe to delete)
examples/case-study-SCCS010/       a finished conversion to learn from
effort/effort-log.csv              time log
```

## Why separate agents

- The spec is reviewable by people who do not read COBOL.
- The expected results in the spec are checked against the real COBOL
  before any ABAP is written, so mistakes in the analysis surface early.
- The ABAP agent cannot "fill gaps" from the COBOL: anything unclear must be
  in the spec as an open question, so a human decides it.
- Re-generating ABAP after a spec change is cheap.

## Adapting to another project

- Different naming: `CLAUDE.md` settings + `.claude/rules/abap-naming.md`.
- Different source platform or encoding: `scripts/read_cobol.py --enc`, and
  section 10 of `.claude/skills/cobol-to-abap/reference/cobol-abap-mapping.md`.
- New trap found during a conversion: add it to the mapping reference so the
  next conversion catches it.

## Sharing

Before sharing the kit outside the project team:

- delete `examples/case-study-SCCS010/input/`, `input/*/` and `.work/`
  (customer source code; the case-study spec and ABAP stay readable);
- reset the paths in `config.json` (they are machine-specific);
- keep `output/` only if the receiver may see those results.
