from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from tools._shared import ROOT, err, fold_text

NOTES_DIR = ROOT / "notes"
MAX_CHARS = 20000


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def _slug(title: str, text: str) -> str:
    """ASCII-only file-name part: no path separators, no dots, at most 40 chars."""
    source = title.strip() or text.strip().splitlines()[0]
    slug = re.sub(r"[^a-z0-9]+", "-", fold_text(source)).strip("-")
    return slug[:40].strip("-") or "note"


def _free_path(directory: Path, stamp: str, slug: str) -> Path:
    path = directory / f"{stamp}_{slug}.md"
    counter = 2
    while path.exists():
        path = directory / f"{stamp}_{slug}-{counter}.md"
        counter += 1
    return path


def save_note(text: str = "", title: str = "", confirmed: bool = False) -> dict[str, Any]:
    """Write a note to notes/. A write action: only runs when confirmed is exactly True."""
    # Strict check on purpose: a truthy string such as "false" must NOT count as confirmation.
    if confirmed is not True:
        return {
            "tool": "save_note",
            "status": "needs_confirmation",
            "message": "Only save after the user explicitly confirms (confirmed must be the boolean true).",
        }
    try:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")
        if len(text) > MAX_CHARS:
            raise ValueError(f"text is longer than {MAX_CHARS} characters")
        title = title if isinstance(title, str) else ""
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        path = _free_path(NOTES_DIR, _stamp(), _slug(title, text))
        body = (f"# {title.strip()}\n\n" if title.strip() else "") + text.strip() + "\n"
        path.write_text(body, encoding="utf-8")
        try:
            shown = str(path.relative_to(ROOT))
        except ValueError:
            shown = str(path)
        return {"tool": "save_note", "status": "saved", "path": shown, "chars": len(text.strip())}
    except Exception as exc:
        return err("save_note", exc)
