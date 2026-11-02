"""Publisher / domain assessment backed by a configurable JSON source database (backend/data/sources.json).

An unlisted domain is reported as "unlisted" - never as fake or untrustworthy.
"""
import json
import logging
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse

from config import Config
from services.url_extractor import is_public_ip

log = logging.getLogger("truthlens.source")
_SECOND_LEVEL = {"co.uk", "org.uk", "ac.uk", "gov.uk", "co.in", "org.in", "gov.in", "ac.in", "com.au", "co.jp", "co.nz",
                 "com.br", "co.za"}

_db = None


def _load_db():
    global _db
    if _db is None:
        try:
            _db = json.loads(Config.SOURCES_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            log.warning("Could not read sources database: %s", exc)
            _db = {"sources": {}, "categories": {}, "fact_checking_references": []}
    return _db


def extract_domain(value: str):
    """Return the lower-case hostname (without 'www.') from a URL or bare domain, or None."""
    if not value:
        return None
    value = value.strip()
    parsed = urlparse(value if "://" in value else "https://" + value)
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host or "." not in host:
        return None
    return host[4:] if host.startswith("www.") else host


def registrable_domain(host: str) -> str:
    parts = host.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in _SECOND_LEVEL:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def lookup_reputation(host: str):
    db = _load_db()
    sources = db["sources"]
    candidates = [host, registrable_domain(host)]
    parts = host.split(".")
    candidates += [".".join(parts[i:]) for i in range(len(parts) - 1)]
    for c in candidates:
        if c in sources:
            entry = sources[c]
            return {"listed": True, "matched_domain": c, "name": entry["name"], "category": entry["category"],
                    "category_description": db["categories"].get(entry["category"], ""),
                    "country": entry.get("country")}
    return {"listed": False, "matched_domain": None, "name": None, "category": "unlisted",
            "category_description": "This domain is not in the local source database. "
                                    "That does not mean it is unreliable - it simply has not been assessed here.",
            "country": None}


def tls_info(host: str, timeout: float = 4.0):
    """Read the TLS certificate of a public host (handshake only). Returns {available: False,...} on any problem."""
    try:
        addrs = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
        ip = addrs[0][4][0]
        if not all(is_public_ip(a[4][0]) for a in addrs):
            return {"available": False, "reason": "Host resolves to a non-public address."}
        ctx = ssl.create_default_context()
        with socket.create_connection((ip, 443), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as tls:
                cert = tls.getpeercert()
        def flat(rdn):
            return {k: v for t in rdn for (k, v) in t}
        subject, issuer = flat(cert.get("subject", ())), flat(cert.get("issuer", ()))
        not_after = cert.get("notAfter")
        expires = None
        if not_after:
            expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc).isoformat()
        return {"available": True, "valid": True, "subject_common_name": subject.get("commonName"),
                "subject_organization": subject.get("organizationName"),
                "issuer": issuer.get("organizationName") or issuer.get("commonName"), "expires": expires}
    except ssl.SSLCertVerificationError as exc:
        return {"available": True, "valid": False, "reason": f"Certificate verification failed: {exc.verify_message}"}
    except Exception as exc:
        return {"available": False, "reason": f"TLS check unavailable ({exc.__class__.__name__})."}


def assess_source(value: str, deep: bool = False, scheme_hint: str = None, site_name: str = None):
    """Build the source assessment. `deep=True` performs a live TLS handshake (used by the Source Credibility page)."""
    host = extract_domain(value)
    if not host:
        return {"available": False, "reason": "No publisher domain could be determined (pasted text has no URL)."}
    rep = lookup_reputation(host)
    scheme = scheme_hint or (urlparse(value).scheme if "://" in value else None)
    result = {
        "available": True,
        "domain": host,
        "registrable_domain": registrable_domain(host),
        "https": (scheme == "https") if scheme else None,
        "publisher_name": rep["name"] or site_name,
        "publisher_name_source": "source database" if rep["name"] else ("page metadata" if site_name else None),
        "reputation": rep,
        "fact_checking_references": _load_db().get("fact_checking_references", []),
        "disclaimer": "Source information is a starting point and is not a verdict on any individual article.",
    }
    if deep:
        tls = tls_info(host)
        result["tls"] = tls
        if tls.get("available"):
            result["https"] = bool(tls.get("valid"))
            if not result["publisher_name"] and tls.get("subject_organization"):
                result["publisher_name"] = tls["subject_organization"]
                result["publisher_name_source"] = "TLS certificate organisation"
    # Plain-English assessment, deliberately not a score
    cat = rep["category"]
    if cat == "satire":
        result["assessment"] = "Known satire publication - content is not intended as factual reporting."
    elif cat == "fact_checker":
        result["assessment"] = "Listed as a fact-checking organisation."
    elif rep["listed"]:
        result["assessment"] = f"Listed in the source database as: {cat.replace('_', ' ')}."
    else:
        result["assessment"] = "Unlisted source - no reputation information available locally."
    if result["https"] is False:
        result["assessment"] += " The site is not served over valid HTTPS."
    return result
