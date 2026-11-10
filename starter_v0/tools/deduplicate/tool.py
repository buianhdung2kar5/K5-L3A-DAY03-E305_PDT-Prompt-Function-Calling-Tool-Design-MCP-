from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from tools._shared import err


def _source_key(url: str) -> str:
    if not url or any(char.isspace() or ord(char) < 32 for char in url):
        raise ValueError("Each source needs a valid HTTP/HTTPS URL")
    parsed = urlsplit(url)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None):
        raise ValueError("Each source needs a valid HTTP/HTTPS URL without credentials")
    try:
        parsed.port  # Validate malformed or out-of-range ports without fetching.
    except ValueError:
        raise ValueError("Source URL has an invalid port") from None
    query = urlencode([(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True)
                       if not key.lower().startswith("utm_")])
    return urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path or "/", query, ""))


def deduplicate_sources(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Keep the first source per URL; never fetch URLs or mutate input records."""
    try:
        if not isinstance(items, list):
            raise TypeError("items must be a list of source objects")
        unique: list[dict[str, Any]] = []
        seen: set[str] = set()
        for index, item in enumerate(items):
            if not isinstance(item, dict) or not isinstance(item.get("url"), str):
                raise ValueError(f"items[{index}] must be an object with a string URL")
            key = _source_key(item["url"])
            if key not in seen:
                seen.add(key)
                unique.append(dict(item))
        return {"tool": "deduplicate", "items": unique, "input_count": len(items),
                "unique_count": len(unique), "duplicates_removed": len(items) - len(unique)}
    except (TypeError, ValueError):
        # Avoid returning the input URL, which might contain credentials.
        return err("deduplicate", ValueError("Invalid sources: use a list of objects with valid HTTP/HTTPS URLs without credentials"))
