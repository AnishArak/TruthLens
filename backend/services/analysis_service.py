"""Orchestrates one analysis: classifier + XAI + NLP + evidence + source. Outcomes stay separate by design."""
import logging
import sys
from datetime import datetime, timezone

from config import Config
from services import nlp_service, evidence_service, source_service

sys.path.insert(0, str(Config.ML_DIR))
import predict as ml_predict  # noqa: E402

log = logging.getLogger("truthlens.analysis")

CLASSIFIER_DISCLAIMER = ("The classifier detects writing-style patterns learned from its training dataset. "
                         "It does not verify facts, and its confidence is not the probability that the story is true.")


def _verification_status(evidence):
    """Short status stored in history / dashboard."""
    return "Pending" if evidence["status"] != "ok" else evidence["label"]


def analyze(headline: str, text: str, url_meta: dict = None, provider=None):
    """Return the full analysis dict. Raises FileNotFoundError when no model has been trained."""
    classify_input = f"{headline}. {text}" if headline and text != headline else text
    pred = ml_predict.predict(classify_input)
    explanation = ml_predict.explain(classify_input)
    nlp = nlp_service.nlp_features(headline, text)
    evidence = evidence_service.verify(headline, text, provider=provider)
    if url_meta:
        source = source_service.assess_source(url_meta["url"], deep=False, site_name=url_meta.get("site_name"))
    else:
        source = {"available": False, "reason": "No URL supplied, so the publisher could not be assessed."}

    return {
        "headline": headline or text[:120],
        "excerpt": text[: Config.EXCERPT_CHARS],
        "input_type": "url" if url_meta else "text",
        "article": {k: url_meta.get(k) for k in ("url", "domain", "author", "published_at")} if url_meta else None,
        "classification": {
            "label": pred["label"], "confidence": pred["confidence"], "probabilities": pred["probabilities"],
            "model_name": pred["model_name"], "disclaimer": CLASSIFIER_DISCLAIMER,
        },
        "explanation": explanation,
        "nlp": nlp,
        "evidence": evidence,
        "source": source,
        "verification_status": _verification_status(evidence),
        "created_at": datetime.now(timezone.utc),
    }


def to_document(result: dict) -> dict:
    """Privacy-conscious record for MongoDB: excerpt only, never the full article text."""
    c = result["classification"]
    sent = result["nlp"]["sentiment"]
    return {
        "headline": result["headline"][:300],
        "excerpt": result["excerpt"],
        "input_type": result["input_type"],
        "article": result["article"],
        "prediction": c["label"], "confidence": c["confidence"], "model_name": c["model_name"],
        "sentiment": sent.get("label") if sent.get("available") else None,
        "sentiment_compound": sent.get("compound") if sent.get("available") else None,
        "clickbait_score": result["nlp"]["clickbait"]["score"],
        "clickbait_indicators": [i["match"] for i in result["nlp"]["clickbait"]["indicators"]],
        "evidence_refs": [{"title": e["title"], "url": e["url"], "source": e["source"], "relevance": e["relevance"],
                           "stance": e["stance"]} for e in result["evidence"].get("evidence", [])],
        "evidence_label": result["evidence"]["label"],
        "verification_status": result["verification_status"],
        "created_at": result["created_at"],
        "full_result": {k: v for k, v in result.items() if k not in ("created_at",)},
    }


def serialise(result: dict) -> dict:
    out = dict(result)
    out["created_at"] = result["created_at"].isoformat()
    return out
