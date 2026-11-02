"""NLP features: keywords, key phrases, sentiment (VADER) and a RULE-BASED clickbait/sensationalism detector.

Important: the clickbait score below is a transparent rule baseline, NOT a trained classifier, and sensational or
emotional wording alone does not establish that a story is fake.
"""
import re
import sys
from collections import Counter

from config import Config

sys.path.insert(0, str(Config.ML_DIR))
from preprocessing import tokenize, STOPWORDS  # noqa: E402

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _vader = SentimentIntensityAnalyzer()
except Exception:  # package missing
    _vader = None

# phrase -> weight (points added to the 0-100 score). Every rule is visible to the user.
CLICKBAIT_PHRASES = {
    "you won't believe": 25, "you wont believe": 25, "won't believe": 20, "shocking": 15, "shocked": 10,
    "breaking": 10, "secret revealed": 25, "secret": 8, "must watch": 20, "must see": 15, "must read": 12,
    "what happens next": 20, "will blow your mind": 25, "blow your mind": 20, "mind-blowing": 15,
    "goes viral": 12, "went viral": 12, "this is why": 10, "the truth about": 12, "they don't want you to know": 25,
    "exposed": 10, "bombshell": 15, "unbelievable": 12, "jaw-dropping": 15, "gone wrong": 10,
    "doctors hate": 25, "one weird trick": 25, "miracle": 12, "hoax": 8, "cover-up": 10, "cover up": 10,
    "you need to see": 15, "can't stop": 8, "share before": 20, "share this": 12,
}
_LISTICLE_RE = re.compile(r"^\s*\d{1,2}\s+(things|reasons|ways|facts|signs|secrets|tips|photos|celebrities)\b", re.I)


def clickbait_analysis(headline: str, text: str = ""):
    """Rule-based sensationalism indicators. Headline is weighted more strongly than the body."""
    indicators, score = [], 0.0
    head_l, body_l = headline.lower(), (text or "").lower()
    for phrase, weight in CLICKBAIT_PHRASES.items():
        in_head = phrase in head_l
        n_body = body_l.count(phrase)
        if in_head or n_body:
            pts = weight if in_head else min(weight * 0.4, weight) * min(n_body, 2)
            score += pts
            indicators.append({"type": "phrase", "match": phrase, "location": "headline" if in_head else "body",
                               "points": round(pts, 1)})
    if _LISTICLE_RE.search(headline):
        score += 10
        indicators.append({"type": "listicle", "match": "numbered list-style headline", "location": "headline", "points": 10})
    excl = headline.count("!")
    if excl:
        pts = min(excl * 6, 15)
        score += pts
        indicators.append({"type": "punctuation", "match": f"{excl} exclamation mark(s) in headline",
                           "location": "headline", "points": pts})
    caps_words = [w for w in re.findall(r"\b[A-Z]{4,}\b", headline)]
    if caps_words:
        pts = min(len(caps_words) * 6, 18)
        score += pts
        indicators.append({"type": "caps", "match": "ALL-CAPS words: " + ", ".join(caps_words[:5]),
                           "location": "headline", "points": pts})
    if headline.strip().endswith("?") and len(headline.split()) <= 14:
        score += 4
        indicators.append({"type": "question", "match": "question-style headline", "location": "headline", "points": 4})
    score = min(100, round(score))
    level = "Low" if score < 25 else "Moderate" if score < 55 else "High"
    return {
        "score": score, "level": level, "indicators": indicators,
        "method": "Transparent rule-based baseline (phrase list, caps, punctuation, listicle pattern). Not a trained classifier.",
        "note": "Sensational or emotional language alone does not mean a story is fake; real news can also use it.",
    }


def sentiment_analysis(text: str):
    if _vader is None:
        return {"available": False, "reason": "vaderSentiment is not installed (pip install vaderSentiment)."}
    s = _vader.polarity_scores(text[:5000])
    c = s["compound"]
    label = "Positive" if c >= 0.05 else "Negative" if c <= -0.05 else "Neutral"
    # strongest emotive words according to the VADER lexicon
    words = sorted({w for w in re.findall(r"[A-Za-z']+", text[:5000])}, key=str.lower)
    scored = []
    for w in words:
        v = _vader.lexicon.get(w.lower())
        if v is not None and abs(v) >= 1.8:
            scored.append({"word": w.lower(), "valence": round(float(v), 2)})
    scored.sort(key=lambda x: -abs(x["valence"]))
    return {"available": True, "label": label, "compound": round(c, 3),
            "positive": round(s["pos"], 3), "neutral": round(s["neu"], 3), "negative": round(s["neg"], 3),
            "emotive_words": scored[:10], "method": "VADER lexicon-based sentiment"}


def extract_keywords(text: str, top_n: int = 10):
    tokens = [t for t in tokenize(text) if t not in STOPWORDS and len(t) > 2]
    counts = Counter(tokens)
    return [{"keyword": w, "count": c} for w, c in counts.most_common(top_n)]


def extract_phrases(text: str, top_n: int = 8):
    """Most frequent content-word bigrams (adjacent after stopword removal inside each sentence)."""
    bigrams = Counter()
    for sent in re.split(r"[.!?\n]+", text):
        toks = [t for t in tokenize(sent) if t not in STOPWORDS and len(t) > 2]
        bigrams.update(" ".join(p) for p in zip(toks, toks[1:]))
    common = [(p, c) for p, c in bigrams.most_common(top_n * 3) if c >= 2][:top_n]
    if not common:  # short texts: fall back to first bigrams seen
        common = list(bigrams.most_common(top_n))
    return [{"phrase": p, "count": c} for p, c in common]


def nlp_features(headline: str, text: str):
    body = f"{headline}. {text}" if headline and text != headline else text
    return {
        "keywords": extract_keywords(body),
        "phrases": extract_phrases(body),
        "sentiment": sentiment_analysis(body),
        "clickbait": clickbait_analysis(headline or text[:200], text),
    }
