"""Headless tests for the Streamlit UI (app.py). Offline: a fake provider replaces the model."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from providers.base import ModelResponse, ToolCall  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "app.py")


class FakeProvider:
    default_model = "fake-model"

    def __init__(self, responses: list[ModelResponse]) -> None:
        self.responses = list(responses)

    def complete(self, messages, tools=None, *, model=None, temperature=0.0, tool_choice=None) -> ModelResponse:
        return self.responses.pop(0)


def _run_app(monkeypatch, tmp_path, provider_factory) -> AppTest:
    monkeypatch.setenv("RESEARCH_AGENT_TRANSCRIPTS_DIR", str(tmp_path))
    monkeypatch.setattr("providers.make_provider", provider_factory)
    app = AppTest.from_file(APP, default_timeout=30)
    app.run()
    return app


def test_app_starts_with_title_and_sample_questions(monkeypatch, tmp_path) -> None:
    app = _run_app(monkeypatch, tmp_path, lambda name: FakeProvider([]))

    assert not app.exception
    assert "Research Agent" in app.title[0].value
    assert len(app.button) >= 4  # the sample questions (plus the sidebar reset button)


def test_app_clarify_turn_waits_for_user_and_writes_transcript(monkeypatch, tmp_path) -> None:
    clarify = ToolCall("clarify", {"question": "Bạn muốn xem tài khoản nào?", "response_type": "text"})
    provider = FakeProvider([ModelResponse(text=None, tool_calls=[clarify])])
    app = _run_app(monkeypatch, tmp_path, lambda name: provider)

    app.chat_input[0].set_value("Tóm tắt 5 tweet mới nhất").run()

    assert not app.exception
    texts = [message.markdown[0].value for message in app.chat_message]
    assert texts[0] == "Tóm tắt 5 tweet mới nhất"
    assert texts[1] == "Bạn muốn xem tài khoản nào?"

    files = list(tmp_path.glob("*.transcript.json"))
    assert len(files) == 1
    transcript = json.loads(files[0].read_text(encoding="utf-8"))
    assert transcript["source"] == "streamlit_ui"
    assert transcript["model"] == "fake-model"
    assert transcript["turns"][0]["status"] == "waiting_for_user"
    assert transcript["turns"][0]["tool_events"][0]["tool"] == "clarify"


def test_app_plain_answer_is_shown_and_history_is_kept(monkeypatch, tmp_path) -> None:
    provider = FakeProvider([ModelResponse(text="Mình là research agent.", tool_calls=[]),
                             ModelResponse(text="Có 10 tool.", tool_calls=[])])
    app = _run_app(monkeypatch, tmp_path, lambda name: provider)

    app.chat_input[0].set_value("Bạn là gì?").run()
    app.chat_input[0].set_value("Có bao nhiêu tool?").run()

    assert not app.exception
    assert len(app.chat_message) == 4
    assert app.chat_message[3].markdown[0].value == "Có 10 tool."
    transcript = json.loads(next(tmp_path.glob("*.transcript.json")).read_text(encoding="utf-8"))
    assert [turn["turn_index"] for turn in transcript["turns"]] == [1, 2]


def test_app_provider_failure_is_shown_instead_of_crashing(monkeypatch, tmp_path) -> None:
    def broken(name):
        raise RuntimeError("Missing OPENROUTER_API_KEY")

    app = _run_app(monkeypatch, tmp_path, broken)
    app.chat_input[0].set_value("xin chào").run()

    assert not app.exception
    assert "Missing OPENROUTER_API_KEY" in app.chat_message[1].markdown[0].value
    assert list(tmp_path.glob("*.transcript.json")) == []


def test_app_settings_stay_editable_and_changing_them_starts_a_new_transcript(monkeypatch, tmp_path) -> None:
    provider = FakeProvider([ModelResponse(text="một", tool_calls=[]), ModelResponse(text="hai", tool_calls=[])])
    app = _run_app(monkeypatch, tmp_path, lambda name: provider)

    app.chat_input[0].set_value("câu 1").run()
    assert all(not widget.disabled for widget in app.sidebar.text_input)  # not locked after a turn

    app.sidebar.text_input[1].set_value("ui-b").run()  # [0]=model, [1]=version label
    app.chat_input[0].set_value("câu 2").run()

    assert not app.exception
    assert len(app.chat_message) == 4  # conversation kept
    assert len(list(tmp_path.glob("*.transcript.json"))) == 2
