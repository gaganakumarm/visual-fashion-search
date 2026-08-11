"""
Step 1: Load styles.csv, validate against images folder, drop mismatches,
and optionally create a stratified subset (useful for testing on a low-power
machine). Set SUBSET_PER_CATEGORY = None to use the full dataset.
"""
import pandas as pd
import os
from config import CSV_PATH, IMG_DIR, DATA_DIR

SUBSET_PER_CATEGORY = None   # e.g. 500 for a quick ~3k-image test run

def main():
    df = pd.read_csv(CSV_PATH, on_bad_lines="skip")
    print(f"Loaded {len(df)} CSV rows")

    existing = set(os.listdir(IMG_DIR))
    df["image_file"] = df["id"].astype(str) + ".jpg"
    df = df[df["image_file"].isin(existing)].copy()
    print(f"Rows with matching image: {len(df)}")

    df = df.dropna(subset=["baseColour", "season", "usage", "productDisplayName"])
    print(f"Rows after dropping nulls: {len(df)}")

    if SUBSET_PER_CATEGORY:
        parts = []
        for _, group in df.groupby("masterCategory"):
            n = min(len(group), SUBSET_PER_CATEGORY)
            parts.append(group.sample(n, random_state=42))
        df = pd.concat(parts, ignore_index=True)
        print(f"Stratified subset size: {len(df)}")

    out_path = DATA_DIR / "products.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved -> {out_path}")
    print(df["masterCategory"].value_counts())

if __name__ == "__main__":
    main()
