import argparse
import random
import time

import pandas as pd
from datasets import concatenate_datasets, load_dataset
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from transformers import pipeline

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
SAMPLE_SIZE = 300
SEED = 42

SYSTEM_PROMPT = (
    "You are a fact-checking assistant. Given a news article's headline and body text, "
    "decide whether it is REAL news or FAKE news. "
    "Respond with exactly one word: REAL or FAKE."
)


def build_prompt(title, text, max_chars=1500):
    body = text[:max_chars]
    return f"Headline: {title}\n\nArticle:\n{body}\n\nIs this REAL or FAKE?"


def parse_verdict(generated_text):
    upper = generated_text.upper()
    fake_pos = upper.find("FAKE")
    real_pos = upper.find("REAL")
    if fake_pos == -1 and real_pos == -1:
        return None
    if fake_pos == -1:
        return "REAL"
    if real_pos == -1:
        return "FAKE"
    return "FAKE" if fake_pos < real_pos else "REAL"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-size", type=int, default=SAMPLE_SIZE)
    parser.add_argument("--out", default="experiments/local_llm/local_llm_predictions.csv")
    args = parser.parse_args()

    print("Loading dataset (ISOT mirror)...")
    ds = load_dataset("ErfanMoosaviMonazzah/fake-news-detection-dataset-English")
    full = concatenate_datasets([ds["train"], ds["validation"], ds["test"]])
    df = full.to_pandas()

    per_class = args.sample_size // 2
    real_df = df[df["label"] == 1].sample(n=per_class, random_state=SEED)
    fake_df = df[df["label"] == 0].sample(n=per_class, random_state=SEED)
    sample = pd.concat([real_df, fake_df]).sample(frac=1, random_state=SEED).reset_index(drop=True)
    # true_label: 1 = FAKE, 0 = REAL, matching this project's existing model convention (app.py).
    sample["true_label"] = (sample["label"] == 0).astype(int)

    print(f"Loading model {MODEL_ID} (CPU)...")
    generator = pipeline(
        "text-generation",
        model=MODEL_ID,
        device_map="cpu",
        torch_dtype="auto",
    )

    predictions = []
    raw_outputs = []
    start = time.time()
    for i, row in sample.iterrows():
        prompt = build_prompt(row["title"], row["text"])
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        result = generator(messages, max_new_tokens=8, do_sample=False)
        reply = result[0]["generated_text"][-1]["content"]
        verdict = parse_verdict(reply)
        pred_label = 1 if verdict == "FAKE" else 0 if verdict == "REAL" else None
        predictions.append(pred_label)
        raw_outputs.append(reply)
        elapsed = time.time() - start
        print(
            f"[{i + 1}/{len(sample)}] true={'FAKE' if row['true_label'] == 1 else 'REAL'} "
            f"pred={verdict} raw={reply!r} elapsed={elapsed:.1f}s"
        )

    sample["raw_output"] = raw_outputs
    sample["pred_label"] = predictions

    unparsed = sample["pred_label"].isna().sum()
    if unparsed:
        print(f"WARNING: {unparsed} responses could not be parsed; defaulting them to REAL (0).")
    sample["pred_label"] = sample["pred_label"].fillna(0).astype(int)

    y_true = sample["true_label"]
    y_pred = sample["pred_label"]

    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
    recall = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
    f1 = f1_score(y_true, y_pred, pos_label=1, zero_division=0)

    print("\n=== Local LLM (zero-shot) results ===")
    print(f"Model: {MODEL_ID}")
    print(f"Sample size: {len(sample)}")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1-score:  {f1:.4f}")

    sample.to_csv(args.out, index=False)
    print(f"\nPer-article predictions saved to {args.out}")

    summary_path = args.out.replace("_predictions.csv", "_summary.csv")
    pd.DataFrame(
        [
            {
                "model": "local_llm_qwen2.5_1.5b_instruct_zero_shot",
                "loss": None,
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
            }
        ]
    ).to_csv(summary_path, index=False)
    print(f"Summary row saved to {summary_path}")


if __name__ == "__main__":
    main()
