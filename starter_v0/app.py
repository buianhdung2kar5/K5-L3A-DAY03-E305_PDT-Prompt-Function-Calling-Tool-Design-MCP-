"""Streamlit chat UI for the Research Agent.

Run:   streamlit run app.py
Share: cloudflared tunnel --url http://localhost:8501   (see README, "Deploy nhanh")

It wraps the same model->tool loop that chat.py uses (run_model_tool_loop), so
behaviour matches the CLI and the eval. Every session writes a transcript to
transcripts/*.transcript.json in the same format as chat.py.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

# Tool progress lines use emoji; never let a narrow console encoding crash a turn.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass

from chat import json_text, now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).parent
SYSTEM_PROMPT_PATH = ROOT / "artifacts" / "system_prompt.md"
TOOLS_PATH = ROOT / "artifacts" / "tools.yaml"
TRANSCRIPTS_DIR = Path(os.getenv("RESEARCH_AGENT_TRANSCRIPTS_DIR") or ROOT / "transcripts")

PROVIDERS = ["openrouter", "openai", "anthropic", "gemini", "ollama"]
MAX_TURNS_PER_SESSION = 30  # protects your API credit when the link is shared
SAMPLE_QUESTIONS = [
    "Tweet mới nhất của Sam Altman là gì?",
    "Tin công nghệ nổi bật trong tuần này",
    "Hacker News đang bàn gì về Rust?",
    "Tóm tắt bài này giúp mình",
]

st.set_page_config(page_title="Research Agent E305_PDT", page_icon="🔎", layout="centered")


# ---------------------------------------------------------------- state

def init_state() -> None:
    st.session_state.setdefault("messages", [])      # what we render
    st.session_state.setdefault("history", [])       # what the model sees
    st.session_state.setdefault("turn_index", 0)
    st.session_state.setdefault("transcript", None)
    st.session_state.setdefault("transcript_path", None)


def reset_conversation() -> None:
    for key in ("messages", "history", "turn_index", "transcript", "transcript_path", "pending", "settings_signature"):
        st.session_state.pop(key, None)
    init_state()


def get_provider(name: str) -> Any:
    key = f"provider::{name}"
    if key not in st.session_state:
        st.session_state[key] = make_provider(name)
    return st.session_state[key]


def start_transcript(settings: dict[str, Any], model_name: str | None) -> None:
    artifact_version = build_artifact_version(settings["version"], SYSTEM_PROMPT_PATH, TOOLS_PATH)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(settings["version"]), safe_slug(settings["provider"]), timestamp])
    st.session_state.transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": settings["provider"],
        "model": model_name,
        "system_prompt": str(SYSTEM_PROMPT_PATH),
        "tools": str(TOOLS_PATH),
        "history_window": settings["window"],
        "max_tool_rounds": settings["rounds"],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "source": "streamlit_ui",
        "turns": [],
    }


# ---------------------------------------------------------------- rendering

def render_events(events: list[dict[str, Any]]) -> None:
    if not events:
        return
    with st.expander(f"🔧 Tool đã gọi ({len(events)})"):
        for event in events:
            st.markdown(f"**{event.get('tool')}**")
            st.code(json_text(event.get("args", {})), language="json")
            st.caption("Kết quả")
            st.code(json_text(event.get("result"), max_chars=3000), language="json")


def render_message(message: dict[str, Any]) -> None:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("status") == "waiting_for_user":
            st.caption("⏸ Agent đang hỏi lại, hãy trả lời ở khung bên dưới.")
        if message.get("status") in {"max_tool_rounds", "provider_error"}:
            st.caption(f"⚠ Trạng thái: {message['status']}")
        render_events(message.get("events", []))


# ---------------------------------------------------------------- sidebar

def sidebar() -> dict[str, Any]:
    with st.sidebar:
        st.header("Cài đặt")
        provider = st.selectbox("Provider", PROVIDERS, index=0)
        model = st.text_input("Model (để trống = mặc định)", value="")
        version = st.text_input("Nhãn version", value="ui", help="Ghi vào tên file transcript.")
        window = st.slider("Số cặp hội thoại nhớ lại", 1, 10, 5)
        rounds = st.slider("Số vòng tool tối đa", 1, 8, 4)
        st.caption("Đổi cài đặt giữa chừng vẫn giữ hội thoại; từ lượt sau sẽ ghi sang transcript mới.")
        if st.button("Xoá hội thoại", use_container_width=True):
            reset_conversation()
            st.rerun()

        st.divider()
        artifact_version = build_artifact_version(version, SYSTEM_PROMPT_PATH, TOOLS_PATH)
        st.caption(f"Artifact: `{artifact_version.artifact_version}`")
        tool_names = [t["name"] for t in load_tool_declarations(TOOLS_PATH)]
        with st.expander(f"Agent có {len(tool_names)} tool"):
            st.write(", ".join(f"`{n}`" for n in tool_names))
        st.caption(f"Giới hạn {MAX_TURNS_PER_SESSION} lượt mỗi phiên.")

        path = st.session_state.transcript_path
        if path and Path(path).exists():
            st.download_button("Tải transcript (JSON)", Path(path).read_bytes(),
                               file_name=Path(path).name, mime="application/json", use_container_width=True)
    return {"provider": provider, "model": model.strip() or None, "version": version.strip() or "ui",
            "window": window, "rounds": rounds}


# ---------------------------------------------------------------- one turn

def run_turn(user_text: str, settings: dict[str, Any]) -> None:
    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    tools = to_openai_tools(load_tool_declarations(TOOLS_PATH))

    st.session_state.messages.append({"role": "user", "content": user_text})
    render_message(st.session_state.messages[-1])

    try:
        provider = get_provider(settings["provider"])
    except Exception as exc:  # missing SDK or key
        _append_assistant(f"Không khởi tạo được provider `{settings['provider']}`: {type(exc).__name__}: {exc}",
                          status="provider_error")
        return

    model_name = settings["model"] or getattr(provider, "default_model", None)
    signature = (settings["provider"], model_name, settings["version"], settings["window"], settings["rounds"])
    if st.session_state.get("settings_signature") != signature:
        st.session_state.transcript = None  # settings changed: log the next turns to a new transcript
        st.session_state.settings_signature = signature
    if st.session_state.transcript is None:
        start_transcript(settings, model_name)

    st.session_state.turn_index += 1
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, settings["window"]),
        {"role": "user", "content": user_text},
    ]
    record: dict[str, Any] = {
        "turn_index": st.session_state.turn_index, "started_at": now_iso(), "user": user_text,
        "status": "started", "assistant_text": None, "rounds": [], "tool_events": [],
    }

    with st.chat_message("assistant"):
        with st.spinner("Agent đang xử lý..."):
            try:
                result = run_model_tool_loop(provider=provider, messages=messages, tools=tools,
                                             model=settings["model"], max_tool_rounds=settings["rounds"])
                record.update(result)
                st.session_state.history += [{"role": "user", "content": user_text},
                                             {"role": "assistant", "content": result["assistant_text"]}]
                reply = {"role": "assistant", "content": result["assistant_text"],
                         "status": result["status"], "events": result["tool_events"]}
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                record.update({"status": "provider_error", "error": error})
                reply = {"role": "assistant", "content": f"Lỗi khi gọi model: {error}",
                         "status": "provider_error", "events": []}
    st.session_state.messages.append(reply)

    record["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(record)
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)
    st.rerun()


def _append_assistant(text: str, *, status: str) -> None:
    message = {"role": "assistant", "content": text, "status": status, "events": []}
    st.session_state.messages.append(message)
    render_message(message)


# ---------------------------------------------------------------- page

def main() -> None:
    init_state()
    settings = sidebar()

    st.title("🔎 Research Agent")
    st.caption("Team E305_PDT · hỏi tin tức, tweet, bài báo, Hacker News; agent chọn tool và trả lời kèm nguồn.")

    for message in st.session_state.messages:
        render_message(message)

    if not st.session_state.messages:
        st.write("Thử một câu hỏi mẫu:")
        for index, question in enumerate(SAMPLE_QUESTIONS):
            if st.button(question, key=f"sample-{index}", use_container_width=True):
                st.session_state.pending = question
                st.rerun()

    limit_reached = st.session_state.turn_index >= MAX_TURNS_PER_SESSION
    if limit_reached:
        st.warning(f"Đã đạt giới hạn {MAX_TURNS_PER_SESSION} lượt. Bấm “Xoá hội thoại” để bắt đầu lại.")
    typed = st.chat_input("Nhập câu hỏi cho agent...", disabled=limit_reached)
    user_text = st.session_state.pop("pending", None) or typed
    if user_text and not limit_reached:
        run_turn(user_text.strip(), settings)


main()
