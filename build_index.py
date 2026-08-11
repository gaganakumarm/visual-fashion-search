"""
Step 4: Build nearest-neighbor search indexes for:
  1. Image similarity search (upload a photo -> find visually similar products)
  2. Text search (TF-IDF cosine similarity over product names/metadata)
"""
import numpy as np
from sklearn.neighbors import NearestNeighbors
import joblib
from config import DATA_DIR, MODELS_DIR

def main():
    img_feats = np.load(DATA_DIR / "image_features.npy")
    text_feats = np.load(DATA_DIR / "text_features.npy")

    print("Building image similarity index...")
    img_index = NearestNeighbors(n_neighbors=20, metric="cosine", algorithm="brute")
    img_index.fit(img_feats)
    joblib.dump(img_index, MODELS_DIR / "image_index.joblib")

    print("Building text similarity index...")
    text_index = NearestNeighbors(n_neighbors=20, metric="cosine", algorithm="brute")
    text_index.fit(text_feats)
    joblib.dump(text_index, MODELS_DIR / "text_index.joblib")

    print("Done. Saved image_index.joblib and text_index.joblib")

if __name__ == "__main__":
    main()
