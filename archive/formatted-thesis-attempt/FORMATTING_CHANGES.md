# Thesis formatting change record

Reference: `../sample/Sumit_Bhowmik2026_Thesis.pdf`.

The original project is preserved in `../thesis-backup-before-formatting/`. `../TEX OLD.tex` was consulted as a supplementary content source and was left unchanged.

## Active structure

Title page, dedication, abstract, declaration, supervisor certificate, project coordinator certificate, department head certificate, examiner certificate, acknowledgment, contents, list of figures, list of tables, and an empty list of algorithms.

1. Introduction: Challenges and Issues; Motivation of the Research; Research Objectives; Thesis Contributions; Thesis Organization.
2. Related Work: Introduction; Summary. Existing thematic discussion is retained under Introduction without additional numbered headings.
3. Proposed Approach: Introduction; Dataset Description; Data Preprocessing; Model Building. The model subsections describe BiLSTM, BERT, and BERT + BiLSTM, using this research's models rather than the sample's face-recognition models.

Bibliography follows Chapter 3.

## Formatting

A4 pages, 12-point Computer Modern text, 1.25-inch side margins, 1-inch top and bottom margins, and 1.5 line spacing. Certificate headers and the title page use their dedicated spacing. Certificate settings are scoped so they do not alter subsequent pages. Roman page numbering applies to the contents and lists; Arabic numbering begins with Chapter 1 at page 1.

The title page fits on one page. The original unmatched brace in the dedication was fixed. Certificate headers now fit within the text width. Dataset and hyperparameter tables wrap within the margins. Both architecture figures are constrained to the page. Obsolete chapter references and the six-chapter organization description were updated. Conflicting, unused citation and mini-table-of-contents packages were disabled.

## Preserved exclusions

- `IT_Thesis_LaTeX_Format.tex`: includes for Abbreviations, Symbols and Notations, Background Details, Experimental Results, Conclusion and Future Direction, and List of Publications are commented out.
- `chap2-backrounddetails/backrounddetails.tex`: original chapter is entirely commented. Its preprocessing and relevant model explanations were reused in Chapter 3.
- `chap5-experimentalresults/experimentalresults.tex`: original chapter is entirely commented. Dataset description, dataset table, and training configuration were reused in Chapter 3. Evaluation metrics, performance tables, result figures, and discussion remain in the commented original.
- `chap6-conclusion/conclusion.tex`: original chapter is entirely commented.
- `chap3-relatedwork/relatedwork.tex`: the additional literature comparison table and thematic headings are commented. The thematic discussion remains active.
- `chap4-proposedapproach/proposedapproach.tex`: the complete previous chapter is preserved as comments at the end, including its separate problem statement, algorithm, design-rationale heading, and summary. The relevant system and model explanations are retained in the new structure.
- `chap1-introduction/introduction.tex`: the old six-chapter organization is preserved as comments below the replacement three-chapter description.
- `chap0-preamble/abstract.tex`: the original abstract is preserved as comments. The active abstract was shortened using the not-ai preservation approach; the reported model results remain unchanged.
- Supervisor, coordinator, and department head certificate files: original headers are preserved as comments below the replacement headers.

## Restoring material

For a whole excluded chapter, remove the first `% ` from each original line and re-enable its include in the main file. For a retained block, uncomment only that block. Recheck chapter references and rebuild the bibliography after restoring material. Do not uncomment a complete archived version beside its active replacement, as this would duplicate content and labels. The backup provides the simplest way to recover the original six-chapter project.

## Details preserved from the author's source

The degree remains Master of Computer Application, as stated in the current source, although the reference title page states Master of Technology. The author's name, registration number, roll number, supervisor, certificate signatories, and date have not been replaced with the sample author's details. The supervisor's phone number was updated to `+91 7005019955` as supplied by the author.

The dataset counts, hyperparameters, citations, and reported performance values were retained from the supplied research. This task did not independently validate experimental claims or bibliography metadata. Matching the supplied sample is not an independent verification of current university submission rules.

## Bibliography links

Verified URLs are displayed on separate lines beneath their references, in purple, with clickable PDF links. The ISOT dataset URL was replaced with the current [ISOT Research Lab dataset page](https://onlineacademiccommunity.uvic.ca/isot/datasets/). Seventeen of the nineteen active references have links; the Aphiwongsophon and Mehta entries have no confidently verified matching URL.

Some existing citation metadata differs from the publication records. For example, the [Rai paper](https://www.sciencedirect.com/science/article/pii/S2666307422000092) is published in International Journal of Cognitive Computing in Engineering, whereas the supplied entry names a different journal. The supplied citation details were preserved during this link-formatting change. These discrepancies should be checked against the original papers before submission.

## Build instructions

Open `IT_Thesis_LaTeX_Format.tex` as the project entry point. Compile from this folder with pdfLaTeX, then BibTeX, then pdfLaTeX twice. The installed MiKTeX compiler was used because the built-in editor compiler could not initialize for this project. The final PDF was checked for unresolved references, missing citations, overflow, numbering, excluded headings, and page layout.
