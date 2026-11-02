"""REST API. Every endpoint returns {success, data | error}."""
import logging

from flask import Blueprint, current_app, request

from config import Config
from services import analysis_service, source_service, stats_service, url_extractor
from utils.responses import ApiError, fail, ok
from utils.validators import validate_analyze_payload, validate_url_payload

import predict as ml_predict  # ml/ is on sys.path via analysis_service

log = logging.getLogger("truthlens.api")
bp = Blueprint("api", __name__, url_prefix="/api")


def _store():
    return current_app.config["STORE"]


def _persist(result):
    """Save to the database if available. Returns (id|None, persistence_info)."""
    store = _store()
    try:
        new_id = store.save_analysis(analysis_service.to_document(result))
        return new_id, {"saved": True, "message": None}
    except Exception as exc:
        log.warning("Analysis not saved: %s", exc)
        return None, {"saved": False, "message": "MongoDB is unavailable, so this analysis was not saved. "
                                                 "History and dashboard statistics are disabled until it is running."}


def _run(headline, text, url_meta=None):
    if not ml_predict.model_available():
        raise ApiError("No trained model found. Add the dataset and run `python ml/train.py` first.", 503,
                       "MODEL_NOT_TRAINED")
    try:
        result = analysis_service.analyze(headline, text, url_meta)
    except ValueError as exc:
        raise ApiError(str(exc), 422, "UNPROCESSABLE_TEXT")
    new_id, persistence = _persist(result)
    data = analysis_service.serialise(result)
    data["id"] = new_id
    data["persistence"] = persistence
    return data


@bp.post("/analyze")
def analyze():
    mode, text = validate_analyze_payload(request.get_json(silent=True))
    if mode == "headline":
        return ok(_run(text, text))
    # Article mode: first line (if short) is treated as the headline when no explicit title was sent
    title = (request.get_json(silent=True).get("headline") or "").strip()
    if not title:
        first = text.split("\n", 1)[0].strip()
        title = first if 10 <= len(first) <= 200 and "\n" in text else text[:100].rsplit(" ", 1)[0]
    return ok(_run(title, text))


@bp.post("/analyze-url")
def analyze_url():
    url = validate_url_payload(request.get_json(silent=True))
    article = url_extractor.extract_from_url(url)
    return ok(_run(article["headline"], article["text"], article))


@bp.post("/source")
def source():
    """Source Credibility page: assess a URL or bare domain (includes a live TLS check)."""
    payload = request.get_json(silent=True) or {}
    value = (payload.get("url") or "").strip()
    if not value:
        raise ApiError("Enter a URL or domain.", 400, "EMPTY_URL")
    host = source_service.extract_domain(value)
    if not host:
        raise ApiError("That does not look like a valid domain.", 400, "INVALID_URL")
    url_extractor.validate_url(value if "://" in value else "https://" + value)  # SSRF guard before TLS probe
    return ok(source_service.assess_source(value if "://" in value else "https://" + value, deep=True))


def _db_required():
    st = _store().status()
    if not st["available"]:
        raise ApiError("MongoDB is not connected, so history is disabled. " + (st["error"] or ""), 503, "DB_UNAVAILABLE")


@bp.get("/history")
def history():
    _db_required()
    rows = _store().list_analyses(search=request.args.get("search") or None,
                                  prediction=(request.args.get("prediction") or "").upper() or None,
                                  status=request.args.get("status") or None)
    return ok(rows, count=len(rows))


@bp.get("/history/<analysis_id>")
def history_item(analysis_id):
    _db_required()
    doc = _store().get_analysis(analysis_id)
    if not doc:
        raise ApiError("Analysis not found.", 404, "NOT_FOUND")
    return ok(doc)


@bp.delete("/history/<analysis_id>")
def history_delete(analysis_id):
    _db_required()
    if not _store().delete_analysis(analysis_id):
        raise ApiError("Analysis not found.", 404, "NOT_FOUND")
    return ok({"deleted": analysis_id})


@bp.get("/dashboard")
def dashboard():
    st = _store().status()
    rows = _store().all_for_stats() if st["available"] else []
    data = stats_service.dashboard(rows)
    data["database"] = st
    return ok(data)


@bp.get("/model-metrics")
def model_metrics():
    metrics = stats_service.load_model_metrics()
    if not metrics:
        return ok({"trained": False, "message": "No metrics yet. Run `python ml/train.py` after adding the dataset."})
    _store().save_model_metrics(metrics)
    return ok(dict(metrics, trained=True))


@bp.get("/health")
def health():
    from services import evidence_service
    provider, reason = evidence_service.get_provider()
    return ok({
        "status": "ok",
        "model_trained": ml_predict.model_available(),
        "database": _store().status(),
        "evidence_provider": {"configured": provider is not None, "name": provider.name if provider else None,
                              "reason": reason},
        "sentence_transformers_enabled": Config.USE_SENTENCE_TRANSFORMERS,
    })
