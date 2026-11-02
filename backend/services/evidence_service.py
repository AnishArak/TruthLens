"""Evidence retrieval and comparison.

Pipeline: extract claims -> build queries -> retrieve via a pluggable provider -> score semantic similarity ->
assign a stance heuristic -> aggregate to one of four labels.

Honesty rules:
  * Nothing is invented. With SEARCH_PROVIDER=none (or a missing key) the result is status "unavailable".
  * Similarity measures topical closeness, not truth. Stance (supports/contradicts) is a transparent HEURISTIC
    (negation / contradiction-cue mismatch between claim and evidence snippet), not natural-language inference.
    The response says so, and the UI repeats it.
"""
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime

import requests

from config import Config

log = logging.getLogger("truthlens.evidence")

LABEL_SUPPORT = "Supporting evidence found"
LABEL_CONTRA = "Contradicting evidence found"
LABEL_MIXED = "Mixed evidence"
LABEL_NONE = "Insufficient evidence"
LABEL_UNAVAILABLE = "Evidence retrieval unavailable"

MIN_RELEVANCE = 0.30       # below this a result is considered unrelated and ignored
NEGATION = {"not", "no", "never", "false", "fake", "hoax", "denied", "denies", "deny", "debunked", "untrue",
            "misleading", "incorrect", "baseless", "unfounded", "refuted", "rejected", "disputed", "myth"}


# ---------------------------------------------------------------- claim extraction
_NUM_RE = re.compile(r"\d")
_CLAIM_VERBS = re.compile(r"\b(said|says|announced|confirmed|claimed|claims|reported|will|plans?|banned|approved|"
                          r"signed|killed|died|won|lost|rose|fell|increased|decreased|found|revealed|arrested|"
                          r"launched|declared|ordered|warned|cut|raised)\b", re.I)
_NAMED_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")


def extract_claims(headline: str, text: str, max_claims: int = 3):
    """Pick check-worthy sentences: ones with figures, named entities and reporting/event verbs."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text or "") if 40 <= len(s.strip()) <= 300]
    candidates = []
    if headline and len(headline) >= 15:
        candidates.append((3.0, headline.strip()))  # the headline is itself a claim
    for i, s in enumerate(sentences[:40]):
        score = 0.0
        score += 1.5 if _NUM_RE.search(s) else 0
        score += min(len(_NAMED_RE.findall(s)), 3) * 0.7
        score += 1.2 if _CLAIM_VERBS.search(s) else 0
        score += 0.5 if i < 5 else 0
        if s.endswith("?") or s.lower().startswith(("click", "subscribe", "follow", "read more")):
            score -= 3
        if score > 1.5:
            candidates.append((score, s))
    seen, claims = set(), []
    for score, s in sorted(candidates, key=lambda x: -x[0]):
        key = re.sub(r"\W+", " ", s.lower())[:60]
        if key in seen:
            continue
        seen.add(key)
        claims.append({"claim": s, "check_worthiness": round(score, 1), "query": build_query(s)})
        if len(claims) >= max_claims:
            break
    return claims


def build_query(claim: str, max_words: int = 12) -> str:
    """Condense a claim into a search query: keep numbers, capitalised entities and longer words."""
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-]*", claim)
    keep = [w for w in words if w[0].isupper() or w[0].isdigit() or len(w) > 5]
    return " ".join(keep[:max_words]) or " ".join(words[:max_words])


# ---------------------------------------------------------------- providers
class SearchProvider(ABC):
    name = "base"

    @abstractmethod
    def search(self, query: str, limit: int = 5):
        """Return a list of {title, snippet, url, source, published_at}. Raise on transport failure."""


class NewsAPIProvider(SearchProvider):
    name = "newsapi"

    def __init__(self, key):
        self.key = key

    def search(self, query, limit=5):
        r = requests.get("https://newsapi.org/v2/everything", timeout=8,
                         params={"q": query, "pageSize": limit, "language": "en", "sortBy": "relevancy"},
                         headers={"X-Api-Key": self.key})
        r.raise_for_status()
        return [{"title": a.get("title") or "", "snippet": a.get("description") or "", "url": a.get("url"),
                 "source": (a.get("source") or {}).get("name"), "published_at": a.get("publishedAt")}
                for a in r.json().get("articles", []) if a.get("url")]


class SerpAPIProvider(SearchProvider):
    name = "serpapi"

    def __init__(self, key):
        self.key = key

    def search(self, query, limit=5):
        r = requests.get("https://serpapi.com/search.json", timeout=10,
                         params={"engine": "google_news", "q": query, "api_key": self.key})
        r.raise_for_status()
        out = []
        for a in r.json().get("news_results", [])[:limit]:
            src = a.get("source")
            out.append({"title": a.get("title") or "", "snippet": a.get("snippet") or a.get("title") or "",
                        "url": a.get("link"), "source": src.get("name") if isinstance(src, dict) else src,
                        "published_at": a.get("date")})
        return [o for o in out if o["url"]]


def get_provider():
    """Return (provider|None, reason_if_none). Add new providers here."""
    name = Config.SEARCH_PROVIDER
    if name in ("", "none"):
        return None, "No search provider configured. Set SEARCH_PROVIDER and an API key in .env to enable evidence retrieval."
    if name == "newsapi":
        return (NewsAPIProvider(Config.NEWSAPI_KEY), None) if Config.NEWSAPI_KEY else (None, "SEARCH_PROVIDER=newsapi but NEWSAPI_KEY is empty.")
    if name == "serpapi":
        return (SerpAPIProvider(Config.SERPAPI_KEY), None) if Config.SERPAPI_KEY else (None, "SEARCH_PROVIDER=serpapi but SERPAPI_KEY is empty.")
    return None, f"Unknown SEARCH_PROVIDER '{name}'. Use none, newsapi or serpapi."


# ---------------------------------------------------------------- similarity
_st_model = None
_st_failed = False


def _sentence_model():
    global _st_model, _st_failed
    if _st_model is None and not _st_failed and Config.USE_SENTENCE_TRANSFORMERS:
        try:
            from sentence_transformers import SentenceTransformer
            _st_model = SentenceTransformer(Config.SENTENCE_MODEL)
        except Exception as exc:
            log.warning("Sentence-Transformers unavailable (%s); using TF-IDF similarity.", exc)
            _st_failed = True
    return _st_model


def similarity_scores(claim: str, texts):
    """Return (scores, method). Semantic embeddings when enabled, TF-IDF cosine otherwise (labelled)."""
    if not texts:
        return [], "none"
    model = _sentence_model()
    if model is not None:
        from sentence_transformers import util
        emb = model.encode([claim] + list(texts), convert_to_tensor=True)
        sims = util.cos_sim(emb[0], emb[1:])[0].tolist()
        return [max(0.0, float(s)) for s in sims], f"Sentence-Transformers ({Config.SENTENCE_MODEL}) cosine"
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    try:
        vec = TfidfVectorizer(stop_words="english").fit([claim] + list(texts))
        m = vec.transform([claim] + list(texts))
        return [float(s) for s in cosine_similarity(m[0], m[1:])[0]], "TF-IDF cosine (lexical fallback)"
    except ValueError:
        return [0.0] * len(texts), "TF-IDF cosine (lexical fallback)"


def stance_heuristic(claim: str, evidence: str) -> str:
    """supports / contradicts, from negation-cue mismatch. Heuristic only - see module docstring."""
    c = set(re.findall(r"[a-z']+", claim.lower())) & NEGATION
    e = set(re.findall(r"[a-z']+", evidence.lower())) & NEGATION
    if e and not c:
        return "contradicts"
    if c and not e:
        return "contradicts"
    return "supports"


def aggregate(items):
    sup = sum(1 for i in items if i["stance"] == "supports")
    con = sum(1 for i in items if i["stance"] == "contradicts")
    if sup == 0 and con == 0:
        return LABEL_NONE
    if sup and con:
        return LABEL_MIXED
    return LABEL_SUPPORT if sup else LABEL_CONTRA


# ---------------------------------------------------------------- main entry
def verify(headline: str, text: str, provider=None):
    claims = extract_claims(headline, text)
    base = {"claims": claims, "method_notes": [
        "Relevance is similarity between the claim and the retrieved snippet; it measures topical closeness, not truth.",
        "Supporting/contradicting is a simple negation-cue heuristic, not natural-language inference. "
        "Always read the linked sources yourself."]}
    if provider is None:
        provider, reason = get_provider()
        if provider is None:
            return dict(base, status="unavailable", label=LABEL_UNAVAILABLE, reason=reason, evidence=[],
                        provider=None)
    if not claims:
        return dict(base, status="no_claims", label=LABEL_NONE, evidence=[], provider=provider.name,
                    reason="No check-worthy factual claims could be extracted from the text.")

    all_items, errors, method = [], [], "none"
    for c in claims:
        try:
            results = provider.search(c["query"], limit=5)
        except Exception as exc:
            log.warning("Search failed for %r: %s", c["query"], exc)
            errors.append(f"{exc.__class__.__name__}")
            continue
        texts = [f"{r['title']}. {r['snippet']}" for r in results]
        scores, method = similarity_scores(c["claim"], texts)
        for r, t, s in zip(results, texts, scores):
            if s < MIN_RELEVANCE:
                continue
            all_items.append({"claim": c["claim"], "title": r["title"], "snippet": r["snippet"], "url": r["url"],
                              "source": r["source"], "published_at": r["published_at"],
                              "relevance": round(s, 3), "stance": stance_heuristic(c["claim"], t)})
    if errors and not all_items:
        return dict(base, status="error", label=LABEL_UNAVAILABLE, evidence=[], provider=provider.name,
                    reason=f"The search provider request failed ({errors[0]}). Check your API key and network.")
    all_items.sort(key=lambda i: -i["relevance"])
    return dict(base, status="ok", label=aggregate(all_items), evidence=all_items[:12], provider=provider.name,
                similarity_method=method, reason=None)
