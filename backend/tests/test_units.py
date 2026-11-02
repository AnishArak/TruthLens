import pytest

from services import evidence_service as ev
from services import nlp_service as nlp
from services import source_service as src
from services import url_extractor as ux
from utils.responses import ApiError


# ---- SSRF protection -------------------------------------------------------
@pytest.mark.parametrize("url", [
    "http://localhost/admin", "http://127.0.0.1/", "http://10.0.0.5/x", "http://192.168.1.1/",
    "http://169.254.169.254/latest/meta-data", "http://[::1]/", "http://0.0.0.0/", "http://foo.internal/",
])
def test_blocks_internal_addresses(url):
    with pytest.raises(ApiError) as e:
        ux.validate_url(url)
    assert e.value.status == 400


@pytest.mark.parametrize("url", ["ftp://example.com/x", "file:///etc/passwd", "javascript:alert(1)", "gopher://x.com"])
def test_blocks_bad_schemes(url):
    with pytest.raises(ApiError):
        ux.validate_url(url)


def test_blocks_credentials_in_url():
    with pytest.raises(ApiError):
        ux.validate_url("http://user:pw@127.0.0.1/")


def test_is_public_ip():
    assert not ux.is_public_ip("10.1.2.3") and not ux.is_public_ip("127.0.0.1")
    assert ux.is_public_ip("8.8.8.8")


def test_parse_article_strips_scripts():
    html = """<html><head><title>T</title><meta property="og:title" content="Big Headline Here">
    <meta name="author" content="Jane Doe"></head><body><script>alert(1)</script><article>
    <p>%s</p><p>%s</p></article></body></html>""" % ("Sentence one is a reasonably long paragraph of text. " * 2,
                                                       "Another paragraph with enough content to be kept here. " * 2)
    a = ux.parse_article(html, "https://example.com/a")
    assert a["headline"] == "Big Headline Here" and a["author"] == "Jane Doe"
    assert "alert" not in a["text"] and a["domain"] == "example.com"


# ---- NLP ---------------------------------------------------------------------
def test_clickbait_high_for_sensational_headline():
    r = nlp.clickbait_analysis("SHOCKING secret revealed: you won't believe what happens next!!", "")
    assert r["score"] >= 55 and r["level"] == "High" and r["indicators"]
    assert "not a trained classifier" in r["method"].lower()


def test_clickbait_low_for_plain_headline():
    assert nlp.clickbait_analysis("City council approves annual budget", "")["score"] < 25


def test_keywords_and_phrases():
    text = "Climate summit opens. Climate summit leaders discuss emissions targets and emissions policy."
    assert nlp.extract_keywords(text)[0]["keyword"] in ("climate", "summit", "emissions")
    assert any(p["phrase"] == "climate summit" for p in nlp.extract_phrases(text))


# ---- Source ------------------------------------------------------------------
def test_domain_extraction():
    assert src.extract_domain("https://www.BBC.co.uk/news/x") == "bbc.co.uk"
    assert src.extract_domain("nonsense") is None


def test_unknown_domain_not_labelled_fake():
    r = src.assess_source("https://some-random-blog.example/post")
    assert r["reputation"]["listed"] is False and r["reputation"]["category"] == "unlisted"
    assert "fake" not in r["assessment"].lower()


def test_known_domain_listed():
    assert src.assess_source("https://www.reuters.com/a")["reputation"]["name"] == "Reuters"


# ---- Evidence ----------------------------------------------------------------
def test_claim_extraction_prefers_factual_sentences():
    text = ("Prime Minister John Smith announced a 20 percent cut in fuel tax on Monday. "
            "Click here to subscribe to our newsletter for more updates today. "
            "Opposition leader Mary Jones said the plan will cost 5 billion dollars.")
    claims = ev.extract_claims("Fuel tax cut announced by government", text)
    assert claims and all("subscribe" not in c["claim"].lower() for c in claims)


def test_evidence_unavailable_without_provider(monkeypatch):
    monkeypatch.setattr(ev.Config, "SEARCH_PROVIDER", "none")
    r = ev.verify("Fuel tax cut announced by government", "Prime Minister John Smith announced a 20 percent cut in fuel tax.")
    assert r["status"] == "unavailable" and r["evidence"] == [] and r["label"] == ev.LABEL_UNAVAILABLE


class FakeProvider(ev.SearchProvider):
    """Test double: returns canned results. Never used by the running app."""
    name = "fake"

    def search(self, query, limit=5):
        return [{"title": "Government announces fuel tax cut", "snippet": "Prime Minister John Smith announced a 20 percent cut in fuel tax.",
                 "url": "https://example.com/1", "source": "Example", "published_at": "2026-01-01"},
                {"title": "Unrelated gardening tips", "snippet": "Roses need sun.", "url": "https://example.com/2",
                 "source": "Garden", "published_at": None}]


def test_evidence_with_provider_filters_unrelated():
    r = ev.verify("Fuel tax cut announced by government",
                  "Prime Minister John Smith announced a 20 percent cut in fuel tax on Monday.", provider=FakeProvider())
    assert r["status"] == "ok" and r["label"] == ev.LABEL_SUPPORT
    assert all("gardening" not in e["title"].lower() for e in r["evidence"])
    assert all(0 <= e["relevance"] <= 1 for e in r["evidence"])


def test_aggregate_labels():
    s, c = {"stance": "supports"}, {"stance": "contradicts"}
    assert ev.aggregate([]) == ev.LABEL_NONE and ev.aggregate([s, c]) == ev.LABEL_MIXED
    assert ev.aggregate([c]) == ev.LABEL_CONTRA
