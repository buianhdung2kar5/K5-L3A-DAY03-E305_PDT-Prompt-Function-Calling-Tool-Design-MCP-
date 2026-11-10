from __future__ import annotations

import ipaddress
from typing import Any
from urllib.parse import urlparse

from tools._shared import err

# Real domains of brands that phishing links often imitate. Only used to flag
# look-alike hosts such as "paypa1.com" or "paypal.com.evil.io".
BRANDS: dict[str, tuple[str, ...]] = {
    "google": ("google.com", "googleapis.com", "google.com.vn"),
    "paypal": ("paypal.com",),
    "facebook": ("facebook.com",),
    "apple": ("apple.com", "icloud.com"),
    "microsoft": ("microsoft.com", "live.com", "office.com"),
    "amazon": ("amazon.com",),
    "openai": ("openai.com",),
    "github": ("github.com",),
    "telegram": ("telegram.org", "t.me"),
}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "ow.ly", "cutt.ly"}
LEET = str.maketrans({"0": "o", "1": "l", "3": "e", "5": "s", "$": "s"})


def _is_real(host: str, real: tuple[str, ...]) -> bool:
    return any(host == d or host.endswith("." + d) for d in real)


def check_url(url: str = "") -> dict[str, Any]:
    """Statically inspect a URL string. Never opens the URL."""
    try:
        if not isinstance(url, str) or not url.strip():
            raise ValueError("url must be a non-empty string")
        raw = url.strip()
        parsed = urlparse(raw)
        reasons: list[str] = []
        warnings: list[str] = []

        if not parsed.scheme or not parsed.netloc and parsed.scheme in ("http", "https"):
            return {"tool": "check_url", "url": raw, "normalized_url": raw, "safe": False,
                    "verdict": "invalid", "reasons": ["not_a_full_url"], "warnings": []}

        if parsed.scheme not in ("http", "https"):
            reasons.append(f"scheme_not_allowed:{parsed.scheme}")
        host = (parsed.hostname or "").lower().rstrip(".")
        if not host:
            reasons.append("missing_host")
        try:
            port = parsed.port
        except ValueError:
            port = None
            reasons.append("invalid_port")

        if parsed.username is not None or "@" in parsed.netloc:
            reasons.append("userinfo_in_url")
        if host:
            try:
                ipaddress.ip_address(host)
                reasons.append("host_is_ip_address")
            except ValueError:
                pass
            if any(label.startswith("xn--") for label in host.split(".")):
                reasons.append("punycode_host")
            folded = host.translate(LEET)
            for brand, real in BRANDS.items():
                if brand in folded and not _is_real(host, real):
                    reasons.append(f"brand_lookalike:{brand}")
                    break
            if host in SHORTENERS:
                warnings.append("url_shortener")
            if host.count(".") >= 4:
                warnings.append("many_subdomains")
        if port not in (None, 80, 443):
            warnings.append(f"non_standard_port:{port}")
        if len(raw) > 200:
            warnings.append("very_long_url")

        verdict = "suspicious" if reasons else "safe"
        return {"tool": "check_url", "url": raw, "normalized_url": raw,
                "host": host, "safe": not reasons, "verdict": verdict,
                "reasons": reasons, "warnings": warnings}
    except Exception as exc:
        return err("check_url", exc)
