"""
FastAPI backend for the Fashion Search + Auto-Tagger app.

Endpoints:
  GET  /api/product/{id}          -> single product metadata
  POST /api/search/text           -> text query -> similar products
  POST /api/search/image          -> upload photo -> visually similar products + predicted tags
  GET  /api/random                -> a few random products (for homepage grid)
  GET  /api/stats                 -> catalogue size + category breakdown
  GET  /images/{filename}         -> serves the actual product image
  GET  /                          -> frontend
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
from PIL import Image
import io
import tempfile
import os

from config import DATA_DIR, MODELS_DIR, IMG_DIR, STATIC_DIR
from extract_features import extract_image_features

app = FastAPI(title="Myntra Fashion Search + Auto-Tagger")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ---- Load everything once at startup ----
print("Loading data + models...")
df = pd.read_csv(DATA_DIR / "products_final.csv")
img_feats = np.load(DATA_DIR / "image_features.npy")
text_feats = np.load(DATA_DIR / "text_features.npy")

img_index = joblib.load(MODELS_DIR / "image_index.joblib")
text_index = joblib.load(MODELS_DIR / "text_index.joblib")
tfidf = joblib.load(MODELS_DIR / "tfidf_vectorizer.joblib")

TARGETS = ["masterCategory", "subCategory", "baseColour", "season", "usage"]
classifiers = {t: joblib.load(MODELS_DIR / f"clf_{t}.joblib") for t in TARGETS}
label_encoders = {t: joblib.load(MODELS_DIR / f"le_{t}.joblib") for t in TARGETS}
COLOR_DIM = 24
print(f"Loaded {len(df)} products.")

app.mount("/images", StaticFiles(directory=str(IMG_DIR)), name="images")


def row_to_dict(row):
    return {
        "id": int(row["id"]),
        "name": row["productDisplayName"],
        "gender": row["gender"],
        "masterCategory": row["masterCategory"],
        "subCategory": row["subCategory"],
        "articleType": row["articleType"],
        "baseColour": row["baseColour"],
        "season": row["season"],
        "usage": row["usage"],
        "image_url": f"/images/{row['image_file']}",
    }


@app.get("/")
def serve_index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/random")
def random_products(n: int = 12):
    sample = df.sample(min(n, len(df)))
    return [row_to_dict(r) for _, r in sample.iterrows()]


@app.get("/api/samples")
def sample_products(n: int = 12):
    """Return deterministic, category-diverse products for the help modal."""
    parts = []
    for _, group in df.groupby("masterCategory"):
        take = group.sample(min(2, len(group)), random_state=42)
        parts.append(take)
    combined = pd.concat(parts).head(n)
    return [row_to_dict(r) for _, r in combined.iterrows()]


@app.get("/api/product/{product_id}")
def get_product(product_id: int):
    match = df[df["id"] == product_id]
    if match.empty:
        raise HTTPException(404, "Product not found")
    return row_to_dict(match.iloc[0])


class TextQuery(BaseModel):
    query: str
    k: int = 12


@app.post("/api/search/text")
def search_text(q: TextQuery):
    vec = tfidf.transform([q.query]).toarray().astype(np.float32)
    dist, ind = text_index.kneighbors(vec, n_neighbors=min(q.k, len(df)))
    results = []
    for i, d in zip(ind[0], dist[0]):
        item = row_to_dict(df.iloc[i])
        item["score"] = round(1 - float(d), 4)
        results.append(item)
    return results


@app.post("/api/search/image")
async def search_image(file: UploadFile = File(...), k: int = Form(12)):
    contents = await file.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(400, "Invalid image file")

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        img.save(tmp.name)
        tmp_path = tmp.name
    try:
        feat = extract_image_features(tmp_path).reshape(1, -1).astype(np.float32)
    finally:
        os.remove(tmp_path)

    dist, ind = img_index.kneighbors(feat, n_neighbors=min(k, len(df)))
    results = []
    for i, d in zip(ind[0], dist[0]):
        item = row_to_dict(df.iloc[i])
        item["score"] = round(1 - float(d), 4)
        results.append(item)

    predicted_tags = {}
    for target in TARGETS:
        clf = classifiers[target]
        le = label_encoders[target]
        x = feat[:, :COLOR_DIM] if target == "baseColour" else feat
        pred_idx = clf.predict(x)[0]
        proba = clf.predict_proba(x)[0]
        confidence = float(np.max(proba))
        predicted_tags[target] = {
            "value": le.inverse_transform([pred_idx])[0],
            "confidence": round(confidence, 3),
        }

    return {"predicted_tags": predicted_tags, "similar_products": results}


@app.get("/api/stats")
def stats():
    return {
        "total_products": len(df),
        "categories": df["masterCategory"].value_counts().to_dict(),
    }
