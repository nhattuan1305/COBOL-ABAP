"""Find every source file a COBOL program needs (COPY + CALL, all levels) and copy them into input/<ID>/.

It reads the program, collects the names after COPY and CALL, finds those files
by name under the source folder(s), and repeats for each file found.

The source folder comes from "source_dirs" in config.json (kit root). Relative
paths there are resolved from the kit root. --src overrides it for one run.

Usage:
  python scripts/collect_deps.py SJFS010 --dry-run          # only show the tree
  python scripts/collect_deps.py SJFS010                    # copy into input/SJFS010/
  python scripts/collect_deps.py SJFS010 SCCS060            # one folder per ID
  python scripts/collect_deps.py SJFS010 --depth 1          # direct dependencies only
  python scripts/collect_deps.py SJFS010 --src "D:/other/sources"
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[1]
CONFIG = KIT_ROOT / "config.json"


def source_dirs(cli_src: list[str] | None) -> list[Path]:
    if cli_src:
        dirs = cli_src
    else:
        try:
            dirs = json.loads(CONFIG.read_text(encoding="utf-8"))["source_dirs"]
        except (OSError, ValueError, KeyError) as e:
            sys.exit(f"Cannot read source_dirs from {CONFIG}: {e}\nSet it there, or pass --src.")
    paths = [p if p.is_absolute() else KIT_ROOT / p for p in map(Path, dirs)]
    bad = [str(p) for p in paths if not p.is_dir()]
    if bad:
        sys.exit("Source folder not found: " + ", ".join(bad) + f"\nFix source_dirs in {CONFIG}, or pass --src.")
    return paths

RE_COPY = re.compile(r"\bCOPY\s+([A-Z0-9@#$][A-Z0-9@#$_-]*)", re.I)
RE_CALL = re.compile(r"\bCALL\s+['\"]([A-Z0-9@#$_-]+)['\"]", re.I)       # COBOL static call
RE_CALL_CL = re.compile(r"\bCALL\s+PGM\(\s*(?:[^/)]*/)?([A-Z0-9@#$_]+)", re.I)  # CL call
RE_CALL_DYN = re.compile(r"\bCALL\s+([A-Z][A-Z0-9-]*)\b(?!\s*PGM)", re.I)    # COBOL dynamic call
RE_CL_COMMENT = re.compile(r"/\*.*?(\*/|$)")                                # CL comment /* ... */


def refs(text: str) -> tuple[list[tuple[str, str]], list[str]]:
    """Return ([(kind, name)], [dynamic-call notes]) from source text, skipping comments and deleted lines."""
    found, dynamic = [], []
    for line in text.replace("\r\n", "\n").split("\n"):
        line = RE_CL_COMMENT.sub(" ", line)
        tag, body = line[:6], line[6:]
        if "!DEL!" in tag or body[:1] in ("*", "/"):
            continue
        for m in RE_COPY.finditer(body):
            found.append(("COPY", m.group(1).upper()))
        for m in RE_CALL.finditer(body):
            found.append(("CALL", m.group(1).upper()))
        for m in RE_CALL_CL.finditer(line):
            found.append(("CALL", m.group(1).upper()))
        m = RE_CALL_DYN.search(body)
        if m and not RE_CALL.search(body) and m.group(1).upper() != "PGM":
            dynamic.append(line.strip())
    return found, dynamic


def build_index(src_dirs: list[Path]) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for d in src_dirs:
        for f in d.rglob("*"):
            if f.is_file():
                index.setdefault(f.stem.upper(), []).append(f)
    # prefer original folders over extracted copies (folder names starting with "_")
    for paths in index.values():
        paths.sort(key=lambda p: (any(part.startswith("_") for part in p.parts), len(p.parts), str(p)))
    return index


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", help="COBOL member names, e.g. SJFS010")
    ap.add_argument("--src", action="append", help="source folder, overrides config.json (repeatable)")
    ap.add_argument("--out", default=str(KIT_ROOT / "input"), help="parent folder; files go to <out>/<ID>/ (default: input/)")
    ap.add_argument("--depth", type=int, default=99, help="max levels to follow (default: all)")
    ap.add_argument("--dry-run", action="store_true", help="show the tree, copy nothing")
    ap.add_argument("--selftest", action="store_true", help="run the parser self-test and exit")
    args = ap.parse_args()

    if args.selftest:
        selftest()
        return
    if not args.ids:
        ap.error("give at least one COBOL ID")

    dirs = source_dirs(args.src)
    index = build_index(dirs)
    print(f"Indexed {sum(len(v) for v in index.values())} files from: {', '.join(map(str, dirs))}\n")

    for program_id in (i.upper() for i in args.ids):
        collect(program_id, index, Path(args.out) / program_id, args.depth, args.dry_run)


def collect(program_id: str, index: dict[str, list[Path]], out: Path, depth: int, dry_run: bool) -> None:
    """Print the dependency tree of one program and copy its files into out/ (= input/<ID>/)."""
    seen: set[str] = set()
    to_copy: list[Path] = []
    missing: list[str] = []
    dynamic_calls: list[str] = []

    def visit(name: str, kind: str, level: int) -> None:
        indent = "    " * level
        if name in seen:
            print(f"{indent}{kind} {name}  (already listed)")
            return
        seen.add(name)
        paths = index.get(name)
        if not paths:
            missing.append(name)
            print(f"{indent}{kind} {name}  ** NOT FOUND **")
            return
        path = paths[0]
        print(f"{indent}{kind} {name}  {path}")
        to_copy.append(path)
        if level >= depth:
            return
        text = path.read_bytes().decode("cp932", errors="replace")
        found, dyn = refs(text)
        dynamic_calls.extend(f"{name}: {d}" for d in dyn)
        for k, n in dict.fromkeys(found):  # keep order, drop duplicates
            visit(n, k, level + 1)

    print(f"===== {program_id}")
    visit(program_id, "PGM ", 0)
    print(f"\nFiles: {len(to_copy)}   Not found: {len(missing)}")
    if missing:
        print("  not found: " + ", ".join(missing))
    if dynamic_calls:
        print("  dynamic CALL (target decided at run time, check by hand):")
        for d in dynamic_calls:
            print("    " + d)

    if dry_run:
        print("--dry-run: nothing copied\n")
        return
    out.mkdir(parents=True, exist_ok=True)
    for p in to_copy:
        shutil.copy2(p, out / p.name)
    print(f"Copied {len(to_copy)} files to {out}\n")


def selftest() -> None:
    src = "\n".join([
        "       PROCEDURE DIVISION USING SJFS01R.",
        "           COPY CVTCOMMON.",
        "           COPY  SJFS02R  SUPPRESS.",
        "           CALL  'SJFS020'  USING  SJFS02R.",
        "      *    CALL  'IGNORED1'  USING X.",
        "!DEL!      CALL  'IGNORED2'.",
        "             CALL       PGM(QGPL/CCURDAT2) PARM(&D)",
        "           CALL  WS-PGM-NAME  USING X.",
        "    /* ----  CALL MOTO USER-ID GET ---------------------------------*/",
    ])
    found, dyn = refs(src)
    assert found == [("COPY", "CVTCOMMON"), ("COPY", "SJFS02R"), ("CALL", "SJFS020"), ("CALL", "CCURDAT2")], found
    assert len(dyn) == 1 and "WS-PGM-NAME" in dyn[0], dyn
    print("selftest OK")


if __name__ == "__main__":
    main()
