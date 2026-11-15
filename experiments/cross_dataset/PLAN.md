# This semester's experiment plan

Goal: show how models behave outside ISOT, and improve that.

## Why
All current models score about 95% on ISOT, which is likely inflated by source artifacts (the "(Reuters)" tag, source style, subject and date). The paper's LIAR numbers (0.95) also need re-checking, since published LIAR results are far lower.

## Steps
1. **Honest baseline** (`run_cross_dataset.py`): clean ISOT, deduplicate titles, train a GRU on one dataset and test on the other, 5 seeds, report mean and std plus AUC.
   - Needs `experiments/data/Fake.csv`, `True.csv` and `experiments/data/liar/{train,valid,test}.tsv`.
   - Output goes to `experiments/results/cross_dataset/`.
2. **Re-run BiLSTM, BERT and BERT+BiLSTM** with the same cleaning and splits. Train BiLSTM for more than 3 epochs.
3. **Improve cross-domain performance**: train on mixed datasets, augmentation, stronger encoders (RoBERTa, DeBERTa), full article body instead of headline.
4. **LLM direction**: few-shot prompting, LoRA fine-tuning of a small LLM, retrieval-augmented classification. Compare on the same test set.
5. **Explainability**: LIME or SHAP on the best model to confirm it uses content, not source markers.
6. Add the results to `paper/main.tex` and the thesis Chapter 5.

## Status
- [x] Step 1: GRU cross-dataset baseline run (5 seeds)
- [x] Step 2 (partly): BERT fine-tuned on ISOT, LIAR2 and mixed (3 seeds each); BiLSTM and BERT+BiLSTM not re-run
- [x] Step 3 (partly): mixed training done, ISOT accuracy kept at 0.984; still untested on a third dataset
- [x] Step 6 (partly): cross-dataset table added to paper and thesis Chapter 5
- [ ] Remaining: RoBERTa/DeBERTa, article-body input, LLM/RAG classification, LIME/SHAP explainability
