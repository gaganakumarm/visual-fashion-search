"""
Step 2: Extract feature vectors for every product.

IMAGE FEATURES (classical CV, CPU-friendly):
  - Color histogram in HSV space (captures dominant colors)
  - Histogram of Oriented Gradients on a downsized grayscale image (captures
    shape/silhouette)
  Concatenated and L2-normalized into one vector per image.

TEXT FEATURES:
  - TF-IDF over productDisplayName + category metadata

To upgrade to deep embeddings (CLIP/ResNet) on a machine with a GPU, swap
extract_image_features() for a torch/CLIP forward pass -- everything
downstream (index, classifiers, API) works unchanged, since it just expects
a fixed-size numpy vector per product.
"""
import pandas as pd
import numpy as np
from PIL import Image
from skimage.feature import hog
from skimage.color import rgb2gray
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
import os
import time
from config import IMG_DIR, DATA_DIR, MODELS_DIR

IMG_SIZE = (64, 64)
COLOR_BINS = 8

def extract_image_features(path):
    img = Image.open(path).convert("RGB").resize(IMG_SIZE)
    arr = np.array(img) / 255.0

    hsv = np.array(Image.fromarray((arr * 255).astype("uint8")).convert("HSV")) / 255.0
    hist = []
    for ch in range(3):
        h, _ = np.histogram(hsv[:, :, ch], bins=COLOR_BINS, range=(0, 1))
        hist.append(h)
    color_feat = np.concatenate(hist).astype(np.float32)
    color_feat = color_feat / (color_feat.sum() + 1e-6)

    gray = rgb2gray(arr)
    hog_feat = hog(
        gray, orientations=8, pixels_per_cell=(8, 8),
        cells_per_block=(2, 2), feature_vector=True
    ).astype(np.float32)

    feat = np.concatenate([color_feat, hog_feat])
    norm = np.linalg.norm(feat)
    return feat / norm if norm > 0 else feat

def main():
    df = pd.read_csv(DATA_DIR / "products.csv")
    print(f"Extracting image features for {len(df)} products...")

    feats = []
    t0 = time.time()
    for i, row in df.iterrows():
        path = os.path.join(IMG_DIR, row["image_file"])
        try:
            feats.append(extract_image_features(path))
        except Exception as e:
            feats.append(None)
            print(f"  failed on {row['image_file']}: {e}")
        if (i + 1) % 2000 == 0:
            elapsed = time.time() - t0
            print(f"  {i+1}/{len(df)}  ({elapsed:.1f}s elapsed)")

    valid_mask = [f is not None for f in feats]
    df = df[valid_mask].reset_index(drop=True)
    feats = np.stack([f for f in feats if f is not None])
    print(f"Image feature matrix: {feats.shape}")

    text_corpus = (
        df["productDisplayName"].fillna("") + " " +
        df["articleType"].fillna("") + " " +
        df["baseColour"].fillna("") + " " +
        df["usage"].fillna("")
    )
    tfidf = TfidfVectorizer(max_features=1000, stop_words="english")
    text_feats = tfidf.fit_transform(text_corpus).toarray().astype(np.float32)
    print(f"Text feature matrix: {text_feats.shape}")

    np.save(DATA_DIR / "image_features.npy", feats)
    np.save(DATA_DIR / "text_features.npy", text_feats)
    joblib.dump(tfidf, MODELS_DIR / "tfidf_vectorizer.joblib")
    df.to_csv(DATA_DIR / "products_final.csv", index=False)

    print("Saved image_features.npy, text_features.npy, tfidf_vectorizer.joblib, products_final.csv")

if __name__ == "__main__":
    main()
