# Catalogue — Visual Fashion Search & Auto-Tagger

An end-to-end ML + web app built on the **Myntra Fashion Product Images
Dataset** (44,072 products after cleaning, tested end-to-end on the full
set). Upload a garment photo and get:

1. **Auto-predicted tags** — category, sub-category, colour, season, occasion
   — shown as swing tags in the UI
2. **Visually similar products** from the full catalogue

Or just type a query (e.g. *"red ethnic kurta women"*) for text-based search.

---

## Setup on your Windows machine

### 1. Unzip this project
Unzip `fashion-search-app.zip` anywhere, e.g. `C:\Users\gagan\fashion-app\`.

### 2. Put your dataset inside the project folder
Copy your `archive` folder (the one with `styles.csv` and `images\` inside
it) into the project root, so it looks like this:

```
fashion-app\
├── archive\                 <- copy this in from your Downloads
│   ├── styles.csv
│   └── images\
│       ├── 1163.jpg
│       └── ... (44,441 images)
├── app\main.py
├── static\index.html
├── config.py
├── prepare_data.py
├── extract_features.py
├── train_classifiers.py
├── build_index.py
├── requirements.txt
└── models\                  <- trained classifiers already included
```

(If you'd rather not copy/move your dataset, set an environment variable
instead — see "Using a dataset in a different location" below.)

### 3. Install Python dependencies
Open **PowerShell** or **Command Prompt** in the project folder:
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
> Needs Python 3.9+. Check with `python --version`. If `python` isn't
> recognized, install it from python.org and make sure "Add to PATH" is
> checked during install.

### 4. Run the pipeline (builds everything from your raw images)
Still inside the activated venv:
```powershell
python prepare_data.py
python extract_features.py
python train_classifiers.py
python build_index.py
```
On the full 44k dataset this takes about **3–4 minutes total** (mostly
`extract_features.py`). You'll see progress printed every 2,000 images.

### 5. Start the app
```powershell
cd app
uvicorn main:app --host 0.0.0.0 --port 8000
```
Open **http://localhost:8000** in your browser. You should see the
catalogue homepage — try the text search bar or drag a photo into the
"Search by photo" tab.

To stop the server, press `Ctrl+C` in that terminal.

### Using a dataset in a different location
Instead of copying `archive\` into the project, you can point to it
directly (PowerShell):
```powershell
$env:DATASET_DIR = "C:\Users\gagan\Downloads\archive"
python prepare_data.py
```
Set the same `$env:DATASET_DIR` before every script/run in that terminal
session (or set it as a permanent Windows environment variable via System
Properties → Environment Variables).

---

## How it works

```
archive/styles.csv + archive/images/   (your raw Myntra dataset)
        │
        ▼
 1. prepare_data.py       cleans CSV, matches rows to actual image files
        │
        ▼
 2. extract_features.py   image features (HSV colour histogram + HOG shape)
        │                 text features  (TF-IDF over product names/metadata)
        ▼
 3. train_classifiers.py  one classifier per tag (category, colour, season, usage)
        │
        ▼
 4. build_index.py        k-NN search index for image + text similarity
        │
        ▼
 5. app/main.py           FastAPI backend: search + auto-tag endpoints
        │
        ▼
    static/index.html     frontend (vanilla HTML/CSS/JS, no build step)
```

All paths are centralized in `config.py` — nothing else has a hardcoded
path, so this runs the same on Windows, Mac, or Linux.

### Why classical CV features instead of a deep model (CLIP/ResNet)?

This was originally built in a resource-constrained sandbox (1 CPU core, no
GPU). A colour histogram + HOG shape descriptor is a legitimate classical
computer vision approach and processes the **entire 44k-image dataset in
under 4 minutes on a single CPU core** — no GPU, no multi-GB model
downloads.

**To upgrade to deep embeddings** (recommended if your machine has a GPU):
replace `extract_image_features()` in `extract_features.py` with a CLIP or
ResNet forward pass. Everything downstream (index, classifiers, API) is
agnostic to how the vector was produced — it just expects a fixed-size
numpy array per image.

### Known limitation: colour prediction accuracy

`baseColour` is the weakest predictor (~25% accuracy across 46 fine-grained
classes — e.g. "Steel" vs "Grey" vs "Charcoal" look nearly identical in a
histogram). Worth mentioning if you present this project — a CLIP-based
color embedding would likely improve this substantially.

| Tag | Accuracy | Macro F1 | # Classes |
|---|---|---|---|
| masterCategory | 93.8% | 0.64 | 7 |
| subCategory | 84.8% | 0.59 | 45 |
| season | 62.9% | 0.64 | 4 |
| usage | 69.7% | 0.33 | 8 |
| baseColour | 24.6% | 0.02 | 46 |

---

## Project structure

```
config.py                # central path config (edit RAW_DIR here if needed)
prepare_data.py          # Step 1: clean + validate dataset
extract_features.py      # Step 2: image + text feature extraction
train_classifiers.py     # Step 3: auto-tagger training
build_index.py           # Step 4: similarity search index
app/main.py               # FastAPI backend (search + auto-tag API)
static/index.html         # Frontend
models/                   # Trained classifiers (included) + search indexes (you generate)
data/                     # Cleaned CSVs + feature matrices (you generate)
requirements.txt
```

## API reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/random?n=12` | GET | Random products for the homepage grid |
| `/api/product/{id}` | GET | Single product's metadata |
| `/api/search/text` | POST | `{"query": "...", "k": 12}` → similar products |
| `/api/search/image` | POST | multipart file upload → predicted tags + similar products |
| `/api/stats` | GET | Catalogue size + category breakdown |
| `/images/{filename}` | GET | Serves the actual product image |

Interactive API docs at **http://localhost:8000/docs** once running.

## Troubleshooting

- **`ModuleNotFoundError`** — make sure the venv is activated
  (`venv\Scripts\activate`) before running any script.
- **`FileNotFoundError` on styles.csv** — check `archive\styles.csv` and
  `archive\images\` exist in the project root, or set `$env:DATASET_DIR`.
- **Port 8000 already in use** — run
  `uvicorn main:app --host 0.0.0.0 --port 8001` instead, then open
  `http://localhost:8001`.
- **Server takes a while to start** — it's loading ~450MB of search-index
  data into memory; this is normal and only happens once at startup.

## Ideas for extending this project

- Swap classical features for CLIP embeddings for a big jump in search
  quality and colour accuracy
- Add a "complete the look" recommender using co-purchase/category patterns
- Batch mode: upload multiple photos, export a CSV of predicted tags
- Deploy behind a proper ANN index (FAISS/HNSW) for sub-100ms search at scale
- Host it publicly (Render, Railway, or a small cloud VM) so it's a live
  link you can put on a resume
