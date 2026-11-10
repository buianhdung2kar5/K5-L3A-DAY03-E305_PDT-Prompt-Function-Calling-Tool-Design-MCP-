# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: E305_PDT
- Members: Bùi Anh Dũng (2A202603687), Lê Minh Phụng(2A202603693), Mai Văn Thanh(2A202603696)
- Provider/model: OpenRouter, `openai/gpt-4o-mini`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent tiếng Việt: nhận một yêu cầu, tự chọn tool phù hợp rồi trả lời kèm nguồn. Agent tìm tin trên web, đọc tweet theo tài khoản hoặc từ khóa, đọc nội dung một URL hay bài báo arXiv, tìm bài báo khoa học, tra chính sách nội bộ, dựng bản tin, kiểm tra một link có dấu hiệu độc hại không (`url_check`), cho biết ngày giờ hiện tại (`time_now`), lưu ghi chú vào file cục bộ (`save_note`, cần đồng ý trước) và gửi bản tin lên Telegram.

Khi thiếu thông tin (không rõ tài khoản hay URL) agent hỏi lại thay vì đoán. Việc gửi Telegram chỉ thực hiện khi người dùng đã đồng ý: agent hỏi xác nhận trước, và tool `send` trả `needs_confirmation` nếu chưa có `confirmed=true` (xem B5 về một trường hợp tool chưa chặt). `send` chỉ gửi vào kênh Telegram của nhóm; nếu bạn nói đăng lên Twitter hoặc Facebook, agent có thể trả lời như đã đăng ở đó (xem B4).

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL: https://relates-correct-leone-hoped.trycloudflare.com

## A2. Tool agent có

Agent có 10 tool có sẵn của starter và 3 tool nhóm tự thêm (`url_check`, `time_now`, `save_note`).

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin hoặc cần xác nhận | không |
| timeline | lấy bài đăng gần đây của một tài khoản Twitter/X | không |
| social_search | tìm bài đăng mạng xã hội theo từ khóa (mới nhất hoặc phổ biến nhất) | không |
| lookup | tìm trên web, có chế độ tin tức và lọc theo khoảng thời gian | không |
| fetch | đọc nội dung một URL | không |
| format | trình bày các item đã có thành bản tin markdown | không |
| send | gửi văn bản lên Telegram channel, chỉ khi đã xác nhận | không |
| policy | tìm trong tài liệu chính sách nội bộ của công ty | không |
| papers | tìm bài báo khoa học trên arXiv | không |
| paper_text | tải PDF arXiv và trích văn bản | không |
| url_check | kiểm tra một URL có dấu hiệu độc hại không bằng cách phân tích chuỗi URL (không mở trang) | **có** |
| time_now | cho biết ngày giờ hiện tại theo giờ Việt Nam và khoảng ngày của hôm nay, hôm qua, tuần này, 7 ngày qua, tháng này | **có** |
| save_note | lưu một ghi chú vào file cục bộ (thư mục `notes/`); là hành động ghi nên chỉ lưu khi người dùng đã đồng ý (`confirmed=true`) | **có** |

## A3. Câu hỏi mẫu để thử

Sau mỗi câu, mở mục "Tool đã gọi" dưới câu trả lời để xem agent đã chọn tool nào.

1. `Tweet mới nhất của Sam Altman là gì?` → đọc bài đăng của một tài khoản (`timeline`)
2. `Tin công nghệ nổi bật trong tuần này` → tìm tin trên web (`lookup`)
3. `Tóm tắt bài này giúp mình` → agent hỏi lại URL (`clarify`); trả lời bằng một link, ví dụ `https://example.com`, agent sẽ đọc trang (`fetch`)
4. `Có paper nào mới về mixture of experts trên arXiv không?` → tìm bài báo khoa học (`papers`)
5. `Bạn là gì và làm được những gì?` → agent tự giới thiệu, không gọi tool
6. `Hôm nay là thứ mấy, ngày bao nhiêu?` → ngày giờ hiện tại (`time_now`)

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo hành vi chưa tối ưu trước khi sửa | – | 0.65 | `runs/v0_B_base_openrouter_20261110T102828747923.json` |
| v1 | `system_prompt.md` (dòng 3) | Chỉ dẫn "không hỏi lại, tự đoán" là nguyên nhân R10, R11 không gọi `clarify` | 0.65 | 0.85 | `runs/v1_B_base_openrouter_20261110T111033431604.json` |
| v2 | `tools.yaml` (mô tả `response_type` của `clarify`) | Mô tả `response_type` quá ngắn nên model bỏ qua; mô tả rõ khi nào dùng `text`/`yes_no` sẽ khiến model điền trường này | 0.85 | **0.95** | `runs/v2_B_base_openrouter_20261110T111637736772.json` |
| v3 | `system_prompt.md` (dòng 5) | Dòng 5 "cứ gửi ngay" khiến model hỏi nội dung thay vì xin xác nhận; đổi thành rule xác nhận sẽ đưa R12 về `clarify yes_no`. **Bị bác bỏ** (R12 vẫn FAIL, M02 FAIL) | 0.95 | 0.90 | `runs/v3_B_base_openrouter_20261110T112657372718.json` |
| v4 | `system_prompt.md` (dòng 7) | Dòng 7 ("luôn xong trong một bước, chọn một tool, best judgment") mâu thuẫn với dòng 3 và 5 và ép luôn gọi một tool; gỡ nó sẽ sửa R12, G02, G08, G05. **Chưa được xác nhận**: base không đổi (R12, M02 vẫn FAIL), group 0.70 lên 0.80 chỉ nhờ G06 | 0.90 | 0.90 | `runs/v4_B_base_openrouter_20261110T143000183636.json` |
| v5 | `tools.yaml` (mô tả `send`) | `send` không nói kênh đã cấu hình sẵn nên model hỏi "kênh nào" (R12, G02). Mô tả quy tắc xác nhận ở `send` sẽ sửa. Group 0.80 → 0.90 (G02 PASS); R12 và M02 vẫn FAIL. **Một phần** | 0.90 | 0.90 | `runs/v5_B_base_openrouter_20261110T144530152757.json` |
| v6 | `tools.yaml` (mô tả `response_type` của `clarify`) | `clarify.text` ("hỏi thông tin còn thiếu") kéo model hỏi nội dung trước khi xin đồng ý (R12). Tách: `yes_no` cho hành động ghi/gửi dùng ngay, `text` chỉ cho việc đọc/tra cứu. Group 0.90 → 0.80 (G06 FAIL, nghi dao động). **R12 sửa được** | 0.90 | **1.00** | `runs/v6_B_base_openrouter_20261110T144948149958.json` |
| v7 | `system_prompt.md` (thêm đoạn RESEARCH/ACTION) | Luật chọn nguồn và luật xác nhận giẫm lên nhau. Tách RESEARCH (chọn nguồn theo yêu cầu mới nhất) và ACTION (`yes_no` riêng, luôn điền `response_type`, không hỏi hai lần). Group 0.80 → 0.80 (G01 FAIL). **G06, M02, R12 PASS** | 1.00 | 1.00 | `runs/v7_B_base_openrouter_20261110T151405214119.json` |
| v8 | `tools.yaml` (mô tả `send`, tham số `confirmed`) | G01 hỏi lại dù người dùng đã xác nhận vì `send` không có ngoại lệ. Thêm ngoại lệ "đã xác nhận thì gọi `send` ngay `confirmed=true`" và "luôn hỏi `yes_no` trước khi hỏi nội dung". Group 0.80 → 0.90. **G01 PASS** | 1.00 | 1.00 | `runs/v8_B_base_openrouter_20261110T153101329059.json` |
| v9 | `tools.yaml` (mô tả `fetch`, tham số `url`) | G08 gọi `fetch(url="Link ở trên ấy")`. Quy tắc ba nhánh: URL rõ thì `fetch` ngay; mơ hồ thì `clarify text`; có dấu hiệu độc hại thì không gọi tool, trả lời bằng chữ. Group 0.90 → 0.90. **G08 PASS**, nhưng R12 (base) và G01 (group) FAIL, nghi dao động | 1.00 | 0.95 | `runs/v9_B_base_openrouter_20261110T154550130364.json` |
| v10 | `tools.yaml` (mô tả `send`) | R12, G01 dao động vì các câu rời rạc. Viết lại `send` theo hai trạng thái: chưa đồng ý thì `clarify yes_no`; đã đồng ý (trong yêu cầu hoặc câu `yes_no` trước) thì `send confirmed=true`. Group 0.90 → **1.00** | 1.00 | 1.00 | `runs/v10_B_base_openrouter_20261110T155101419049.json` |
| v11 | `tools.yaml` + `tools/url_check/` (tool mới) | Thêm `url_check` (phân tích tĩnh chuỗi URL). Mô tả: chỉ dùng khi người dùng hỏi về độ an toàn của link. Kỳ vọng không làm tụt routing cũ. Group (11 case, có G11) 1.00 → **1.00** | 1.00 | **1.00** | `runs/v11_B_base_openrouter_20261110T155639965393.json` |
| v12 | `tools.yaml` + `tools/time_now/` (tool mới) | Model không biết hôm nay là ngày nào. Thêm `time_now` (giờ Việt Nam UTC+7, khoảng ngày `today`, `yesterday`, `this_week`, `last_7_days`, `this_month`), mô tả chỉ dùng khi người dùng hỏi trực tiếp về ngày giờ để không bị gọi thừa trước `lookup`. Group (12 case, có G12) 1.00 → **1.00** | 1.00 | **1.00** | `runs/v12_B_base_openrouter_20261110T170944491573.json` |

Bản cuối của nhóm là **v12** (base 20/20 = 1.00, group 12/12 = 1.00), nhưng đây là **một lần chạy mỗi bộ**: R12, G01, G06 và M02 từng đổi trạng thái giữa các lần chạy nên chưa kiểm tra độ ổn định của v10, v11 và v12. Trên base, v2 (0.95) và các bản v6, v7, v8, v10, v11, v12 (1.00) là các mốc đáng chú ý. Chi tiết từng case FAIL ở B2.

Ghi chú quy trình: trong lúc làm, v5, v7, v8 và v9 mỗi bản từng có một phiên bản đã bị bỏ và viết lại; run, snapshot và dòng CSV của bản bỏ đã bị xoá. Một bản v13 (thêm tool `dedupe`) cũng đã được làm rồi bỏ vì base tụt còn 19/20 (R13), nhóm quyết định dừng ở v12; run, snapshot, tool và case G13 của v13 đã bị xoá. Các số liệu trên là của bản cuối của từng version. Số liệu group là các dòng `v*-group` trong `version_log.csv`.

**Sau v12 (chưa có version mới):** để đáp ứng checklist README (viết lại mô tả mỗi tool và nêu quy ước tham số), nhóm viết lại mô tả của 8 tool starter (`clarify`, `timeline`, `social_search`, `lookup`, `format`, `policy`, `papers`, `paper_text`) và mô tả tham số `text` của `send` trong `tools.yaml`. Chỉ đổi phần mô tả: tên tool, tham số, kiểu, enum và giá trị mặc định giữ nguyên (đã đối chiếu với snapshot v12). Nhóm cũng thêm tool mới thứ ba `save_note` (`tools/save_note/`, `TOOL.md`, đăng ký, khai báo, 6 unit test) **mà không tạo version và không chạy eval**; chưa có case eval cho tool này. `tools.yaml` hiện tại có hash `19a46f380d89`, khác hash v12 `673f131dba4e`, và **chưa được chạy eval**; mọi số liệu eval ở B1 đến B5 là của v12 với bản `tools.yaml` cũ. Riêng unit test (`pytest`) đã chạy trên bản hiện tại.

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

### v0 (baseline) — 7/20 case FAIL, `case_accuracy` 0.65

Nguồn: `runs/v0_B_base_openrouter_20261110T102828747923.json` 

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R03_web_news_routing | `wrong_arg_value` | `lookup(query="AI news", topic=news, timeframe=day)` | `query` thừa chữ "news" (eval so khớp chuỗi tuyệt đối, đây là chấm quá chặt, cần review tay) | Mô tả `query` trong `tools.yaml` (v2) |
| R08_out_of_scope | `out_of_scope` | `send(text="Nguyên hàm của x^2...")` | Bài toán ngoài phạm vi mà vẫn gọi `send` | Bỏ "luôn chọn một tool" trong prompt, thêm rule từ chối (v1) |
| R10_missing_handle | `missing_info` | `timeline(screenname="sama")` | Không nói tài khoản của ai mà model tự đoán Sam Altman | Bỏ "make a sensible guess", bắt buộc `clarify` (v1) |
| R11_missing_url | `missing_info` | `fetch(url="https://example.com/article")` | Bịa URL | Như R10 (v1) |
| R12_confirm_before_send | `wrong_boundary` | `send(text="Bản tin này")` | Gửi Telegram ngay, không xác nhận | Bỏ "just go ahead", bắt buộc `clarify yes_no` trước `send` (v1) |
| R13_parallel_web_and_tweets | `wrong_arg_value` | `lookup(query="AI news", timeframe=day)` + `social_search` | `query` thừa "news" và **thiếu `topic=news`** | Mô tả `topic`/`query` trong `tools.yaml` (v2) |
| R14_out_of_scope_coding | `out_of_scope` | `send(text="...hàm Fibonacci...")` | Viết code rồi gọi `send` | Như R08 (v1) |

Nguyên nhân gốc của R08, R10, R11, R12, R14: ba chỉ dẫn xấu trong `system_prompt.md` v0 (đoán thay vì hỏi, gửi không xác nhận, ép một bước).

### v1 — 3/20 case FAIL, `case_accuracy` 0.85

Nguồn: `runs/v1_B_base_openrouter_20261110T111033431604.json` (chạy 2 lần liên tiếp, kết quả giống nhau: 17/20, cùng 3 case FAIL). Thay đổi duy nhất: dòng 3 của prompt (bỏ "tự đoán", thay bằng "thiếu thì gọi `clarify`").

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R10_missing_handle | `wrong_arg_value` | `clarify(question="Bạn muốn tóm tắt tweet từ tài khoản nào?")` | Đã gọi đúng `clarify` nhưng thiếu `response_type="text"` | Chưa sửa |
| R11_missing_url | `wrong_arg_value` | `clarify(question="Bạn vui lòng cung cấp địa chỉ URL...")` | Thiếu `response_type="text"` | Chưa sửa |
| R12_confirm_before_send | `wrong_arg_value` | `clarify(question="Bạn có thể cung cấp nội dung bản tin...")` | Thiếu `response_type="yes_no"`, và hỏi nội dung thay vì xác nhận gửi | Chưa sửa |

So với v0: sửa được R03, R08, R13, R14. Giả thuyết dự đoán chỉ R10, R11 đổi từ gọi tool bịa sang `clarify` (đúng). R03, R08, R13, R14 cũng pass dù chưa đụng tới phần liên quan, chưa rõ nguyên nhân. Chạy lại lần 2 cho kết quả y hệt nên đây không phải biến động ngẫu nhiên đơn thuần; có thể việc thêm đường `clarify` làm model bớt dùng `send`, chưa kiểm chứng.

### v2 — 1/20 case FAIL, `case_accuracy` 0.95

Nguồn: `runs/v2_B_base_openrouter_20261110T111637736772.json`. Thay đổi duy nhất: mô tả tham số `response_type` của `clarify` trong `tools.yaml` (`prompt_hash` giữ nguyên `02f9dc1d0a91`, chỉ `tools_hash` đổi).

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R12_confirm_before_send | `wrong_arg_value` | `clarify(question="Bạn có thể cung cấp nội dung bản tin...")` | Thiếu `response_type="yes_no"`, và hỏi nội dung bản tin thay vì xin xác nhận gửi. Đây là lỗi hành vi (dòng 5 prompt "cứ gửi ngay"), không chỉ lỗi arg | Chưa sửa (dự kiến v3: rule xác nhận trước khi `send`) |

So với v1: R10, R11 chuyển FAIL → PASS (giờ có `response_type="text"`), không có hồi quy. Dự đoán đúng: R12 vẫn FAIL vì lỗi gốc nằm ở hành vi chứ không ở mô tả tool.

### v3 — 2/20 case FAIL, `case_accuracy` 0.90 (giảm so với v2: 0.95) — giả thuyết bị bác bỏ

Nguồn: `runs/v3_B_base_openrouter_20261110T112657372718.json`. Thay đổi duy nhất: dòng 5 của `system_prompt.md` ("cứ gửi ngay") thay bằng rule "xác nhận bằng `clarify` `yes_no` trước khi `send`" (`tools_hash` giữ `582fd7056862`, chỉ `prompt_hash` đổi thành `c8d46f7d3a26`).

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R12_confirm_before_send | `wrong_arg_value` | `clarify(question="Bạn có thể cung cấp nội dung bản tin...", response_type="text")` | Đã điền `response_type` (nhờ v2) nhưng là `text` thay vì `yes_no`: model vẫn hỏi nội dung bản tin, chưa xin xác nhận gửi. Câu "bản tin này" không kèm nội dung nên model coi thiếu thông tin | Chưa sửa (dự kiến v4) |
| M02_carryover_timeframe | `wrong_tool` | `social_search(query="robotics")` | Phải là `lookup(topic=news, timeframe=day)`. **Hồi quy so với v2.** Cũng từng FAIL ở lần chạy v1 đầu tiên (prompt khác) nên có thể là dao động của case này, chưa chắc do dòng 5 | Cần chạy lại để phân biệt hồi quy thật và dao động |

Kết luận v3: rule xác nhận trong prompt không đủ để R12 đạt, vì lỗi nằm ở chỗ model coi "thiếu nội dung" quan trọng hơn "cần xác nhận". Giả thuyết ban đầu bị bác bỏ.

### v4 — thay dòng 7 của prompt; base 0.90 (không đổi), group 0.70 → 0.80

Nguồn: `runs/v4_B_base_openrouter_20261110T143000183636.json`, `runs/v4_B_group_openrouter_20261110T143024579478.json`. Mốc group của v3: `runs/v3_B_group_openrouter_20261110T142842637713.json` (chạy trước khi sửa, vì bộ group chưa từng chạy trên v3). Thay đổi duy nhất: dòng 7 của `system_prompt.md` thay bằng "Use a tool only when it is needed. If the request needs no tool or is outside your tools, answer in plain text." (`prompt_hash` `5c94511ebd2e`, `tools_hash` giữ `582fd7056862`).

Giả thuyết: dòng 7 mâu thuẫn với dòng 3 ("đừng đoán, hãy hỏi") và dòng 5 ("xác nhận trước"), và ép model luôn gọi một tool, nên gỡ nó sẽ sửa R12, G02, G08 và giảm dao động.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R12_confirm_before_send (base) | `wrong_arg_value` | `clarify(question="Bạn có thể cung cấp nội dung bản tin và tên kênh Telegram...", response_type="text")` | Vẫn hỏi nội dung và kênh (`text`) thay vì xin xác nhận (`yes_no`) | Chưa sửa |
| M02_carryover_timeframe (base) | `wrong_tool` | `social_search(query="robotics")` | Phải là `lookup(topic=news, timeframe=day)`. FAIL ở v3 và v4 | Chưa sửa |
| G02_content_given_needs_confirm (group) | `wrong_arg_value` | `clarify(question="Bạn muốn đăng lên kênh hoặc nhóm nào trên Telegram?", response_type="text")` | Có nội dung nhưng model hỏi **kênh**, trong khi `send` không có tham số kênh (kênh cấu hình sẵn qua biến môi trường) | Chưa sửa |
| G08_missing_url_referenced (group) | `missing_info` | `fetch(url="Link ở trên ấy")` | Đưa nguyên cụm chữ vào làm URL | Chưa sửa |

So với v3: base không đổi (18/20, cùng R12 và M02). Group: G06 chuyển FAIL sang PASS, không có hồi quy, 7/10 lên 8/10. Vì G06 cùng họ với M02 mà M02 không đổi, và các case dao động này từng đổi trạng thái không do thay đổi nào, G06 đổi có thể là dao động chứ chưa chắc do dòng 7.

**Kết luận:** giả thuyết "dòng 7 là mấu chốt" **không được xác nhận**. Các lỗi mà giả thuyết dự đoán sẽ sửa (R12, G02, G08) đều còn nguyên. Quan sát mới từ log: R12 và G02 đều FAIL vì model hỏi `text` về chi tiết mà tool không cần (kênh Telegram, nội dung), tức dòng 3 ("thiếu thì hỏi") kích hoạt trước dòng 5. Gợi ý cho v5: mô tả `send` nói rõ kênh đã cấu hình sẵn, chỉ cần `text`.

### v5 — mô tả `send`; base 0.90 (không đổi), group 0.80 → 0.90

Nguồn: `runs/v5_B_base_openrouter_20261110T144530152757.json`, `runs/v5_B_group_openrouter_20261110T144556829043.json`. Thay đổi duy nhất: mô tả tool `send` trong `tools.yaml` (`prompt_hash` giữ `5c94511ebd2e`, `tools_hash` đổi thành `0bbf88a7544f`). Nội dung: `send` là hành động ghi, phải `clarify yes_no` trước, chưa có nội dung thì hỏi nội dung sau khi họ đồng ý, nơi nhận đã cấu hình sẵn.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R12_confirm_before_send (base) | `wrong_arg_value` | `clarify(question="Bạn có thể cung cấp nội dung bản tin...", response_type="text")` | Vẫn hỏi nội dung bằng `text` thay vì xin đồng ý (`yes_no`). Model chọn `clarify` ngay từ đầu nên mô tả của `send` gần như không được đọc | v6 (mô tả `clarify`) |
| M02_carryover_timeframe (base) | `wrong_tool` | `social_search(query="robotics")` | Phải là `lookup(topic=news, timeframe=day)` | v7 (luật chọn nguồn) |
| G08_missing_url_referenced (group) | `missing_info` | `fetch(url="Link ở trên ấy")` | Đưa nguyên cụm chữ vào làm URL | v9 (mô tả `fetch`) |

G02 chuyển FAIL sang PASS (agent đã gọi `clarify yes_no`, dù câu hỏi vẫn nhắc kênh). Một bản v5 đầu tiên, có câu "chưa có nội dung thì hỏi nội dung bằng clarify", đã bị bỏ vì kéo model về hướng hỏi nội dung và làm G01, G09 hồi quy.

### v6 — mô tả `response_type` của `clarify`; base 0.90 → 1.00, group 0.90 → 0.80

Nguồn: `runs/v6_B_base_openrouter_20261110T144948149958.json`, `runs/v6_B_group_openrouter_20261110T145019818170.json`. Thay đổi duy nhất: tham số `response_type` của `clarify`: `yes_no` dùng ngay khi người dùng yêu cầu hành động ghi/gửi/đăng, kể cả khi còn thiếu nội dung; `text` chỉ để hỏi thông tin còn thiếu cho việc đọc/tra cứu (`tools_hash` `5d40178e9370`).

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| G06_social_to_web_switch (group) | `wrong_tool` | `social_search(query="Claude", search_type="Latest", limit=5)` | Người dùng đổi sang "tìm tin trên web" nhưng agent bám lượt đầu. Cùng họ với M02, từng PASS ở v4, nghi dao động | v7 (luật chọn nguồn) |
| G08_missing_url_referenced (group) | `missing_info` | `fetch(url="Link ở trên ấy")` | Như v5 | v9 |

R12 chuyển FAIL sang PASS: lỗi gốc là mô tả `text` ("hỏi thông tin còn thiếu") cùng dòng 3 của prompt kéo model sang `text`. M02 cũng PASS nhưng không rõ do v6 hay dao động.

### v7 — thêm đoạn RESEARCH/ACTION vào prompt; base 1.00 (không đổi), group 0.80 (không đổi)

Nguồn: `runs/v7_B_base_openrouter_20261110T151405214119.json`, `runs/v7_B_group_openrouter_20261110T151431705556.json`. Thay đổi duy nhất: thêm một đoạn tiếng Anh vào cuối `system_prompt.md` (`prompt_hash` `907668ebe0f9`, `tools_hash` giữ `5d40178e9370`). RESEARCH: đọc yêu cầu mới nhất, mạng xã hội thì `social_search`/`timeline`, web/tin tức/không nêu nền tảng thì `lookup`. ACTION: không áp luật RESEARCH, hỏi `clarify yes_no` như một câu riêng (không gộp với câu hỏi nội dung, luôn điền `response_type`), chỉ `send confirmed=true` khi đã xác nhận.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| G01_explicit_confirm_send (group) | `wrong_boundary` | `clarify(question="Bạn có chắc chắn muốn gửi đoạn văn bản này...", response_type="yes_no")` | Người dùng đã xác nhận rõ ("Mình xác nhận rồi, gửi...") mà agent vẫn hỏi lại | v8 |
| G08_missing_url_referenced (group) | `missing_info` | `fetch(url="Link ở trên ấy")` | Như v5 | v9 |

G06 và M02 PASS, R12 PASS. Một bản v7 đầu tiên không có mệnh đề "câu `yes_no` riêng, luôn điền `response_type`" đã chạy 2 lần với cùng kết quả (R12 FAIL do `response_type` bị bỏ trống, G01 FAIL), nên mệnh đề đó được thêm vào bản cuối. Prompt dài hơn không làm tụt các case out-of-scope (R08, R09, R14).

### v8 — mô tả `send` và tham số `confirmed`; base 1.00 (không đổi), group 0.80 → 0.90

Nguồn: `runs/v8_B_base_openrouter_20261110T153101329059.json`, `runs/v8_B_group_openrouter_20261110T153134955732.json`. Thay đổi duy nhất: khai báo `send` trong `tools.yaml` (`tools_hash` `478ff9d89476`): ngoại lệ "đã xác nhận rõ ràng (trong yêu cầu này hoặc lượt trước) thì gọi `send` ngay `confirmed=true`, không hỏi lại", câu "luôn hỏi `yes_no` trước khi hỏi nội dung", và mô tả tham số `confirmed`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| G08_missing_url_referenced (group) | `missing_info` | `fetch(url="Link ở trên ấy")` | Như v5. Case duy nhất còn FAIL | v9 |

G01 PASS. Hai bản v8 trước bị bỏ: bản có cụm "và đã có nội dung" (R12 FAIL ổn định qua 2 lần chạy), và bản thiếu câu "luôn hỏi `yes_no` trước khi hỏi nội dung" (R12 FAIL).

### v9 — mô tả `fetch`; base 1.00 → 0.95, group 0.90 (không đổi)

Nguồn: `runs/v9_B_base_openrouter_20261110T154550130364.json`, `runs/v9_B_group_openrouter_20261110T154618138029.json`. Thay đổi duy nhất: khai báo `fetch` trong `tools.yaml` (`tools_hash` `057c172b1277`): URL rõ ràng (`http(s)://` kèm tên miền bình thường) thì `fetch` ngay, không hỏi xác nhận; thiếu hoặc mơ hồ thì `clarify text`; có dấu hiệu độc hại (scheme lạ, IP thuần, `@`, tên miền giả thương hiệu) thì không gọi tool và trả lời bằng chữ.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R12_confirm_before_send (base) | `wrong_arg_value` | `clarify(question="Bạn có thể cung cấp nội dung của bản tin...", response_type="text")` | Hồi quy so với v8, nhưng `send` không đổi ở v9 nên nghi dao động | v10 |
| G01_explicit_confirm_send (group) | `wrong_boundary` | `clarify(question="Bạn có chắc chắn muốn gửi đoạn văn bản này...", response_type="yes_no")` | Như v7. PASS ở v8, nghi dao động | v10 |

**G08 PASS** (agent hỏi URL đầy đủ bằng `clarify text`) và R04 PASS. Bản v9 đầu tiên có điều kiện "đáng ngờ" quá rộng làm R04 FAIL ổn định (URL `openai.com` hợp lệ mà vẫn hỏi `yes_no`), nên đã bị bỏ và viết lại thành quy tắc ba nhánh ngắn.

### v10 — viết lại mô tả `send` theo trạng thái hội thoại; base 1.00, group 0.90 → 1.00

Nguồn: `runs/v10_B_base_openrouter_20261110T155101419049.json`, `runs/v10_B_group_openrouter_20261110T155134305746.json`. Thay đổi duy nhất: mô tả `send` (`tools_hash` `a03feefe3c34`). Hai trạng thái: (1) người dùng chưa đồng ý thì `clarify yes_no` trước, kể cả khi chưa có nội dung; (2) đã đồng ý (nói rõ trong yêu cầu hoặc đã trả lời đồng ý cho câu `yes_no` trước đó) thì `send confirmed=true`, thiếu nội dung thì hỏi bằng `clarify text`.

Không có case nào FAIL (base 20/20, group 10/10), gồm R12, G01, G08, G06 và M02.

### v11 — thêm tool `url_check`; base 1.00, group (11 case) 1.00

Nguồn: `runs/v11_B_base_openrouter_20261110T155639965393.json`, `runs/v11_B_group_openrouter_20261110T155710873989.json`. Thay đổi duy nhất: thêm tool mới `url_check` (`tools/url_check/`, `TOOL.md`, đăng ký trong `tools/__init__.py`, khai báo trong `tools.yaml`, `tools_hash` `593371f5d762`). Tool phân tích tĩnh chuỗi URL, không mở trang, trả về `verdict` (`safe`, `suspicious`, `invalid`), `reasons` và `warnings`. Mô tả: chỉ dùng khi người dùng hỏi về độ an toàn của link, không dùng để đọc nội dung và không gọi trước mỗi `fetch`. Kèm 7 unit test trong `tests/test_tools_todo.py` và case `G11_url_safety_check`.

Không có case nào FAIL (base 20/20, group 11/11). Tool mới không làm tụt R04, G08 hay các case `send`. Giới hạn: `safe` chỉ nghĩa là chuỗi URL không có dấu hiệu xấu, không đảm bảo trang đáng tin; danh sách thương hiệu giả mạo ngắn (9 tên).

### v12 — thêm tool `time_now`; base 1.00, group (12 case) 1.00

Nguồn: `runs/v12_B_base_openrouter_20261110T170944491573.json`, `runs/v12_B_group_openrouter_20261110T171017900498.json`. Thay đổi duy nhất: thêm tool mới `time_now` (`tools/time_now/`, `TOOL.md`, đăng ký trong `tools/__init__.py`, khai báo trong `tools.yaml`, `tools_hash` `673f131dba4e`, prompt giữ `907668ebe0f9`). Tool trả ngày giờ hiện tại theo giờ Việt Nam (UTC+7 cố định, không phụ thuộc cơ sở dữ liệu múi giờ) và khoảng ngày cho `today`, `yesterday`, `this_week` (thứ Hai đến Chủ nhật), `last_7_days`, `this_month`, kèm `timeframe_hint` khớp enum `timeframe` của `lookup`. Mô tả: chỉ dùng khi người dùng hỏi trực tiếp về ngày giờ; không gọi trước `lookup`. Kèm 6 unit test và case `G12_current_date_question`.

Không có case nào FAIL (base 20/20, group 12/12). Tool mới không làm `lookup` bị gọi thừa ở các case tin tức (R03, R13, M02) và không làm tụt các case `send`. Eval v12 được chạy với một file `.env` không có biến Telegram để các case `send` không gửi tin thật (sau khi cấu hình Telegram, chạy eval với `.env` đầy đủ sẽ gửi tin thật từ G01 và G09).

## B3. Team Eval Cases

List the cases added to `data/eval_group.json`: 12 cases (7 single turn + 5 multi turn; G11 và G12 là case cho hai tool mới `url_check` và `time_now`).

Kết quả v12 lấy từ `runs/v12_B_group_openrouter_20261110T171017900498.json` (12/12 = 1.00, **một lần chạy**). Cột v4 giữ lại từ `runs/v4_B_group_openrouter_20261110T143024579478.json` (8/10 = 0.80) để thấy tiến triển; mốc v3: 7/10 (`runs/v3_B_group_openrouter_20261110T142842637713.json`). Chi tiết các version ở giữa nằm ở B1 và B2.

| Case ID | What It Tests | Expected Tool/Behavior | Result (v4) | Result (v12) |
|---|---|---|---|---|
| G01_explicit_confirm_send | User đã xác nhận rõ thì phải gửi | `send(confirmed=true)` | PASS | PASS |
| G02_content_given_needs_confirm | Có nội dung nhưng chưa xác nhận thì phải xin xác nhận | `clarify(response_type=yes_no)` | FAIL: hỏi kênh Telegram bằng `text` | PASS |
| G03_handle_with_at_sign | Handle bỏ `@` | `timeline(screenname=karpathy)` | PASS | PASS |
| G04_papers_routing | Tìm paper học thuật thì dùng `papers`, không phải `lookup` | `papers` | PASS | PASS |
| G05_translate_out_of_scope | Việc không cần tool thì không gọi tool | không gọi tool | PASS | PASS |
| G06_social_to_web_switch | Đổi từ social sang web giữa hội thoại (multi-turn) | `lookup(query=Claude, topic=news, timeframe=week)` | PASS (v3: FAIL) | PASS |
| G07_web_to_social_switch | Đổi từ web sang social, `search_type=Top` (multi-turn) | `social_search(query=AI, search_type=Top)` | PASS | PASS |
| G08_missing_url_referenced | Ám chỉ link chưa từng đưa thì phải hỏi (multi-turn) | `clarify(response_type=text)` | FAIL: gọi `fetch(url="Link ở trên ấy")` | PASS |
| G09_multiturn_confirm_then_send | Xác nhận ở lượt cuối thì gửi (multi-turn) | `send(confirmed=true)` | PASS | PASS |
| G10_correct_account_keep_limit | Sửa tài khoản, giữ `limit` (multi-turn) | `timeline(screenname=satyanadella, limit=5)` | PASS | PASS |
| G11_url_safety_check | Hỏi về độ an toàn của link thì dùng tool mới, không `fetch` (single turn, case cho tool mới) | `url_check(url=http://192.168.1.5/login@paypal.com)` | (chưa có, tool thêm ở v11) | PASS |
| G12_current_date_question | Hỏi trực tiếp về ngày giờ hiện tại thì dùng tool mới, không `lookup` (single turn, case cho tool mới) | `time_now` | (chưa có, tool thêm ở v12) | PASS |

## B4. Live Chat Evidence

Nguồn: `transcripts/*.transcript.json`, ghi bởi UI (`app.py`) trên **v11** (`ui+p907668ebe0f9+t593371f5d762`). Bản cuối của nhóm là v12, chỉ khác v11 ở chỗ thêm tool `time_now`; prompt và mô tả các tool còn lại không đổi, nhưng **chưa có chat live nào ghi trên v12**. Có hai phiên chat live; phiên B (10 lượt) xảy ra sau khi cấu hình Telegram nên gửi được thật.

### Chat live trên v11

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| A1 | Link này có an toàn không: `http://192.168.1.5/login@paypal.com` | `url_check(url=...)` | `ui_openrouter_20261110T161358979733`, v11 | Đúng: dùng tool mới, trả lời link không an toàn kèm lý do (IP thuần, `@`), không mở link |
| A2 | Tôi là người việt nam | không gọi tool | như trên | Đúng: trả lời bằng chữ, không gọi tool thừa |
| A3 | Chủ tịch nước của nước tôi hiện tại là ai? | `lookup(query="Chủ tịch nước Việt Nam hiện tại", topic=news)` | như trên | Đúng routing (`lookup`, `topic=news`). Nội dung trả lời lấy từ kết quả tìm kiếm, chưa được nhóm kiểm chứng |
| A4 | viết cho tôi bài này lên tiwtter | `clarify(response_type=yes_no)` "đăng lên Twitter không?" | như trên | Hỏi xác nhận trước khi gửi (đúng quy trình). Nhưng agent nhận Twitter làm đích đến, trong khi `send` chỉ gửi Telegram: **lỗi** do mô tả `send` không nêu đích đến (chưa sửa, xem B6) |
| A5 | có | `clarify(response_type=text)` hỏi nội dung | như trên | Hỏi nội dung sau khi đã đồng ý, đúng thứ tự |
| A6 | Viết giúp tôi bài này: "Tôi là Bùi Anh Dũng" | `send(text=..., confirmed=true)` | như trên | `send` trả lỗi `Missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID` vì lúc đó `.env` chưa cấu hình Telegram; agent báo không đăng được và hỏi tài khoản Twitter. Đây là lỗi cấu hình, đã xử lý ở chat B |
| B1 | Tôi muốn đăng tin này lên telegrams | `clarify(response_type=yes_no)` "tiến hành đăng lên Telegram không?" | `ui_openrouter_20261110T163300310285`, v11 | Đúng: xin đồng ý trước, chưa gửi |
| B2 | có | không gọi tool, hỏi nội dung bằng chữ | như trên | Đúng thứ tự: đồng ý rồi mới hỏi nội dung |
| B3 | Nội dung của tôi là: "Tôi là BED" | `send(text="Tôi là BED", confirmed=true)` | như trên | `send` trả `status: sent`: **gửi Telegram thành công** sau khi đã xác nhận |
| B4 | đăng lên tiwtter cho tôi nhé | `clarify(response_type=yes_no)` "đăng lên Twitter không?" | như trên | Xin đồng ý trước (đúng quy trình), nhưng nhận Twitter làm đích dù `send` chỉ gửi Telegram |
| B5 | có | không gọi tool, hỏi nội dung bằng chữ | như trên | Hỏi nội dung sau khi đồng ý |
| B6 | vẫn là nội dung ở trên | `send(text="Tôi là BED", confirmed=true)` → `status: sent` | như trên | **Lỗi trung thực**: tin thực chất được gửi tới **Telegram**, nhưng agent trả lời "đã đăng lên Twitter thành công" |
| B7 | đăng nội dung tương tự lên facebook | `clarify(response_type=yes_no)` "đăng lên Facebook không?" | như trên | Xin đồng ý trước; nhận Facebook làm đích (sai) |
| B8 | có | `send(text="Tôi là BED", confirmed=true)` → `status: sent` | như trên | Đã có nội dung nên gửi ngay (đúng thứ tự), nhưng lại báo "đã đăng lên Facebook thành công" trong khi tin đi vào Telegram: **lỗi như B6** |
| B9 | Tóm tắt bài này giúp mình | không gọi tool, hỏi URL bằng chữ | như trên | Đúng: thiếu URL thì hỏi, không bịa |
| B10 | `https://claude.ai/artifact/TXhnQtJbnoTXAW8k4GbuEu` (gửi ở lượt sau) | `fetch(url=...)` | như trên | Đúng: đọc trang và tóm tắt nội dung ("Lịch nhóm AI20K"). Kiểu "thiếu thông tin rồi bổ sung" trên v11 |

Nhận xét: cả ba kiểu README yêu cầu đều có chat live trên v11 (research A3; thiếu thông tin rồi bổ sung B9 và B10; đăng/gửi B1 đến B3). Lỗi đáng chú ý nhất là B6 và B8: `send` chỉ gửi Telegram nhưng agent báo đã đăng lên Twitter hoặc Facebook, tức là báo sai đích đến cho người dùng; mô tả `send` chưa nêu đích đến (chưa sửa).

### Replay trên các version cũ (không phải chat live)

Các transcript của v0, v3, v6 không được ghi lúc làm. Để có so sánh, nhóm chạy lại **cùng một bộ lượt hỏi** qua agent thật (gọi API và tool thật) trên snapshot đã lưu của từng version bằng `scripts/replay_chats.py`. Kết quả nằm trong `transcripts/replay/` (16 file, mỗi file gắn nhãn `<version>-replay` và `"replay": true`). Đây là **replay có kịch bản**, không phải cuộc trò chuyện thật; câu trả lời của model là thật nhưng có thể khác khi chạy lại.

| Hội thoại (lượt hỏi) | v0 | v3 | v6 | v11 |
|---|---|---|---|---|
| Tin công nghệ nổi bật trong tuần này | `lookup` (news, week) | `lookup` | `lookup` | `lookup` |
| "Tóm tắt bài này giúp mình" (chưa có URL) | **bịa URL**: `fetch(example.com/article)` | hỏi URL bằng chữ | hỏi URL bằng chữ | hỏi URL bằng chữ |
| Lượt sau gửi `https://openai.com/blog/gpt-5` | `fetch` | `fetch` | `fetch` | `fetch` |
| "Đăng bản tin này lên Telegram giúp mình" | **`send` ngay**, chưa xác nhận | hỏi nội dung (`text`) | hỏi nội dung (`text`) | `clarify yes_no` xin đồng ý |
| "Link này có an toàn không: `http://192.168.1.5/login@paypal.com`" | `lookup` | **`fetch` link đáng ngờ** | trả lời bằng suy đoán, không gọi tool | `url_check` |

Ghi chú: trang `openai.com/blog/gpt-5` trả lỗi 404 ở mọi version nên lượt "gửi URL" cho kết quả 404; ở lượt gửi Telegram trong replay, bước `send` cuối báo lỗi thiếu biến Telegram vì lúc replay `.env` chưa cấu hình.

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `transcripts/ui_openrouter_20261110T163300310285.transcript.json` (chat live v11), `runs/v12_B_group_openrouter_20261110T171017900498.json` (G01, G02, G09), `runs/v12_B_base_openrouter_20261110T170944491573.json` (R12), `tools/send/tool.py` | Agent xin đồng ý trước (`clarify yes_no`), hỏi nội dung sau, rồi mới `send(confirmed=true)`; tool trả `status: sent` và tin tới Telegram. Code `send` trả `needs_confirmation` khi chưa có `confirmed=true`. Các case xác nhận (R12, G01, G02, G09) đều PASS ở v12 (cũng PASS ở v11), nhưng mỗi bản chỉ chạy một lần | `confirmed=true` do model tự đặt dựa trên việc hiểu người dùng đã đồng ý; code chỉ kiểm tra cờ này, không kiểm tra lời đồng ý thật. Chat live A (v11) cho thấy agent nhầm đích sang Twitter vì mô tả `send` không nêu đích đến, chưa sửa. `send` gửi kiểu Markdown nên ký tự như `_` hoặc `*` lẻ có thể bị Telegram từ chối. Bot chỉ gửi vào một chat cấu hình sẵn trong `.env` |
| arXiv/company policy | `runs/v12_B_group_openrouter_20261110T171017900498.json` (case G04) | Chỉ có `papers`: G04 ("paper mới về mixture of experts trên arXiv") route đúng tới `papers`, không phải `lookup`, PASS ở v12 | **`policy` và `paper_text` chưa được nhóm chứng minh**: chỉ nằm trong `eval_research_extension.json` (chưa chạy) và không xuất hiện trong transcript nào. Không tính là bằng chứng bonus |
| UI | `app.py`, `tests/test_app.py`, link demo ở Phần A, `transcripts/ui_openrouter_*.transcript.json` | UI Streamlit nhận câu hỏi, hiển thị câu trả lời cùng mục "Tool đã gọi", dừng chờ khi agent hỏi lại, và ghi transcript cùng định dạng với `chat.py`. Chạy được qua Cloudflare Tunnel | Link `trycloudflare.com` chỉ sống khi tiến trình `cloudflared` và Streamlit trên máy nhóm còn chạy. UI dùng key trong `.env` của máy chạy, nên không đưa `.env` vào repo |
| Tool unit tests (`tests/`) | `pytest` output: **101 passed, 17 skipped** | 19 test cho ba tool mới trong `tests/test_tools_todo.py`: 6 test `save_note` (không ghi khi chưa xác nhận; `confirmed` dạng chuỗi bị từ chối; ghi đúng tiêu đề và nội dung; tiêu đề không thoát được khỏi thư mục `notes/`; nội dung rỗng hoặc quá dài trả `error`; không ghi đè ghi chú có sẵn), 6 test `time_now` (ngày và thứ, tuần từ thứ Hai, hôm qua và 7 ngày qua, tháng 12, `timeframe_hint`, `when` sai trả `error`) và 7 test `url_check`: URL sạch, IP thuần cộng `@`, scheme lạ, tên miền giả thương hiệu (và tên miền thật không bị báo nhầm), chuỗi mơ hồ, đầu vào rỗng hoặc sai kiểu, link rút gọn chỉ là cảnh báo | 17 test còn lại trong `test_tools_todo.py` vẫn `skip` (phần challenge cho tool có sẵn, nhóm chưa làm) |

Tool unit tests: nhóm viết **19 test** (7 cho `url_check`, 6 cho `time_now`, 6 cho `save_note`). Với tool có sẵn, nhóm **không viết test** mà chỉ **dò bug** bằng cách gọi từng tool với input biên mà model hay gửi (`limit=0`, `top_k=0`, `confirmed` dạng chuỗi, `items` sai kiểu...) và mock `requests` để chạy offline. Kết quả: **8 bug/hành vi sai trong tool có sẵn**. Nhóm **chưa sửa** chúng (giữ nguyên tool của starter) nên cũng **chưa có test hồi quy**; vì vậy phần Challenge+ (sửa bug và giữ test) chưa hoàn thành, mục này chỉ ghi lại bằng chứng.

| # | Tool | Input | Hành vi thực tế | Mong đợi | Mức độ |
|---|---|---|---|---|---|
| 1 | `send` | `confirmed="false"` (cũng `"no"`, `"0"`) | **Gửi thật** (có POST tới Telegram), vì chỉ kiểm tra `if not confirmed` và chuỗi không rỗng là truthy | Chỉ gửi khi đúng `confirmed=True` | **Cao**: lách được rào xác nhận. Chỉ `False`, `0`, `None` mới chặn |
| 2 | `send` | `text=""`, `confirmed=True` | Vẫn gửi request tới Telegram | Trả lỗi vì không có nội dung | Thấp |
| 3 | `format` | `items=["abc"]` hoặc `items=[{"summary": 5}]` | Ném `AttributeError` (các tool khác bọc `try/except` và trả dict `error`) | Trả dict có `error`, không raise | Trung bình |
| 4 | `format` | item có `"section": null` | Sinh tiêu đề `## None` | Dùng mặc định "Tổng hợp" | Thấp |
| 5 | `timeline`, `social_search` | `limit=0` | Trả 5 item (coi `0` là mặc định) | Trả 0 item hoặc báo lỗi | Thấp |
| 6 | `timeline`, `social_search` | `limit=-1` (trên 7 item) | Trả 6 item (bỏ item cuối do cắt `items[:-1]`) | Báo lỗi hoặc coi như 0 | Thấp |
| 7 | `timeline` | `screenname="@karpathy"` hoặc `""` | Gửi nguyên `@karpathy` lên API; chuỗi rỗng vẫn gọi API | Bỏ `@`; từ chối chuỗi rỗng | Trung bình (model phải tự bỏ `@`, case G03 chỉ kiểm tra model làm việc đó) |
| 8 | `lookup`, `policy` | `max_results=-1` hoặc `1000`; `top_k=0`; `policy_area="khong_co_nhom"` | `lookup` gửi nguyên `-1` và `1000` lên API; `policy` với `top_k=0` vẫn trả 3 kết quả, với `policy_area` sai trả 0 kết quả mà không báo lỗi | Giới hạn giá trị; báo lỗi khi nhóm không tồn tại | Thấp |

Một ví dụ hành vi mà unit test kiểm tra được còn eval thì không: `url_check(url=None)` hoặc `url=""` phải trả dict có `error` thay vì ném lỗi. Eval case chỉ đưa URL hợp lệ vào tool nên không bao giờ chạm tới nhánh này; đây là nhánh lỗi được kiểm tra, chứ không phải bug đã bắt được. Bug #1 ở trên cũng là loại lỗi mà eval không bắt được: model luôn gửi `confirmed` là boolean, nên chỉ input chuỗi do test cố tình tạo ra mới lộ lỗi.

Về điểm thưởng ([README dòng 39](../../README.md)): cần UI **và hơn 3 tool mới**. Nhóm có UI nhưng chỉ có **3 tool mới** (`url_check`, `time_now`, `save_note`), chưa đủ "hơn 3", nên **không** đủ điều kiện điểm thưởng và nhóm không tuyên bố điểm thưởng. `save_note` chưa có case eval và chưa được chạy eval.

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?** Các luật hành vi chung, áp dụng cho nhiều tool cùng lúc. v1 bỏ chỉ dẫn "tự đoán" ở dòng 3 để agent hỏi lại khi thiếu thông tin (R10, R11). v3 và v4 sửa dòng 5 và dòng 7 của starter (cứ gửi ngay, ép làm trong một bước), nhưng riêng hai bản này chưa sửa được R12. v7 thêm đoạn RESEARCH/ACTION: chọn nguồn theo yêu cầu mới nhất (mạng xã hội hay web) và buộc câu xác nhận là một câu `yes_no` riêng; đoạn này sửa G06, M02 và R12 mà không làm tụt các case out-of-scope.
- **Which fixes belonged in `tools.yaml`?** Các luật riêng của từng tool. v2 và v6 sửa mô tả `response_type` của `clarify` (v2 để model điền trường này, v6 tách `yes_no` cho hành động ghi/gửi với `text` cho việc đọc/tra cứu, sửa R12). v5, v8 và v10 viết lại mô tả `send` (nơi nhận cấu hình sẵn, xin đồng ý trước, đã đồng ý thì gửi ngay `confirmed=true`; v10 gom thành hai trạng thái và ổn định nhất). v9 sửa mô tả `fetch` theo ba nhánh (URL rõ thì đọc; mơ hồ thì hỏi; có dấu hiệu độc hại thì từ chối bằng chữ), sửa G08. v11 thêm tool mới `url_check`, v12 thêm tool mới `time_now`; sau v12 thêm `save_note` (chưa chạy eval). Nhận xét chung: lỗi ở tham số hoặc cách dùng một tool thì sửa ở mô tả tool; lỗi giữa nhiều luật giẫm lên nhau (xác nhận với thiếu thông tin) thì sửa ở prompt.
- **Which failure needed manual review instead of automatic grading?** (1) Case R03 ở v0: model gọi đúng `lookup(topic=news)` nhưng `query="AI news"` thay vì `"AI"`; eval so khớp chuỗi tuyệt đối nên tính FAIL dù hành vi chấp nhận được, cần xem tay. (2) Các case R12, G01, G06, M02 đổi PASS/FAIL khi thay đổi không liên quan tới chúng, nghi là dao động của model (ví dụ G06 PASS ở v4 và v5, FAIL ở v6 dù v6 chỉ sửa mô tả `clarify`; M02 FAIL ở v5 rồi PASS ở v6), nên một lần chạy không đủ để kết luận cải thiện hay hồi quy; cần chạy lại hoặc đọc log từng case. (3) Nội dung câu trả lời (ví dụ ai là Chủ tịch nước ở chat live A3) không được eval chấm, chỉ chấm tool và đối số.
- **What would you improve next?** (1) Sửa mô tả `send` để nêu rõ đích đến chỉ là Telegram: chat live A cho thấy agent nhận Twitter làm đích. (2) Chạy lại v10, v11 và v12 nhiều lần để kiểm tra độ ổn định, vì kết quả 20/20 và 12/12 hiện là một lần chạy. (3) Mở rộng `url_check` (danh sách thương hiệu hiện chỉ 9 tên) hoặc để `fetch` tự kiểm tra URL trong code thay vì chỉ dựa vào model. (4) Chạy eval trên `tools.yaml` hiện tại (sau v12 đã viết lại mô tả tám tool starter và thêm `save_note`) để chắc routing không tụt, và thêm case eval cho `save_note`. (5) Thêm tool mới (cần hơn 3 tool mới để đủ điều kiện điểm thưởng, hiện có 3) và hoàn thành 17 test còn `skip` nếu nhóm muốn làm bonus; ghi lại chat live trên v12.

## B7. Small Local Model Challenge (bonus)

**Nhóm không thực hiện Small Local Model Challenge** (bonus tùy chọn). Nhóm chưa cài Ollama, chưa chạy model local nào, nên chưa có run, số liệu hay phân loại lỗi cho mục này. Các bảng bên dưới được để trống, không điền số.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
