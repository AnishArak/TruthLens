# TruthLens — Architecture

```
 Browser (React, Vite :5173)
        │  /api (Vite proxy in dev)
        ▼
 Flask API (:5000)  routes/api.py
   ├─ validators → analysis_service ──┬─ ml/predict.py  (TF-IDF + best classifier, LIME)
   │                                  ├─ nlp_service    (keywords, VADER, rule-based clickbait)
   │                                  ├─ evidence_service (claims → SearchProvider → similarity → stance heuristic)
   │                                  └─ source_service (domain, TLS, sources.json)
   ├─ url_extractor (SSRF-safe fetch + BeautifulSoup)
   ├─ stats_service (dashboard + metrics.json)
   └─ database/mongo.py (MongoStore; degrades gracefully)
 MongoDB: analyses, model_metrics
```

## Design decisions

1. **Three separate outcomes.** Classification, evidence and source results are returned in different keys and rendered in
   different cards. There is no combined score.
2. **Nothing fabricated.** Missing model, provider, DB, LIME or VADER each produce an explicit "unavailable" state with a reason.
3. **Pluggable evidence providers.** `SearchProvider.search(query, limit)` returns `{title, snippet, url, source, published_at}`.
4. **Graceful persistence.** If MongoDB is down, `/api/analyze` still returns a result plus `persistence.saved=false`;
   `/api/history` returns 503 `DB_UNAVAILABLE`; `/api/dashboard` returns zeros with the DB status.
5. **Privacy.** Only a 500-character excerpt and derived features are stored — not the full article text.
6. **ML leakage controls.** TF-IDF lives inside each `Pipeline` and is fit on the training split only; agency datelines are
   stripped; duplicate and label-conflicting articles are removed before the split.

## Data flow for `POST /api/analyze`

validate → classify (`predict`) → explain (`LIME`) → NLP features → extract claims → search (if configured) →
similarity + stance heuristic → source assessment (URL input only) → save (if DB) → JSON.

## MongoDB collections

- `analyses`: headline, excerpt, prediction, confidence, model_name, sentiment, clickbait_score/indicators,
  evidence_refs, evidence_label, verification_status, created_at, full_result.
- `model_metrics`: copy of `metrics.json` written when `/api/model-metrics` is requested.
- `users`: not created (no authentication is implemented).

## Error handling

`ApiError(message, status, code)` is converted to `{success:false, error:{message, code}}`. Codes include `EMPTY_TEXT`,
`TEXT_TOO_SHORT`, `BLOCKED_HOST`, `EXTRACTION_FAILED`, `ROBOTS_DISALLOWED`, `MODEL_NOT_TRAINED`, `DB_UNAVAILABLE`.
