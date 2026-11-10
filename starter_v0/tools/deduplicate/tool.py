from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from tools._shared import err


def canonical_url(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Each item needs a nonempty HTTP(S) URL")
    parts = urlsplit(url.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        raise ValueError("Only HTTP(S) URLs without credentials are accepted")
    # Accessing port validates malformed ports too.
    port = parts.port
    host = parts.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    if port and (parts.scheme.lower(), port) not in {("http", 80), ("https", 443)}:
        host += f":{port}"
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}]
    # Preserve path case, scheme, meaningful query parameters and trailing slash.
    return urlunsplit((parts.scheme.lower(), host, parts.path or "/", urlencode(sorted(query)), ""))


def deduplicate_sources(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Remove duplicate URLs locally without changing the first source item."""
    try:
        if not isinstance(items, list) or len(items) > 200:
            raise ValueError("items must be a list of at most 200 source objects")
        unique: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("Every item must be an object with a URL")
            key = canonical_url(item.get("url"))
            if key not in seen:
                seen.add(key)
                unique.append(dict(item))
        return {"tool": "deduplicate_sources", "items": unique,
                "input_count": len(items), "item_count": len(unique),
                "duplicate_count": len(items) - len(unique)}
    except Exception as exc:
        return err("deduplicate_sources", exc)
