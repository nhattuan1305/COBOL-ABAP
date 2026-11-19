"""Print COBOL / copybook / CL sources as UTF-8 with original line numbers.

Sources exported from IBM i (AS/400) are usually Shift-JIS (cp932). The file is
decoded as UTF-8 first; if that fails it falls back to cp932 (override with --enc).

Sources live in input/<ID>/ (one folder per program, filled by collect_deps.py).

Usage:
  python scripts/read_cobol.py --root input/SCCS010 SCCS010            # the program
  python scripts/read_cobol.py --root input/SCCS010 SCCS01R CVTCOMMON  # its copybooks
  python scripts/read_cobol.py --root input/SCCS010 --refs SCCS010     # only COPY / CALL lines
  python scripts/read_cobol.py --enc cp932 path/to/file.txt
"""
import argparse
import re
import sys
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_EXT = {".txt", ".cbl", ".cob", ".cpy", ".clp", ".clle", ".src", ""}


def find(name: str, root: Path) -> Path:
    p = Path(name)
    if p.is_file():
        return p
    stem = p.stem.upper()
    hits = sorted(
        f for f in root.rglob("*")
        if f.is_file() and f.stem.upper() == stem and f.suffix.lower() in SOURCE_EXT
    )
    if not hits:
        sys.exit(f"NOT FOUND: {name} (searched under {root})")
    return hits[0]


def decode(raw: bytes, enc: str | None) -> tuple[str, str]:
    if enc:
        return raw.decode(enc, errors="replace"), enc
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return raw.decode("cp932", errors="replace"), "cp932"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="+", help="member name (e.g. SCCS010) or file path")
    ap.add_argument("--root", default=str(KIT_ROOT / "input"), help="folder to search (default: input/)")
    ap.add_argument("--refs", action="store_true", help="print only COPY / CALL statements")
    ap.add_argument("--enc", help="force encoding, e.g. cp932, utf-8")
    args = ap.parse_args()

    root = Path(args.root)
    for name in args.names:
        path = find(name, root)
        text, enc = decode(path.read_bytes(), args.enc)
        # split on LF only: str.splitlines() would also split on chars like \x1c / \x85
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        print(f"===== {path} ({len(lines)} lines, {enc})")
        for no, line in enumerate(lines, 1):
            if args.refs:
                body = line[6:]
                if body[:1] == "*" or not re.search(r"\b(COPY|CALL)\b", body, re.I):
                    continue
            print(f"{no:4} {line.rstrip()}")


if __name__ == "__main__":
    main()
