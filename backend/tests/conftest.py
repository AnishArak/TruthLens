import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT / "ml"))

try:
    import flask_cors  # noqa: F401
except ImportError:  # sandbox without the package: tests do not exercise CORS
    stub = types.ModuleType("flask_cors")
    stub.CORS = lambda *a, **k: None
    sys.modules["flask_cors"] = stub


@pytest.fixture(scope="session")
def model_path(tmp_path_factory):
    """Train a tiny model on SYNTHETIC data (test-only) so API tests do not need the Kaggle dataset."""
    import pandas as pd
    import random
    random.seed(1)
    fake_w = "shocking secret revealed hoax conspiracy miracle exposed banned bombshell outrage insane".split()
    real_w = "government minister parliament budget committee policy election court report officials economy".split()
    common = "people today country president city week year state vote market".split()
    data, out = tmp_path_factory.mktemp("data"), tmp_path_factory.mktemp("model")

    def mk(spec):
        return pd.DataFrame([{"title": " ".join(random.choices(spec, k=6) + random.choices(common, k=3)),
                              "text": " ".join(random.choices(spec, k=40) + random.choices(common, k=40)),
                              "subject": "s", "date": "d"} for _ in range(200)])
    mk(fake_w).to_csv(data / "Fake.csv", index=False)
    mk(real_w).to_csv(data / "True.csv", index=False)
    subprocess.run([sys.executable, str(ROOT / "ml" / "train.py"), "--data-dir", str(data), "--model-dir", str(out)],
                   check=True, capture_output=True)
    return out / "best_model.joblib"


@pytest.fixture()
def client(model_path, monkeypatch):
    import predict
    monkeypatch.setattr(predict, "MODEL_PATH", model_path)
    predict.reload_model()
    from app import create_app
    from database.mongo import MemoryStore
    app = create_app(store=MemoryStore())
    app.config["TESTING"] = True
    return app.test_client()
