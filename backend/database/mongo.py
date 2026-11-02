"""Persistence layer.

MongoStore  - real MongoDB via PyMongo. Connection problems never crash the app; they just disable persistence.
MemoryStore - in-memory store used ONLY by automated tests (never selected by the running app).
Both expose the same interface so routes/services do not care which one they get.
"""
import logging
import uuid
from datetime import datetime, timezone

log = logging.getLogger("truthlens.db")

REQUIRED_FIELDS = ("headline", "prediction", "confidence", "model_name", "verification_status", "created_at")


def validate_document(doc):
    """Light schema validation before writing to the analyses collection."""
    missing = [f for f in REQUIRED_FIELDS if f not in doc]
    if missing:
        raise ValueError(f"Analysis document missing fields: {', '.join(missing)}")
    if doc["prediction"] not in ("REAL", "FAKE"):
        raise ValueError("prediction must be REAL or FAKE")
    if not 0 <= float(doc["confidence"]) <= 1:
        raise ValueError("confidence must be between 0 and 1")


def _public(doc):
    out = dict(doc)
    out["id"] = str(out.pop("_id"))
    if isinstance(out.get("created_at"), datetime):
        out["created_at"] = out["created_at"].astimezone(timezone.utc).isoformat()
    return out


class MongoStore:
    persistent = True

    def __init__(self, uri, db_name):
        self.uri, self.db_name = uri, db_name
        self.client = self.db = None
        self.error = None
        self.connect()

    def connect(self):
        try:
            from pymongo import MongoClient, DESCENDING
            self._desc = DESCENDING
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
            self.client.admin.command("ping")  # fail fast if the server is not running
            self.db = self.client[self.db_name]
            self.db.analyses.create_index([("created_at", DESCENDING)])
            self.error = None
            log.info("Connected to MongoDB database '%s'", self.db_name)
        except ImportError:
            self.db, self.error = None, "PyMongo is not installed (pip install pymongo)."
        except Exception as exc:
            self.db, self.error = None, f"Cannot reach MongoDB at {self.uri}: {exc.__class__.__name__}"
            log.warning(self.error)

    @property
    def available(self):
        return self.db is not None

    def status(self):
        if not self.available:
            self.connect()  # allow recovery once the user starts mongod
        return {"available": self.available, "error": self.error, "backend": "mongodb"}

    # -- analyses ---------------------------------------------------------
    def save_analysis(self, doc):
        validate_document(doc)
        if not self.available:
            raise RuntimeError(self.error or "Database unavailable")
        res = self.db.analyses.insert_one(dict(doc))
        return str(res.inserted_id)

    def list_analyses(self, search=None, prediction=None, status=None, limit=200):
        if not self.available:
            raise RuntimeError(self.error or "Database unavailable")
        q = {}
        if search:
            import re
            q["headline"] = {"$regex": re.escape(search), "$options": "i"}
        if prediction in ("REAL", "FAKE"):
            q["prediction"] = prediction
        if status:
            q["verification_status"] = status
        cur = self.db.analyses.find(q, {"full_result": 0}).sort("created_at", self._desc).limit(limit)
        return [_public(d) for d in cur]

    def get_analysis(self, analysis_id):
        if not self.available:
            raise RuntimeError(self.error or "Database unavailable")
        from bson import ObjectId
        if not ObjectId.is_valid(analysis_id):
            return None
        d = self.db.analyses.find_one({"_id": ObjectId(analysis_id)})
        return _public(d) if d else None

    def delete_analysis(self, analysis_id):
        if not self.available:
            raise RuntimeError(self.error or "Database unavailable")
        from bson import ObjectId
        if not ObjectId.is_valid(analysis_id):
            return False
        return self.db.analyses.delete_one({"_id": ObjectId(analysis_id)}).deleted_count == 1

    def all_for_stats(self, limit=5000):
        if not self.available:
            raise RuntimeError(self.error or "Database unavailable")
        cur = self.db.analyses.find({}, {"prediction": 1, "verification_status": 1, "created_at": 1,
                                         "headline": 1, "confidence": 1}).sort("created_at", self._desc).limit(limit)
        return [_public(d) for d in cur]

    # -- model metrics ----------------------------------------------------
    def save_model_metrics(self, metrics):
        if not self.available:
            return False
        try:
            self.db.model_metrics.replace_one({"trained_at": metrics.get("trained_at")}, metrics, upsert=True)
            return True
        except Exception as exc:
            log.warning("Could not store model metrics: %s", exc)
            return False


class MemoryStore:
    """Test double with the same interface as MongoStore."""
    persistent = False

    def __init__(self):
        self.docs = {}
        self.metrics = []

    available = True

    def status(self):
        return {"available": True, "error": None, "backend": "memory"}

    def save_analysis(self, doc):
        validate_document(doc)
        new_id = uuid.uuid4().hex
        self.docs[new_id] = dict(doc, _id=new_id)
        return new_id

    def _all(self):
        return sorted((_public(d) for d in self.docs.values()), key=lambda d: d["created_at"], reverse=True)

    def list_analyses(self, search=None, prediction=None, status=None, limit=200):
        rows = self._all()
        if search:
            rows = [r for r in rows if search.lower() in r["headline"].lower()]
        if prediction in ("REAL", "FAKE"):
            rows = [r for r in rows if r["prediction"] == prediction]
        if status:
            rows = [r for r in rows if r["verification_status"] == status]
        return [{k: v for k, v in r.items() if k != "full_result"} for r in rows[:limit]]

    def get_analysis(self, analysis_id):
        d = self.docs.get(analysis_id)
        return _public(d) if d else None

    def delete_analysis(self, analysis_id):
        return self.docs.pop(analysis_id, None) is not None

    def all_for_stats(self, limit=5000):
        return self._all()[:limit]

    def save_model_metrics(self, metrics):
        self.metrics.append(metrics)
        return True
