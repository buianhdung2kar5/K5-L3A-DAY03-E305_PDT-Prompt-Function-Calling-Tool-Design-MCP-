"""Run five scripted, real CLI turns; do not use this in offline pytest."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TURNS = [
    'Tìm 1 tin web về AI hôm nay rồi trình bày thành một bullet có nguồn.',
    'Tóm tắt một bài viết khác mà tôi chưa gửi URL. Đừng lấy link của tin trước.',
    'https://example.com/ Đây là URL của bài đó, chỉ đọc đúng link này.',
    'Đăng lên Telegram nội dung: Kiểm tra bản tin nghiên cứu v3.',
    'Xác nhận gửi đúng nội dung: Kiểm tra bản tin nghiên cứu v3.',
    '/exit',
]

if __name__ == '__main__':
    command = [sys.executable, '-X', 'utf8', '-u', 'chat.py', '--provider', 'gemini',
               '--model', 'gemini-3.5-flash-lite', '--version', 'v3',
               '--system-prompt', 'artifacts/v3/system_prompt.md', '--tools', 'artifacts/v3/tools.yaml',
               '--request-delay', '5', '--max-tool-rounds', '4']
    result = subprocess.run(command, cwd=ROOT, input='\n'.join(TURNS)+'\n', text=True,
                            encoding='utf-8', capture_output=True)
    log = ROOT / 'analysis/live_demo_cli.txt'
    log.write_text(result.stdout + result.stderr, encoding='utf-8')
    print(result.stdout)
    if result.returncode:
        print(result.stderr)
    raise SystemExit(result.returncode)
