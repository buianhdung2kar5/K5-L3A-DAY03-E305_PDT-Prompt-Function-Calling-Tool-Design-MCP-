"""Rebuild the UTF-8 report and version log from real, immutable evidence."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def link(path):
    return f'[{path.name}](../{path.relative_to(ROOT).as_posix()})'


def main():
    runs = [(p, read(p)) for p in sorted((ROOT / 'runs').glob('*.json'))]
    versions = {}
    for path, run in runs:
        if run.get('suite') == 'base' and run.get('version') in ('v0', 'v1', 'v2', 'v3'):
            versions[run['version']] = (path, run)
    hypotheses = {
        'v0': ('baseline', 'Đo hành vi starter trước tối ưu.'),
        'v1': ('system_prompt.md', 'Ranh giới hỏi lại/xác nhận rõ hơn sẽ giảm đoán và gửi sớm.'),
        'v2': ('tools.yaml + đăng ký deduplicate', 'Mô tả trách nhiệm và convention args rõ hơn sẽ giảm nhầm tool/args; bổ sung deduplicate.'),
        'v3': ('system_prompt.md', 'Lập kế hoạch theo trạng thái hội thoại và nhiều nguồn sẽ khắc phục hỏi thừa/bỏ sót bước.'),
    }
    fields = ['version', 'author', 'changed_artifact', 'artifact_version', 'prompt_hash', 'tools_hash', 'reason', 'hypothesis', 'metric_before', 'metric_after', 'run_file']
    previous = None
    with (ROOT / 'artifacts/version_log.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for version in ('v0', 'v1', 'v2', 'v3'):
            if version not in versions:
                continue
            path, run = versions[version]
            changed, hypothesis = hypotheses[version]
            writer.writerow(dict(version=version, author='Thanh', changed_artifact=changed,
                                 artifact_version=run['artifact_version'], prompt_hash=run['prompt_hash'], tools_hash=run['tools_hash'],
                                 reason='Gemini gemini-3.5-flash-lite; xem report và JSON để kiểm tra provenance', hypothesis=hypothesis,
                                 metric_before=json.dumps(previous, ensure_ascii=False) if previous else 'N/A',
                                 metric_after=json.dumps(run['summary'], ensure_ascii=False), run_file=path.relative_to(ROOT).as_posix()))
            previous = run['summary']
    metrics = ['| Version | Giả thuyết / thay đổi | Case đạt | Routing | Args | Multi-turn | Lỗi API | Run |', '|---|---|---:|---:|---:|---:|---:|---|']
    failures = ['| Version / case | Nhãn dataset | Sai lệch quan sát | Chi tiết chấm | Actual tool calls |', '|---|---|---|---|---|']
    for version, (path, run) in versions.items():
        s = run['summary']
        multi = [c for c in run['results'] if c.get('is_multiturn') and c['result'].get('failure_type') != 'provider_error']
        multi_score = f"{sum(c['result']['passed'] for c in multi)}/{len(multi)}"
        metrics.append(f"| {version} | {hypotheses[version][1]} | {s['passed_cases']}/{s['measured_cases']} ({s['case_accuracy']:.0%}) | {s.get('tool_routing_accuracy', 0):.0%} | {s.get('argument_accuracy', 0):.0%} | {multi_score} | {s['provider_error_cases']} | {link(path)} |")
        for case in run['results']:
            r = case['result']
            if not r['passed']:
                calls = json.dumps(r.get('actual_tool_calls', []), ensure_ascii=False)
                failures.append(f"| {version} / {case['id']} | {r.get('failure_type')} | {r.get('observed_mismatch')} | {cell('; '.join(r['failures']))} | `{cell(calls)}` |")
    group_runs = [(p, r) for p, r in runs if r.get('suite') == 'group' and r.get('version') == 'v3']
    group = group_runs[-1] if group_runs else None
    group_results = {c['id']: c for c in group[1]['results']} if group else {}
    group_table = ['| Case | Nguồn | Kiểm tra | Kết quả |', '|---|---|---|---|']
    dataset = read(ROOT / 'data/eval_group.json')
    for case in dataset['cases']:
        result = group_results.get(case['id'], {}).get('result')
        status = ('PASS' if result['passed'] else 'FAIL') if result else 'Chưa chạy'
        origin = 'Bổ sung T01–T10' if case['id'].startswith('T') else 'Case người dùng cung cấp'
        group_table.append(f"| {case['id']} | {origin} | {cell(case.get('metadata', {}).get('what_it_tests', ''))} | {status} |")
    live = ['| Transcript | Lượt | Yêu cầu | Tools | Trạng thái |', '|---|---:|---|---|---|']
    for path in sorted((ROOT / 'transcripts').glob('*v3*.transcript.json')):
        transcript = read(path)
        for turn in transcript['turns']:
            tools = ', '.join(e.get('tool', '') for e in turn.get('tool_events', [])) or 'không gọi tool'
            live.append(f"| {link(path)} | {turn['turn_index']} | {cell(turn['user'])} | {tools} | {turn['status']} |")
    test_path = ROOT / 'analysis/pytest_final.txt'
    test_summary = test_path.read_text(encoding='utf-8').strip().splitlines()[-1] if test_path.exists() else 'Chờ lần kiểm thử cuối.'
    endpoint = ROOT / 'artifacts/ui_endpoint.json'
    endpoint_info = read(endpoint) if endpoint.exists() else {}
    public = endpoint_info.get('public_url', 'Chưa có; dùng UI local.')
    group_score = f"{group[1]['summary']['passed_cases']}/{group[1]['summary']['measured_cases']} ca đạt; {link(group[0])}" if group else 'Đang chuẩn bị.'
    user_score = sum(c['result']['passed'] for c in group_results.values() if c['id'].startswith('G'))
    group_failure_table = ['| Case nhóm lỗi | Chi tiết | Actual calls |', '|---|---|---|']
    for case in group_results.values():
        r = case['result']
        if not r['passed']:
            group_failure_table.append(f"| {case['id']} | {cell('; '.join(r['failures']))} | `{cell(json.dumps(r.get('actual_tool_calls', []), ensure_ascii=False))}` |")
    report = f'''# Research Agent — Báo cáo thực nghiệm

Provider/model: **Gemini / gemini-3.5-flash-lite**. Team/members: chờ người dùng điền tên.
Các số liệu dưới đây lấy từ run JSON, không điền điểm giả. Xem [version_log.csv](version_log.csv).

# PHẦN A — Giới thiệu agent

## A1. Chức năng và UI

Agent tìm tin web/bài đăng, đọc URL, gộp nguồn trùng, định dạng bản tin và gửi Telegram sau khi duyệt.
UI có chọn phiên bản v0–v3, xem tool trace, từng case và tải JSON.

- Local: http://127.0.0.1:8501
- Public demo: {public}
- Mã truy cập lưu riêng trong `.env` (`UI_ACCESS_CODE`), không đưa vào report.
- Hướng dẫn: [RUNBOOK.md](../RUNBOOK.md).

## A2. Tool

| Tool | Chức năng | Nhóm tự thêm? |
|---|---|---|
| clarify | Hỏi dữ liệu thiếu hoặc xin xác nhận | Không |
| timeline | Bài gần đây của tài khoản X/Twitter | Không |
| social_search | Tìm bài theo chủ đề, Top/Latest | Không |
| lookup | Tìm tin web theo chủ đề/thời gian | Không |
| fetch | Đọc đúng URL được cung cấp | Không |
| format | Định dạng các item đã có | Không |
| deduplicate | Bỏ URL trùng, giữ nguồn đầu tiên; chạy local | **Có** |
| send | Gửi bản nháp đã xác nhận lên Telegram | Không |
| policy | Tra cứu markdown chính sách nội bộ | Không |
| papers / paper_text | Tìm và đọc paper arXiv | Không |

## A3. Câu hỏi demo

1. Tìm 3 tin web về AI hôm nay.
2. Lấy 3 bài gần nhất của @karpathy.
3. Tóm tắt bài này giúp tôi. (Agent phải hỏi URL nếu chưa có.)
4. Bỏ trùng danh sách URL đã có trước khi định dạng bản tin.
5. Gửi Telegram nội dung "Kiểm tra bản tin". Xem bản nháp và duyệt hoặc hủy.

# PHẦN B — Bằng chứng

## B1. Version Evidence

{chr(10).join(metrics)}

Mỗi phiên bản có snapshot `artifacts/vN/` và SHA-256 trong CSV/JSON.
v1 chỉ sửa prompt; v2 giữ prompt v1, viết rõ tool declaration và thêm deduplicate;
v3 giữ tools v2, sửa prompt về lập kế hoạch từ trạng thái hội thoại.
v2 có thêm tool nên không thể tách riêng ảnh hưởng của việc thêm tool và viết lại description.
Không đổi nội dung `data/eval_base.json` và không sửa kết quả để tăng điểm.

**Baseline:** run gốc v0 đo 16/20 ca, 4 ca bị HTTP 429 (15 request/phút).
Run resumed giữ nguyên 16 kết quả, chỉ thay 4 lỗi provider bằng retry thật, đạt 13/20.
Run gốc và retry vẫn được giữ, có `provenance` trong run resumed.
Các vòng sau dùng `--case-delay 5`; harness chấm và adapter Gemini được giữ nguyên về logic.
Adapter Gemini hiện chưa áp dụng `tool_choice`; accuracy chỉ đo routing/args, không đánh giá chất lượng nội dung.

## B2. Failure Analysis

{chr(10).join(failures)}

Nhãn `failure_type` là nhãn dataset, không luôn đúng với sai lệch thực tế.
Ví dụ v0 R03/M06 gọi đúng lookup nhưng sai query chính xác; R13 vừa sai query vừa thiếu social_search.
Query thêm "news today" có thể vẫn hợp ngữ nghĩa nhưng trượt đối sánh của harness: cần đọc thủ công, giữ điểm gốc.
v1 R11 đã hỏi URL đúng nhưng thiếu arg response_type; R12 hỏi nội dung còn thiếu bằng text,
trong khi expected yêu cầu yes_no. Đây là hạn chế của chấm args so với đánh giá hành vi.
v0 R12 thực sự gửi tin thử với confirmed=true tự sinh; các vòng cải tiến và UI phải kiểm soát ranh giới này.

## B3. Group eval

Giữ nguyên 10 case G01–G10 người dùng cung cấp. Bổ sung 10 case T01–T10,
gồm 5 single-turn và 5 multi-turn; tổng bộ nhóm là 20 ca (10 + 10).
T01/T06 kiểm tra routing tới tool mới; canonical URL được kiểm thử riêng bằng unit test.
Không thay expected của người dùng theo kết quả model. Kết quả: **{group_score}**.
Các case G01–G10 người dùng cung cấp: **{user_score}/10 đạt**.
Snapshot dataset thực tế đã chạy: [eval_group_used.json](eval_group_used.json).

{chr(10).join(group_table)}

{chr(10).join(group_failure_table)}

Ca thiếu `max_results` vẫn bị chấm FAIL dù tool có default=5; yêu cầu lấy 3 cần truyền rõ 3.

## B4. Live Chat Evidence

{chr(10).join(live)}

Log lưu user text, rounds, actual tool calls/results, model, version và hashes.
Transcript v0 cũ có text mất dấu do nhập qua PowerShell được giữ nguyên làm bằng chứng lịch sử;
demo mới dùng script UTF-8. Test offline không được tính là live evidence.

## B5. Tool mới, UI và unit test

Tool mới: [deduplicate/TOOL.md](../tools/deduplicate/TOOL.md), đăng ký đầy đủ trong code/YAML.
Không gọi mạng, không mutate input; bỏ tracking/fragment khi so sánh URL, giữ tham số có nghĩa.
Giữ phân biệt scheme, path case và dấu slash cuối để tránh gộp nhầm tài liệu khác.

Đã thay các TODO skipped bằng test thật; HTTP trong test đều mock.
Regression quan trọng: `send(confirmed="false")` trước đây vẫn gửi vì chuỗi không rỗng là truthy.
Đã yêu cầu `confirmed is True` và text không rỗng; test kiểm tra không có HTTP khi sai kiểu/thiếu nội dung.
Thay đổi code send này không sửa điểm routing/args của các run đã lưu.
UI luôn stage send để người dùng duyệt chính xác text, bất kể model tự điền confirmed=true.
Một lượt duyệt chỉ được consume một lần; hủy không gọi API. Lỗi API không tự gửi lại.

Kiểm thử cuối: **{test_summary}**. Xem [pytest_final.txt](../analysis/pytest_final.txt).
UI được kiểm tra bằng Streamlit AppTest và HTTP health; chưa kiểm tra hình ảnh bằng trình duyệt tự động.
WebSocket local/public đã kiểm tra form mã truy cập xuất hiện trước dữ liệu chat/eval.
UI v3 có một lượt đăng nhập + Gemini + deduplicate thật trong bảng transcript B4.
Preflight Gemini: [provider_preflight.txt](../analysis/provider_preflight.txt).
Kiểm tra snapshot, bộ case người dùng, UTF-8 và credential scan: [submission_checks.txt](../analysis/submission_checks.txt).
CSV tổng hợp mọi run (bao gồm v0 gốc/resumed và group): [all_runs.csv](../analysis/all_runs.csv).

## B6. Reflection

- System prompt xử lý hỏi lại, hủy/xác nhận, tham chiếu hội thoại và kế hoạch nhiều bước.
- Tool declarations xử lý trách nhiệm tool và convention query/topic/timeframe/handle/search_type.
- Cần đọc thủ công các query tương đương, câu hỏi text thay yes_no và chất lượng nguồn trả về.
- Ranh giới gửi cần cả rule model và duyệt tại tầng thực thi, không chỉ một boolean do model tự đặt.
- UTF-8: viết lại tài liệu mất dấu và thêm `.editorconfig`; log raw cũ không bị viết lại.
- Team/members và các hoạt động debate thực tế cần người dùng bổ sung; không tự nhận đã tham gia.

## B7. Bonus local model

Chưa chạy challenge Ollama hai model; đây là bonus tùy chọn, không thuộc bằng chứng bắt buộc đã báo cáo.
'''
    (ROOT / 'artifacts/REPORT.md').write_text(report, encoding='utf-8')
    print('Updated UTF-8 REPORT.md and version_log.csv from', len(versions), 'real versions.')


if __name__ == '__main__':
    main()
