"""Safe article extraction from a URL.

Security measures (SSRF protection):
  * only http/https
  * hostname resolved up-front; every resolved IP must be public (no loopback/private/link-local/reserved/multicast)
  * redirects are followed manually (max 3) and each hop is re-validated
  * response body read in chunks and capped at URL_MAX_BYTES; only text/html accepted
  * short timeouts; nothing downloaded is executed - HTML is parsed to plain text only
  * robots.txt is honoured: if it disallows our user-agent we do not fetch the page
Known limitation: DNS-rebinding between validation and connection is reduced (not eliminated) by validating each hop.
"""
import ipaddress
import logging
import re
import socket
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from config import Config
from utils.responses import ApiError

log = logging.getLogger("truthlens.url")
USER_AGENT = "TruthLensBot/1.0 (+academic project; article text analysis)"
MAX_REDIRECTS = 3


def is_public_ip(ip_str: str) -> bool:
    ip = ipaddress.ip_address(ip_str)
    return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                or ip.is_multicast or ip.is_unspecified or getattr(ip, "is_site_local", False))


def validate_url(url: str) -> str:
    """Return the normalised URL or raise ApiError. Blocks internal addresses."""
    url = url.strip()
    # Scheme-like prefixes without "//" (javascript:, data:, mailto:) must be rejected, not treated as host:port.
    if "://" not in url and re.match(r"^[A-Za-z][A-Za-z0-9+.\-]*:(?!\d+(/|$))", url):
        raise ApiError("Only http and https URLs are allowed.", 400, "INVALID_URL_SCHEME")
    try:
        parsed = urlparse(url if "://" in url else "https://" + url)
        host, port = parsed.hostname, parsed.port
    except ValueError:
        raise ApiError("That does not look like a valid URL.", 400, "INVALID_URL")
    if parsed.scheme not in ("http", "https"):
        raise ApiError("Only http and https URLs are allowed.", 400, "INVALID_URL_SCHEME")
    if not host:
        raise ApiError("That does not look like a valid URL.", 400, "INVALID_URL")
    if parsed.username or parsed.password:
        raise ApiError("URLs containing credentials are not allowed.", 400, "INVALID_URL")
    if host.lower() in ("localhost",) or host.lower().endswith((".local", ".internal", ".localhost")):
        raise ApiError("Internal addresses are not allowed.", 400, "BLOCKED_HOST")
    try:
        infos = socket.getaddrinfo(host, port or (443 if parsed.scheme == "https" else 80),
                                   proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise ApiError("Could not resolve that domain name.", 400, "DNS_FAILED")
    for info in infos:
        if not is_public_ip(info[4][0]):
            raise ApiError("Internal or private network addresses are not allowed.", 400, "BLOCKED_HOST")
    return parsed.geturl()


def _safe_get(url, accept="text/html,application/xhtml+xml", max_bytes=None, timeout=None):
    """GET with manual redirects, validation on every hop and a streamed size cap."""
    max_bytes = max_bytes or Config.URL_MAX_BYTES
    timeout = timeout or Config.URL_FETCH_TIMEOUT
    current = validate_url(url)
    for _ in range(MAX_REDIRECTS + 1):
        try:
            resp = requests.get(current, headers={"User-Agent": USER_AGENT, "Accept": accept},
                                timeout=timeout, allow_redirects=False, stream=True)
        except requests.exceptions.Timeout:
            raise ApiError("The website took too long to respond.", 504, "FETCH_TIMEOUT")
        except requests.exceptions.RequestException:
            raise ApiError("Could not connect to that website.", 502, "FETCH_FAILED")
        if resp.status_code in (301, 302, 303, 307, 308) and resp.headers.get("Location"):
            current = validate_url(urljoin(current, resp.headers["Location"]))
            resp.close()
            continue
        break
    else:
        raise ApiError("Too many redirects.", 502, "TOO_MANY_REDIRECTS")

    if resp.status_code >= 400:
        resp.close()
        raise ApiError(f"The website returned an error (HTTP {resp.status_code}).", 502, "FETCH_HTTP_ERROR")
    ctype = resp.headers.get("Content-Type", "")
    if "html" not in ctype.lower() and "text/plain" not in ctype.lower() and "robots" not in accept:
        resp.close()
        raise ApiError("That URL does not point to an HTML page.", 415, "UNSUPPORTED_CONTENT")
    chunks, size = [], 0
    for chunk in resp.iter_content(chunk_size=16384):
        size += len(chunk)
        if size > max_bytes:
            resp.close()
            raise ApiError("The page is too large to analyse.", 413, "RESPONSE_TOO_LARGE")
        chunks.append(chunk)
    resp.close()
    encoding = resp.encoding or "utf-8"
    return b"".join(chunks).decode(encoding, errors="replace"), current


def robots_allows(url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        body, _ = _safe_get(robots_url, accept="text/plain,robots", max_bytes=200_000, timeout=4)
    except ApiError:
        return True  # no readable robots.txt -> no stated restriction
    rp = RobotFileParser()
    rp.parse(body.splitlines())
    return rp.can_fetch(USER_AGENT, url)


def _meta(soup, *names):
    for n in names:
        tag = soup.find("meta", attrs={"property": n}) or soup.find("meta", attrs={"name": n})
        if tag and tag.get("content", "").strip():
            return tag["content"].strip()
    return None


def parse_article(html: str, final_url: str) -> dict:
    """Extract headline/body/author/date from HTML. Output is plain text only (sanitised)."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe", "form", "nav", "footer", "aside", "header", "svg"]):
        tag.decompose()

    h1 = soup.find("h1")
    headline = _meta(soup, "og:title", "twitter:title") or (h1.get_text(" ", strip=True) if h1 else None) \
        or (soup.title.get_text(strip=True) if soup.title else "")

    container = soup.find("article") or soup.find("main") or soup
    paragraphs = [p.get_text(" ", strip=True) for p in container.find_all("p")]
    paragraphs = [p for p in paragraphs if len(p) >= 40]
    if len(" ".join(paragraphs)) < 200 and container is not soup:  # fall back to whole page
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) >= 40]
    text = "\n".join(paragraphs)[: Config.MAX_TEXT_CHARS]

    author = _meta(soup, "author", "article:author", "twitter:creator")
    if not author:
        a = soup.find(attrs={"rel": "author"}) or soup.find(class_="author")
        author = a.get_text(" ", strip=True)[:120] if a else None
    published = _meta(soup, "article:published_time", "og:article:published_time", "date", "pubdate", "publishdate")
    if not published:
        t = soup.find("time")
        published = (t.get("datetime") or t.get_text(strip=True)) if t else None
    site_name = _meta(soup, "og:site_name", "application-name")

    return {"headline": (headline or "")[:300], "text": text, "author": author, "published_at": published,
            "site_name": site_name, "url": final_url, "domain": urlparse(final_url).hostname}


def extract_from_url(url: str) -> dict:
    """Public entry point. Raises ApiError with a user-friendly message when extraction is not possible."""
    safe_url = validate_url(url)
    if not robots_allows(safe_url):
        raise ApiError("This website's robots.txt does not allow automated access. "
                       "Please paste the article text manually.", 403, "ROBOTS_DISALLOWED")
    html, final_url = _safe_get(safe_url)
    article = parse_article(html, final_url)
    if len(article["text"]) < 200:
        raise ApiError("Could not extract enough article text from that page (it may be paywalled or "
                       "JavaScript-rendered). Please paste the article text manually.", 422, "EXTRACTION_FAILED")
    return article
