"""TODO(student): Tool Unit Test Challenge.

Each test below is a stub. Replace `pytest.skip(...)` with a real test.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS  # noqa: F401

TODO = "TODO(student): implement this test"


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    # Call clarify with response_type="choice" and 2 options.
    # Assert: options are returned unchanged, awaiting_user is True.
    pytest.skip(TODO)


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    # Items with section "A", "B", "A" -> markdown has exactly one "## A" and one "## B".
    pytest.skip(TODO)


def test_format_thread_numbers_items() -> None:
    # template="thread" -> lines start with "1/", "2/", ...
    pytest.skip(TODO)


def test_format_empty_items_does_not_crash() -> None:
    # items=None and items=[] -> item_count == 0, no exception.
    pytest.skip(TODO)


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    # Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID, mock HTTP.
    # Assert: exactly one POST, URL contains the token, json has chat_id + text, status == "sent".
    pytest.skip(TODO)


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    pytest.skip(TODO)


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    # timeframe=None -> request body has no "time_range" key.
    pytest.skip(TODO)


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    # Mock {"data": {"markdown": "...", "metadata": {"title": "T", "sourceURL": "https://..."}}}
    # Assert title/url/source/summary in result["items"][0].
    pytest.skip(TODO)


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    pytest.skip(TODO)


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    # Mock {"timeline": [...]} with 1 item missing tweet_id and 6 valid items, limit=3.
    # Assert 3 items, and each url looks like https://x.com/<handle>/status/<id>.
    pytest.skip(TODO)


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    # Assert the request params carry the query and search_type ("Top" / "Latest").
    pytest.skip(TODO)


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    pytest.skip(TODO)


def test_policy_area_filter_only_returns_that_area() -> None:
    # policy_area="data_privacy" -> every result has policy_area == "data_privacy".
    pytest.skip(TODO)


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    # One policy file contains a quoted line that tries to give the assistant orders.
    # Query that section (source_citation) and assert: that line is in untrusted_text, NOT in facts.
    pytest.skip(TODO)


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

def test_my_new_tool_happy_path() -> None:
    pytest.skip(TODO)


def test_my_new_tool_bad_input_from_model() -> None:
    pytest.skip(TODO)


def test_my_new_tool_failure_returns_error_dict() -> None:
    pytest.skip(TODO)


# ---------------- url_check (new team tool) ----------------

def test_url_check_clean_https_url_is_safe() -> None:
    result = TOOL_FUNCTIONS["url_check"](url="https://openai.com/blog/gpt-5")
    assert result["verdict"] == "safe"
    assert result["safe"] is True
    assert result["reasons"] == []


def test_url_check_flags_ip_host_and_userinfo_as_suspicious() -> None:
    result = TOOL_FUNCTIONS["url_check"](url="http://192.168.1.5/login@paypal.com")
    assert result["verdict"] == "suspicious"
    assert result["safe"] is False
    assert "host_is_ip_address" in result["reasons"]


def test_url_check_flags_non_http_scheme() -> None:
    result = TOOL_FUNCTIONS["url_check"](url="javascript:alert(1)")
    assert result["safe"] is False
    assert any(r.startswith("scheme_not_allowed") for r in result["reasons"])


def test_url_check_flags_brand_lookalike_but_not_the_real_domain() -> None:
    fake = TOOL_FUNCTIONS["url_check"](url="https://paypa1.com/signin")
    real = TOOL_FUNCTIONS["url_check"](url="https://www.paypal.com/signin")
    assert "brand_lookalike:paypal" in fake["reasons"]
    assert real["verdict"] == "safe"


def test_url_check_vague_text_is_invalid_not_a_crash() -> None:
    result = TOOL_FUNCTIONS["url_check"](url="link ở trên ấy")
    assert result["verdict"] == "invalid"
    assert result["safe"] is False


def test_url_check_empty_and_wrong_type_return_error_dict() -> None:
    assert "error" in TOOL_FUNCTIONS["url_check"](url="")
    assert "error" in TOOL_FUNCTIONS["url_check"](url=None)  # type: ignore[arg-type]


def test_url_check_shortener_is_a_warning_not_a_block() -> None:
    result = TOOL_FUNCTIONS["url_check"](url="https://bit.ly/abc123")
    assert result["safe"] is True
    assert "url_shortener" in result["warnings"]


# ---------------- time_now (new team tool) ----------------

def _fixed_now(monkeypatch, year: int, month: int, day: int) -> None:
    from datetime import datetime

    from tools.time_now import tool as time_tool

    monkeypatch.setattr(time_tool, "_now", lambda: datetime(year, month, day, 9, 30, tzinfo=time_tool.VN_TZ))


def test_time_now_today_returns_vietnam_date_and_weekday(monkeypatch) -> None:
    _fixed_now(monkeypatch, 2026, 11, 10)
    result = TOOL_FUNCTIONS["time_now"](when="today")
    assert result["date"] == "2026-11-10"
    assert result["weekday"] == "Thứ Ba"
    assert result["start"] == result["end"] == "2026-11-10"
    assert result["now"].endswith("+07:00")


def test_time_now_this_week_runs_monday_to_sunday(monkeypatch) -> None:
    _fixed_now(monkeypatch, 2026, 11, 10)
    result = TOOL_FUNCTIONS["time_now"](when="this_week")
    assert (result["start"], result["end"]) == ("2026-11-09", "2026-11-15")


def test_time_now_yesterday_and_last_7_days(monkeypatch) -> None:
    _fixed_now(monkeypatch, 2026, 11, 10)
    yesterday = TOOL_FUNCTIONS["time_now"](when="yesterday")
    week = TOOL_FUNCTIONS["time_now"](when="last_7_days")
    assert yesterday["start"] == yesterday["end"] == "2026-11-09"
    assert (week["start"], week["end"]) == ("2026-11-04", "2026-11-10")


def test_time_now_this_month_handles_december_wrap(monkeypatch) -> None:
    _fixed_now(monkeypatch, 2026, 12, 15)
    result = TOOL_FUNCTIONS["time_now"](when="this_month")
    assert (result["start"], result["end"]) == ("2026-12-01", "2026-12-31")


def test_time_now_timeframe_hint_matches_lookup_enum(monkeypatch) -> None:
    _fixed_now(monkeypatch, 2026, 11, 10)
    allowed = {"day", "week", "month", "year"}
    for when in ("now", "today", "yesterday", "this_week", "last_7_days", "this_month"):
        assert TOOL_FUNCTIONS["time_now"](when=when)["timeframe_hint"] in allowed


def test_time_now_unknown_when_returns_error_dict_not_raise() -> None:
    result = TOOL_FUNCTIONS["time_now"](when="next_year")
    assert result["error"] == "ValueError"
    assert "tool" in result


# ---------------- save_note (new team tool, write action) ----------------

def _notes_dir(monkeypatch, tmp_path):
    from tools.save_note import tool as note_tool

    monkeypatch.setattr(note_tool, "NOTES_DIR", tmp_path / "notes")
    monkeypatch.setattr(note_tool, "_stamp", lambda: "20261110T100000")
    return tmp_path / "notes"


def test_save_note_without_confirmation_writes_nothing(monkeypatch, tmp_path) -> None:
    notes = _notes_dir(monkeypatch, tmp_path)
    result = TOOL_FUNCTIONS["save_note"](text="Họp nhóm 9h sáng mai")
    assert result["status"] == "needs_confirmation"
    assert not notes.exists()


def test_save_note_string_confirmed_is_rejected_unlike_a_truthy_check(monkeypatch, tmp_path) -> None:
    notes = _notes_dir(monkeypatch, tmp_path)
    for bad in ("false", "no", "true", "0", 1):
        result = TOOL_FUNCTIONS["save_note"](text="x", confirmed=bad)
        assert result["status"] == "needs_confirmation"
    assert not notes.exists()


def test_save_note_confirmed_writes_title_and_text(monkeypatch, tmp_path) -> None:
    notes = _notes_dir(monkeypatch, tmp_path)
    result = TOOL_FUNCTIONS["save_note"](text="Họp nhóm 9h sáng mai", title="Lịch họp", confirmed=True)
    assert result["status"] == "saved"
    files = list(notes.glob("*.md"))
    assert len(files) == 1
    assert files[0].name == "20261110T100000_lich-hop.md"
    assert files[0].read_text(encoding="utf-8") == "# Lịch họp\n\nHọp nhóm 9h sáng mai\n"


def test_save_note_title_cannot_escape_the_notes_folder(monkeypatch, tmp_path) -> None:
    notes = _notes_dir(monkeypatch, tmp_path)
    TOOL_FUNCTIONS["save_note"](text="x", title="../../etc/passwd Họp!", confirmed=True)
    files = list(tmp_path.rglob("*.md"))
    assert len(files) == 1 and files[0].parent == notes
    assert "/" not in files[0].name and ".." not in files[0].name


def test_save_note_empty_or_oversized_text_returns_error_and_writes_nothing(monkeypatch, tmp_path) -> None:
    notes = _notes_dir(monkeypatch, tmp_path)
    assert "error" in TOOL_FUNCTIONS["save_note"](text="   ", confirmed=True)
    assert "error" in TOOL_FUNCTIONS["save_note"](text="a" * 20001, confirmed=True)
    assert "error" in TOOL_FUNCTIONS["save_note"](text=None, confirmed=True)  # type: ignore[arg-type]
    assert not notes.exists()


def test_save_note_never_overwrites_an_existing_note(monkeypatch, tmp_path) -> None:
    notes = _notes_dir(monkeypatch, tmp_path)
    TOOL_FUNCTIONS["save_note"](text="first", title="Same", confirmed=True)
    TOOL_FUNCTIONS["save_note"](text="second", title="Same", confirmed=True)
    contents = sorted(path.read_text(encoding="utf-8") for path in notes.glob("*.md"))
    assert len(contents) == 2
    assert "first" in contents[0] + contents[1] and "second" in contents[0] + contents[1]

