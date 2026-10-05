from datasets import load_dataset, concatenate_datasets

ds = load_dataset("ErfanMoosaviMonazzah/fake-news-detection-dataset-English")
full = concatenate_datasets([ds["train"], ds["validation"], ds["test"]])
print("total:", len(full))
import collections
print(collections.Counter(full["label"]))
print(collections.Counter(full["subject"]))
