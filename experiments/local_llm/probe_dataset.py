from datasets import load_dataset

candidates = [
    "GonzaloA/fake_news",
    "mohammadjavadpirhadi/fake-and-real-news-dataset",
    "ErfanMoosaviMonazzah/fake-news-detection-dataset-English",
]

for name in candidates:
    try:
        ds = load_dataset(name)
        print(f"OK: {name}")
        print(ds)
        first_split = list(ds.keys())[0]
        print(ds[first_split][0])
        print("=" * 40)
    except Exception as e:
        print(f"FAIL: {name} -> {type(e).__name__}: {e}")
        print("=" * 40)
