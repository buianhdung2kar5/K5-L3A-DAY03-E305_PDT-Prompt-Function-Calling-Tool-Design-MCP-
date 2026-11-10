---
name: deduplicate
track: core
kind: local_formatter
provider: local
requires_env: []
inputs: [items]
outputs: [items, input_count, item_count, duplicate_count]
side_effect: false
requires_confirmation: false
---

# Gộp nguồn trùng URL

Dùng khi đã có danh sách nguồn và cần bỏ trùng trước khi định dạng bản tin.
Không tìm kiếm hoặc xác minh nội dung trên mạng. Giữ nguyên item xuất hiện đầu tiên.

Khóa so sánh bỏ fragment và tham số `utm_*`, `fbclid`, `gclid`, chuẩn hóa host/port mặc định
và thứ tự query. Giữ khác biệt về scheme, chữ hoa trong path, dấu `/` cuối path,
và tham số query có nghĩa; không suy đoán hai bài khác URL có cùng nội dung.

Nhận tối đa 200 object có URL HTTP(S). Sai kiểu, thiếu URL hoặc URL có credentials
trả error dict. Không mutate input, không gọi API, không ghi file.
