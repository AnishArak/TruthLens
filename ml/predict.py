"""Inference and LIME explanations for the saved TruthLens model."""
import sys
from pathlib import Path

import joblib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preprocessing import clean_text  # noqa: E402

import os

# TRUTHLENS_MODEL_PATH lets tests point at a different model file.
MODEL_PATH = Path(os.environ.get("TRUTHLENS_MODEL_PATH") or
                  Path(__file__).resolve().parent / "saved_models" / "best_model.joblib")
CLASS_NAMES = ["REAL", "FAKE"]

_bundle = None


def model_available() -> bool:
    return MODEL_PATH.exists()


def _load():
    global _bundle
    if _bundle is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError("No trained model found. Run: python ml/train.py")
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def reload_model():
    global _bundle
    _bundle = None


def predict(text: str) -> dict:
    """Return the classifier output. This is a statistical text-pattern prediction, NOT a fact check."""
    bundle = _load()
    cleaned = clean_text(text)
    if not cleaned:
        raise ValueError("Text has no usable words after preprocessing.")
    proba = bundle["pipeline"].predict_proba([cleaned])[0]
    idx = int(np.argmax(proba))
    return {
        "label": CLASS_NAMES[idx],
        "confidence": float(proba[idx]),
        "probabilities": {"REAL": float(proba[0]), "FAKE": float(proba[1])},
        "model_name": bundle["model_name"],
        "cleaned_text": cleaned,
    }


def explain(text: str, num_features: int = 12, num_samples: int = 500) -> dict:
    """LIME explanation over the preprocessed tokens. Returns {available, ...}; never fabricates output."""
    try:
        from lime.lime_text import LimeTextExplainer
    except ImportError:
        return {"available": False, "reason": "LIME is not installed (pip install lime)."}
    try:
        bundle = _load()
        pipe = bundle["pipeline"]
        cleaned = clean_text(text)
        if len(cleaned.split()) < 3:
            return {"available": False, "reason": "Text is too short for a meaningful word-level explanation."}
        # Cap very long texts to keep LIME fast; explanation covers the first 400 content words.
        words = cleaned.split()
        truncated = len(words) > 400
        cleaned = " ".join(words[:400])
        explainer = LimeTextExplainer(class_names=CLASS_NAMES, random_state=42)
        exp = explainer.explain_instance(cleaned, pipe.predict_proba, num_features=num_features,
                                         num_samples=num_samples, labels=(1,))
        # LIME weights are for class index 1 (FAKE): positive pushes towards FAKE, negative towards REAL.
        features = [{"word": w, "weight": float(wt), "pushes_towards": "FAKE" if wt > 0 else "REAL"}
                    for w, wt in exp.as_list(label=1)]
        return {
            "available": True,
            "method": "LIME (local surrogate over preprocessed tokens)",
            "features": features,
            "truncated": truncated,
            "limitations": ("Word-level explanations describe which words influenced this model locally. "
                            "They show correlation learned from the training data, not why a claim is true or false."),
        }
    except Exception as exc:  # explanation must never break the analysis
        return {"available": False, "reason": f"LIME failed: {exc}"}
