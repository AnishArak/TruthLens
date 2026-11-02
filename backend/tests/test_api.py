ARTICLE = ("Government minister announces new budget policy\n" + "The parliament committee reviewed the budget report today. " * 6)


def test_health(client):
    d = client.get("/api/health").get_json()["data"]
    assert d["status"] == "ok" and d["model_trained"] is True and d["evidence_provider"]["configured"] is False


def test_analyze_article(client):
    r = client.post("/api/analyze", json={"mode": "article", "text": ARTICLE})
    assert r.status_code == 200
    d = r.get_json()["data"]
    assert d["classification"]["label"] in ("REAL", "FAKE")
    assert 0 <= d["classification"]["confidence"] <= 1
    assert d["evidence"]["status"] == "unavailable"          # no provider configured -> never fabricated
    assert d["verification_status"] == "Pending"
    assert d["source"]["available"] is False                  # pasted text has no publisher
    assert "excerpt" in d and len(d["excerpt"]) <= 500
    assert d["id"] and d["persistence"]["saved"] is True


def test_analyze_headline(client):
    r = client.post("/api/analyze", json={"mode": "headline", "text": "Shocking secret revealed about hoax conspiracy"})
    assert r.status_code == 200 and r.get_json()["data"]["classification"]["label"] == "FAKE"


def test_validation_errors(client):
    assert client.post("/api/analyze", json={"mode": "article", "text": ""}).status_code == 400
    assert client.post("/api/analyze", json={"mode": "article", "text": "too short"}).status_code == 400
    assert client.post("/api/analyze", json={"mode": "nope", "text": "x" * 200}).status_code == 400
    assert client.post("/api/analyze", data="not json", content_type="text/plain").status_code == 400
    assert client.post("/api/analyze", json={"mode": "article", "text": "x" * 60000}).status_code == 413


def test_analyze_url_blocks_ssrf(client):
    r = client.post("/api/analyze-url", json={"url": "http://127.0.0.1:5000/api/health"})
    assert r.status_code == 400 and r.get_json()["error"]["code"] == "BLOCKED_HOST"
    assert client.post("/api/analyze-url", json={"url": ""}).status_code == 400


def test_history_crud_and_dashboard(client):
    a = client.post("/api/analyze", json={"mode": "article", "text": ARTICLE}).get_json()["data"]
    client.post("/api/analyze", json={"mode": "headline", "text": "Shocking secret revealed about hoax conspiracy"})
    rows = client.get("/api/history").get_json()["data"]
    assert len(rows) == 2 and all("full_result" not in r for r in rows)
    assert len(client.get("/api/history?prediction=FAKE").get_json()["data"]) >= 1
    assert len(client.get("/api/history?search=zzzz").get_json()["data"]) == 0
    detail = client.get(f"/api/history/{a['id']}").get_json()["data"]
    assert detail["full_result"]["classification"]["label"] == a["classification"]["label"]
    dash = client.get("/api/dashboard").get_json()["data"]
    assert dash["totals"]["total"] == 2 and dash["totals"]["pending"] == 2 and len(dash["activity"]) == 14
    assert client.delete(f"/api/history/{a['id']}").status_code == 200
    assert client.get(f"/api/history/{a['id']}").status_code == 404
    assert client.delete("/api/history/missing").status_code == 404


def test_db_unavailable_still_analyses(client):
    class Down:
        available = False
        def status(self): return {"available": False, "error": "down", "backend": "mongodb"}
        def save_analysis(self, doc): raise RuntimeError("down")
        def all_for_stats(self): raise RuntimeError("down")
    client.application.config["STORE"] = Down()
    r = client.post("/api/analyze", json={"mode": "article", "text": ARTICLE})
    assert r.status_code == 200 and r.get_json()["data"]["persistence"]["saved"] is False
    assert client.get("/api/history").status_code == 503
    assert client.get("/api/dashboard").status_code == 200


def test_model_metrics_endpoint(client):
    assert client.get("/api/model-metrics").status_code == 200


def test_not_found_and_source_validation(client):
    assert client.get("/api/nope").status_code == 404
    assert client.post("/api/source", json={"url": ""}).status_code == 400
    assert client.post("/api/source", json={"url": "http://localhost"}).status_code == 400
