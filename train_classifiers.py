"""
Step 3: Train one classifier per tag (masterCategory, subCategory, baseColour,
season, usage) using the image feature vectors -- the "auto-tagger".
"""
import numpy as np
import pandas as pd
import json
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import LabelEncoder
import joblib
import time
from config import DATA_DIR, MODELS_DIR

TARGETS = ["masterCategory", "subCategory", "baseColour", "season", "usage"]
COLOR_DIM = 24  # first 24 dims of the image feature vector = HSV color histogram

def main():
    df = pd.read_csv(DATA_DIR / "products_final.csv")
    X = np.load(DATA_DIR / "image_features.npy")
    print(f"X shape: {X.shape}")

    results = {}
    for target in TARGETS:
        print(f"\n--- Training classifier for '{target}' ---")
        y_raw = df[target].astype(str)
        le = LabelEncoder()
        y = le.fit_transform(y_raw)
        print(f"  classes: {len(le.classes_)}")

        # baseColour is a color-only task -- using the full vector (mostly
        # shape/texture) dilutes the signal, so restrict to the color slice.
        X_use = X[:, :COLOR_DIM] if target == "baseColour" else X
        class_weight = None if target == "baseColour" else "balanced"

        X_train, X_test, y_train, y_test = train_test_split(
            X_use, y, test_size=0.15, random_state=42,
            stratify=y if min(np.bincount(y)) >= 2 else None
        )

        t0 = time.time()
        clf = LogisticRegression(max_iter=300, class_weight=class_weight)
        clf.fit(X_train, y_train)
        train_time = time.time() - t0

        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="macro")
        print(f"  train_time={train_time:.1f}s  acc={acc:.3f}  macro_f1={f1:.3f}")

        joblib.dump(clf, MODELS_DIR / f"clf_{target}.joblib")
        joblib.dump(le, MODELS_DIR / f"le_{target}.joblib")
        results[target] = {
            "accuracy": acc, "macro_f1": f1, "n_classes": len(le.classes_),
            "feature_dim": "color_only" if target == "baseColour" else "full"
        }

    with open(MODELS_DIR / "classifier_meta.json", "w") as f:
        json.dump({"targets": TARGETS, "color_dim": COLOR_DIM, "results": results}, f, indent=2)

    print("\n=== Summary ===")
    for t, r in results.items():
        print(f"{t:15s} acc={r['accuracy']:.3f}  macro_f1={r['macro_f1']:.3f}  classes={r['n_classes']}")

if __name__ == "__main__":
    main()
