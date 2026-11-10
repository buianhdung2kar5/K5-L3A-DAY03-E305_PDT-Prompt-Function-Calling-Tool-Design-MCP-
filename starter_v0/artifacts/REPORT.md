# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team:
- Members:
- Provider/model: OpenRouter / `openai/gpt-4o-mini`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent hỗ trợ tìm tin trên web/Twitter, đọc URL và paper arXiv, tra cứu policy nội bộ rồi trình bày bản tin có nguồn. Tool mới `deduplicate` lọc các nguồn trùng URL trong danh sách đã có; thao tác gửi Telegram yêu cầu xác nhận của người dùng.

**Link dùng thử (deploy):** Tạm hoãn UI; hiện dùng chatbot terminal với `python chat.py --provider openrouter --version v7` từ thư mục `starter_v0`.

**Trạng thái đã đo:** base v7 đạt 19/20, group revision3 đạt 9/10; 132 unit/contract/example test PASS. Chức năng Twitter đang gặp HTTP 403; Telegram chưa cấu hình đủ; đây là các giới hạn thực thi được ghi trong Phần B.

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi dữ liệu còn thiếu hoặc xin xác nhận trước khi gửi | không |
| timeline | Lấy tweet theo tài khoản và số lượng; hiện API Twitter trả 403 | không |
| social_search | Tìm tweet theo từ khóa, chế độ Top/Latest; hiện API Twitter trả 403 | không |
| lookup | Tìm thông tin/tin tức trên web theo khoảng thời gian | không |
| fetch | Đọc nội dung một URL cụ thể bằng Firecrawl | không |
| format | Trình bày nguồn có sẵn thành digest, bullet, section hoặc thread | không |
| send | Gửi đúng nội dung đã xác nhận lên Telegram; hiện thiếu cấu hình bot/chat ID | không |
| policy | Tra cứu handbook nội bộ, tách nội dung instruction khỏi facts | không |
| papers | Tìm paper trên arXiv; có thể trả danh sách rỗng | không |
| paper_text | Tải PDF arXiv và trích text vào file local; chưa có live evidence riêng | không |
| deduplicate | Lọc URL trùng, bỏ fragment/utm_* khi so sánh, giữ bản ghi đầu tiên; chạy local | có |

## A3. Câu hỏi mẫu để thử

1. Tìm tin tức robotics trên web trong hôm nay.
2. Đọc và tóm tắt trang https://openai.com/news/.
3. Chính sách nội bộ yêu cầu trích nguồn trong bản tin như thế nào?
4. Lọc URL trùng trong danh sách này, giữ bản ghi đầu tiên: [{"url":"https://example.org/report?utm_source=mail","title":"Bản đầu"},{"url":"https://example.org/report","title":"Bản lặp"}].
5. Chuẩn bị đăng lên Telegram nội dung "Bản tin nghiên cứu đã sẵn sàng", hỏi tôi xác nhận trước khi gửi. Chỉ kiểm tra luồng xác nhận nếu chưa cấu hình Telegram.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Số liệu lấy từ `artifacts/version_log.csv` và các run JSON được dẫn trong bảng. Case/routing/arguments/multiturn lần lượt là độ chính xác theo case, chọn tool, tham số và case nhiều lượt. Các tỷ lệ được ghi theo thang 0–1. So sánh trong cùng suite và cùng bộ case; group revision2 khác bộ group ban đầu.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo hiệu năng ban đầu trước tối ưu | — | case 0.70; routing 0.75; arguments 0.70; multiturn 1.00 | `runs/v0_B_base_openrouter_20261110T103606490951.json` |
| v1 | `system_prompt.md` | Quy tắc rõ về câu ngoài phạm vi sẽ ngăn gọi `send` sai | case 0.70; routing 0.75; arguments 0.70; multiturn 1.00 | case 0.80; routing 0.80; arguments 0.80; multiturn 1.00 | `runs/v1_B_base_openrouter_20261110T104800610653.json` |
| v2 | `system_prompt.md` | Hỏi lại thông tin bắt buộc thay vì đoán handle/URL | case 0.80; routing 0.80; arguments 0.80; multiturn 1.00 | case 0.90; routing 0.90; arguments 0.90; multiturn 1.00 | `runs/v2_B_base_openrouter_20261110T110517815246.json` |
| v3 | `system_prompt.md` | Yêu cầu xác nhận trước gửi sẽ gọi `clarify(response_type="yes_no")` | case 0.90; routing 0.90; arguments 0.90; multiturn 1.00 | case 0.90; routing 0.95; arguments 0.90; multiturn 1.00 | `runs/v3_B_base_openrouter_20261110T111328408800.json` |
| v4 (group) | `tools.yaml` | Explicit tool boundaries will fix confirmation type and missing URL routing | case 0.80; routing 0.90; arguments 0.80; multiturn 0.80 | case 0.80; routing 0.80; arguments 0.80; multiturn 0.60 | `runs/v4_B_group_openrouter_20261110T115423168004.json` |
| v5 (group) | `tools.yaml` | Latest source instruction and literal URL evidence should control tool selection | case 0.80; routing 0.80; arguments 0.80; multiturn 0.60 | case 0.90; routing 0.90; arguments 0.90; multiturn 0.80 | `runs/v5_B_group_openrouter_20261110T115531644353.json` |
| v6 (group) | `tools.yaml` | Unresolved article references require clarify even when user asks to proceed | case 0.90; routing 0.90; arguments 0.90; multiturn 0.80 | case 0.90; routing 0.90; arguments 0.90; multiturn 0.80 | `runs/v6_B_group_openrouter_20261110T115628092428.json` |
| v6 (base) | `tools.yaml` | Unresolved article references require clarify even when user asks to proceed | case 0.90; routing 0.95; arguments 0.90; multiturn 1.00 | case 0.90; routing 0.95; arguments 0.90; multiturn 1.00 | `runs/v6_B_base_openrouter_20261110T115744407489.json` |
| v7 (group) | Tool mới + khai báo tool | Bổ sung khả năng lọc nguồn trùng và làm rõ routing; vòng mở rộng tính năng | — (group revision3) | case_accuracy=0.90; tool_routing_accuracy=0.90; argument_accuracy=0.90; multiturn_accuracy=1.00 | `runs/v7_B_group_openrouter_20261110T124902405911.json` |
| v7 (base) | Tool mới + khai báo tool | Bổ sung khả năng lọc nguồn trùng và làm rõ routing; vòng mở rộng tính năng | case 0.90; routing 0.95; arguments 0.90; multiturn 1.00 | case_accuracy=0.95; tool_routing_accuracy=1.00; argument_accuracy=0.95; multiturn_accuracy=1.00 | `runs/v7_B_base_openrouter_20261110T125015213861.json` |

Bảng dùng các lượt v2/v3 sau khi lưu thay đổi prompt. Các file của hai lượt thử trước khi lưu thay đổi hiện không còn trong thư mục runs; không dùng các lượt đó làm bằng chứng. Các run chính được dẫn trong bảng vẫn có đủ file JSON.

## B2. Failure Analysis

Phân tích từ `results[*].result.failures` và actual tool calls trong run JSON. Bảng ghi lịch sử lỗi và trạng thái mới nhất đã quan sát; một case chuyển PASS trong một lượt chưa đủ để kết luận nguyên nhân cải thiện riêng của nó.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | `send` | Câu hỏi tích phân ngoài phạm vi; agent gọi `send` thay vì không gọi tool. Tool chặn gửi và trả `needs_confirmation`. | Quy tắc phạm vi trong v1 sửa được case này. |
| R10_missing_handle | missing_info | v0: `timeline(screenname="sama")`; v2: `clarify` | Baseline đoán handle khi người dùng chưa cung cấp. | v2 đã PASS sau khi thay quy tắc đoán bằng hỏi lại. |
| R11_missing_url | missing_info | v2: `fetch(url="https://example.com")`; v3: `clarify` | v2 vẫn tự tạo URL khi thiếu link. | PASS ở v3; vòng này thay quy tắc gửi nên chưa thể kết luận nguyên nhân riêng cho cải thiện case này. |
| R12_confirm_before_send | wrong_boundary | v7: `clarify(response_type="text")` | Hỏi nội dung thay vì yes_no như expected của base. | Vẫn FAIL ở base v7; cần review trường hợp vừa thiếu nội dung vừa yêu cầu gửi. |
| R13_parallel_web_and_tweets | wrong_tool | v0: `lookup` + `social_search`; v1: `lookup` + `timeline` | Các run cũ có lỗi query/topic hoặc chọn sai tool thứ hai. | v2 đã PASS; thay đổi nhắm vào hỏi lại nên chưa thể kết luận nguyên nhân cải thiện riêng case này. |
| R14_out_of_scope_coding | out_of_scope | `send` | Yêu cầu viết code ngoài phạm vi nhưng agent gọi `send` thay vì không gọi tool. Tool chặn gửi và trả `needs_confirmation`. | Quy tắc phạm vi trong v1 sửa được case này. |
| R01_user_tweets_routing | wrong_tool | v3/v6: clarify; v7: timeline | v3 hỏi số lượng; v6 hỏi handle Sam Altman dù expected là timeline. | v7 PASS sau khi bổ sung mô tả timeline, ánh xạ tên/handle và mặc định limit. |

## B3. Team Eval Cases

Bộ hiện tại: `day04_v2_research_group_revision3`; 10 case, 5 single-turn và 5 multi-turn. G04 tạm dùng papers đã được thay bằng case chọn tool mới deduplicate theo ghi chú của bộ cũ. Snapshot trước thay đổi: `data/archive/eval_group_revision2.json`. Vì case thay đổi, điểm group revision2 và revision3 không phải phép so sánh cùng bộ dữ liệu.

Lịch sử revision2: v3 8/10, v4 8/10, v5 9/10, v6 9/10; xem các run tương ứng trong B1/version log. Bộ ban đầu revision1 nằm ở `data/archive/eval_group_revision1.json`, đạt 10/10 tại `runs/v3_B_group_openrouter_20261110T112143143930.json`.

Run revision3: `runs/v7_B_group_openrouter_20261110T124902405911.json`; 9/10 PASS, routing 0.90, arguments 0.90, multiturn 1.00; không có provider error.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_explicit_confirm_send | User đã xác nhận rõ ràng -> phải gửi với confirmed=true, không hỏi lại thừa. | `send(confirmed=true, text="Hôm nay có 3 tin AI nổi bật")` | FAIL: missing tool call send; extra tool call clarify; thực tế clarify yes_no, hỏi lại dù đã xác nhận. |
| G02_content_given_needs_confirm | Có nội dung nhưng chưa xác nhận -> phải xin xác nhận yes_no trước khi gửi. Dùng để phân biệt lỗi R12 do thiếu nội dung hay do ranh giới xác nhận. | `clarify(response_type="yes_no")` | PASS |
| G03_handle_with_at_sign | Handle phải bỏ dấu @ khi truyền vào screenname. | `timeline(screenname="karpathy")` | PASS; tool error: 403 Client Error: Forbidden |
| G04_deduplicate_sources | Nguồn đã có và cần lọc URL trùng: chọn deduplicate. Case chấm routing; nội dung input/output được kiểm tra bằng unit test và đối chiếu tool result của run. | `deduplicate()` | PASS |
| G05_translate_out_of_scope | Việc không cần tool (dịch ngắn) -> không được gọi tool. | Không gọi tool | PASS |
| G06_social_to_web_switch | Đổi từ social_search sang lookup giữa hội thoại, giữ chủ đề và timeframe. | `lookup(query="Claude", topic="news", timeframe="week")` | PASS |
| G07_web_to_social_switch | Đổi từ lookup sang social_search, search_type=Top cho 'phổ biến nhất'. | `social_search(query="AI", search_type="Top")` | PASS; tool error: 403 Client Error: Forbidden |
| G08_missing_url_referenced | User ám chỉ 'link ở trên' nhưng chưa từng đưa URL -> phải hỏi lại, không bịa URL. | `clarify(response_type="text")` | PASS |
| G09_multiturn_confirm_then_send | Sau khi user xác nhận ở lượt cuối -> gửi với confirmed=true. | `send(confirmed=true, text="Hôm nay có 3 tin AI")` | PASS; tool error: Missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID env var |
| G10_correct_account_keep_limit | Sửa tài khoản giữa chừng nhưng giữ nguyên limit. | `timeline(screenname="satyanadella", limit=5)` | PASS; tool error: 403 Client Error: Forbidden |

Case G04 chấm routing, không chấm từng trường items trong args. Đã đối chiếu tool result riêng: input_count=3, unique_count=2, duplicates_removed=1; giữ đúng URL và thứ tự của bản ghi đầu tiên. Test code kiểm tra riêng dữ liệu và output.

G08 PASS trong lượt v7 sau khi từng FAIL ở v4–v6; cần thêm các lượt đo để kết luận ổn định. Group v7 còn G01 hỏi xác nhận thừa. PASS routing/args không chứng minh API thực thi thành công; Twitter 403 và thiếu cấu hình Telegram vẫn được ghi nhận. Lượt sandbox `runs/v3_B_group_openrouter_20261110T114518706087.json` có 10 provider error, không dùng kết luận chất lượng agent.

## B4. Live Chat Evidence

Transcript: `transcripts/v3_openrouter_20261110T113455193875.transcript.json`; provider/model: `openrouter / openai/gpt-4o-mini`; artifact: `v3+p47f0065f4e30+t5b22a2476d41`. Transcript hiện có 6 lượt user; bảng dưới phân tích 4 lượt đầu đã review. Credential trong các lượt bổ sung đã được che trước khi commit; không kết luận về kết quả gửi của các lượt chưa phân tích.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tìm tin tức robotics trong hôm nay. | `lookup(query="robotics", topic="news", timeframe="day", max_results=5)` | `v3+p47f0065f4e30+t5b22a2476d41`; turn 1 | Tool trả 5 item; agent trả lời có link nguồn. Phạm vi ngày xuất bản của từng nguồn chưa được kiểm chứng riêng. |
| 2 | Tóm tắt bài viết này giúp tôi. | `fetch` (URL Berkeley News từ lượt 1) | `v3+p47f0065f4e30+t5b22a2476d41`; turn 2 | Firecrawl trả nội dung và agent tóm tắt. Agent tự chọn một bài từ lịch sử dù người dùng chưa chỉ rõ bài nào; đây là điểm cần review, không phải bằng chứng đã hỏi lại khi thiếu URL. |
| 3 | Đăng lên Telegram nội dung: Bản tin hôm nay đã sẵn sàng. | `clarify(response_type="yes_no")` | `v3+p47f0065f4e30+t5b22a2476d41`; turn 3 | Đúng ranh giới xác nhận: hỏi trước khi gửi; status waiting_for_user; chưa gọi send. |
| 4 | Yes | `send(confirmed=true)` | `v3+p47f0065f4e30+t5b22a2476d41`; turn 4 | Gọi send sau xác nhận, giữ đúng nội dung. Tool trả RuntimeError: thiếu TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID; chưa gửi Telegram thành công. Agent báo thất bại thay vì báo đã gửi. |

Điểm cần cải thiện: lượt 2 chọn bài khi tham chiếu còn mơ hồ. Lượt 4 yêu cầu cấu hình bot trong câu trả lời; thông tin cấu hình cần được điền vào `.env`, không yêu cầu người dùng gửi token trong chat. Có thể kiểm tra thêm yêu cầu thiếu URL trong một phiên chat mới không có URL ở lịch sử.

## B5. Bonus Evidence

Ghi bằng chứng đã có và phạm vi thực sự được kiểm tra; các phần chưa thực hiện được đánh dấu rõ.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `transcripts/v3_openrouter_20261110T113455193875.transcript.json`, turns 3–4 | Hỏi yes_no rồi gọi send với confirmed=true sau xác nhận | Gửi thật chưa thành công vì thiếu cấu hình Telegram; cần đặt token/chat ID trong .env. |
| arXiv (`papers`) | `runs/v6_B_group_openrouter_20261110T115628092428.json`, G04 | Chọn đúng papers và query; không có error dict | Kết quả items rỗng (0 bài), chưa chứng minh tìm được paper phù hợp hoặc đọc toàn văn bằng paper_text. |
| Company policy | `tests/test_tools_todo.py`; `artifacts/tool_unit_tests.txt` | Unit test xác nhận lọc policy_area, query rỗng và tách dòng instruction vào untrusted_text | Đây là kiểm tra code local; chưa có live transcript riêng chứng minh model xử lý nội dung policy không đáng tin. |
| UI | Chưa có bằng chứng | Tạm hoãn theo phạm vi hiện tại | Chưa triển khai/đánh giá UI trong phần báo cáo này. |
| Tool unit tests (`tests/`) | `artifacts/tool_unit_tests.txt`; `tests/test_tools_todo.py` | 65 test case trong file tool tests, gồm 17 case mới cho deduplicate; toàn suite 132 PASS, 0 failed, 0 skipped | Mock HTTP; chặn network thật; dùng key giả. Tool mới không có I/O. |
| Tool mới deduplicate | `tools/deduplicate/tool.py`; `tools/deduplicate/TOOL.md`; group v7 G04 | Lọc 3 nguồn còn 2; giữ bản đầu, không mutate input; đăng ký trong tools registry và YAML | Lọc theo URL, không kiểm chứng nội dung hoặc nhận diện hai URL khác nhau cùng bài. Input lỗi trả error dict, không trả URL có credential. |

Đã thay 14 stub cho tool có sẵn bằng test thật và thêm các trường hợp tham số/nhánh lỗi, 48 test case cho tool có sẵn trong `test_tools_todo.py`, cộng thêm 17 case cho tool mới deduplicate (65 case trong file). Kiểm tra nhóm section, đánh số thread, input rỗng, request/response mapping, giới hạn kết quả, tách instruction không đáng tin khỏi facts, thiếu key, HTTP 403/429 và timeout. Ví dụ: test kiểm tra `search_type` thực sự được truyền vào request RapidAPI; eval routing chỉ kiểm tra args model nên không phát hiện được nếu tool bỏ quên tham số đó. Các test hiện PASS, chưa phát hiện bug mới cần sửa trong code tool.

Tool mới deduplicate đã có 17 test case: happy path, dữ liệu sai từ model, URL lỗi/credential/port, input rỗng, giữ khác biệt query/scheme/path và không mutate input. Trước triển khai, 17 case đều FAIL do chưa đăng ký tool; sau triển khai đều PASS. Toàn suite mới có 132 PASS; không phát hiện bug mới cần sửa trong tool có sẵn. Yêu cầu tool mới, TOOL.md, registry/YAML, ít nhất 3 test và case eval routing đã có bằng chứng. Thông tin nhóm/thành viên và author tạm để trống theo yêu cầu.

## B6. Reflection

**Những sửa đổi thuộc system prompt.** Các quy tắc chung của agent được sửa trong v1–v3: giới hạn phạm vi research/news, hỏi lại khi thiếu dữ liệu bắt buộc và yêu cầu xác nhận trước khi gửi. Trên cùng base suite, case accuracy tăng từ 14/20 ở v0 lên 16/20 ở v1 và 18/20 ở v2; v3 giữ 18/20 nhưng routing tăng từ 0.90 lên 0.95. R08/R14 chuyển PASS sau quy tắc phạm vi; R10 chuyển PASS sau quy tắc hỏi lại. Đây là kết quả các lượt đo đã lưu, chưa phải bằng chứng về độ ổn định trên mọi cách diễn đạt.

**Những sửa đổi thuộc tools.yaml.** v4–v6 làm rõ điều kiện dùng clarify/fetch/send, ý nghĩa response_type và confirmed, yêu cầu URL có thật trong ngữ cảnh, cùng việc ưu tiên nguồn được chọn ở lượt mới nhất khi đổi giữa Twitter và web. Trên group revision2 cố định, v3 đạt 8/10; v4 vẫn 8/10 và phát sinh lỗi chọn nguồn ở G06; v5 sửa được G06 và đạt 9/10; v6 giữ 9/10. G02 chuyển sang hỏi xác nhận yes_no, nhưng G08 vẫn bịa URL. Vì vậy tăng mô tả chưa giải quyết hoàn toàn tham chiếu thiếu dữ liệu. Base v6 đạt 18/20, routing 0.95, bằng các metric tổng hợp của base v3. R01 và R12 vẫn FAIL. Hash prompt không đổi từ v3 đến v6; các lượt sau chủ yếu kiểm chứng thay đổi khai báo tool.

**Bổ sung v7.** Đã hoàn thiện mô tả khi dùng/không dùng và convention tham số cho cả 11 tool; bổ sung deduplicate chạy local kèm hợp đồng input/output và test. Base v7 đạt 19/20, routing 1.00, arguments 0.95; R01 chuyển PASS, R12 vẫn FAIL. Group revision3 đạt 9/10; tool mới chọn đúng và output 3→2 nguồn được đối chiếu riêng. G08 chuyển PASS nhưng G01 hỏi xác nhận thêm. Do vừa thêm tool vừa hoàn thiện nhiều mô tả và đổi G04, v7 là lượt mở rộng tính năng, không dùng để quy kết cải thiện cho một câu mô tả cụ thể. Transcript live hiện có vẫn là v3; chưa có phiên live v7 riêng.

**Những tình huống cần review thủ công.** Điểm eval chỉ kiểm tra tool calls và args: G01/G09 PASS dù Telegram thiếu cấu hình, còn G03/G07/G10 PASS dù RapidAPI trả 403. G04 của group revision2 PASS khi chọn papers đúng nhưng items rỗng; G04 revision3 là case khác dành cho deduplicate. Trong live chat, câu “bài viết này” dẫn đến tự chọn một bài từ nhiều nguồn trước đó, cần người xem quyết định tham chiếu đã đủ rõ chưa. Base R12 vừa thiếu nội dung cụ thể vừa yêu cầu gửi, còn expected chỉ chấp nhận yes_no; cần phân biệt việc hỏi nội dung với xin phép hành động khi thiết kế case mới. Giữ nguyên expected của bộ base đã dùng để so sánh và ghi nhận hạn chế chấm điểm này. Việc gọi lookup đúng timeframe cũng chưa bảo đảm mọi bài được trả về xuất bản đúng ngày yêu cầu.

**Hướng cải thiện tiếp.** Ưu tiên đo độ ổn định khi xác định URL từ ngữ cảnh để tránh tái phát lỗi G08; bổ sung kiểm tra đầu vào fetch nhằm không gửi câu tham chiếu hoặc URL không hợp lệ cho API. Kiểm tra thêm các tên tài khoản để xác nhận ánh xạ của R01 ổn định; làm rõ thứ tự hỏi dữ liệu/xác nhận cho R12 và tránh hỏi xác nhận lặp ở group G01. Khắc phục quyền truy cập RapidAPI; nếu làm bonus Telegram thì cấu hình token/chat ID trong .env và kiểm tra riêng kết quả thực thi. Tool mới deduplicate, 17 test và case G04 đã hoàn thành ở v7; tiếp theo nên bổ sung case biến thể để kiểm tra độ ổn định. UI tạm hoãn. Các thay đổi sau cần có run riêng, metric và hash, chạy lại base và cùng group revision3; khi tuyên bố ổn định cần đo nhiều lượt vì từng case đã có dao động dù metric tổng có thể giữ nguyên.

## B7. Small Local Model Challenge (bonus)

Không thực hiện trong phạm vi hiện tại. Chưa có run Ollama, chưa so sánh ít nhất hai model local và chưa thực hiện các vòng tối ưu riêng cho local. Không có số liệu để kết luận hiệu năng hoặc chọn model local so với cloud.
