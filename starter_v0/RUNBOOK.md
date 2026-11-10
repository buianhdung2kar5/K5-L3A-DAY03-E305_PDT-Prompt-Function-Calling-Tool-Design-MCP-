# Hướng dẫn chạy Research Agent

Mở PowerShell tại `starter_v0/`. Dùng Python trong `.venv`, không cần activate.
Các file tài liệu được lưu UTF-8; `.editorconfig` giúp IDE giữ đúng encoding.

## 1. Môi trường và key

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -X utf8 scripts/preflight_provider.py --provider gemini --model gemini-3.5-flash-lite
```

Key được đọc từ `.env`: `GEMINI_API_KEY`, `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`,
`RAPIDAPI_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. Không ghi đè hoặc commit `.env`.

## 2. Đọc bằng chứng v0–v3

- `artifacts/REPORT.md`: điểm, giả thuyết từng vòng, phân tích lỗi và hạn chế của bộ chấm.
- `artifacts/version_log.csv`: snapshot hash và metric trước/sau.
- `artifacts/v0/` đến `artifacts/v3/`: prompt/tools của từng lần đo.
- `runs/`: kết quả API thật. Run v0 resumed chỉ thay đúng 4 lỗi API; bản gốc còn nguyên.
- `data/eval_base.json`: giữ nguyên. `data/eval_group.json`: giữ 10 case người dùng, thêm T01–T10.

Đo một phiên bản đã chụp, ví dụ v3:

```powershell
.\.venv\Scripts\python.exe -X utf8 run_eval.py --provider gemini --model gemini-3.5-flash-lite --version v3 --system-prompt artifacts/v3/system_prompt.md --tools artifacts/v3/tools.yaml --suite base --case-delay 5
.\.venv\Scripts\python.exe -X utf8 run_eval.py --provider gemini --model gemini-3.5-flash-lite --version v3 --system-prompt artifacts/v3/system_prompt.md --tools artifacts/v3/tools.yaml --suite group --eval-cases data/eval_group.json --case-delay 5
```

Eval chạy tool thật. Các ca đã xác nhận có thể gửi tin Telegram vào chat cấu hình.
Không tự chạy lại chỉ để tìm điểm đẹp hơn. Khi có lỗi 429, đọc hạn mức/phút hoặc/ngày,
chờ đủ thời gian; không gọi lặp liên tục.

## 3. UI và mã truy cập

Mở **http://127.0.0.1:8501** nếu server đang chạy.
Mã truy cập nằm ở dòng `UI_ACCESS_CODE` trong `.env`; không đưa mã vào report hoặc Git.
Link public nếu đã khởi chạy được ghi trong `artifacts/ui_endpoint.json` và REPORT.
Tunnel tạm chỉ hoạt động khi máy, UI và cloudflared còn chạy.

Khởi động local nếu cần:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address=127.0.0.1 --server.port=8501 --server.headless=true --browser.gatherUsageStats=false
```

- Chọn **Phiên bản agent**; đổi phiên bản sẽ bắt đầu hội thoại mới với đúng snapshot.
- Nhập yêu cầu; mở trace để xem tool và kết quả thật.
- Tab **Đánh giá** hiển thị run base/group của các phiên bản, có expected/actual từng ca.
- Tin Telegram luôn được xem trước, chỉ gửi khi bấm **Xác nhận gửi**; **Hủy gửi** không gọi API.
- Tải transcript hoặc run JSON ngay trên UI. Transcript thật lưu trong `transcripts/`.
- Sau khi đổi key hoặc mã trong `.env`, khởi động lại UI.

## 4. Chat CLI và kiểm thử

```powershell
.\.venv\Scripts\python.exe -X utf8 chat.py --provider gemini --model gemini-3.5-flash-lite --version v3 --system-prompt artifacts/v3/system_prompt.md --tools artifacts/v3/tools.yaml
.\.venv\Scripts\python.exe -X utf8 -m pytest -q
```

Các test tool/UI đều offline, dùng fake provider và HTTP mock.
Live demo được lưu riêng; không tính test mock thành bằng chứng chạy thật.

## 5. Tạo lại report

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/update_evidence.py
```

Script đọc JSON thật và ghi UTF-8 trực tiếp, tránh mất dấu khi truyền tiếng Việt qua pipe PowerShell.
Tên thành viên/team và bằng chứng debate thực tế cần người dùng điền.
Small Local Model Challenge là bonus tùy chọn, chưa chạy trong phần bắt buộc này.
