"""Build a small, git-friendly demo dataset under deploy/."""
import argparse
import os
import shutil

import pandas as pd

from config import CSV_PATH, IMG_DIR, ROOT


DEPLOY_ARCHIVE = ROOT / "deploy" / "archive"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--per-category",
        type=int,
        default=300,
        help="Maximum products to keep per masterCategory",
    )
    args = parser.parse_args()
    if args.per_category < 1:
        parser.error("--per-category must be at least 1")

    print(f"Reading full dataset from {CSV_PATH} ...")
    df = pd.read_csv(CSV_PATH, on_bad_lines="skip")

    existing = set(os.listdir(IMG_DIR))
    df["image_file"] = df["id"].astype(str) + ".jpg"
    df = df[df["image_file"].isin(existing)].copy()
    df = df.dropna(
        subset=["baseColour", "season", "usage", "productDisplayName"]
    )
    print(f"Valid rows available: {len(df)}")

    parts = []
    for _, group in df.groupby("masterCategory"):
        count = min(len(group), args.per_category)
        parts.append(group.sample(count, random_state=42))
    demo_df = pd.concat(parts, ignore_index=True)
    print(f"Demo subset size: {len(demo_df)}")
    print(demo_df["masterCategory"].value_counts())

    output_columns = [column for column in demo_df.columns if column != "image_file"]
    deploy_images = DEPLOY_ARCHIVE / "images"
    DEPLOY_ARCHIVE.mkdir(parents=True, exist_ok=True)
    deploy_images.mkdir(exist_ok=True)
    demo_df[output_columns].to_csv(DEPLOY_ARCHIVE / "styles.csv", index=False)

    print("Copying images...")
    copied = 0
    for filename in demo_df["image_file"]:
        source = IMG_DIR / filename
        destination = deploy_images / filename
        if source.exists() and not destination.exists():
            shutil.copyfile(source, destination)
            copied += 1
    print(f"Copied {copied} images to {deploy_images}")

    total_size = sum(file.stat().st_size for file in deploy_images.glob("*"))
    total_size += (DEPLOY_ARCHIVE / "styles.csv").stat().st_size
    print(f"\nDemo archive size: {total_size / 1e6:.1f} MB")
    print(f"Saved to: {DEPLOY_ARCHIVE}")
    print("\nNext: run the four-step pipeline pointed at deploy/.")


if __name__ == "__main__":
    main()
