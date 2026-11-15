"""Train BiLSTM, BERT and BERT+BiLSTM on one dataset and save predictions and loss curves for the figures.

Run from the repository root:
  python experiments/cross_dataset/train_three_models.py --dataset isot
  python experiments/cross_dataset/train_three_models.py --dataset liar
"""

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

from finetune_transformer import device, load, split

OUT = Path("experiments/results/figures_data")
BERT = "bert-base-uncased"
SETTINGS = {
    "bilstm": {"lr": 1e-3, "weight_decay": 0.0},
    "bert": {"lr": 2e-5, "weight_decay": 0.01},
    "bert_bilstm": {"lr": 2e-5, "weight_decay": 0.01},
}


class BiLSTMClassifier(nn.Module):
    def __init__(self, vocab, dim=128, hidden=128):
        super().__init__()
        self.emb = nn.Embedding(vocab, dim, padding_idx=0)
        self.lstm = nn.LSTM(dim, hidden, num_layers=2, batch_first=True, bidirectional=True, dropout=0.5)
        self.drop = nn.Dropout(0.5)
        self.out = nn.Linear(2 * hidden, 2)

    def forward(self, ids, mask):
        seq, _ = self.lstm(self.emb(ids))
        pooled = seq.masked_fill(~mask.bool().unsqueeze(-1), -1e4).max(dim=1).values
        return self.out(self.drop(pooled))


class BertClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = AutoModelForSequenceClassification.from_pretrained(BERT, num_labels=2)

    def forward(self, ids, mask):
        return self.net(input_ids=ids, attention_mask=mask).logits


class BertBiLSTMClassifier(nn.Module):
    def __init__(self, dev, hidden=128):
        super().__init__()
        self.dev = dev
        self.bert = AutoModel.from_pretrained(BERT).to(dev)
        self.drop_in = nn.Dropout(0.1)
        self.lstm = nn.LSTM(self.bert.config.hidden_size, hidden, batch_first=True, bidirectional=True)
        self.dense = nn.Linear(2 * hidden, hidden)
        self.drop_out = nn.Dropout(0.3)
        self.out = nn.Linear(hidden, 2)

    def forward(self, ids, mask):
        states = self.drop_in(self.bert(input_ids=ids, attention_mask=mask).last_hidden_state.cpu())
        mask = mask.cpu()
        seq, _ = self.lstm(states)
        pooled = seq.masked_fill(~mask.bool().unsqueeze(-1), -1e4).max(dim=1).values
        return self.out(self.drop_out(torch.relu(self.dense(pooled))))


def build(name, tok, dev):
    if name == "bilstm":
        return BiLSTMClassifier(tok.vocab_size)
    return BertClassifier().to(dev) if name == "bert" else BertBiLSTMClassifier(dev)


def batches(tok, frame, bs, max_len, shuffle, rng):
    idx = rng.permutation(len(frame)) if shuffle else np.arange(len(frame))
    texts, labels = frame["text"].tolist(), frame["label"].tolist()
    for i in range(0, len(idx), bs):
        j = idx[i:i + bs]
        enc = tok([texts[k] for k in j], truncation=True, max_length=max_len, padding=True, return_tensors="pt")
        yield enc["input_ids"], enc["attention_mask"], torch.tensor([labels[k] for k in j])


def evaluate(model, tok, dev, frame, bs, max_len, loss_fn):
    model.eval()
    probs, total = [], 0.0
    with torch.no_grad():
        for ids, mask, y in batches(tok, frame, bs, max_len, False, None):
            logits = model(ids.to(dev), mask.to(dev)).float()
            total += loss_fn(logits, y.to(logits.device)).item() * len(y)
            probs.append(torch.softmax(logits, -1)[:, 1].cpu().numpy())
    return np.concatenate(probs), total / len(frame)


def train_one(name, dataset, sets, args, dev):
    train, val, test = sets
    torch.manual_seed(args.seed)
    rng = np.random.RandomState(args.seed)
    tok = AutoTokenizer.from_pretrained(BERT)
    dev = torch.device("cpu") if name == "bilstm" else dev
    model = build(name, tok, dev)
    cfg = SETTINGS[name]
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["weight_decay"])
    steps = args.epochs * ((len(train) + args.bs - 1) // args.bs)
    sched = get_linear_schedule_with_warmup(opt, int(0.06 * steps), steps)
    loss_fn = nn.CrossEntropyLoss()
    hist = {"train_loss": [], "val_loss": []}
    best, best_state = float("inf"), None
    for epoch in range(args.epochs):
        model.train()
        t0, running, seen = time.time(), 0.0, 0
        for ids, mask, y in batches(tok, train, args.bs, args.max_len, True, rng):
            logits = model(ids.to(dev), mask.to(dev)).float()
            loss = loss_fn(logits, y.to(logits.device))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad()
            running += loss.item() * len(y)
            seen += len(y)
        _, vloss = evaluate(model, tok, dev, val, args.bs, args.max_len, loss_fn)
        hist["train_loss"].append(running / seen)
        hist["val_loss"].append(vloss)
        print(f"  {dataset} {name} epoch {epoch + 1}: train {running / seen:.4f} val {vloss:.4f} ({time.time() - t0:.0f}s)", flush=True)
        if vloss < best:
            best = vloss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    probs, tloss = evaluate(model, tok, dev, test, args.bs, args.max_len, loss_fn)
    np.savez(OUT / f"{dataset}_{name}.npz", y=test["label"].values, p=probs, test_loss=tloss, **hist)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["isot", "liar"], required=True)
    ap.add_argument("--models", nargs="+", default=["bilstm", "bert", "bert_bilstm"])
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--max-len", type=int, default=64)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    dev = device()
    sets = split(load(args.dataset), args.seed)
    print("device:", dev, "| dataset:", args.dataset, "| sizes:", [len(s) for s in sets], flush=True)
    for name in args.models:
        if (OUT / f"{args.dataset}_{name}.npz").exists():
            print(f"  {args.dataset} {name} already finished, skipping", flush=True)
            continue
        train_one(name, args.dataset, sets, args, dev)
    pd.Series({"done": True}).to_json(OUT / f"{args.dataset}_done.json")


if __name__ == "__main__":
    main()
