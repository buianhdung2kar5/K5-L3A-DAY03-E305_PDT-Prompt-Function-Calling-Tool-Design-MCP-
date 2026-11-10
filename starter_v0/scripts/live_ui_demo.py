"""One real v3 UI turn, including access-code login, using Gemini and a local tool."""
from __future__ import annotations

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


if __name__ == '__main__':
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=90).run()
    assert not app.exception
    if not app.chat_input:
        app.text_input[0].set_value(os.environ['UI_ACCESS_CODE'])
        next(b for b in app.button if b.label == 'Mở demo').click().run()
    assert app.session_state['transcript']['version'] == 'v3'
    app.chat_input[0].set_value(
        'Chỉ bỏ URL trùng trong danh sách đã có, không tìm thêm, không định dạng: '
        '[{"url":"https://example.org/a?utm_source=email","title":"Nguồn đầu"},'
        '{"url":"https://example.org/a#top","title":"Nguồn trùng"}]'
    ).run()
    assert not app.exception
    turn = app.session_state['transcript']['turns'][-1]
    assert turn['status'] == 'answered', turn['status']
    assert [e['tool'] for e in turn['tool_events']] == ['deduplicate']
    assert turn['tool_events'][0]['result']['duplicate_count'] == 1
    print('LIVE_UI_V3: login + Gemini + deduplicate passed')
    print('Transcript:', Path(app.session_state['transcript_path']).relative_to(ROOT))
