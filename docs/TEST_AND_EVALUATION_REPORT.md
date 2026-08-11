# Test and Evaluation Report

## Visual Fashion Search

| Report field | Value |
|---|---|
| Evaluation date | 11 August 2026 |
| Test environment | Windows, PowerShell |
| Python version | 3.12.7 |
| Application framework | FastAPI 0.141.1, Uvicorn 0.52.1 |
| Evaluation type | Local functional, integration, data-integrity, and error-handling evaluation |
| Overall result | **PASS** |

## 1. Purpose

This Test and Evaluation Report documents the checks performed on the Visual
Fashion Search application. The goal was to confirm that the application can
start successfully, load its dataset and trained artifacts, serve its web
interface, and execute its primary text-search, image-search, and auto-tagging
workflows as expected.

The evaluation also checked common failure cases and confirmed that testing did
not leave the repository or local server in an altered state.

## 2. System under test

The application is an end-to-end fashion retrieval system consisting of:

- a FastAPI backend;
- a browser-based frontend served by FastAPI;
- a catalogue containing product metadata and images;
- TF-IDF features and a nearest-neighbour index for text retrieval;
- colour and HOG image features with a nearest-neighbour index for visual
  retrieval; and
- scikit-learn classifiers for category, subcategory, colour, season, and usage
  prediction.

The main application entry point is `app/main.py`. The frontend is contained in
`static/index.html`.

## 3. Evaluation scope

The following areas were evaluated:

1. Python source-code compilation.
2. Runtime dependency availability.
3. Dataset and feature-matrix consistency.
4. Loading of persisted models and indexes.
5. FastAPI application startup.
6. Frontend and API documentation availability.
7. Catalogue statistics and product retrieval.
8. Text-search relevance and requested result counts.
9. Image search, auto-tagging, and requested result counts.
10. Expected handling of missing resources and invalid requests.
11. Clean shutdown and repository cleanliness.

The evaluation did not retrain the machine-learning models because the required
processed data and trained artifacts were already present. It verified that
those artifacts load and operate correctly in the running application.

## 4. Test environment

The tests used the project's existing virtual environment and the following
installed package versions:

| Component | Version |
|---|---:|
| Python | 3.12.7 |
| FastAPI | 0.141.1 |
| Uvicorn | 0.52.1 |
| pandas | 3.0.5 |
| NumPy | 2.5.2 |
| scikit-learn | 1.9.0 |
| scikit-image | 0.26.0 |
| Pillow | 12.3.0 |
| joblib | 1.5.3 |

The server was started locally at `http://127.0.0.1:8000`.

## 5. Test methodology

Testing was performed in four stages:

1. **Static validation:** compile the Python files and import all required
   libraries.
2. **Artifact validation:** compare catalogue and feature-matrix row counts,
   verify representative images, and load the persisted indexes and vectorizer.
3. **Live integration testing:** start Uvicorn and send HTTP requests to the
   frontend and API endpoints.
4. **Cleanup validation:** stop the test server, confirm port 8000 is released,
   and confirm that testing did not create repository changes.

## 6. Detailed test results

### TE-01: Python source compilation

**Objective:** Confirm that the primary application and data-pipeline modules
contain no Python syntax errors.

**Files checked:**

- `config.py`
- `prepare_data.py`
- `extract_features.py`
- `train_classifiers.py`
- `build_index.py`
- `build_demo_dataset.py`
- `app/main.py`

**Method:** Run Python's `py_compile` module against every listed file.

**Expected result:** All files compile without an exception.

**Observed result:** All files compiled successfully.

**Status:** PASS

### TE-02: Runtime dependency imports

**Objective:** Confirm that the dependencies required by the application are
available in the virtual environment.

**Method:** Import FastAPI, Uvicorn, pandas, NumPy, scikit-learn, scikit-image,
Pillow, and joblib in one Python process.

**Expected result:** All imports complete successfully.

**Observed result:** Every required package imported successfully.

**Status:** PASS

### TE-03: Dataset and feature consistency

**Objective:** Confirm that catalogue records correspond one-to-one with the
stored image and text feature rows.

**Method:** Load `products_final.csv`, `image_features.npy`, and
`text_features.npy`, then compare their first dimensions.

**Observed values:**

| Artifact | Observed value |
|---|---:|
| Catalogue products | 44,064 |
| Image feature shape | `(44064, 1592)` |
| Text feature shape | `(44064, 1000)` |

The catalogue contained valid IDs, the frontend file was present, and the
representative image-file checks passed.

**Expected result:** All row counts match and required files exist.

**Observed result:** The catalogue and both feature matrices contain exactly
44,064 aligned rows.

**Status:** PASS

### TE-04: Persisted artifact loading

**Objective:** Confirm that the application can deserialize its search
artifacts.

**Artifacts checked:**

- `image_index.joblib`
- `text_index.joblib`
- `tfidf_vectorizer.joblib`

**Expected result:** Each artifact loads without an exception.

**Observed result:** All three artifacts loaded successfully.

**Status:** PASS

### TE-05: Application startup

**Objective:** Confirm that FastAPI starts through the documented Uvicorn entry
point and becomes ready for requests.

**Command:**

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Expected result:** The application loads the data and models and listens on
port 8000.

**Observed result:** The application became responsive at
`http://127.0.0.1:8000`.

**Status:** PASS

### TE-06: Frontend availability

**Request:** `GET /`

**Expected result:** HTTP 200 with the Vision Console HTML interface.

**Observed result:** HTTP 200; the response contained the expected Vision
Console content.

**Status:** PASS

### TE-07: API documentation availability

**Request:** `GET /docs`

**Expected result:** HTTP 200 with the FastAPI interactive documentation.

**Observed result:** HTTP 200.

**Status:** PASS

### TE-08: Catalogue statistics

**Request:** `GET /api/stats`

**Expected result:** A valid product total and category breakdown.

**Observed result:** The endpoint reported 44,064 products and returned the
following category totals:

| Category | Products |
|---|---:|
| Apparel | 21,353 |
| Accessories | 11,244 |
| Footwear | 9,197 |
| Personal Care | 2,139 |
| Free Items | 105 |
| Sporting Goods | 25 |
| Home | 1 |
| **Total** | **44,064** |

**Status:** PASS

### TE-09: Random catalogue results

**Request:** `GET /api/random?n=5`

**Expected result:** Five valid product records.

**Observed result:** Five product records were returned.

**Status:** PASS

### TE-10: Deterministic sample results

**Request:** `GET /api/samples?n=6`

**Expected result:** Six sample product records for the frontend help flow.

**Observed result:** Six product records were returned.

**Status:** PASS

### TE-11: Product lookup

**Request:** `GET /api/product/10008`

**Expected result:** Product metadata for ID 10008.

**Observed result:** The response contained product ID 10008 and its associated
metadata.

**Status:** PASS

### TE-12: Text search

**Request:**

```http
POST /api/search/text
Content-Type: application/json

{"query": "red shoes", "k": 3}
```

**Expected result:** Three ranked, relevant products with similarity scores.

**Observed result:** Three ranked products were returned. The highest-ranked
result was `Nike Men Red Shoes` with a similarity score of `0.8847`. The next
two results were also red footwear products, demonstrating useful semantic
matching for the test query.

**Status:** PASS

### TE-13: Image search and auto-tagging

**Request:** `POST /api/search/image` using `archive/images/10008.jpg` with
`k=3`.

**Expected result:** Predicted fashion attributes and three ranked visually
similar products.

**Observed result:** The endpoint returned all five predicted tag groups and
three similar products. The source product, `Nike Men Town Navy Blue T-Shirts`,
was the highest-ranked match with a similarity score of `0.9695`.

Observed predictions included:

| Attribute | Prediction | Confidence |
|---|---|---:|
| Master category | Apparel | 0.833 |
| Subcategory | Topwear | 0.397 |
| Base colour | Black | 0.255 |
| Season | Fall | 0.606 |
| Usage | Sports | 0.915 |

The test confirms that the complete upload, feature-extraction, classification,
and nearest-neighbour retrieval path is operational. Confidence values are
model outputs and should not be interpreted as a formal accuracy measurement.

**Status:** PASS

### TE-14: Missing-product handling

**Request:** `GET /api/product/-1`

**Expected result:** HTTP 404.

**Observed result:** HTTP 404.

**Status:** PASS

### TE-15: Invalid text-search request

**Request:** `POST /api/search/text` with an empty JSON object.

**Expected result:** HTTP 422 because the required `query` field is missing.

**Observed result:** HTTP 422.

**Status:** PASS

### TE-16: Shutdown and workspace integrity

**Objective:** Confirm that the test process shuts down cleanly and does not
alter project files.

**Expected result:** Port 8000 is released and the Git working tree remains
unchanged apart from this report.

**Observed result:** The temporary Uvicorn process stopped, port 8000 was no
longer listening, and the functional tests created no project changes.

**Status:** PASS

## 7. Results summary

| Test area | Passed | Failed |
|---|---:|---:|
| Static and dependency validation | 2 | 0 |
| Data and model integrity | 2 | 0 |
| Startup and web delivery | 3 | 0 |
| Functional API behavior | 6 | 0 |
| Error handling | 2 | 0 |
| Cleanup and integrity | 1 | 0 |
| **Total** | **16** | **0** |

All 16 evaluated checks passed.

## 8. Evaluation and interpretation

The results demonstrate that the current local build is operational as an
end-to-end application. The backend starts correctly, the frontend is served,
the persisted models are compatible with the installed runtime, and the main
search workflows return structured and relevant results. The tested validation
paths also return appropriate HTTP status codes.

The text-search example showed strong qualitative relevance: all leading
results matched both the requested colour and product type. The image-search
example correctly retrieved the source image as the closest product and
returned plausible high-level tags. Some lower-confidence attribute predictions
show that model quality can vary by attribute, even though the inference
pipeline itself is functioning correctly.

## 9. Limitations and residual risks

This report confirms functional correctness for the evaluated environment and
test inputs. It does not claim exhaustive correctness. The following items were
outside the scope of this run:

- formal machine-learning accuracy, precision, recall, F1, or retrieval metrics
  against a labelled holdout dataset;
- complete model retraining from the raw dataset;
- load, stress, concurrency, and long-duration stability testing;
- automated cross-browser visual and interaction testing;
- accessibility and responsive-layout audits;
- security penetration testing and adversarial file-upload testing;
- performance benchmarking on production infrastructure; and
- deployment-platform or container validation.

The frontend also loads Google Fonts from external domains. A network failure
may change typography, but it should not prevent the local API and core search
features from operating.

## 10. Final assessment

**Overall result: PASS**

The Visual Fashion Search application is working as expected for its documented
local workflow and the tested functional requirements. It is suitable for local
demonstration and review. Before a production release, the additional quality,
security, performance, and model-metric evaluations listed above should be
completed.

## 11. Reproduction commands

From the project root in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

While the server is running, the primary manual verification URLs are:

- Application: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- Catalogue statistics: `http://localhost:8000/api/stats`

Stop the server with `Ctrl+C` after testing.
