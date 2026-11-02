# TruthLens — AI-Powered Fake News Detection & Verification

TruthLens analyses news articles, headlines and URLs with NLP and machine learning, explains the prediction with LIME,
extracts claims, retrieves evidence (when a search provider is configured) and assesses the publisher.

> **Important:** the ML classifier detects *writing-style patterns* learned from its training data. It does **not** verify
> facts. TruthLens therefore reports three independent outcomes — **ML classification**, **evidence verification** and
> **source assessment** — and never merges them into one "truth score".

| URL | Service |
|---|---|
| http://localhost:5173 | React frontend |
| http://localhost:5000 | Flask API (`/api/health`) |

## Project layout

```
TruthLens/
├── frontend/   React + Vite + Tailwind (pages, components, services)
├── backend/    Flask API: routes/, services/, database/, utils/, tests/, data/sources.json
├── ml/         preprocessing.py, train.py, evaluation.py, predict.py, dataset/, saved_models/
├── docs/       project_report.md, architecture.md, viva_questions.md
├── .env.example
└── README.md
```

## Prerequisites (Windows 10/11)

- Python 3.10+ (tick **Add python.exe to PATH** in the installer)
- Node.js 18+ (LTS)
- MongoDB Community Server (optional but needed for history/dashboard) — https://www.mongodb.com/try/download/community
- VS Code

All commands below are for **PowerShell** in the VS Code terminal (`` Ctrl+` ``), run from the `TruthLens` folder.

## 1. Python virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
If PowerShell blocks the script: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then retry. (Or use `.\venv\Scripts\activate.bat` in cmd.)

## 2. Backend dependencies

```powershell
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
python -c "import nltk; nltk.download('stopwords')"
```
(The NLTK download is optional; a built-in stopword list is used if it is missing.)

Optional heavier extras:
```powershell
pip install sentence-transformers          # better evidence similarity (also set USE_SENTENCE_TRANSFORMERS=true)
pip install spacy; python -m spacy download en_core_web_sm
pip install transformers torch             # reserved for an optional transformer classifier (not wired by default)
```

## 3. Frontend dependencies

```powershell
cd frontend
npm install
cd ..
```

## 4. Environment variables

```powershell
copy .env.example .env
```
Edit `.env` as needed. Defaults work for local MongoDB and no search provider.

## 5. Add the Kaggle dataset

1. Download **Fake and Real News Dataset**: https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset
2. Unzip and place **`Fake.csv`** and **`True.csv`** in `ml\dataset\`.

## 6. Train the models

```powershell
python ml\train.py
```
This cleans the data, splits 80/20 (stratified, seed 42), trains Logistic Regression, Multinomial Naive Bayes and Linear SVM
(TF-IDF is fit on training data only), evaluates all three on the test split, picks the best by F1 and writes:

- `ml\saved_models\best_model.joblib`
- `ml\saved_models\metrics.json` (real metrics shown on the Model Performance page)

Quick smoke test on a subset: `python ml\train.py --sample 5000` (the UI flags sampled runs).

## 7. Start MongoDB (optional but recommended)

MongoDB Community installs as a Windows service and normally starts automatically. Check with:
```powershell
Get-Service MongoDB
Start-Service MongoDB        # run PowerShell as Administrator if needed
```
Default connection: `mongodb://localhost:27017` (`MONGO_URI` in `.env`). For MongoDB Atlas, paste your connection string there.
Without MongoDB, analysis still works; history and dashboard statistics are disabled and the UI says so.

## 8. Start the Flask backend (terminal 1)

```powershell
.\venv\Scripts\Activate.ps1
python backend\app.py
```
Check: http://localhost:5000/api/health

## 9. Start the React frontend (terminal 2)

```powershell
cd frontend
npm run dev
```
Open http://localhost:5173. The Vite dev server proxies `/api` to the backend.

## 10. Enable evidence retrieval (optional)

Evidence verification needs a live search provider. Without one, the app shows **"Evidence retrieval unavailable"** and
never invents sources.

```ini
# .env
SEARCH_PROVIDER=newsapi      # or serpapi
NEWSAPI_KEY=your_key_here    # https://newsapi.org
```
Restart the backend. New providers can be added by subclassing `SearchProvider` in `backend/services/evidence_service.py`.

## Tests

```powershell
python -m pytest backend\tests -q
```
Tests train a tiny model on **synthetic** data in a temp folder (never your real model) and use an in-memory store instead of MongoDB.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/analyze` | `{mode: "article"\|"headline", text}` |
| POST | `/api/analyze-url` | `{url}` |
| POST | `/api/source` | `{url}` source credibility lookup |
| GET | `/api/history` | `?search=&prediction=&status=` |
| GET / DELETE | `/api/history/<id>` | detail / delete |
| GET | `/api/dashboard` | statistics from stored analyses |
| GET | `/api/model-metrics` | real metrics from `metrics.json` |
| GET | `/api/health` | model / DB / provider status |

Responses are `{success, data}` or `{success: false, error: {message, code}}`.

## What works without extra setup

| Feature | Needs |
|---|---|
| Landing, navigation, About | nothing |
| Classification, LIME, keywords, sentiment, clickbait | trained model (dataset + `train.py`) |
| URL extraction, Source Credibility | internet access from your machine |
| History, Dashboard statistics | MongoDB |
| Evidence verification | search API key |
| Better semantic similarity | `sentence-transformers` + `USE_SENTENCE_TRANSFORMERS=true` |

## Security notes

URL analysis blocks localhost/private/link-local addresses (SSRF), restricts to http/https, validates every redirect,
caps response size, enforces timeouts, honours `robots.txt`, and only parses HTML text (no scripts are executed).

## Preprocessing note

The pipeline implements: lower-casing, URL/HTML/dateline removal, regex tokenization and stopword removal.
**Stemming and lemmatization are optional and are NOT applied by default** (`clean_text(text, stem=True)` enables
Porter stemming). Do not claim them in reports unless you enable and evaluate them.

## Troubleshooting

| Problem | Fix |
|---|---|
| `No trained model found` / HTTP 503 `MODEL_NOT_TRAINED` | Add `Fake.csv`, `True.csv` and run `python ml\train.py` |
| `Dataset not found` | Files must be in `ml\dataset\` with exact names `Fake.csv` / `True.csv` |
| Cannot reach the backend in the UI | Start `python backend\app.py`; confirm http://localhost:5000/api/health |
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| MongoDB offline in the sidebar | `Start-Service MongoDB` or fix `MONGO_URI`; app keeps working without it |
| `ModuleNotFoundError` | Activate the venv, then `pip install -r backend\requirements.txt` |
| Port 5000 busy | Set `FLASK_PORT=5001` in `.env` and `VITE_BACKEND_URL=http://localhost:5001` before `npm run dev` |
| `npm install` fails | Use Node 18+; delete `node_modules` and `package-lock.json`, retry |
| LIME slow on first request | Normal: it samples 500 perturbations; later requests are faster |
| URL analysis says extraction failed | Page is paywalled / JS-rendered / blocks bots — paste the text instead |
| Evidence says unavailable | Set `SEARCH_PROVIDER` and the matching key in `.env`, restart backend |
| Very high accuracy (~99%) | Expected on this dataset (strong source artefacts); it does **not** imply real-world accuracy — see Limitations |
