# Project backup

Remote repository: https://github.com/mdakashhossain1/m.tech

## Folder structure

| Location | Contents |
| --- | --- |
| `m.tech paper/` | Current thesis source, bibliography, images, formatting change record, and compiled PDF |
| `sample/` | Reference thesis PDF |
| `thesis-backup-before-formatting/` | Original thesis project before formatting changes |
| `ppt/` | Presentations and supporting material |
| `experiments/` | Training notebooks, evaluation scripts, results, model weights, and tokenizers |
| Root files | Original paper source and PDF, application, notebook, model weights, figures, and dependency files |

PDFs, presentations, experiment results, model weights, and archived source files are included in Git. Logs, LaTeX build intermediates, Python caches, notebook checkpoints, local environments, and the temporary `tmp/` preview folder are ignored. Ignored files remain on this computer but are not backed up to GitHub.

## Save later changes

Run these commands from the project root after making changes:

```powershell
git status --short
git add .
git commit -m "Describe the changes you made"
git push origin main
```

Local edits reach GitHub only after a successful push. Check the push output and repository commit history when saving important changes.

## Restore on another computer

```powershell
git clone https://github.com/mdakashhossain1/m.tech.git
cd m.tech
```

The current thesis entry point is `m.tech paper/IT_Thesis_LaTeX_Format.tex`. Compile from its folder with pdfLaTeX, BibTeX, and pdfLaTeX twice. The compiled PDF is also stored in the repository, so reading it does not require a LaTeX installation.

The original formatting backup and commented source blocks are retained for restoring excluded thesis sections. See `m.tech paper/FORMATTING_CHANGES.md` for details.
