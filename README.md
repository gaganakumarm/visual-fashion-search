# Vision Console — Visual Fashion Search

Vision Console is an end-to-end machine-learning and FastAPI application built
with the Myntra Fashion Product Images dataset. Search by natural-language
description or upload a garment photo to predict attributes and retrieve
visually similar products.

The dark, high-contrast interface includes text and photo search, a
machine-vision attribute readout with confidence bars, responsive result cards,
and a help modal with test images.

## How it works

```text
archive/styles.csv + archive/images/
                ↓
        prepare_data.py
                ↓
       extract_features.py
        ↙              ↘
 image features       TF-IDF features
        ↓                    ↓
train_classifiers.py    build_index.py
        └──────────┬─────────┘
                   ↓
             app/main.py
                   ↓
          static/index.html
```

Image search uses HSV colour histograms and Histogram of Oriented Gradients
(HOG). Text search uses TF-IDF. Scikit-learn classifiers predict category,
subcategory, colour, season, and usage.

## Local full-dataset setup

Python 3.9 or newer is required.

```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Place the raw dataset at `archive/styles.csv` and `archive/images/`, then run:

```powershell
python prepare_data.py
python extract_features.py
python train_classifiers.py
python build_index.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://localhost:8000`. API documentation is available at
`http://localhost:8000/docs`.

## Deployable demo dataset

The complete dataset and generated artifacts are too large for a normal GitHub
repository and many free-tier cloud instances. `build_demo_dataset.py` creates
a deterministic, category-balanced subset under `deploy/` without changing
the full local `archive/`, `data/`, or `models/` directories.

Build the demo archive:

```powershell
python build_demo_dataset.py
```

The default keeps up to 300 products per master category. For a smaller build:

```powershell
python build_demo_dataset.py --per-category 150
```

Build the demo features and models in separate directories:

```powershell
$env:DATASET_DIR = "$PWD\deploy\archive"
$env:APP_DATA_DIR = "$PWD\deploy\data"
$env:APP_MODELS_DIR = "$PWD\deploy\models"

python prepare_data.py
python extract_features.py
python train_classifiers.py
python build_index.py
```

Test the demo in the same PowerShell window:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The reduced `deploy/archive`, `deploy/data`, and `deploy/models` directories
are committed to Git. Their full-size root equivalents are intentionally
ignored.

To restore full-dataset defaults in PowerShell:

```powershell
Remove-Item Env:DATASET_DIR
Remove-Item Env:APP_DATA_DIR
Remove-Item Env:APP_MODELS_DIR
```

## Project structure

```text
app/main.py               FastAPI application and API endpoints
static/index.html         Vision Console frontend
config.py                 Environment-aware path configuration
prepare_data.py           Cleans metadata and validates images
extract_features.py       Generates image and text vectors
train_classifiers.py      Trains attribute classifiers
build_index.py            Builds nearest-neighbour indexes
build_demo_dataset.py     Creates the deployment subset
archive/                  Full raw dataset (local only)
data/                     Full generated features (local only)
models/                   Full models; large indexes ignored
deploy/                   Commit-ready demo archive, features, and models
```

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/random?n=12` | GET | Random catalogue products |
| `/api/samples?n=12` | GET | Deterministic help-modal samples |
| `/api/product/{id}` | GET | Product metadata |
| `/api/search/text` | POST | Text similarity search |
| `/api/search/image` | POST | Image analysis and visual similarity search |
| `/api/stats` | GET | Catalogue size and category breakdown |
| `/images/{filename}` | GET | Product image assets |

## Full versus demo data

| Location | Purpose | Committed |
|---|---|---|
| `archive/` | Full raw dataset | No |
| `data/` | Full feature matrices | No |
| `models/image_index.joblib` | Full image index | No |
| `models/text_index.joblib` | Full text index | No |
| `deploy/archive/` | Reduced raw dataset | Yes |
| `deploy/data/` | Reduced feature matrices | Yes |
| `deploy/models/` | Reduced models and indexes | Yes |

## Known limitation

Fine-grained colour prediction is the weakest classifier because visually
similar labels such as grey, charcoal, and steel overlap in classical colour
histograms. A CLIP-based embedding is a natural future improvement.
