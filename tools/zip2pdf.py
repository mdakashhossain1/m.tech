"""Compile a zipped LaTeX project into a PDF with the installed MiKTeX.

Usage:
  python zip2pdf.py project.zip      (PDF is written next to the zip)
  python zip2pdf.py                  (opens a file picker)
Drag a zip onto zip2pdf.bat to do the same without a terminal.
"""

import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

MIKTEX_DIRS = [
    Path.home() / "AppData/Local/Programs/MiKTeX/miktex/bin/x64",
    Path("C:/Program Files/MiKTeX/miktex/bin/x64"),
]


def find_tool(name):
    found = shutil.which(name)
    if found:
        return found
    for d in MIKTEX_DIRS:
        candidate = d / f"{name}.exe"
        if candidate.exists():
            return str(candidate)
    sys.exit(f"{name} not found. Install MiKTeX first.")


def pick_zip():
    from tkinter import Tk, filedialog

    root = Tk()
    root.withdraw()
    chosen = filedialog.askopenfilename(title="Choose the zip file", filetypes=[("Zip files", "*.zip")])
    root.destroy()
    if not chosen:
        sys.exit("No file chosen.")
    return Path(chosen)


def find_main(folder):
    candidates = []
    for tex in folder.rglob("*.tex"):
        text = tex.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"^\s*\\documentclass", text, re.M) and "\\begin{document}" in text:
            candidates.append((len(text), tex))
    if not candidates:
        sys.exit("No main .tex file (with \\documentclass and \\begin{document}) found in the zip.")
    return max(candidates, key=lambda c: c[0])[1]


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="ignore")


def compile_tex(main, pdflatex, bibtex):
    cwd, stem = main.parent, main.stem
    args = [pdflatex, "-interaction=nonstopmode", "-halt-on-error", main.name]
    first = run(args, cwd)
    if first.returncode != 0:
        print(first.stdout[-1500:])
        sys.exit("pdflatex failed on the first pass. See the log above.")
    aux = (cwd / f"{stem}.aux").read_text(encoding="utf-8", errors="ignore") if (cwd / f"{stem}.aux").exists() else ""
    if "\\bibdata" in aux:
        run([bibtex, stem], cwd)
    for _ in range(3):
        run(args, cwd)
    pdf = cwd / f"{stem}.pdf"
    if not pdf.exists():
        sys.exit("No PDF was produced.")
    return pdf


def main():
    zip_path = Path(sys.argv[1]) if len(sys.argv) > 1 else pick_zip()
    pdflatex, bibtex = find_tool("pdflatex"), find_tool("bibtex")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(work)
        tex = find_main(work)
        print(f"Compiling {tex.name} ...")
        pdf = compile_tex(tex, pdflatex, bibtex)
        out = zip_path.with_suffix(".pdf")
        shutil.copyfile(pdf, out)
    print(f"Done: {out}")


if __name__ == "__main__":
    main()
