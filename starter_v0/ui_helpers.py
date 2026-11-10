"""UI boundaries; the baseline prompt, tools and eval remain unchanged."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from providers.base import ToolCall

ROOT = Path(__file__).resolve().parent
MODEL = "gemini-3.5-flash-lite"
PROMPT = ROOT / "artifacts" / "v0" / "system_prompt.md"
TOOLS = ROOT / "artifacts" / "v0" / "tools.yaml"


def redact(value: Any) -> Any:
    """Remove configured credentials from displayed and persisted UI diagnostics."""
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        for key, secret in os.environ.items():
            if secret and any(marker in key for marker in ("API_KEY", "TOKEN", "SECRET", "PASSWORD", "CHAT_ID", "ACCESS_CODE")):
                value = value.replace(secret, "[redacted]")
        return re.sub(r"https://api\.telegram\.org/bot[^/\s]+", "https://api.telegram.org/bot[redacted]", value)
    return value


def guarded_executor(state: Any, execute: Callable) -> Callable:
    def run(call: ToolCall) -> dict[str, Any]:
        if call.name != "send":
            return redact(execute(call))
        text = call.args.get("text")
        if not isinstance(text, str) or not text.strip():
            result = {"awaiting_user": True, "question": "Bạn muốn gửi nội dung gì lên Telegram?"}
        else:
            # Model-supplied confirmed=true never authorizes a UI send.
            state["pending_send"] = text
            result = {"awaiting_user": True, "question": "Bản nháp đã sẵn sàng. Hãy xem nội dung và bấm xác nhận bên dưới.", "status": "pending_confirmation"}
        return {"tool": call.name, "args": redact(call.args), "result": result}
    return run


def resolve_send(state: Any, approved: bool, execute: Callable) -> dict[str, Any] | None:
    # Consume first: Streamlit reruns cannot submit the same approval twice.
    text = state.pop("pending_send", None)
    if text is None:
        return None
    if not approved:
        return {"tool": "send", "args": {}, "result": {"status": "cancelled"}}
    return redact(execute(ToolCall("send", {"text": text, "confirmed": True})))


def available_versions() -> list[str]:
    return [version for version in ('v3', 'v2', 'v1', 'v0')
            if (ROOT / 'artifacts' / version / 'tools.yaml').is_file()]


def load_runs() -> list[tuple[Path, dict[str, Any]]]:
    runs = []
    for path in sorted((ROOT / "runs").glob("v*_B_*_gemini_*.json"), reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("model") == MODEL:
                runs.append((path, data))
        except (OSError, ValueError):
            continue
    return runs
