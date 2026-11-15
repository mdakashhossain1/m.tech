#!/usr/bin/env python3
"""
Build script for the thesis (IT_Thesis_LaTeX_Format.tex).

This does NOT compile LaTeX itself -- there is no PDF-rendering TeX engine
written in Python. Instead it drives a real TeX engine (pdflatex/bibtex,
e.g. from MiKTeX or TeX Live) through the pass sequence this document needs
(citations via natbib/bibtex, table of contents, list of figures/tables/
algorithms all need multiple passes to stabilize), and then filters the
.log file down to the lines that actually indicate a failure, instead of
making you scroll through hundreds of lines of benign package-version
chatter.

Usage:
    python scripts/compile.py            # full build (pdflatex, bibtex, pdflatex x2)
    python scripts/compile.py --quick     # single pdflatex pass only (fast iteration)
    python scripts/compile.py --clean     # remove aux/log/toc/etc. build artifacts
    python scripts/compile.py --engine xelatex   # use a different engine
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JOBNAME = "IT_Thesis_LaTeX_Format"
TEX_FILE = PROJECT_ROOT / f"{JOBNAME}.tex"

# Extensions produced by a LaTeX build that --clean should remove.
CLEAN_EXTENSIONS = [
    ".aux", ".log", ".toc", ".lof", ".lot", ".loa", ".out", ".bbl", ".blg",
    ".fls", ".fdb_latexmk", ".synctex.gz", ".maf", ".mtc", ".mtc0", ".mlf",
    ".mlt", ".auxlock",
]

# Common install locations to fall back to if the engine isn't on PATH yet
# (e.g. right after installing MiKTeX, before the shell has picked up PATH).
FALLBACK_DIRS = [
    Path(r"C:\Program Files\MiKTeX\miktex\bin\x64"),
    Path.home() / "AppData/Local/Programs/MiKTeX/miktex/bin/x64",
    Path(r"C:\texlive\2025\bin\windows"),
    Path(r"C:\texlive\2024\bin\windows"),
]


def clean_build_artifacts() -> int:
    """Remove the main job's build files plus every per-chapter .aux file
    \\include creates (chap1-introduction/introduction.aux, etc.). A stale
    chapter .aux left over from a previous run can make pdflatex reuse old
    cross-reference/label data instead of what's in the current .tex source."""
    removed = 0
    for ext in CLEAN_EXTENSIONS:
        f = PROJECT_ROOT / f"{JOBNAME}{ext}"
        if f.exists():
            f.unlink()
            removed += 1
    for aux in PROJECT_ROOT.glob("chap*/*.aux"):
        aux.unlink()
        removed += 1
    return removed


def find_executable(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    for d in FALLBACK_DIRS:
        candidate = d / f"{name}.exe"
        if candidate.exists():
            return str(candidate)
    return None


def run(cmd: list[str], cwd: Path) -> int:
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout[-2000:])  # tail only; the .log file has the full detail
    if result.returncode != 0:
        print(f"  -> exited with code {result.returncode} (this is normal for pdflatex when there are LaTeX errors; details are parsed from the .log below)")
    return result.returncode


ERROR_LINE_RE = re.compile(r"^(?P<file>.+?):(?P<line>\d+): (?P<msg>.+)$")


def parse_log_for_errors(log_path: Path) -> list[str]:
    """Extract real errors from a -file-line-error log, with a couple of
    context lines for each, skipping benign package/version chatter."""
    if not log_path.exists():
        return [f"No log file found at {log_path} -- the engine may not have run at all."]

    text = log_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    # TeX labels some pagination quirks (e.g. a longtable row splitting across
    # a page boundary) as "ignored error" -- it already recovered on its own,
    # so these are noise, not build failures.
    BENIGN_MARKERS = ("ignored error",)

    blocks = []
    for i, line in enumerate(lines):
        m = ERROR_LINE_RE.match(line)
        if m and not any(marker in m.group("msg") for marker in BENIGN_MARKERS):
            context = lines[i : i + 4]
            blocks.append("\n".join(context))

    if "Fatal error occurred, no output PDF file produced" in text:
        blocks.append("FATAL: no output PDF file produced (see full log for the cause above).")

    return blocks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--quick", action="store_true", help="Single pdflatex pass only, no bibtex, no second pass (fast iteration, citations/TOC/refs will show as '??').")
    parser.add_argument("--clean", action="store_true", help="Remove build artifacts (.aux/.log/.toc/etc.) and exit.")
    parser.add_argument("--engine", default="pdflatex", help="TeX engine to use (pdflatex, xelatex, lualatex). Default: pdflatex.")
    args = parser.parse_args()

    if args.clean:
        removed = clean_build_artifacts()
        print(f"Removed {removed} build artifact(s).")
        return 0

    if not TEX_FILE.exists():
        print(f"ERROR: could not find {TEX_FILE}")
        return 1

    engine = find_executable(args.engine)
    bibtex = find_executable("bibtex")

    if engine is None:
        print(
            f"ERROR: could not find '{args.engine}' on PATH or in common install locations.\n"
            "Install a TeX distribution (MiKTeX recommended for Windows: https://miktex.org/download)\n"
            "and make sure its bin directory is on PATH, then re-run this script.\n"
            "If you just installed MiKTeX, you may need to open a new terminal for PATH to update."
        )
        return 1

    print(f"Using engine: {engine}")

    if not args.quick:
        removed = clean_build_artifacts()
        print(f"Cleaned {removed} stale build artifact(s) before full rebuild.")

    engine_cmd = [
        engine,
        "-file-line-error",
        "-interaction=nonstopmode",
        f"{JOBNAME}.tex",
    ]

    print("\n=== Pass 1: initial compile ===")
    run(engine_cmd, cwd=PROJECT_ROOT)

    if not args.quick:
        if bibtex is None:
            print("WARNING: bibtex not found; skipping bibliography step (citations will show as '??').")
        else:
            print("\n=== Running bibtex (bibliography) ===")
            run([bibtex, JOBNAME], cwd=PROJECT_ROOT)

        print("\n=== Pass 2: resolve citations/references ===")
        run(engine_cmd, cwd=PROJECT_ROOT)

        print("\n=== Pass 3: stabilize table of contents/lists ===")
        run(engine_cmd, cwd=PROJECT_ROOT)

    log_path = PROJECT_ROOT / f"{JOBNAME}.log"
    pdf_path = PROJECT_ROOT / f"{JOBNAME}.pdf"

    errors = parse_log_for_errors(log_path)

    print("\n" + "=" * 60)
    if errors:
        print(f"FOUND {len(errors)} ERROR BLOCK(S):\n")
        for block in errors:
            print(block)
            print("-" * 60)
    else:
        print("No '!'-level errors found in the log.")

    if pdf_path.exists():
        print(f"\nPDF produced: {pdf_path}")
        return 0 if not errors else 1
    else:
        print(f"\nNo PDF was produced at {pdf_path}. Compilation failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
