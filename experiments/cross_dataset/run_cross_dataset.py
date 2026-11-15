"""Cross-dataset generalization test for a GRU headline classifier.

Trains on one dataset and evaluates on its own held-out split and on the other
dataset, over several seeds. ISOT is cleaned of source artifacts first.

Data (not committed, place yourself):
  experiments/data/Fake.csv, True.csv        ISOT / Kaggle "fake-and-real-news-dataset"
  experiments/data/liar/{train,valid,test}.tsv   LIAR (Wang 2017), tab-separated

Run from the repository root:
  python experiments/cross_dataset/run_cross_dataset.py --seeds 5
"""

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from tensorflow.keras import callbacks
from tensorflow.keras.layers import Dense, Dropout, Embedding, GlobalMaxPooling1D, GRU
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer

DATA = Path("experiments/data")
OUT = Path("experiments/results/cross_dataset")
VOCAB, MAXLEN = 10000, 40
LIAR_FAKE = {"pants-fire", "false", "barely-true"}
DATELINE = re.compile(r"^[A-Z][A-Za-z .,/'-]{1,40}\s*\((reuters)\)\s*[-–—]?\s*", re.I)


def clean(text):
    text = DATELINE.sub("", str(text))
    text = re.sub(r"\breuters\b", " ", text, flags=re.I)
    text = re.sub(r"https?://\S+|pic\.twitter\.com/\S+", " ", text)
    return re.sub(r"[^a-z0-9\s]", " ", text.lower()).split()


def load_isot():
    fake = pd.read_csv(DATA / "Fake.csv").assign(label=1)
    real = pd.read_csv(DATA / "True.csv").assign(label=0)
    df = pd.concat([fake, real], ignore_index=True).dropna(subset=["title"])
    df = df.drop_duplicates(subset="title")
    return pd.DataFrame({"text": df["title"], "label": df["label"]})


def load_liar():
    cols = ["id", "label_raw", "statement"]
    parts = [pd.read_csv(DATA / "liar" / f"{s}.tsv", sep="\t", header=None, usecols=[0, 1, 2], names=cols)
             for s in ("train", "valid", "test")]
    df = pd.concat(parts, ignore_index=True)
    return pd.DataFrame({"text": df["statement"], "label": df["label_raw"].isin(LIAR_FAKE).astype(int)})


def prepare(df):
    out = df.copy()
    out["tokens"] = out["text"].apply(lambda t: " ".join(clean(t)))
    return out[out["tokens"].str.len() > 0].reset_index(drop=True)


def build_model():
    model = Sequential([
        Embedding(VOCAB, 100),
        GRU(64, dropout=0.3, return_sequences=True),
        GlobalMaxPooling1D(),
        Dropout(0.3),
        Dense(1, activation="sigmoid"),
    ])
    model.compile(optimizer=Adam(1e-3, clipnorm=1.0), loss="binary_crossentropy")
    return model


def score(y, prob):
    pred = (prob >= 0.5).astype(int)
    return {
        "accuracy": accuracy_score(y, pred),
        "precision": precision_score(y, pred, zero_division=0),
        "recall": recall_score(y, pred, zero_division=0),
        "f1": f1_score(y, pred, zero_division=0),
        "auc": roc_auc_score(y, prob),
    }


def run(source_name, source, target_name, target, seed):
    tr, rest = train_test_split(source, test_size=0.3, stratify=source["label"], random_state=seed)
    va, te = train_test_split(rest, test_size=0.5, stratify=rest["label"], random_state=seed)
    tok = Tokenizer(num_words=VOCAB, oov_token="<OOV>")
    tok.fit_on_texts(tr["tokens"])

    def enc(frame):
        return pad_sequences(tok.texts_to_sequences(frame["tokens"]), maxlen=MAXLEN, padding="post", truncating="post")

    np.random.seed(seed)
    model = build_model()
    model.fit(enc(tr), tr["label"].values, validation_data=(enc(va), va["label"].values), epochs=12, batch_size=64,
              verbose=0, callbacks=[callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True)])
    rows = []
    for split_name, frame in ((f"{source_name} (in-domain)", te), (f"{target_name} (cross-domain)", target)):
        prob = model.predict(enc(frame), verbose=0).ravel()
        rows.append({"train": source_name, "test": split_name, "seed": seed, **score(frame["label"].values, prob)})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    datasets = {"ISOT": prepare(load_isot()), "LIAR": prepare(load_liar())}
    for name, df in datasets.items():
        print(name, len(df), "samples, fake ratio", round(df["label"].mean(), 3))

    rows = []
    for src, tgt in (("ISOT", "LIAR"), ("LIAR", "ISOT")):
        for seed in range(args.seeds):
            rows += run(src, datasets[src], tgt, datasets[tgt], seed)
            print("done", src, "->", tgt, "seed", seed)

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "runs.csv", index=False)
    summary = df.groupby(["train", "test"])[["accuracy", "precision", "recall", "f1", "auc"]].agg(["mean", "std"]).round(4)
    summary.to_csv(OUT / "summary.csv")
    (OUT / "summary.json").write_text(json.dumps(json.loads(summary.to_json()), indent=2))
    print(summary)


if __name__ == "__main__":
    main()
