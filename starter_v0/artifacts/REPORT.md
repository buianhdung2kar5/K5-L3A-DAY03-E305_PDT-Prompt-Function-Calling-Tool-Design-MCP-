# Research Agent — Báo cáo thực nghiệm

Team:E305_PDT
members:Mai Văn Thanh - 2A202603696
Provider/model: **Gemini / gemini-3.5-flash-lite**.
Các số liệu dưới đây lấy từ run JSON, không điền điểm giả. Xem [version_log.csv](version_log.csv).

# PHẦN A — Giới thiệu agent

## A1. Chức năng và UI

Agent tìm tin web/bài đăng, đọc URL, gộp nguồn trùng, định dạng bản tin và gửi Telegram sau khi duyệt.
UI có chọn phiên bản v0–v3, xem tool trace, từng case và tải JSON.

- Local: http://127.0.0.1:8501
- Public demo: https://sunny-would-drivers-intention.trycloudflare.com
- Mã truy cập lưu riêng trong `.env` (`UI_ACCESS_CODE`), không đưa vào report.
- Hướng dẫn: [RUNBOOK.md](../RUNBOOK.md).

## A2. Tool

| Tool                | Chức năng                                    | Nhóm tự thêm? |
| ------------------- | -------------------------------------------- | ------------- |
| clarify             | Hỏi dữ liệu thiếu hoặc xin xác nhận          | Không         |
| timeline            | Bài gần đây của tài khoản X/Twitter          | Không         |
| social_search       | Tìm bài theo chủ đề, Top/Latest              | Không         |
| lookup              | Tìm tin web theo chủ đề/thời gian            | Không         |
| fetch               | Đọc đúng URL được cung cấp                   | Không         |
| format              | Định dạng các item đã có                     | Không         |
| deduplicate         | Bỏ URL trùng, giữ nguồn đầu tiên; chạy local | **Có**        |
| send                | Gửi bản nháp đã xác nhận lên Telegram        | Không         |
| policy              | Tra cứu markdown chính sách nội bộ           | Không         |
| papers / paper_text | Tìm và đọc paper arXiv                       | Không         |

## A3. Câu hỏi demo

1. Tìm 3 tin web về AI hôm nay.
2. Lấy 3 bài gần nhất của @karpathy.
3. Tóm tắt bài này giúp tôi. (Agent phải hỏi URL nếu chưa có.)
4. Bỏ trùng danh sách URL đã có trước khi định dạng bản tin.
5. Gửi Telegram nội dung "Kiểm tra bản tin". Xem bản nháp và duyệt hoặc hủy.

# PHẦN B — Bằng chứng

## B1. Version Evidence

| Version | Giả thuyết / thay đổi                                                                    |    Case đạt | Routing | Args | Multi-turn | Lỗi API | Run                                                                                                                |
| ------- | ---------------------------------------------------------------------------------------- | ----------: | ------: | ---: | ---------: | ------: | ------------------------------------------------------------------------------------------------------------------ |
| v0      | Đo hành vi starter trước tối ưu.                                                         | 13/20 (65%) |     80% |  65% |        4/6 |       0 | [v0_B_base_gemini_20261110T114349443637_resumed.json](../runs/v0_B_base_gemini_20261110T114349443637_resumed.json) |
| v1      | Ranh giới hỏi lại/xác nhận rõ hơn sẽ giảm đoán và gửi sớm.                               | 13/20 (65%) |     90% |  65% |        3/6 |       0 | [v1_B_base_gemini_20261110T115430203782.json](../runs/v1_B_base_gemini_20261110T115430203782.json)                 |
| v2      | Mô tả trách nhiệm và convention args rõ hơn sẽ giảm nhầm tool/args; bổ sung deduplicate. | 15/20 (75%) |     95% |  75% |        5/6 |       0 | [v2_B_base_gemini_20261110T115844805819.json](../runs/v2_B_base_gemini_20261110T115844805819.json)                 |
| v3      | Lập kế hoạch theo trạng thái hội thoại và nhiều nguồn sẽ khắc phục hỏi thừa/bỏ sót bước. | 18/20 (90%) |    100% |  90% |        6/6 |       0 | [v3_B_base_gemini_20261110T120312230857.json](../runs/v3_B_base_gemini_20261110T120312230857.json)                 |

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

| Version / case                   | Nhãn dataset    | Sai lệch quan sát | Chi tiết chấm                                                              | Actual tool calls                                                                                                                                                               |
| -------------------------------- | --------------- | ----------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| v0 / R03_web_news_routing        | wrong_tool      | wrong_arg_value   | query: expected 'AI', got 'AI news today'                                  | `[{"name": "lookup", "args": {"topic": "news", "timeframe": "day", "query": "AI news today", "max_results": 5}}]`                                                               |
| v0 / R10_missing_handle          | missing_info    | missing_tool_call | missing tool call clarify; extra tool call timeline                        | `[{"name": "timeline", "args": {"limit": 5, "screenname": "sama"}}]`                                                                                                            |
| v0 / R11_missing_url             | missing_info    | missing_tool_call | missing tool call clarify; extra tool call lookup                          | `[{"name": "lookup", "args": {"query": "tóm tắt tin tức nổi bật hôm nay"}}]`                                                                                                    |
| v0 / R12_confirm_before_send     | wrong_boundary  | missing_tool_call | missing tool call clarify; extra tool call send                            | `[{"name": "send", "args": {"text": "Bản tin cập nhật tự động hôm nay.", "confirmed": true}}]`                                                                                  |
| v0 / R13_parallel_web_and_tweets | wrong_tool      | wrong_arg_value   | query: expected 'AI', got 'AI news today'; missing tool call social_search | `[{"name": "lookup", "args": {"max_results": 5, "timeframe": "day", "topic": "news", "query": "AI news today"}}]`                                                               |
| v0 / M02_carryover_timeframe     | wrong_arg_value | wrong_arg_value   | query: expected 'robotics', got 'robotics news today'                      | `[{"name": "lookup", "args": {"timeframe": "day", "topic": "news", "query": "robotics news today"}}]`                                                                           |
| v0 / M06_switch_tool             | wrong_tool      | wrong_arg_value   | query: expected 'OpenAI', got 'OpenAI tin tức mới nhất'                    | `[{"name": "lookup", "args": {"topic": "news", "query": "OpenAI tin tức mới nhất", "timeframe": "week"}}]`                                                                      |
| v1 / R03_web_news_routing        | wrong_tool      | wrong_arg_value   | query: expected 'AI', got 'AI news today'                                  | `[{"name": "lookup", "args": {"topic": "news", "timeframe": "day", "query": "AI news today"}}]`                                                                                 |
| v1 / R11_missing_url             | missing_info    | wrong_arg_value   | response_type: expected 'text', got None                                   | `[{"name": "clarify", "args": {"question": "Bạn vui lòng cung cấp địa chỉ (URL) của bài viết cần tóm tắt nhé!"}}]`                                                              |
| v1 / R12_confirm_before_send     | wrong_boundary  | wrong_arg_value   | response_type: expected 'yes_no', got 'text'                               | `[{"name": "clarify", "args": {"question": "Bạn vui lòng cung cấp nội dung bản tin mà bạn muốn đăng lên Telegram nhé?", "response_type": "text"}}]`                             |
| v1 / R13_parallel_web_and_tweets | wrong_tool      | wrong_arg_value   | query: expected 'AI', got 'AI news today'; missing tool call social_search | `[{"name": "lookup", "args": {"topic": "news", "max_results": 5, "query": "AI news today", "timeframe": "day"}}]`                                                               |
| v1 / M01_clarify_then_fill       | missing_info    | missing_tool_call | missing tool call timeline; extra tool call clarify                        | `[{"name": "clarify", "args": {"question": "Xin lỗi, bạn muốn lấy 5 tweet mới nhất của tài khoản nào?", "response_type": "choice", "options": ["Elon Musk"]}}]`                 |
| v1 / M02_carryover_timeframe     | wrong_arg_value | wrong_arg_value   | query: expected 'robotics', got 'robotics AI news today'                   | `[{"name": "lookup", "args": {"query": "robotics AI news today", "timeframe": "day", "topic": "news"}}]`                                                                        |
| v1 / M06_switch_tool             | wrong_tool      | wrong_arg_value   | query: expected 'OpenAI', got 'OpenAI tin tức mới nhất'                    | `[{"name": "lookup", "args": {"topic": "news", "query": "OpenAI tin tức mới nhất", "timeframe": "week"}}]`                                                                      |
| v2 / R03_web_news_routing        | wrong_tool      | wrong_arg_value   | query: expected 'AI', got 'AI artificial intelligence news'                | `[{"name": "lookup", "args": {"timeframe": "day", "query": "AI artificial intelligence news", "topic": "news"}}]`                                                               |
| v2 / R11_missing_url             | missing_info    | wrong_arg_value   | response_type: expected 'text', got None                                   | `[{"name": "clarify", "args": {"question": "Bạn vui lòng cung cấp URL của bài viết cần tóm tắt nhé?"}}]`                                                                        |
| v2 / R12_confirm_before_send     | wrong_boundary  | wrong_arg_value   | response_type: expected 'yes_no', got 'text'                               | `[{"name": "clarify", "args": {"question": "Bạn chưa cung cấp nội dung bản tin cần đăng lên Telegram. Vui lòng gửi nội dung bản tin cho mình nhé!", "response_type": "text"}}]` |
| v2 / R13_parallel_web_and_tweets | wrong_tool      | missing_tool_call | missing tool call social_search                                            | `[{"name": "lookup", "args": {"max_results": 5, "timeframe": "day", "topic": "news", "query": "AI"}}]`                                                                          |
| v2 / M02_carryover_timeframe     | wrong_arg_value | wrong_arg_value   | query: expected 'robotics', got 'robotics AI news'                         | `[{"name": "lookup", "args": {"query": "robotics AI news", "topic": "news", "timeframe": "day"}}]`                                                                              |
| v3 / R03_web_news_routing        | wrong_tool      | wrong_arg_value   | query: expected 'AI', got 'AI artificial intelligence news'                | `[{"name": "lookup", "args": {"topic": "news", "query": "AI artificial intelligence news", "timeframe": "day"}}]`                                                               |
| v3 / R11_missing_url             | missing_info    | wrong_arg_value   | response_type: expected 'text', got None                                   | `[{"name": "clarify", "args": {"question": "Bạn vui lòng cung cấp đường dẫn (URL) của bài viết cần tóm tắt nhé."}}]`                                                            |

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
Không thay expected của người dùng theo kết quả model. Kết quả: **19/20 ca đạt; [v3_B_group_gemini_20261110T120625298902.json](../runs/v3_B_group_gemini_20261110T120625298902.json)**.
Các case G01–G10 người dùng cung cấp: **10/10 đạt**.
Snapshot dataset thực tế đã chạy: [eval_group_used.json](eval_group_used.json).

| Case                            | Nguồn                    | Kiểm tra                                                                                                                                          | Kết quả |
| ------------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| G01_explicit_confirm_send       | Case người dùng cung cấp | User đã xác nhận rõ ràng -> phải gửi với confirmed=true, không hỏi lại thừa.                                                                      | PASS    |
| G02_content_given_needs_confirm | Case người dùng cung cấp | Có nội dung nhưng chưa xác nhận -> phải xin xác nhận yes_no trước khi gửi. Dùng để phân biệt lỗi R12 do thiếu nội dung hay do ranh giới xác nhận. | PASS    |
| G03_handle_with_at_sign         | Case người dùng cung cấp | Handle phải bỏ dấu @ khi truyền vào screenname.                                                                                                   | PASS    |
| G04_papers_routing_provisional  | Case người dùng cung cấp | Tìm paper học thuật -> papers, không phải lookup.                                                                                                 | PASS    |
| G05_translate_out_of_scope      | Case người dùng cung cấp | Việc không cần tool (dịch ngắn) -> không được gọi tool.                                                                                           | PASS    |
| G06_social_to_web_switch        | Case người dùng cung cấp | Đổi từ social_search sang lookup giữa hội thoại, giữ chủ đề và timeframe.                                                                         | PASS    |
| G07_web_to_social_switch        | Case người dùng cung cấp | Đổi từ lookup sang social_search, search_type=Top cho 'phổ biến nhất'.                                                                            | PASS    |
| G08_missing_url_referenced      | Case người dùng cung cấp | User ám chỉ 'link ở trên' nhưng chưa từng đưa URL -> phải hỏi lại, không bịa URL.                                                                 | PASS    |
| G09_multiturn_confirm_then_send | Case người dùng cung cấp | Sau khi user xác nhận ở lượt cuối -> gửi với confirmed=true.                                                                                      | PASS    |
| G10_correct_account_keep_limit  | Case người dùng cung cấp | Sửa tài khoản giữa chừng nhưng giữ nguyên limit.                                                                                                  | PASS    |
| T01_deduplicate_tracking        | Bổ sung T01–T10          | Route tới tool mới khi chỉ cần bỏ nguồn trùng; logic canonical URL được unit test riêng.                                                          | PASS    |
| T02_unknown_account             | Bổ sung T01–T10          | Không mặc định tài khoản nổi tiếng khi thiếu handle.                                                                                              | PASS    |
| T03_web_climate_week            | Bổ sung T01–T10          | Tách query, thời gian, loại tin và số lượng.                                                                                                      | FAIL    |
| T04_social_top_robotics         | Bổ sung T01–T10          | Đúng social_search và enum Top.                                                                                                                   | PASS    |
| T05_draft_requires_approval     | Bổ sung T01–T10          | Có text nhưng chưa duyệt không được gửi ngay.                                                                                                     | PASS    |
| T06_deduplicate_context         | Bổ sung T01–T10          | Tool mới lấy item đúng từ ngữ cảnh.                                                                                                               | PASS    |
| T07_correct_limit               | Bổ sung T01–T10          | Giữ handle và áp dụng sửa limit mới nhất.                                                                                                         | PASS    |
| T08_correct_timeframe           | Bổ sung T01–T10          | Sửa timeframe thay vì giữ tháng ở lượt cũ.                                                                                                        | PASS    |
| T09_cancel_send                 | Bổ sung T01–T10          | Hủy gửi không gọi send hay tool khác.                                                                                                             | PASS    |
| T10_read_previous_url           | Bổ sung T01–T10          | Giữ URL ngữ cảnh, không hỏi lại hoặc thay lookup.                                                                                                 | PASS    |

| Case nhóm lỗi        | Chi tiết                          | Actual calls                                                                               |
| -------------------- | --------------------------------- | ------------------------------------------------------------------------------------------ |
| T03_web_climate_week | max_results: expected 3, got None | `[{"name": "lookup", "args": {"query": "climate", "timeframe": "week", "topic": "news"}}]` |

Ca thiếu `max_results` vẫn bị chấm FAIL dù tool có default=5; yêu cầu lấy 3 cần truyền rõ 3.

## B4. Live Chat Evidence

| Transcript                                                                                                                      | Lượt | Yêu cầu                                                                                                                                                                                                   | Tools          | Trạng thái       |
| ------------------------------------------------------------------------------------------------------------------------------- | ---: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- | ---------------- |
| [ui_v3_4c08a048064b438faa9501621dc99d3b.transcript.json](../transcripts/ui_v3_4c08a048064b438faa9501621dc99d3b.transcript.json) |    1 | Chỉ bỏ URL trùng trong danh sách đã có, không tìm thêm, không định dạng: [{"url":"https://example.org/a?utm_source=email","title":"Nguồn đầu"},{"url":"https://example.org/a#top","title":"Nguồn trùng"}] | deduplicate    | answered         |
| [v3_gemini_20261110T120654001029.transcript.json](../transcripts/v3_gemini_20261110T120654001029.transcript.json)               |    1 | Tìm 1 tin web về AI hôm nay rồi trình bày thành một bullet có nguồn.                                                                                                                                      | lookup, format | answered         |
| [v3_gemini_20261110T120654001029.transcript.json](../transcripts/v3_gemini_20261110T120654001029.transcript.json)               |    2 | Tóm tắt một bài viết khác mà tôi chưa gửi URL. Đừng lấy link của tin trước.                                                                                                                               | clarify        | waiting_for_user |
| [v3_gemini_20261110T120654001029.transcript.json](../transcripts/v3_gemini_20261110T120654001029.transcript.json)               |    3 | https://example.com/ Đây là URL của bài đó, chỉ đọc đúng link này.                                                                                                                                        | fetch          | answered         |
| [v3_gemini_20261110T120654001029.transcript.json](../transcripts/v3_gemini_20261110T120654001029.transcript.json)               |    4 | Đăng lên Telegram nội dung: Kiểm tra bản tin nghiên cứu v3.                                                                                                                                               | clarify        | waiting_for_user |
| [v3_gemini_20261110T120654001029.transcript.json](../transcripts/v3_gemini_20261110T120654001029.transcript.json)               |    5 | Xác nhận gửi đúng nội dung: Kiểm tra bản tin nghiên cứu v3.                                                                                                                                               | send           | answered         |

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

Kiểm thử cuối: **97 passed in 4.31s**. Xem [pytest_final.txt](../analysis/pytest_final.txt).
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
