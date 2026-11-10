"""Check the real Streamlit WebSocket gate without invoking the model."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from streamlit.proto.BackMsg_pb2 import BackMsg
from streamlit.proto.ForwardMsg_pb2 import ForwardMsg
from websockets.sync.client import connect

ROOT = Path(__file__).resolve().parents[1]


def check_gate(base_url):
    websocket_url = base_url.replace('https://', 'wss://').replace('http://', 'ws://') + '/_stcore/stream'
    with connect(websocket_url, subprotocols=['streamlit'], origin=base_url, open_timeout=15) as ws:
        message = BackMsg()
        message.rerun_script.query_string = ''
        ws.send(message.SerializeToString())
        elements = []
        for _ in range(80):
            response = ForwardMsg()
            response.ParseFromString(ws.recv(timeout=20))
            if response.WhichOneof('type') == 'delta' and response.delta.WhichOneof('type') == 'new_element':
                elements.append(response.delta.new_element.WhichOneof('type'))
            if response.WhichOneof('type') == 'script_finished':
                break
    assert 'text_input' in elements, elements
    assert 'chat_input' not in elements and 'arrow_data_frame' not in elements, elements
    return 'pass: login form only; chat and eval data hidden'


if __name__ == '__main__':
    log = (ROOT / '.venv/tunnel_final.log').read_text(encoding='utf-8')
    public_url = re.findall(r'https://[a-z0-9-]+\.trycloudflare\.com', log)[-1]
    local_url = 'http://127.0.0.1:8501'
    info = {'local_url': local_url, 'public_url': public_url,
            'authentication': 'UI_ACCESS_CODE in private .env',
            'checked_at': datetime.now(timezone.utc).isoformat(),
            'note': 'Temporary quick tunnel; expires when the process stops.'}
    for name, base in [('local', local_url), ('public', public_url)]:
        info[name + '_health'] = urlopen(base + '/_stcore/health', timeout=20).status
        info[name + '_auth_gate'] = check_gate(base)
    (ROOT / 'artifacts/ui_endpoint.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
    print(json.dumps(info, indent=2))
