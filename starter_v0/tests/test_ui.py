"""Offline UI integration checks, not live-chat evidence."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import chat
import providers
from conftest import FakeResponse
from providers.base import ModelResponse, ToolCall
from ui_helpers import guarded_executor, redact, resolve_send


APP = Path(__file__).resolve().parents[1] / "app.py"


def test_model_confirmation_cannot_send_and_approval_is_consumed_once():
    state, calls = {}, []
    def execute(call):
        calls.append(call)
        return {"tool": call.name, "args": call.args, "result": {"status": "sent"}}
    result = chat.run_model_tool_loop(
        provider=type("Provider", (), {"complete": lambda *a, **k: ModelResponse(tool_calls=[
            ToolCall("send", {"text": "Exact draft", "confirmed": True})])})(),
        messages=[], tools=[], model="offline", max_tool_rounds=2,
        tool_executor=guarded_executor(state, execute),
    )
    assert result["status"] == "waiting_for_user"
    assert calls == []
    assert resolve_send(state, True, execute)["result"]["status"] == "sent"
    assert calls[0].args == {"text": "Exact draft", "confirmed": True}
    assert resolve_send(state, True, execute) is None
    assert len(calls) == 1


def test_empty_draft_and_cancellation_never_execute():
    state = {}
    def forbidden(call):
        pytest.fail("No send should execute")
    event = guarded_executor(state, forbidden)(ToolCall("send", {"text": " "}))
    assert event["result"]["awaiting_user"]
    assert "pending_send" not in state
    state["pending_send"] = "Draft"
    assert resolve_send(state, False, forbidden)["result"]["status"] == "cancelled"
    assert "pending_send" not in state


def test_secret_redaction_in_nested_tool_errors(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "unit-secret-value")
    result = redact({"events": [{"error": "unit-secret-value https://api.telegram.org/bot123:private/sendMessage"}]})
    assert "unit-secret-value" not in str(result)
    assert "123:private" not in str(result)


@pytest.fixture
def ui(monkeypatch):
    monkeypatch.delenv('UI_ACCESS_CODE', raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "offline-only")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "offline-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "offline-chat")
    class Provider:
        def complete(self, *args, **kwargs):
            return ModelResponse(tool_calls=[ToolCall("send", {"text": "Nội dung cần duyệt", "confirmed": True})])
    monkeypatch.setattr(providers, "make_provider", lambda _: Provider())
    saved = []
    monkeypatch.setattr(chat, "write_transcript", lambda path, data: saved.append(data))
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not app.exception
    return app, saved


def test_ui_renders_baseline_and_guards_real_send(ui, fake_http):
    app, saved = ui
    calls = fake_http(FakeResponse({"ok": True}))
    assert len(app.metric) == 4
    app.chat_input[0].set_value("Gửi bản tin lên Telegram").run()
    assert not app.exception
    assert calls == []
    assert app.session_state["pending_send"] == "Nội dung cần duyệt"
    next(button for button in app.button if button.label == "Xác nhận gửi").click().run()
    assert not app.exception
    assert len(calls) == 1
    assert calls[0]["json"]["text"] == "Nội dung cần duyệt"
    assert saved[-1]["turns"][-1]["status"] == "sent"
    app.run()
    assert len(calls) == 1


def test_ui_cancel_does_not_send(ui, fake_http):
    app, saved = ui
    calls = fake_http(FakeResponse({"ok": True}))
    app.chat_input[0].set_value("Gửi tin").run()
    next(button for button in app.button if button.label == "Hủy gửi").click().run()
    assert not app.exception
    assert calls == []
    assert saved[-1]["turns"][-1]["status"] == "cancelled"


def test_public_ui_requires_access_code_before_showing_data(monkeypatch):
    monkeypatch.setenv('UI_ACCESS_CODE', 'offline-access-code')
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not app.exception
    assert len(app.chat_input) == 0
    assert len(app.metric) == 0
    app.text_input[0].set_value('wrong')
    app.button[0].click().run()
    assert app.error
    assert len(app.chat_input) == 0
    app.text_input[0].set_value('offline-access-code')
    app.button[0].click().run()
    assert not app.exception
    assert len(app.chat_input) == 1
