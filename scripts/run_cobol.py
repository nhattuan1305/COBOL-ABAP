"""Run a pure-logic COBOL subroutine locally with GnuCOBOL and check test cases.

For program <ID> it:
  1. copies input/<ID>/ to .work/<ID>/ and comments out IBM-only lines,
  2. generates a driver from the program's LINKAGE SECTION,
  3. compiles driver + every COBOL program in input/<ID>/ (missing CALL
     targets such as CL programs become empty stubs),
  4. runs every case of output/<ID>/cases.json and compares with "expect",
  5. writes output/<ID>/cobol-test.md.

cases.json:
  {
    "defaults": {"INT_DNUM_DAT": 13, "DEC_DNUM_DAT": 5},
    "show": ["AFTR_CNVR_QTY"],                  optional extra output fields
    "cases": [
      {"id": "T1", "in": {"BEFR_CNVR_QTY": "-1,234.56"},
       "expect": {"AFTR_CNVR_QTY": "-1234.56", "RTN_CD": "OK"}},
      {"id": "T9", "in": {"INT_DNUM_DAT": {"raw": " 5"}}, "expect": {"RTN_CD": "NG"}},
      {"id": "P1", "in": {"BEFR_CNVR_QTY": "1,2"}}            no expect = probe, show only
    ]
  }
  Field names: COBOL or ABAP style (INT-DNUM-DAT / INT_DNUM_DAT), with
  subscripts for OCCURS (SB_ARRAY_STR(2)) and "NAME OF GROUP" if a name is
  ambiguous. Text fields take strings (leading blanks kept). Numeric fields
  take numbers or numeric strings; {"raw": "..."} moves the bytes as they
  are (DISPLAY numerics only). Text results are compared without trailing
  blanks, numeric results by value.

Usage:
  python scripts/run_cobol.py SCCS010
  python scripts/run_cobol.py SCCS010 --stub SCCS560      # replace a program by an empty stub
  python scripts/run_cobol.py SCCS010 --input DIR --cases FILE --out DIR
  python scripts/run_cobol.py --selftest

Exit code: 0 all PASS, 1 some FAIL, 2 build / setup error.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

from collect_deps import refs  # same folder

KIT_ROOT = Path(__file__).resolve().parents[1]
CONFIG = KIT_ROOT / "config.json"
ENC = "cp932"

# IBM i only syntax GnuCOBOL rejects; extend when cobc reports a new one.
IBM_LINE = re.compile(rb"\s*PROCESS\b", re.I)                    # whole line -> comment
IBM_CLAUSE = re.compile(rb"DATA-AREA\s+IS\s+[A-Z0-9@#$_-]+", re.I)  # clause -> blanks, keep the period
# Words reserved in GnuCOBOL but used as data names in IBM i sources.
NOT_RESERVED = "SHIFT-OUT,SHIFT-IN,NEW"
COBC_FLAGS = ["-x", "-std=ibm", "-ext", "txt", f"-fnot-reserved={NOT_RESERVED}",
              "-fdefaultbyte=0"]  # x'00' init = IBM PROCESS STDINZHEX00


class SetupError(Exception):
    pass


# ---------------------------------------------------------------- environment

def cobol_env() -> dict:
    env = dict(os.environ)
    gdir = None
    try:
        gdir = json.loads(CONFIG.read_text(encoding="utf-8")).get("gnucobol_dir")
    except (OSError, ValueError):
        pass
    if gdir:
        g = Path(gdir)
        if not (g / "bin").is_dir():
            raise SetupError(f"gnucobol_dir in {CONFIG} has no bin/ folder: {g}")
        # same variables as GnuCOBOL's set_env.cmd
        env.update({
            "COB_MAIN_DIR": str(g) + os.sep,
            "COB_CONFIG_DIR": str(g / "config"),
            "COB_COPY_DIR": str(g / "copy"),
            "COB_CFLAGS": f"-I{g / 'include'}",
            "COB_LDFLAGS": f"-L{g / 'lib'}",
            "COB_LIBRARY_PATH": str(g / "extras"),
            "PATH": str(g / "bin") + os.pathsep + env.get("PATH", ""),
        })
    if not shutil.which("cobc", path=env["PATH"]):
        raise SetupError("cobc not found. Install GnuCOBOL and set gnucobol_dir in config.json "
                         "(see scripts/README.md).")
    return env


# ---------------------------------------------------------------- source reading

def code_lines(path: Path, folder: Path, depth: int = 0) -> list[str]:
    """Code area (columns 8-72) of non-comment lines, with COPY members expanded."""
    if depth > 10:
        raise SetupError(f"COPY nesting too deep at {path.name}")
    out = []
    for raw in path.read_bytes().replace(b"\r\n", b"\n").split(b"\n"):
        if raw[6:7] in (b"*", b"/"):
            continue
        code = raw[7:72].decode(ENC, errors="replace").rstrip()
        m = re.match(r"\s*COPY\s+([A-Z0-9@#$_-]+)(?:\s+(?:OF|IN)\s+\S+)?(\s+SUPPRESS)?\s*\.?\s*$", code, re.I)
        if m:
            member = find_member(folder, m.group(1))
            out.extend(code_lines(member, folder, depth + 1))
        else:
            out.append(code)
    return out


def find_member(folder: Path, name: str) -> Path:
    for f in folder.iterdir():
        if f.is_file() and f.stem.upper() == name.upper():
            return f
    raise SetupError(f"COPY member {name} not found in {folder}. Run collect_deps.py first.")


def entries(lines: list[str]) -> list[str]:
    """Split data-division text into entries ending with a period."""
    text = " ".join(lines)
    text = re.sub(r"'[^']*'|\"[^\"]*\"", "''", text)  # literals may contain periods
    return [e.strip() for e in re.split(r"\.(?=\s|$)", text) if e.strip()]


# ---------------------------------------------------------------- data items

class Item:
    def __init__(self, level, name, pic, usage, occurs, parent):
        self.level, self.name, self.pic, self.usage = level, name, pic, usage
        self.occurs, self.parent = occurs, parent

    def chain(self):
        """Qualifiers from self to the 01 level, skipping FILLER."""
        node, names = self, []
        while node:
            if node.name != "FILLER":
                names.append(node.name)
            node = node.parent
        return names

    def dims(self):
        node, d = self, []
        while node:
            if node.occurs:
                d.append(node.occurs)
            node = node.parent
        return list(reversed(d))

    def record(self):
        node = self
        while node.parent:
            node = node.parent
        return node.name


def expand_pic(pic: str) -> str:
    return re.sub(r"(.)\((\d+)\)", lambda m: m.group(1) * int(m.group(2)), pic.upper())


def classify(item: Item):
    """Return (kind, info): ('num', (int_digits, scale, signed, display)) / ('text', bytes) / ('dbcs', n)."""
    p = expand_pic(item.pic)
    if re.fullmatch(r"S?9*V?9*", p) and "9" in p:
        whole, _, frac = p.lstrip("S").partition("V")
        display = item.usage in ("", "DISPLAY")
        return "num", (len(whole), len(frac), p.startswith("S"), display)
    if re.fullmatch(r"[NG]+", p):
        return "dbcs", len(p)
    if "P" in p:
        raise SetupError(f"PIC with P scaling not supported: {item.name} {item.pic}")
    return "text", len(p)  # X, A and edited pictures


def parse_items(ents: list[str]) -> list[Item]:
    items, stack = [], []
    for e in ents:
        tok = e.split()
        if not tok or not tok[0].isdigit():
            continue
        level = int(tok[0])
        if level in (66, 77, 88):
            continue
        name = tok[1].upper() if len(tok) > 1 and not re.fullmatch(
            r"PIC|PICTURE|OCCURS|REDEFINES|USAGE|VALUE|COMP.*|BINARY|PACKED-DECIMAL", tok[1], re.I) else "FILLER"
        up = " ".join(tok).upper()
        pic = re.search(r"\bPIC(?:TURE)?\s+(?:IS\s+)?(\S+)", up)
        occ = re.search(r"\bOCCURS\s+(\d+)", up)
        usage = re.search(r"\b(COMP-3|COMPUTATIONAL-3|PACKED-DECIMAL|COMP-4|COMP-5|COMP|BINARY|DISPLAY)\b", up)
        while stack and stack[-1].level >= level:
            stack.pop()
        it = Item(level, name, pic.group(1) if pic else None,
                  usage.group(1) if usage else "", int(occ.group(1)) if occ else 0,
                  stack[-1] if stack else None)
        stack.append(it)
        items.append(it)
    return items


def resolve(key: str, items: list[Item]):
    """Map a cases.json key to (item, subscripts)."""
    k = key.strip().upper().replace("_", "-")
    m = re.fullmatch(r"(.+?)\s*\(\s*([\d\s,]+)\)", k)
    subs = [int(x) for x in re.split(r"[\s,]+", m.group(2).strip())] if m else []
    names = [n.strip() for n in re.split(r"\s+OF\s+", m.group(1) if m else k)]
    hits = [it for it in items if it.pic and it.name != "FILLER" and it.chain()[0] == names[0]
            and all(n in it.chain()[1:] for n in names[1:])]
    if not hits:
        raise SetupError(f"field {key!r} not found in the LINKAGE SECTION")
    if len(hits) > 1:
        raise SetupError(f"field {key!r} is ambiguous; write it as "
                         + " or ".join(f"'{h.name} OF {h.chain()[1]}'" for h in hits))
    it = hits[0]
    if len(subs) != len(it.dims()):
        raise SetupError(f"field {key!r} needs {len(it.dims())} subscript(s)")
    return it, subs


def ref(it: Item, subs: list[int]) -> str:
    s = " OF ".join(it.chain())
    return s + (f" ({', '.join(map(str, subs))})" if subs else "")


# ---------------------------------------------------------------- driver

def build_driver(program: str, using: list[str], linkage: list[str], inputs, outputs) -> str:
    """inputs/outputs: list of (key, item, subs). Returns free-format COBOL source."""
    ws_in, ws_out, moves_in, moves_out = [], [], [], []
    in_len = out_len = 0
    for n, (key, it, subs) in enumerate(inputs, 1):
        kind, info = classify(it)
        width = info if kind == "text" else 40
        ws_in += [f"   05 CT-I{n}-F PIC X.", f"   05 CT-I{n}-V PIC X({width})."]
        in_len += 1 + width
        r = ref(it, subs)
        if kind == "text":
            moves_in.append(f"    IF CT-I{n}-F = 'T' MOVE CT-I{n}-V TO {r} END-IF")
        else:
            moves_in.append(f"    IF CT-I{n}-F = 'N' COMPUTE {r} = FUNCTION NUMVAL(CT-I{n}-V) END-IF")
            nbytes = info[0] + info[1]
            moves_in.append(f"    IF CT-I{n}-F = 'R' MOVE CT-I{n}-V(1:{nbytes}) TO {r}(1:{nbytes}) END-IF")
    for n, (key, it, subs) in enumerate(outputs, 1):
        kind, info = classify(it)
        if kind == "text":
            pic = f"X({info})"
        else:
            whole, scale = max(info[0], 1), info[1]
            pic = f"-9({whole})" + (f".9({scale})" if scale else "")
        ws_out.append(f"   05 CT-O{n} PIC {pic}.")
        out_len += out_width(it)
        moves_out.append(f"    MOVE {ref(it, subs)} TO CT-O{n}")
    src = [
        "       >>SOURCE FORMAT IS FREE",  # column 8: cobc reads the file as fixed format first
        "IDENTIFICATION DIVISION.", "PROGRAM-ID. CTDRIVER.",
        "ENVIRONMENT DIVISION.", "INPUT-OUTPUT SECTION.", "FILE-CONTROL.",
        "    SELECT CT-CASES ASSIGN TO 'cases.dat' ORGANIZATION LINE SEQUENTIAL.",
        "    SELECT CT-RESULTS ASSIGN TO 'results.dat' ORGANIZATION LINE SEQUENTIAL.",
        "DATA DIVISION.", "FILE SECTION.",
        "FD CT-CASES.", f"01 CT-CASE-REC PIC X({max(in_len, 1)}).",
        "FD CT-RESULTS.", f"01 CT-RES-REC PIC X({max(out_len, 1)}).",
        "WORKING-STORAGE SECTION.",
        "01 CT-EOF PIC X VALUE 'N'.",
        "01 CT-IN.", *(ws_in or ["   05 FILLER PIC X."]),
        "01 CT-OUT.", *(ws_out or ["   05 FILLER PIC X."]),
        *[l.strip() for l in linkage if l.strip()],
        "PROCEDURE DIVISION.",
        "CT-MAIN.",
        "    OPEN INPUT CT-CASES OUTPUT CT-RESULTS",
        "    PERFORM UNTIL CT-EOF = 'Y'",
        "      READ CT-CASES INTO CT-IN",
        "        AT END MOVE 'Y' TO CT-EOF",
        "        NOT AT END PERFORM CT-ONE",
        "      END-READ",
        "    END-PERFORM",
        "    CLOSE CT-CASES CT-RESULTS",
        "    STOP RUN.",
        "CT-ONE.",
        *[f"    INITIALIZE {u}" for u in using],
        *moves_in,
        f"    CALL '{program}' USING {' '.join(using)}",
        *moves_out,
        "    WRITE CT-RES-REC FROM CT-OUT.",
    ]
    return "\n".join(src) + "\n"


def encode_inputs(case_in: dict, inputs) -> bytes:
    rec = b""
    for key, it, subs in inputs:
        kind, info = classify(it)
        width = info if kind == "text" else 40
        if key not in case_in:
            rec += b" " + b" " * width
            continue
        v = case_in[key]
        if isinstance(v, dict) and "raw" in v:
            if kind != "num" or not info[3]:
                raise SetupError(f"'raw' is only allowed for DISPLAY numeric fields: {key}")
            flag, data = b"R", str(v["raw"]).encode(ENC)
        elif kind == "text":
            flag, data = b"T", str(v).encode(ENC)
        else:
            flag, data = b"N", str(v).encode(ENC)
        if len(data) > width:
            raise SetupError(f"value for {key} is longer than the field ({len(data)} > {width} bytes)")
        rec += flag + data.ljust(width)
    return rec


def out_width(it: Item) -> int:
    kind, info = classify(it)
    return info if kind == "text" else 1 + max(info[0], 1) + (1 + info[1] if info[1] else 0)


def decode_outputs(line: bytes, outputs) -> dict:
    res, pos = {}, 0
    for key, it, subs in outputs:
        width = out_width(it)
        chunk = line[pos:pos + width].ljust(width)
        pos += width
        res[key] = chunk.decode(ENC, errors="replace")
    return res


def same(kind: str, expected, actual: str) -> bool:
    if kind == "num":
        try:
            return Decimal(str(expected).strip() or "0") == Decimal(actual.strip())
        except InvalidOperation:
            return False
    return str(expected).rstrip() == actual.rstrip()


# ---------------------------------------------------------------- main

def run(program: str, in_dir: Path, cases_file: Path, out_dir: Path, stubs: list[str]) -> int:
    if not in_dir.is_dir():
        raise SetupError(f"{in_dir} not found. Run: python scripts/collect_deps.py {program}")
    if not cases_file.is_file():
        raise SetupError(f"{cases_file} not found (the cobol-tester agent writes it from spec section 9)")
    spec = json.loads(cases_file.read_text(encoding="utf-8"))
    env = cobol_env()

    work = KIT_ROOT / ".work" / program
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    changed = []
    for f in in_dir.iterdir():
        if not f.is_file():
            continue
        lines = f.read_bytes().replace(b"\r\n", b"\n").split(b"\n")
        for i, line in enumerate(lines):
            if line[6:7] in (b"*", b"/"):
                continue
            new = line
            if IBM_LINE.match(line[7:]):
                new = line[:6].ljust(6) + b"*" + line[7:]
            else:
                new = IBM_CLAUSE.sub(lambda m: b" " * len(m.group(0)), line)
            if new != line:
                lines[i] = new
                changed.append(f"{f.name} L{i + 1}: {line[7:].decode(ENC, 'replace').strip()}")
        (work / f.name).write_bytes(b"\n".join(lines))

    # COBOL programs = files with a PROCEDURE DIVISION; the rest are copybooks / CL
    programs = {}
    for f in work.iterdir():
        data = f.read_bytes()
        m = re.search(rb"PROGRAM-ID\.\s+([A-Z0-9@#$_-]+)", data, re.I)
        if m and re.search(rb"PROCEDURE\s+DIVISION", data, re.I):
            name = m.group(1).decode().upper()
            if name not in [s.upper() for s in stubs]:
                programs[name] = f
    main = programs.get(program.upper())
    if not main:
        raise SetupError(f"program {program} not found in {in_dir}")
    file_io = [n for n, f in programs.items() if re.search(rb"\bSELECT\s+\S+\s+ASSIGN\b", f.read_bytes(), re.I)]

    called = set()
    for f in programs.values():
        called |= {n for k, n in refs(f.read_bytes().decode(ENC, errors="replace"))[0] if k == "CALL"}
    stub_names = sorted((called - set(programs)) | {s.upper() for s in stubs})
    stub_files = []
    for s in stub_names:
        p = work / f"STUB_{s}.cbl"
        p.write_text(f"       >>SOURCE FORMAT IS FREE\nIDENTIFICATION DIVISION.\nPROGRAM-ID. {s}.\n"
                     "PROCEDURE DIVISION.\n    GOBACK.\n", encoding="ascii")
        stub_files.append(p.name)

    lines = code_lines(main, work)
    text = "\n".join(lines).upper()
    lk = re.search(r"LINKAGE\s+SECTION", text)
    pd = re.search(r"PROCEDURE\s+DIVISION\s+USING\s+(.*?)\.", text, re.S)
    if not lk or not pd:
        raise SetupError(f"{program} has no LINKAGE SECTION / PROCEDURE DIVISION USING: not a callable subroutine")
    using = [u for u in pd.group(1).split() if u not in ("BY", "REFERENCE", "CONTENT", "VALUE")]
    linkage = text[lk.end():pd.start()].lstrip(". \n").split("\n")
    if any(re.search(r"\bCOPY\b", line) for line in linkage):
        raise SetupError("COPY ... REPLACING in the LINKAGE SECTION is not supported by the driver")
    items = parse_items(entries(linkage))

    defaults = spec.get("defaults", {})
    cases = spec.get("cases", [])
    in_keys = list(dict.fromkeys([*defaults, *[k for c in cases for k in c.get("in", {})]]))
    out_keys = list(dict.fromkeys([*[k for c in cases for k in c.get("expect", {})], *spec.get("show", [])]))
    inputs = [(k, *resolve(k, items)) for k in in_keys]
    outputs = [(k, *resolve(k, items)) for k in out_keys]
    for k, it, _ in inputs + outputs:
        if classify(it)[0] == "dbcs":
            raise SetupError(f"PIC N/G field {k} is not supported by the driver yet")

    (work / "ctdriver.cbl").write_text(build_driver(program.upper(), using, linkage, inputs, outputs),
                                       encoding=ENC)
    exe = "ctdriver.exe" if os.name == "nt" else "ctdriver"
    cmd = [shutil.which("cobc", path=env["PATH"]), *COBC_FLAGS, "-I", ".", "-o", exe, "ctdriver.cbl",
           *[f.name for f in programs.values()], *stub_files]
    build = subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True, encoding=ENC, errors="replace")
    if build.returncode != 0:
        raise SetupError("cobc failed:\n" + (build.stdout + build.stderr)[-4000:])

    with open(work / "cases.dat", "wb") as fh:
        for c in cases:
            fh.write(encode_inputs({**defaults, **c.get("in", {})}, inputs) + b"\r\n")
    runp = subprocess.run([str(work / exe)], cwd=work, env=env, capture_output=True)
    if runp.returncode != 0:
        raise SetupError(f"driver ended with code {runp.returncode}:\n"
                         + (runp.stdout + runp.stderr).decode(ENC, "replace")[-4000:])
    results = (work / "results.dat").read_bytes().replace(b"\r\n", b"\n").split(b"\n")

    if len(results) < len(cases):
        raise SetupError(f"driver wrote {len(results)} result lines for {len(cases)} cases")
    rows, fails = [], 0
    for c, line in zip(cases, results):
        got = decode_outputs(line, outputs)
        exp = c.get("expect", {})
        bad = [k for k in exp if not same(classify(resolve(k, items)[0])[0], exp[k], got[k])]
        status = "PROBE" if not exp else ("FAIL" if bad else "PASS")
        fails += status == "FAIL"
        rows.append((c.get("id", "?"), c.get("in", {}), exp, got, status, bad))

    write_report(out_dir / "cobol-test.md", program, cases_file, changed, stub_names, file_io, rows, cmd)
    total = sum(r[4] != "PROBE" for r in rows)
    print(f"{program}: {total - fails}/{total} PASS, {fails} FAIL, {len(rows) - total} probe(s)")
    for r in rows:
        if r[4] != "PASS":
            print(f"  {r[0]} {r[4]} in={json.dumps(r[1], ensure_ascii=False)} "
                  + " ".join(f"{k}: exp={r[2].get(k)!r} got={r[3][k].strip()!r}" for k in (r[5] or r[3])))
    if stub_names:
        print("  stubs (empty programs): " + ", ".join(stub_names))
    if file_io:
        print("  WARNING file I/O in: " + ", ".join(file_io) + " (not pure logic, results may be meaningless)")
    print(f"  report: {out_dir / 'cobol-test.md'}")
    return 1 if fails else 0


def write_report(path, program, cases_file, changed, stubs, file_io, rows, cmd):
    def cell(v):
        return json.dumps(v, ensure_ascii=False).replace("|", "\\|") if v not in ({}, None) else ""
    out = [f"# {program}: COBOL test run (GnuCOBOL)", "",
           f"Cases: `{cases_file.name}`. Result: "
           f"{sum(r[4] == 'PASS' for r in rows)} PASS, {sum(r[4] == 'FAIL' for r in rows)} FAIL, "
           f"{sum(r[4] == 'PROBE' for r in rows)} probe.", "",
           "## Run conditions", "",
           f"- Compile: `cobc {' '.join(cmd[1:])}`",
           "- IBM-only syntax removed in the work copy (originals unchanged): " + ("; ".join(changed) or "none"),
           "- Stubbed programs (do nothing): " + (", ".join(stubs) or "none"),
           "- Programs with file I/O: " + (", ".join(file_io) or "none"),
           "- Runs in ASCII, not EBCDIC: comparisons / sorting that mix letters and digits may differ from IBM i.",
           "", "## Cases", "",
           "| # | Input | Expected | COBOL result | Status |", "|---|---|---|---|---|"]
    for cid, cin, exp, got, status, bad in rows:
        shown = {k: v.strip() for k, v in got.items()}
        out.append(f"| {cid} | {cell(cin)} | {cell(exp)} | {cell(shown)} | {status}"
                   + (f" ({', '.join(bad)})" if bad else "") + " |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def selftest() -> None:
    ents = entries(["01  REC.", "  03  A  PIC X(20).", "  03  B  PIC S9(13)V9(05).",
                    "  03  G.", "    05  FILLER OCCURS 3 TIMES.", "      07  C  PIC S9(03) COMP-3.",
                    "  03  D REDEFINES G PIC X(6)."])
    items = parse_items(ents)
    a, _ = resolve("A", items)
    assert classify(a) == ("text", 20)
    b, _ = resolve("B", items)
    assert classify(b) == ("num", (13, 5, True, True))
    c, subs = resolve("C(2)", items)
    assert classify(c) == ("num", (3, 0, True, False)) and subs == [2] and ref(c, subs) == "C OF G OF REC (2)"
    try:
        resolve("C", items)
        raise AssertionError("missing subscript not detected")
    except SetupError:
        pass
    print("selftest OK")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("id", nargs="?", help="COBOL program, e.g. SCCS010")
    ap.add_argument("--input", help="source folder (default: input/<ID>)")
    ap.add_argument("--cases", help="cases file (default: output/<ID>/cases.json)")
    ap.add_argument("--out", help="report folder (default: output/<ID>)")
    ap.add_argument("--stub", action="append", default=[], help="replace this called program by an empty stub")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.id:
        ap.error("give a COBOL program ID")
    pid = a.id.upper()
    try:
        return run(pid,
                   Path(a.input) if a.input else KIT_ROOT / "input" / pid,
                   Path(a.cases) if a.cases else KIT_ROOT / "output" / pid / "cases.json",
                   Path(a.out) if a.out else KIT_ROOT / "output" / pid,
                   a.stub)
    except SetupError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
