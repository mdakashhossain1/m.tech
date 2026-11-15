"""Fine-tune a transformer on ISOT, LIAR2 or both, and test in-domain and cross-domain.

Uses PyTorch with DirectML (AMD GPU on Windows) when available, otherwise CPU.
Run from the repository root:
  python experiments/cross_dataset/finetune_transformer.py --model bert-base-uncased --train isot --seeds 3
"""

import argparse
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

DATA = Path("experiments/data")
OUT = Path("experiments/results/cross_dataset")
DATELINE = re.compile(r"^[A-Z][A-Za-z .,/'-]{1,40}\s*\((reuters)\)\s*[-–—]?\s*", re.I)
LIAR_FAKE = {0, 1, 2}


def clean(text):
    text = DATELINE.sub("", str(text))
    text = re.sub(r"\breuters\b", " ", text, flags=re.I)
    text = re.sub(r"https?://\S+|pic\.twitter\.com/\S+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load(name):
    if name == "isot":
        df = pd.read_parquet(DATA / "isot_hf.parquet").dropna(subset=["title"]).drop_duplicates(subset="title")
        out = pd.DataFrame({"text": df["title"], "label": (df["label"] == 0).astype(int)})
    else:
        df = pd.read_parquet(DATA / "liar2.parquet")
        out = pd.DataFrame({"text": df["statement"], "label": df["label"].isin(LIAR_FAKE).astype(int)})
    out["text"] = out["text"].apply(clean)
    return out[out["text"].str.len() > 0].reset_index(drop=True)


def split(df, seed):
    tr, rest = train_test_split(df, test_size=0.3, stratify=df["label"], random_state=seed)
    va, te = train_test_split(rest, test_size=0.5, stratify=rest["label"], random_state=seed)
    return tr, va, te


def device():
    try:
        import torch_directml
        return torch_directml.device()
    except Exception:
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def batches(tok, texts, labels, bs, max_len, shuffle, rng):
    idx = rng.permutation(len(texts)) if shuffle else np.arange(len(texts))
    for i in range(0, len(idx), bs):
        j = idx[i:i + bs]
        enc = tok([texts[k] for k in j], truncation=True, max_length=max_len, padding=True, return_tensors="pt")
        yield enc, torch.tensor([labels[k] for k in j])


def predict(model, tok, dev, frame, bs, max_len):
    model.eval()
    probs = []
    with torch.no_grad():
        for enc, _ in batches(tok, frame["text"].tolist(), frame["label"].tolist(), bs * 2, max_len, False, None):
            logits = model(**{k: v.to(dev) for k, v in enc.items()}).logits
            probs.append(torch.softmax(logits.float(), -1)[:, 1].cpu().numpy())
    return np.concatenate(probs)


def score(y, p):
    pred = (p >= 0.5).astype(int)
    return {
        "accuracy": accuracy_score(y, pred),
        "precision": precision_score(y, pred, zero_division=0),
        "recall": recall_score(y, pred, zero_division=0),
        "f1": f1_score(y, pred, zero_division=0),
        "auc": roc_auc_score(y, p),
    }


def run(args, seed, dev):
    torch.manual_seed(seed)
    rng = np.random.RandomState(seed)
    sets = {n: split(load(n), seed) for n in ("isot", "liar")}
    names = ["isot", "liar"] if args.train == "mixed" else [args.train]
    train = pd.concat([sets[n][0] for n in names]).reset_index(drop=True)
    val = pd.concat([sets[n][1] for n in names]).reset_index(drop=True)
    if args.max_train:
        train = train.sample(n=min(args.max_train, len(train)), random_state=seed).reset_index(drop=True)

    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(args.model, num_labels=2).to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    steps = args.epochs * ((len(train) + args.bs - 1) // args.bs)
    sched = get_linear_schedule_with_warmup(opt, int(0.06 * steps), steps)

    best, best_state = -1, None
    for epoch in range(args.epochs):
        model.train()
        t0 = time.time()
        for enc, y in batches(tok, train["text"].tolist(), train["label"].tolist(), args.bs, args.max_len, True, rng):
            loss = model(**{k: v.to(dev) for k, v in enc.items()}, labels=y.to(dev)).loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad()
        vf1 = f1_score(val["label"], (predict(model, tok, dev, val, args.bs, args.max_len) >= 0.5).astype(int))
        print(f"  seed {seed} epoch {epoch + 1}: val F1 {vf1:.4f} ({time.time() - t0:.0f}s)", flush=True)
        if vf1 > best:
            best = vf1
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)

    rows = []
    for tgt in ("isot", "liar"):
        te = sets[tgt][2] if tgt in names else pd.concat(sets[tgt])
        kind = "in-domain" if tgt in names else "cross-domain"
        p = predict(model, tok, dev, te, args.bs, args.max_len)
        rows.append({"model": args.model, "train": args.train, "test": f"{tgt} ({kind})", "seed": seed,
                     **score(te["label"].values, p)})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="bert-base-uncased")
    ap.add_argument("--train", choices=["isot", "liar", "mixed"], default="isot")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--max-len", type=int, default=64)
    ap.add_argument("--max-train", type=int, default=0)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    dev = device()
    print("device:", dev, "| model:", args.model, "| train:", args.train, flush=True)
    rows = []
    for seed in range(args.seeds):
        rows += run(args, seed, dev)
        name = f"{args.model.replace('/', '_')}_{args.train}{args.tag}.csv"
        pd.DataFrame(rows).to_csv(OUT / name, index=False)
    df = pd.DataFrame(rows)
    print(df.groupby("test")[["accuracy", "precision", "recall", "f1", "auc"]].agg(["mean", "std"]).round(4).to_string())


if __name__ == "__main__":
    main()
