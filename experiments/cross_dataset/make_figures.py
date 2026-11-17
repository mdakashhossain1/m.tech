"""Draw the confusion matrix, ROC, precision-recall and loss figures from saved predictions.

Run from the repository root after train_three_models.py has finished for both datasets:
  python experiments/cross_dataset/make_figures.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import auc, confusion_matrix, precision_recall_curve, roc_curve

DATA = Path("experiments/results/figures_data")
TARGETS = {
    "Confusion.png": [Path("paper/figures"), Path("thesis/chap5-experimentalresults")],
    "ROC.png": [Path("paper/figures"), Path("thesis/chap5-experimentalresults")],
    "PR Curve.png": [Path("paper/figures")],
    "PR_Curve.png": [Path("thesis/chap5-experimentalresults")],
    "Loss.jpg": [Path("paper/figures"), Path("thesis/chap5-experimentalresults")],
}
DATASETS = [("isot", "ISOT"), ("liar", "LIAR")]
MODELS = [("bilstm", "BiLSTM", "#d95f02"), ("bert", "BERT", "#1b9e77"), ("bert_bilstm", "BERT+BiLSTM", "#7570b3")]


def load(dataset, model):
    return np.load(DATA / f"{dataset}_{model}.npz")


def save(fig, name):
    for folder in TARGETS[name]:
        fig.savefig(folder / name, dpi=200, bbox_inches="tight")
    plt.close(fig)


def confusion():
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.5))
    for r, (ds, ds_label) in enumerate(DATASETS):
        for c, (m, m_label, _) in enumerate(MODELS):
            d = load(ds, m)
            cm = confusion_matrix(d["y"], (d["p"] >= 0.5).astype(int), labels=[0, 1])
            ax = axes[r][c]
            ax.imshow(cm, cmap="Blues")
            for i in range(2):
                for j in range(2):
                    ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center", color="white" if cm[i, j] > cm.max() / 2 else "black")
            ax.set_xticks([0, 1], ["Real", "Fake"])
            ax.set_yticks([0, 1], ["Real", "Fake"])
            ax.set_title(f"{ds_label}: {m_label}", fontsize=10)
            ax.set_xlabel("Predicted")
            ax.set_ylabel("Actual")
    fig.tight_layout()
    save(fig, "Confusion.png")


def curves(kind, name):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, (ds, ds_label) in zip(axes, DATASETS):
        for m, m_label, colour in MODELS:
            d = load(ds, m)
            if kind == "roc":
                x, y, _ = roc_curve(d["y"], d["p"])
                ax.plot(x, y, color=colour, label=f"{m_label} (AUC {auc(x, y):.3f})")
            else:
                prec, rec, _ = precision_recall_curve(d["y"], d["p"])
                ax.plot(rec, prec, color=colour, label=f"{m_label} (AUC {auc(rec, prec):.3f})")
        if kind == "roc":
            ax.plot([0, 1], [0, 1], "--", color="grey", linewidth=1)
            ax.set_xlabel("False positive rate")
            ax.set_ylabel("True positive rate")
        else:
            ax.set_xlabel("Recall")
            ax.set_ylabel("Precision")
        ax.set_title(ds_label)
        ax.legend(loc="lower right" if kind == "roc" else "lower left", fontsize=8)
        ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def loss():
    fig, axes = plt.subplots(2, 3, figsize=(11, 6))
    for r, (ds, ds_label) in enumerate(DATASETS):
        for c, (m, m_label, _) in enumerate(MODELS):
            d = load(ds, m)
            epochs = np.arange(1, len(d["train_loss"]) + 1)
            ax = axes[r][c]
            ax.plot(epochs, d["train_loss"], marker="o", label="Training")
            ax.plot(epochs, d["val_loss"], marker="s", label="Validation")
            ax.set_xticks(epochs)
            ax.set_title(f"{ds_label}: {m_label}", fontsize=10)
            ax.set_xlabel("Epoch")
            ax.set_ylabel("Loss")
            ax.grid(alpha=0.3)
            ax.legend(fontsize=8)
    fig.tight_layout()
    save(fig, "Loss.jpg")


def main():
    confusion()
    roc = curves("roc", "ROC.png")
    save(roc, "ROC.png")
    for name in ("PR Curve.png", "PR_Curve.png"):
        save(curves("pr", name), name)
    loss()


if __name__ == "__main__":
    main()
