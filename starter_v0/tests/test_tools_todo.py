"""Completed offline tool challenge, including the new deduplicate tool."""
from __future__ import annotations

import pytest

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS  # noqa: F401
from tools.deduplicate.tool import deduplicate_sources



# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    # Call clarify with response_type="choice" and 2 options.
    # Assert: options are returned unchanged, awaiting_user is True.
    result = TOOL_FUNCTIONS['clarify']('Choose?', response_type='choice', options=['A', 'B'])
    assert result['options'] == ['A', 'B']
    assert result['awaiting_user'] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    # Items with section "A", "B", "A" -> markdown has exactly one "## A" and one "## B".
    result = TOOL_FUNCTIONS['format']([{'summary': 'one', 'section': 'A'}, {'summary': 'two', 'section': 'B'}, {'summary': 'three', 'section': 'A'}])
    assert result['markdown'].count('## A') == 1
    assert result['markdown'].count('## B') == 1
    assert result['item_count'] == 3


def test_format_thread_numbers_items() -> None:
    # template="thread" -> lines start with "1/", "2/", ...
    result = TOOL_FUNCTIONS['format']([{'summary': 'one'}, {'summary': 'two'}], template='thread')
    assert result['markdown'].startswith('1/ one')
    assert '\n\n2/ two' in result['markdown']


def test_format_empty_items_does_not_crash() -> None:
    # items=None and items=[] -> item_count == 0, no exception.
    for items in (None, []):
        result = TOOL_FUNCTIONS['format'](items)
        assert result['item_count'] == 0
        assert 'error' not in result


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    # Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID, mock HTTP.
    # Assert: exactly one POST, URL contains the token, json has chat_id + text, status == "sent".
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'fake-token')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', 'fake-chat')
    calls = fake_http(FakeResponse({'ok': True}))
    result = TOOL_FUNCTIONS['send']('draft', confirmed=True)
    assert result['status'] == 'sent'
    assert len(calls) == 1
    assert calls[0]['method'] == 'POST'
    assert calls[0]['url'] == 'https://api.telegram.org/botfake-token/sendMessage'
    assert calls[0]['json']['chat_id'] == 'fake-chat'
    assert calls[0]['json']['text'] == 'draft'


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse())
    result = TOOL_FUNCTIONS['send']('draft', confirmed=True)
    assert result['error'] == 'RuntimeError'
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    # timeframe=None -> request body has no "time_range" key.
    monkeypatch.setenv('TAVILY_API_KEY', 'fake')
    calls = fake_http(FakeResponse({'results': []}))
    result = TOOL_FUNCTIONS['lookup']('AI', timeframe=None)
    assert 'error' not in result
    assert 'time_range' not in calls[0]['json']


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    # Mock {"data": {"markdown": "...", "metadata": {"title": "T", "sourceURL": "https://..."}}}
    # Assert title/url/source/summary in result["items"][0].
    monkeypatch.setenv('FIRECRAWL_API_KEY', 'fake')
    calls = fake_http(FakeResponse({'data': {'markdown': 'article', 'metadata': {'title': 'T', 'sourceURL': 'https://example.org/article'}}}))
    result = TOOL_FUNCTIONS['fetch']('https://example.org/article')
    assert result['items'][0] == {'title': 'T', 'url': 'https://example.org/article', 'source': 'example.org', 'summary': 'article'}
    assert calls[0]['json'] == {'url': 'https://example.org/article', 'formats': ['markdown']}


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv('FIRECRAWL_API_KEY', 'fake')
    fake_http(FakeResponse({'data': {'markdown': 'x' * 4500}}))
    assert len(TOOL_FUNCTIONS['fetch']('https://example.org')['items'][0]['summary']) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    # Mock {"timeline": [...]} with 1 item missing tweet_id and 6 valid items, limit=3.
    # Assert 3 items, and each url looks like https://x.com/<handle>/status/<id>.
    monkeypatch.setenv('RAPIDAPI_KEY', 'fake')
    calls = fake_http(FakeResponse({'timeline': [{'text': 'missing id'}] + [{'tweet_id': str(i), 'screen_name': 'test', 'text': f'post {i}'} for i in range(6)]}))
    result = TOOL_FUNCTIONS['timeline']('test', limit=3)
    assert [item['url'] for item in result['items']] == [f'https://x.com/test/status/{i}' for i in range(3)]
    assert calls[0]['params'] == {'screenname': 'test'}


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    # Assert the request params carry the query and search_type ("Top" / "Latest").
    monkeypatch.setenv('RAPIDAPI_KEY', 'fake')
    calls = fake_http(FakeResponse({'timeline': []}))
    for search_type in ('Top', 'Latest'):
        TOOL_FUNCTIONS['social_search']('robotics', search_type=search_type)
    assert [call['params'] for call in calls] == [{'query': 'robotics', 'search_type': kind} for kind in ('Top', 'Latest')]


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    assert TOOL_FUNCTIONS['policy']('')['results'] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    # policy_area="data_privacy" -> every result has policy_area == "data_privacy".
    results = TOOL_FUNCTIONS['policy']('data privacy', policy_area='data_privacy')['results']
    assert results
    assert all(item['policy_area'] == 'data_privacy' for item in results)


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    # One policy file contains a quoted line that tries to give the assistant orders.
    # Query that section (source_citation) and assert: that line is in untrusted_text, NOT in facts.
    results = TOOL_FUNCTIONS['policy']('source citation', policy_area='source_citation', top_k=20)['results']
    untrusted = [line for item in results for line in item['untrusted_text']]
    assert untrusted
    for line in untrusted:
        assert all(line not in item['facts'] for item in results)


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

def test_deduplicate_removes_tracking_duplicates_and_preserves_first_source() -> None:
    items = [{'url': 'https://example.org/a?utm_source=x', 'title': 'first'}, {'url': 'https://EXAMPLE.org/a#fragment', 'title': 'second'}, {'url': 'https://example.org/b'}]
    result = deduplicate_sources(items)
    assert result['duplicate_count'] == 1
    assert result['items'] == [items[0], items[2]]
    assert items[0]['url'].endswith('utm_source=x')


def test_deduplicate_rejects_invalid_model_input() -> None:
    for invalid in (None, 'not a list', [{}], [42], [{'url': 'file:///private'}]):
        assert deduplicate_sources(invalid)['error'] == 'ValueError'


def test_deduplicate_returns_error_dict_for_malformed_url_port() -> None:
    result = deduplicate_sources([{'url': 'https://example.org:invalid/path'}])
    assert result['error'] == 'ValueError'
    assert 'message' in result


def test_deduplicate_preserves_meaningful_query_parameters_and_path_case():
    items = [{'url': 'https://example.org/A?id=1'}, {'url': 'https://example.org/A?id=2'}, {'url': 'https://example.org/a?id=1'}]
    assert deduplicate_sources(items)['item_count'] == 3


@pytest.mark.parametrize('confirmed', ['false', 'true', 1, [], None])
def test_send_rejects_model_confirmation_with_wrong_type(confirmed, fake_http):
    calls = fake_http(FakeResponse())
    assert TOOL_FUNCTIONS['send']('draft', confirmed=confirmed)['status'] == 'needs_confirmation'
    assert calls == []


def test_send_rejects_blank_draft_before_http(fake_http):
    calls = fake_http(FakeResponse())
    assert TOOL_FUNCTIONS['send'](' ', confirmed=True)['error'] == 'ValueError'
    assert calls == []
