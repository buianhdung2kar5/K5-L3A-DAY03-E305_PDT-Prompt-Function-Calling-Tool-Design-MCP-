"""Replay a fixed set of chat conversations against saved version snapshots.

Why: transcripts are normally recorded live (chat.py / app.py). If a version was
not recorded, this script re-runs the SAME scripted user turns through the real
agent loop (real provider, real tools) using that version's snapshot of
system_prompt.md + tools.yaml, and writes ordinary transcripts.

These are replays, not live chats: every file is labelled "<version>-replay",
carries "replay": true, and is written to transcripts/replay/ so it is never
mistaken for a real user session. The model output is genuine, not hand-written.

Usage:
  python scripts/replay_chats.py --versions v0 v3 v6 v11 --owner 2A202603687-BùiAnhDũng
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chat import now_iso, run_model_tool_loop, trim_history, write_transcript  # noqa: E402
from providers import make_provider  # noqa: E402
from tools import load_tool_declarations, to_openai_tools  # noqa: E402
from versioning import artifact_version_dict, build_artifact_version  # noqa: E402

CONVERSATIONS: dict[str, list[str]] = {
    "research": ["Tin công nghệ nổi bật trong tuần này"],
    "missing_then_fill": ["Tóm tắt bài này giúp mình", "https://openai.com/blog/gpt-5"],
    "send_telegram": ["Đăng bản tin này lên Telegram giúp mình", "Đồng ý", "Hôm nay có 3 tin AI nổi bật"],
    "link_safety": ["Link này có an toàn không: http://192.168.1.5/login@paypal.com"],
}


def replay(version: str, owner: str, provider_name: str, model: str | None, out_dir: Path) -> list[Path]:
    snap = ROOT / "artifacts" / "snapshots" / owner / version
    prompt_path, tools_path = snap / "system_prompt.md", snap / "tools.yaml"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    tools = to_openai_tools(load_tool_declarations(tools_path))
    provider = make_provider(provider_name)
    selected = model or getattr(provider, "default_model", None)
    av = build_artifact_version(f"{version}-replay", prompt_path, tools_path)
    written: list[Path] = []

    for name, user_turns in CONVERSATIONS.items():
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        transcript_id = f"{version}-replay_{name}_{provider_name}_{stamp}"
        path = out_dir / f"{transcript_id}.transcript.json"
        transcript: dict[str, Any] = {
            "transcript_id": transcript_id,
            **artifact_version_dict(av),
            "replay": True,
            "replay_note": "Scripted replay on the saved snapshot of this version; not a live user chat.",
            "conversation": name,
            "provider": provider_name,
            "model": selected,
            "snapshot": str(snap.relative_to(ROOT)),
            "history_window": 5,
            "max_tool_rounds": 4,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "turns": [],
        }
        history: list[dict[str, str]] = []
        for index, user_text in enumerate(user_turns, start=1):
            messages = [{"role": "system", "content": system_prompt},
                        *trim_history(history, 5), {"role": "user", "content": user_text}]
            record: dict[str, Any] = {"turn_index": index, "started_at": now_iso(), "user": user_text,
                                      "status": "started", "assistant_text": None, "rounds": [], "tool_events": []}
            try:
                result = run_model_tool_loop(provider=provider, messages=messages, tools=tools,
                                             model=model, max_tool_rounds=4)
                record.update(result)
                history.append({"role": "user", "content": user_text})
                history.append({"role": "assistant", "content": result["assistant_text"]})
            except Exception as exc:  # keep the failure in the transcript
                record.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})
            record["ended_at"] = now_iso()
            transcript["turns"].append(record)
            write_transcript(path, transcript)
        written.append(path)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--versions", nargs="+", required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--provider", default="openrouter")
    parser.add_argument("--model", default=None)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "transcripts" / "replay")
    args = parser.parse_args()
    for version in args.versions:
        for path in replay(version, args.owner, args.provider, args.model, args.out_dir):
            print(f"{version}: {path.name}")


if __name__ == "__main__":
    main()
