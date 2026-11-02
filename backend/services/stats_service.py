"""Dashboard statistics computed from stored analyses (real data only) and model metrics from metrics.json."""
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from config import Config


def load_model_metrics():
    if not Config.METRICS_PATH.exists():
        return None
    return json.loads(Config.METRICS_PATH.read_text(encoding="utf-8"))


def dashboard(rows, days=14):
    total = len(rows)
    fake = sum(1 for r in rows if r["prediction"] == "FAKE")
    real = total - fake
    pending = sum(1 for r in rows if r.get("verification_status") == "Pending")
    per_day = Counter(r["created_at"][:10] for r in rows)
    today = datetime.now(timezone.utc).date()
    activity = []
    for i in range(days - 1, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        activity.append({"date": d, "count": per_day.get(d, 0)})
    metrics = load_model_metrics()
    best = None
    if metrics:
        best = next((m for m in metrics["models"] if m["name"] == metrics["best_model"]), None)
    return {
        "totals": {"total": total, "fake": fake, "real": real, "pending": pending},
        "distribution": [{"name": "REAL", "value": real}, {"name": "FAKE", "value": fake}],
        "activity": activity,
        "recent": rows[:6],
        "model": {"trained": bool(metrics), "best_model": metrics["best_model"] if metrics else None,
                  "accuracy": best["accuracy"] if best else None, "precision": best["precision"] if best else None,
                  "recall": best["recall"] if best else None, "f1": best["f1"] if best else None},
    }
