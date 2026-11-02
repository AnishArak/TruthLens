"""Input validation for the analyze endpoints."""
from config import Config
from utils.responses import ApiError

VALID_MODES = ("article", "headline")


def validate_analyze_payload(payload):
    if not isinstance(payload, dict):
        raise ApiError("Request body must be a JSON object.", 400, "INVALID_BODY")
    mode = payload.get("mode", "article")
    if mode not in VALID_MODES:
        raise ApiError(f"mode must be one of {', '.join(VALID_MODES)}.", 400, "INVALID_MODE")
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ApiError("Please provide some text to analyse.", 400, "EMPTY_TEXT")
    text = text.strip()
    minimum = Config.MIN_ARTICLE_CHARS if mode == "article" else Config.MIN_HEADLINE_CHARS
    if len(text) < minimum:
        label = "article" if mode == "article" else "headline"
        raise ApiError(f"The {label} is too short. Enter at least {minimum} characters.", 400, "TEXT_TOO_SHORT")
    if len(text) > Config.MAX_TEXT_CHARS:
        raise ApiError(f"Text is too long (max {Config.MAX_TEXT_CHARS} characters).", 413, "TEXT_TOO_LONG")
    return mode, text


def validate_url_payload(payload):
    if not isinstance(payload, dict):
        raise ApiError("Request body must be a JSON object.", 400, "INVALID_BODY")
    url = payload.get("url")
    if not isinstance(url, str) or not url.strip():
        raise ApiError("Please provide a news article URL.", 400, "EMPTY_URL")
    url = url.strip()
    if len(url) > 2048:
        raise ApiError("URL is too long.", 400, "URL_TOO_LONG")
    return url
