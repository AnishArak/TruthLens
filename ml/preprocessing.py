"""Text preprocessing for TruthLens.

Steps implemented here (and ONLY these - do not claim others in reports):
  1. lower-casing
  2. removal of URLs, HTML tags, and a leading news-agency dateline ("WASHINGTON (Reuters) -")
  3. removal of non-alphabetic characters
  4. tokenization (regex word tokenizer, no heavy NLTK download needed)
  5. stopword removal (NLTK English list if available, otherwise a built-in fallback list)

Stemming and lemmatization are OPTIONAL and are NOT applied by default.
Enable stemming with clean_text(text, stem=True) - it uses NLTK's PorterStemmer.
"""
import re

try:  # NLTK stopwords are used if the corpus is present
    from nltk.corpus import stopwords as _nltk_stopwords
    _STOP = set(_nltk_stopwords.words("english"))
except Exception:  # corpus missing or nltk not installed
    _STOP = set()

_FALLBACK_STOPWORDS = set("""
a about above after again against all am an and any are as at be because been before being below between both
but by can did do does doing down during each few for from further had has have having he her here hers herself
him himself his how i if in into is it its itself just me more most my myself no nor not now of off on once only
or other our ours ourselves out over own same she should so some such than that the their theirs them themselves
then there these they this those through to too under until up very was we were what when where which while who
whom why will with you your yours yourself yourselves said says would could also""".split())

STOPWORDS = _STOP or _FALLBACK_STOPWORDS

_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_HTML_RE = re.compile(r"<[^>]+>")
# Dataset leakage guard: Reuters datelines such as "WASHINGTON (Reuters) -" almost only appear in the REAL class.
_DATELINE_RE = re.compile(r"^\s*[A-Z][A-Za-z\s,\.]{0,40}\((reuters|ap|afp)\)\s*[-–—]\s*", re.IGNORECASE)
_TOKEN_RE = re.compile(r"[a-z]+")


def strip_dateline(text: str) -> str:
    """Remove agency datelines so the model cannot cheat on a publisher artefact."""
    return _DATELINE_RE.sub("", text or "")


def tokenize(text: str):
    return _TOKEN_RE.findall(text.lower())


def clean_text(text: str, stem: bool = False) -> str:
    """Normalise raw text into a space-joined string of lower-case content tokens."""
    if not isinstance(text, str):
        return ""
    text = strip_dateline(text)
    text = _URL_RE.sub(" ", text)
    text = _HTML_RE.sub(" ", text)
    tokens = [t for t in tokenize(text) if t not in STOPWORDS and len(t) > 1]
    if stem:
        from nltk.stem import PorterStemmer
        ps = PorterStemmer()
        tokens = [ps.stem(t) for t in tokens]
    return " ".join(tokens)
