from __future__ import annotations

import json
import os
import hmac
from uuid import uuid4

import streamlit as st

import chat
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from ui_helpers import MODEL, ROOT, available_versions, guarded_executor, load_runs, redact, resolve_send
from versioning import artifact_version_dict, build_artifact_version


st.set_page_config(page_title="Research Lab", page_icon="🔎", layout="wide")

# Public tunnel uses the same UI; require the configured access code before data/API access.
access_code = os.getenv('UI_ACCESS_CODE', '')
if access_code and not st.session_state.get('authenticated'):
    st.title('Research Lab · Đăng nhập demo')
    with st.form('access'):
        entered = st.text_input('Mã truy cập', type='password')
        submitted = st.form_submit_button('Mở demo')
    if submitted:
        if hmac.compare_digest(entered.encode(), access_code.encode()):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error('Mã truy cập chưa đúng.')
    st.stop()
st.markdown("""<style>
.stApp {background: #f5f8f9; color: #152c34;}
.block-container {max-width: 1200px; padding-top: 2rem;}
h1, h2, h3 {letter-spacing: -.025em;}
[data-testid="stMetric"] {background: white; border: 1px solid #dbe6e8;
border-radius: 14px; padding: 18px;}
[data-testid="stSidebar"] {background: #e9f2f1;}
.stButton>button[kind="primary"] {background: #087f73; border-color: #087f73;}
</style>""", unsafe_allow_html=True)


def new_session() -> None:
    session_id = f"ui_{selected_version}_{uuid4().hex}"
    st.session_state.history = []
    st.session_state.messages = []
    st.session_state.pop("pending_send", None)
    st.session_state.transcript_path = ROOT / "transcripts" / f"{session_id}.transcript.json"
    st.session_state.transcript = {
        "transcript_id": session_id,
        **artifact_version_dict(build_artifact_version(selected_version, PROMPT, TOOLS)),
        "provider": "gemini", "model": MODEL,
        "system_prompt": str(PROMPT.relative_to(ROOT)), "tools": str(TOOLS.relative_to(ROOT)),
        "created_at": chat.now_iso(), "source": "streamlit", "turns": [],
    }


def save_turn(record: dict) -> None:
    record = redact(record)
    record["turn_index"] = len(st.session_state.transcript["turns"]) + 1
    record["ended_at"] = chat.now_iso()
    st.session_state.transcript["turns"].append(record)
    chat.write_transcript(st.session_state.transcript_path, st.session_state.transcript)


selected_version = st.sidebar.selectbox('Phiên bản agent', available_versions())
PROMPT = ROOT / 'artifacts' / selected_version / 'system_prompt.md'
TOOLS = ROOT / 'artifacts' / selected_version / 'tools.yaml'
if "transcript" not in st.session_state or st.session_state.transcript.get('version') != selected_version:
    new_session()

with st.sidebar:
    st.subheader("🔎 Research Lab")
    st.caption(f"ARTIFACT / {selected_version}")
    st.write("Gemini Flash-Lite")
    st.code(MODEL, language=None)
    st.caption("Mỗi phiên bản có prompt, tool và hash riêng. Đổi phiên bản sẽ mở hội thoại mới.")
    max_rounds = st.slider("Số vòng tool tối đa mỗi lượt", 1, 4, 3)
    if st.button("Cuộc trò chuyện mới", width="stretch"):
        new_session()
        st.rerun()
    st.divider()
    st.caption("Telegram: bản nháp → xem lại → xác nhận gửi.")
    st.caption("Lỗi 429: chờ hết thời gian giới hạn rồi thử lại. UI không tự lặp request.")

st.caption("RESEARCH AGENT / TOOL EVALUATION")
st.title("Tìm nguồn. Đọc tin. Kiểm chứng.")
st.write("Thử agent nghiên cứu và đối chiếu bằng chứng qua từng phiên bản.")
chat_tab, eval_tab = st.tabs(["💬 Trò chuyện", "📊 Đánh giá"])

with chat_tab:
    if not st.session_state.messages:
        st.info("Bắt đầu với: “Tìm 3 tin mới nhất về AI hôm nay” hoặc “Lấy 3 bài gần nhất của @sama”.")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("events"):
                with st.expander("Tool và kết quả thực tế"):
                    st.json(message["events"])

    if "pending_send" in st.session_state:
        with st.container(border=True):
            st.subheader("Duyệt tin Telegram")
            st.caption("Chỉ nội dung bên dưới sẽ được gửi vào chat đã cấu hình.")
            st.text(st.session_state.pending_send)
            approve, cancel = st.columns(2)
            approved = approve.button("Xác nhận gửi", type="primary", width="stretch")
            cancelled = cancel.button("Hủy gửi", width="stretch")
            if approved or cancelled:
                event = resolve_send(st.session_state, approved, chat.execute_tool_call)
                status = event["result"].get("status")
                answer = ("Đã gửi tin Telegram." if status == "sent" else
                          "Đã hủy gửi." if status == "cancelled" else "Gửi chưa thành công. Xem lỗi trong kết quả tool.")
                st.session_state.messages.append({"role": "assistant", "content": answer, "events": [event]})
                st.session_state.history.extend([
                    {"role": "user", "content": "Xác nhận gửi bản nháp." if approved else "Hủy gửi bản nháp."},
                    {"role": "assistant", "content": answer},
                ])
                save_turn({"user": "[UI] Xác nhận gửi" if approved else "[UI] Hủy gửi",
                           "status": status or "tool_error", "assistant_text": answer, "tool_events": [event]})
                st.rerun()

    ready = bool(os.getenv("GEMINI_API_KEY"))
    if not ready:
        st.warning("Thiếu GEMINI_API_KEY trong starter_v0/.env. Lưu key và khởi động lại UI.")
    user_text = st.chat_input("Bạn muốn nghiên cứu điều gì?", disabled=not ready or "pending_send" in st.session_state)
    if user_text:
        st.session_state.messages.append({"role": "user", "content": redact(user_text)})
        record = {"user": user_text, "started_at": chat.now_iso()}
        try:
            with st.spinner("Đang gọi Gemini và công cụ…"):
                result = chat.run_model_tool_loop(
                    provider=make_provider("gemini"),
                    messages=[{"role": "system", "content": PROMPT.read_text(encoding="utf-8")},
                              *chat.trim_history(st.session_state.history, 5), {"role": "user", "content": user_text}],
                    tools=to_openai_tools(load_tool_declarations(TOOLS)), model=MODEL,
                    max_tool_rounds=max_rounds,
                    tool_executor=guarded_executor(st.session_state, chat.execute_tool_call),
                )
            result = redact(result)
            answer = result["assistant_text"] or "Model chưa trả nội dung. Xem chi tiết tool hoặc thử yêu cầu khác."
            record.update(result)
            st.session_state.messages.append({"role": "assistant", "content": answer, "events": result["tool_events"]})
            context = answer + "\n\nTOOL_RESULTS_JSON:\n" + json.dumps(result["tool_events"], ensure_ascii=False)
            st.session_state.history.extend([{"role": "user", "content": user_text}, {"role": "assistant", "content": context}])
        except Exception as exc:
            detail = redact(str(exc))
            answer = ("Gemini đang giới hạn lượt gọi (429). Chờ theo hạn mức rồi thử lại." if "429" in detail else
                      "Không gọi được provider. Xem chi tiết lỗi và kiểm tra cấu hình.")
            record.update({"status": "provider_error", "error": detail, "assistant_text": answer})
            st.session_state.messages.append({"role": "assistant", "content": answer,
                                               "events": [{"provider_error": detail}]})
        save_turn(record)
        st.rerun()

    if st.session_state.transcript["turns"]:
        st.download_button("Tải transcript JSON", json.dumps(st.session_state.transcript, ensure_ascii=False, indent=2),
                           file_name=st.session_state.transcript_path.name, mime="application/json")

with eval_tab:
    runs = load_runs()
    if not runs:
        st.info("Chưa có run Gemini Flash-Lite trong thư mục runs/.")
    else:
        index = st.selectbox("Run thực tế", range(len(runs)), format_func=lambda i: runs[i][0].name)
        path, run = runs[index]
        summary = run["summary"]
        measured = summary["measured_cases"]
        a, b, c, d = st.columns(4)
        a.metric("Case đạt", f"{summary['passed_cases']}/{measured}")
        b.metric("Chọn tool đúng", f"{summary.get('tool_routing_accuracy', 0):.1%}")
        c.metric("Arguments đúng", f"{summary.get('argument_accuracy', 0):.1%}")
        d.metric("Lỗi API", summary["provider_error_cases"])
        st.caption(f"Đo được {measured}/{summary['total_cases']} ca. Accuracy loại trừ ca lỗi provider. Model: {run['model']}.")
        st.code(run["artifact_version"], language=None)
        if run.get("provenance"):
            st.info("Run tổng hợp: giữ nguyên các ca đã đo, chỉ chạy lại ca lỗi API. Nguồn được lưu trong JSON.")
        rows = []
        for case in run["results"]:
            result = case["result"]
            rows.append({"Case": case["id"], "Kết quả": "PASS" if result["passed"] else "FAIL",
                         "Loại lỗi (dataset)": result.get("failure_type") or "—",
                         "Sai lệch quan sát": result.get("observed_mismatch") or "—",
                         "Chi tiết": "; ".join(result.get("failures", []))})
        st.dataframe(redact(rows), width="stretch", hide_index=True)
        case_id = st.selectbox("Đọc log từng case", [case["id"] for case in run["results"]])
        st.json(redact(next(case for case in run["results"] if case["id"] == case_id)))
        st.download_button("Tải run JSON", json.dumps(redact(run), ensure_ascii=False, indent=2),
                           file_name=path.name, mime="application/json")
