"""Build a single self-contained HTML dashboard from the lab's logs.

Reads (all local, nothing is uploaded):
  - runs/*.json                      eval runs written by run_eval.py
  - artifacts/version_log.csv        version history filled by the team
  - artifacts/system_prompt.md       current prompt
  - artifacts/tools.yaml             current tool declarations
  - artifacts/snapshots/<version>/   saved prompt+tools per version (scripts/snapshot_version.py)
  - ../OutComeRequiredment.md        requirement checklist (progress tab)

Writes analysis/dashboard.html. Re-run after every eval:
  python scripts/build_dashboard.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
MAX_TOOL_RESULT_CHARS = 1500


def shorten(value, limit=MAX_TOOL_RESULT_CHARS):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    return text if len(text) <= limit else text[:limit] + f"... [cắt, tổng {len(text)} ký tự]"


def load_runs(runs_dir: Path) -> list[dict]:
    runs = []
    for path in sorted(runs_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"skip {path.name}: {exc}")
            continue
        if "results" not in data or "summary" not in data:
            continue
        cases = []
        for item in data["results"]:
            res = item.get("result", {})
            cases.append({
                "id": item.get("id"),
                "multiturn": bool(item.get("is_multiturn")),
                "what": (item.get("metadata") or {}).get("what_it_tests", ""),
                "input": item.get("input"),
                "expect": item.get("expect"),
                "passed": bool(res.get("passed")),
                "failure_type": res.get("failure_type"),
                "mismatch": res.get("observed_mismatch"),
                "failures": res.get("failures", []),
                "actual_calls": res.get("actual_tool_calls", []),
                "actual_text": res.get("actual_text"),
                "tool_results": [shorten(r) for r in (item.get("tool_results") or [])],
            })
        runs.append({
            "file": path.name,
            "path": f"runs/{path.name}",
            "version": data.get("version", ""),
            "suite": data.get("suite", ""),
            "provider": data.get("provider", ""),
            "model": data.get("model", ""),
            "generated_at": data.get("generated_at", ""),
            "artifact_version": data.get("artifact_version", ""),
            "prompt_hash": (data.get("prompt_hash") or "")[:12],
            "tools_hash": (data.get("tools_hash") or "")[:12],
            "dataset": data.get("dataset_id", ""),
            "summary": data.get("summary", {}),
            "cases": cases,
        })
    runs.sort(key=lambda r: r["generated_at"])
    return runs


def load_version_log(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle) if any((v or "").strip() for v in row.values())]


def load_progress(path: Path) -> list[dict]:
    if not path.exists():
        return []
    items, section = [], ""
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^#{2,3}\s+(.*)", line)
        if heading:
            section = heading.group(1).strip()
            continue
        row = re.match(r"^\|\s*\[( |x)\]\s*\|\s*(.+?)\s*\|", line)
        if row:
            text = re.sub(r"[`*]", "", row.group(2))
            items.append({"section": section, "done": row.group(1) == "x", "text": text})
    return items


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_blobs(artifacts: Path) -> dict[str, str]:
    """Map 12-char sha256 -> file text, for every snapshot plus the current files.

    Runs only store hashes, so the dashboard looks the text up by hash to show
    the code diff between two versions. Hash is computed on raw bytes (same as
    versioning.file_hash); the text is stored with LF line endings for display.
    """
    paths = list((artifacts / "snapshots").rglob("*"))  # any depth: snapshots/<version>/ or snapshots/<member>/<version>/
    paths += [artifacts / "system_prompt.md", artifacts / "tools.yaml"]
    blobs: dict[str, str] = {}
    for path in paths:
        if not path.is_file():
            continue
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()[:12]
        blobs.setdefault(digest, raw.decode("utf-8").replace("\r\n", "\n"))
    return blobs


TEMPLATE = r"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Eval Dashboard E305_PDT</title>
<style>
:root{
  --bg:#f6f7f9; --panel:#ffffff; --text:#1c2330; --muted:#5d6879; --line:#dfe3ea;
  --accent:#2f5fd0; --pass:#177245; --pass-bg:#e3f5ea; --fail:#b3261e; --fail-bg:#fbe7e5;
  --warn:#8a5a00; --warn-bg:#fff2d6; --none-bg:#eef0f4;
  --c1:#2f5fd0; --c2:#c2410c; --c3:#177245; --c4:#7c3aed;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#12151b; --panel:#1a1f28; --text:#e6e9ef; --muted:#98a2b3; --line:#2b3240;
    --accent:#7aa2ff; --pass:#5fd493; --pass-bg:#16301f; --fail:#ff8a80; --fail-bg:#3a1d1b;
    --warn:#f5c25b; --warn-bg:#3a2e14; --none-bg:#232834;
    --c1:#7aa2ff; --c2:#fb923c; --c3:#5fd493; --c4:#b79cff;
  }
}
:root[data-theme="dark"]{
  --bg:#12151b; --panel:#1a1f28; --text:#e6e9ef; --muted:#98a2b3; --line:#2b3240;
  --accent:#7aa2ff; --pass:#5fd493; --pass-bg:#16301f; --fail:#ff8a80; --fail-bg:#3a1d1b;
  --warn:#f5c25b; --warn-bg:#3a2e14; --none-bg:#232834;
  --c1:#7aa2ff; --c2:#fb923c; --c3:#5fd493; --c4:#b79cff;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header{padding:16px;border-bottom:1px solid var(--line);background:var(--panel)}
header h1{margin:0;font-size:18px}
header p{margin:2px 0 0;color:var(--muted);font-size:12px}
.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:10px}
nav{display:flex;gap:4px;flex-wrap:wrap;padding:8px 16px 0;background:var(--panel);border-bottom:1px solid var(--line)}
nav button{border:0;background:none;color:var(--muted);padding:8px 12px;cursor:pointer;font:inherit;border-bottom:2px solid transparent}
nav button[aria-selected="true"]{color:var(--text);border-bottom-color:var(--accent);font-weight:600}
main{padding:16px;max-width:1200px;margin:0 auto}
section.tab{display:none}
section.tab.on{display:block}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.card h3{margin:0 0 4px;font-size:12px;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.04em}
.big{font-size:28px;font-weight:700}
.delta{font-size:12px;font-weight:600}
.up{color:var(--pass)} .down{color:var(--fail)} .flat{color:var(--muted)}
h2{font-size:15px;margin:22px 0 8px}
table{border-collapse:collapse;width:100%;background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;font-size:13px}
th{background:var(--none-bg);font-size:12px;color:var(--muted)}
tr:last-child td{border-bottom:0}
.wrap{overflow-x:auto}
code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px}
pre{background:var(--none-bg);padding:10px;border-radius:8px;overflow:auto;white-space:pre-wrap;word-break:break-word;margin:6px 0}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;font-size:11px;font-weight:700}
.p-pass{background:var(--pass-bg);color:var(--pass)}
.p-fail{background:var(--fail-bg);color:var(--fail)}
.p-warn{background:var(--warn-bg);color:var(--warn)}
.p-none{background:var(--none-bg);color:var(--muted)}
.cell{cursor:pointer;text-align:center;min-width:74px}
.cell:hover{outline:2px solid var(--accent);outline-offset:-2px}
.cell.sel{outline:2px solid var(--accent);outline-offset:-2px}
select,input[type=checkbox]{font:inherit}
select{padding:5px 8px;border:1px solid var(--line);border-radius:6px;background:var(--panel);color:var(--text)}
label{color:var(--muted);font-size:12px}
.btn{border:1px solid var(--line);background:var(--panel);color:var(--text);padding:5px 10px;border-radius:6px;cursor:pointer;font:inherit}
.detail{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-top:12px}
.detail h3{margin:0 0 6px;font-size:14px}
.kv{display:grid;grid-template-columns:130px 1fr;gap:4px 10px;margin:6px 0}
.kv div:nth-child(odd){color:var(--muted);font-size:12px}
.prog{height:8px;background:var(--none-bg);border-radius:99px;overflow:hidden}
.prog>i{display:block;height:100%;background:var(--accent)}
.muted{color:var(--muted)}
.empty{padding:24px;text-align:center;color:var(--muted);background:var(--panel);border:1px dashed var(--line);border-radius:10px}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;margin-top:6px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px}
svg text{fill:var(--muted);font-size:11px}
.diff{background:var(--panel);border:1px solid var(--line);border-radius:8px;overflow:auto;padding:4px 0;margin:6px 0 14px}
.dl{display:block;white-space:pre-wrap;word-break:break-word;padding:0 10px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px}
.dl.add{background:var(--pass-bg);color:var(--pass)}
.dl.del{background:var(--fail-bg);color:var(--fail)}
.dl.gap{background:var(--none-bg);color:var(--muted);font-style:italic}
.two{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
textarea.md{width:100%;min-height:200px;font:12px ui-monospace,Menlo,Consolas,monospace;background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:8px;padding:8px}
.tag{font-size:11px;font-weight:700}
@media (max-width:600px){ .kv{grid-template-columns:1fr} }
</style>
</head>
<body>
<header>
  <h1>Eval Dashboard — Team E305_PDT</h1>
  <p id="meta"></p>
  <div class="bar">
    <label>Suite <select id="suiteSel"></select></label>
    <button class="btn" id="themeBtn" type="button">Đổi giao diện sáng/tối</button>
  </div>
</header>
<nav role="tablist" id="tabs"></nav>
<main>
  <section class="tab" id="t-overview"></section>
  <section class="tab" id="t-matrix"></section>
  <section class="tab" id="t-compare"></section>
  <section class="tab" id="t-versions"></section>
  <section class="tab" id="t-progress"></section>
  <section class="tab" id="t-files"></section>
</main>
<script>
const DATA = __DATA__;
const $ = (s, r=document) => r.querySelector(s);
const esc = v => String(v ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const pct = v => v == null ? "–" : (v*100).toFixed(0) + "%";
const METRICS = [
  ["case_accuracy","Case đúng","--c1"],
  ["tool_routing_accuracy","Chọn tool","--c2"],
  ["argument_accuracy","Đúng args","--c3"],
  ["multiturn_accuracy","Multi-turn","--c4"],
];
let suite = "all";
let sel = null;

const TABS = [["overview","Tổng quan"],["matrix","Ma trận case"],["compare","So sánh 2 version"],["versions","Version"],["progress","Tiến độ"],["files","Prompt & Tools"]];
function buildTabs(){
  const nav = $("#tabs");
  nav.innerHTML = TABS.map(([id,l],i)=>`<button role="tab" data-t="${id}" aria-selected="${i===0}">${l}</button>`).join("");
  nav.onclick = e => { const b = e.target.closest("button"); if(!b) return; show(b.dataset.t); };
  show("overview");
}
function show(id){
  document.querySelectorAll("#tabs button").forEach(b=>b.setAttribute("aria-selected", b.dataset.t===id));
  document.querySelectorAll("section.tab").forEach(s=>s.classList.toggle("on", s.id==="t-"+id));
}
const runs = () => DATA.runs.filter(r => suite==="all" || r.suite===suite);

function delta(cur, prev){
  if(cur==null || prev==null) return `<span class="delta flat">–</span>`;
  const d = Math.round((cur-prev)*100);
  if(d===0) return `<span class="delta flat">= không đổi</span>`;
  return `<span class="delta ${d>0?"up":"down"}">${d>0?"▲ +":"▼ "}${d} điểm so với lần trước</span>`;
}

function chart(rs){
  if(rs.length===0) return "";
  const W=700,H=240,L=40,R=16,T=14,B=44;
  const n = rs.length, step = n>1 ? (W-L-R)/(n-1) : 0;
  const x = i => n>1 ? L+i*step : (W+L-R)/2;
  const y = v => T+(1-v)*(H-T-B);
  let g = "";
  for(const t of [0,.25,.5,.75,1]) g += `<line x1="${L}" x2="${W-R}" y1="${y(t)}" y2="${y(t)}" stroke="var(--line)"/><text x="${L-6}" y="${y(t)+4}" text-anchor="end">${t*100}%</text>`;
  rs.forEach((r,i)=>{ g += `<text x="${x(i)}" y="${H-24}" text-anchor="middle">${esc(r.version)}</text><text x="${x(i)}" y="${H-10}" text-anchor="middle">${esc(r.suite)}</text>`; });
  METRICS.forEach(([k,,c])=>{
    const pts = rs.map((r,i)=>[i,r.summary[k]]).filter(p=>p[1]!=null);
    if(pts.length>1) g += `<polyline fill="none" stroke="var(${c})" stroke-width="2" points="${pts.map(p=>x(p[0])+","+y(p[1])).join(" ")}"/>`;
    pts.forEach(p=>{ g += `<circle cx="${x(p[0])}" cy="${y(p[1])}" r="4" fill="var(${c})"><title>${esc(rs[p[0]].version)} — ${k}: ${pct(p[1])}</title></circle>`; });
  });
  const legend = METRICS.map(([,l,c])=>`<span><i style="background:var(${c})"></i>${l}</span>`).join("");
  return `<div class="card"><h3>Metric theo từng lần chạy</h3><div class="wrap"><svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Biểu đồ metric theo version">${g}</svg></div><div class="legend">${legend}</div></div>`;
}

function renderOverview(){
  const rs = runs(), el = $("#t-overview");
  if(!rs.length){ el.innerHTML = `<div class="empty">Chưa có file run nào trong <code>runs/</code>. Chạy <code>run_eval.py</code> rồi build lại dashboard.</div>`; return; }
  const last = rs[rs.length-1], prev = rs.length>1 ? rs[rs.length-2] : null;
  const cards = METRICS.map(([k,l])=>`<div class="card"><h3>${l}</h3><div class="big">${pct(last.summary[k])}</div>${delta(last.summary[k], prev?.summary[k])}</div>`).join("");
  const fc = last.summary.failure_counts || {}, om = last.summary.observed_mismatch_counts || {};
  const rowsOf = o => Object.keys(o).length ? Object.entries(o).map(([k,v])=>`<tr><td><code>${esc(k)}</code></td><td>${v}</td></tr>`).join("") : `<tr><td colspan="2" class="muted">Không có</td></tr>`;
  const fails = last.cases.filter(c=>!c.passed);
  const failRows = fails.length ? fails.map(c=>`<tr><td><a href="#" data-goto="${esc(c.id)}">${esc(c.id)}</a></td><td><span class="pill p-fail">${esc(c.failure_type||"")}</span></td><td>${esc(c.mismatch||"")}</td><td>${c.failures.map(esc).join("<br>")}</td></tr>`).join("") : `<tr><td colspan="4" class="muted">Tất cả case đều pass</td></tr>`;
  el.innerHTML = `
    <h2>Lần chạy mới nhất: <code>${esc(last.version)}</code> · ${esc(last.suite)} · ${esc(last.model)}</h2>
    <p class="muted">${esc(last.generated_at)} · ${last.summary.passed_cases}/${last.summary.measured_cases} case pass · <code>${esc(last.artifact_version)}</code> · <a href="../${esc(last.path)}">${esc(last.file)}</a></p>
    <div class="grid">${cards}</div>
    <h2>Biểu đồ</h2>${chart(rs)}
    <h2>Case FAIL của lần chạy mới nhất (${fails.length})</h2>
    <div class="wrap"><table><thead><tr><th>Case</th><th>Loại lỗi (theo thiết kế case)</th><th>Sai lệch quan sát</th><th>Chi tiết</th></tr></thead><tbody>${failRows}</tbody></table></div>
    <div class="grid" style="margin-top:12px">
      <div><h2>failure_counts</h2><table><tbody>${rowsOf(fc)}</tbody></table></div>
      <div><h2>observed_mismatch_counts</h2><table><tbody>${rowsOf(om)}</tbody></table></div>
    </div>`;
  el.querySelectorAll("[data-goto]").forEach(a=>a.onclick=e=>{ e.preventDefault(); show("matrix"); pick(rs.length-1, a.dataset.goto); });
}

function renderMatrix(){
  const rs = runs(), el = $("#t-matrix");
  if(!rs.length){ el.innerHTML = `<div class="empty">Chưa có run.</div>`; return; }
  const ids = []; rs.forEach(r=>r.cases.forEach(c=>{ if(!ids.includes(c.id)) ids.push(c.id); }));
  const onlyFail = $("#onlyFail")?.checked;
  const rows = ids.filter(id => !onlyFail || rs.some(r=>{ const c=r.cases.find(x=>x.id===id); return c && !c.passed; }));
  const head = rs.map(r=>`<th class="cell">${esc(r.version)}<br><span class="muted">${esc(r.suite)}</span></th>`).join("");
  const body = rows.map(id=>{
    const tds = rs.map((r,i)=>{
      const c = r.cases.find(x=>x.id===id);
      if(!c) return `<td class="cell"><span class="pill p-none">–</span></td>`;
      const s = sel && sel.i===i && sel.id===id ? " sel" : "";
      return `<td class="cell${s}" data-i="${i}" data-id="${esc(id)}"><span class="pill ${c.passed?"p-pass":"p-fail"}">${c.passed?"PASS":"FAIL"}</span></td>`;
    }).join("");
    const first = rs.map(r=>r.cases.find(x=>x.id===id)).find(Boolean);
    return `<tr><td><code>${esc(id)}</code>${first?.multiturn?` <span class="pill p-none">multi</span>`:""}</td>${tds}</tr>`;
  }).join("");
  el.innerHTML = `
    <div class="bar"><label><input type="checkbox" id="onlyFail" ${onlyFail?"checked":""}> Chỉ hiện case có lần FAIL</label>
    <span class="muted">Bấm vào ô PASS/FAIL để xem chi tiết bên dưới.</span></div>
    <div class="wrap" style="margin-top:8px"><table><thead><tr><th>Case</th>${head}</tr></thead><tbody>${body}</tbody></table></div>
    <div id="detail"></div>`;
  $("#onlyFail").onchange = renderMatrix;
  el.querySelectorAll("td.cell[data-id]").forEach(td=>td.onclick=()=>pick(+td.dataset.i, td.dataset.id));
  if(sel) renderDetail();
}
function pick(i, id){ sel = {i,id}; renderMatrix(); $("#detail")?.scrollIntoView({behavior:"smooth",block:"nearest"}); }

function renderDetail(){
  const rs = runs(), r = rs[sel.i]; if(!r) return;
  const c = r.cases.find(x=>x.id===sel.id); if(!c) return;
  const input = Array.isArray(c.input) ? c.input.map((t,k)=>`${k+1}. [${t.role}] ${t.content}`).join("\n") : c.input;
  const j = v => JSON.stringify(v, null, 2);
  const calls = c.actual_calls.length ? j(c.actual_calls) : "(không gọi tool nào)";
  const trs = c.tool_results.length ? c.tool_results.map((t,k)=>`<details><summary>Kết quả tool #${k+1}</summary><pre>${esc(t)}</pre></details>`).join("") : `<span class="muted">Không có</span>`;
  $("#detail").innerHTML = `<div class="detail">
    <h3>${esc(c.id)} · ${esc(r.version)} <span class="pill ${c.passed?"p-pass":"p-fail"}">${c.passed?"PASS":"FAIL"}</span></h3>
    <div class="kv">
      <div>Kiểm tra gì</div><div>${esc(c.what)||"–"}</div>
      <div>Loại lỗi (case)</div><div>${esc(c.failure_type)||"–"}</div>
      <div>Sai lệch quan sát</div><div>${esc(c.mismatch)||"–"}</div>
      <div>Lý do FAIL</div><div>${c.failures.length?c.failures.map(esc).join("<br>"):"–"}</div>
      <div>Input</div><div><pre>${esc(input)}</pre></div>
      <div>Mong đợi</div><div><pre>${esc(j(c.expect))}</pre></div>
      <div>Thực tế (tool calls)</div><div><pre>${esc(calls)}</pre></div>
      <div>Text model trả</div><div>${c.actual_text?`<pre>${esc(c.actual_text)}</pre>`:"–"}</div>
      <div>Output của tool</div><div>${trs}</div>
    </div></div>`;
}

function renderVersions(){
  const el = $("#t-versions");
  const log = DATA.version_log;
  const logRows = log.length ? log.map(r=>`<tr><td><code>${esc(r.version)}</code></td><td>${esc(r.changed_artifact)}</td><td>${esc(r.reason)}</td><td>${esc(r.hypothesis)}</td><td>${esc(r.metric_before)||"–"}</td><td>${esc(r.metric_after)||"–"}</td><td><code>${esc(r.run_file)}</code></td></tr>`).join("") : `<tr><td colspan="7" class="muted">version_log.csv chưa có dòng nào</td></tr>`;
  const runFiles = new Set(DATA.runs.map(r=>r.path));
  const loggedFiles = new Set(log.map(r=>r.run_file));
  const missing = DATA.runs.filter(r=>!loggedFiles.has(r.path));
  const runRows = DATA.runs.map(r=>`<tr><td><code>${esc(r.version)}</code></td><td>${esc(r.suite)}</td><td>${esc(r.model)}</td><td>${pct(r.summary.case_accuracy)}</td><td><code>${esc(r.prompt_hash)}</code></td><td><code>${esc(r.tools_hash)}</code></td><td>${esc(r.generated_at)}</td><td>${loggedFiles.has(r.path)?`<span class="pill p-pass">đã ghi</span>`:`<span class="pill p-warn">chưa ghi vào CSV</span>`}</td></tr>`).join("");
  const dangling = log.filter(r=>r.run_file && !runFiles.has(r.run_file));
  el.innerHTML = `
    <h2>version_log.csv</h2>
    <div class="wrap"><table><thead><tr><th>Version</th><th>Sửa</th><th>Lý do</th><th>Giả thuyết</th><th>Trước</th><th>Sau</th><th>Run file</th></tr></thead><tbody>${logRows}</tbody></table></div>
    ${missing.length?`<p><span class="pill p-warn">Cảnh báo</span> ${missing.length} run chưa có trong version_log.csv: ${missing.map(r=>`<code>${esc(r.version)}</code>`).join(", ")}</p>`:""}
    ${dangling.length?`<p><span class="pill p-fail">Lỗi</span> Dòng CSV trỏ tới file không tồn tại: ${dangling.map(r=>`<code>${esc(r.run_file)}</code>`).join(", ")}</p>`:""}
    <h2>Mọi lần chạy trong runs/</h2>
    <div class="wrap"><table><thead><tr><th>Version</th><th>Suite</th><th>Model</th><th>Case đúng</th><th>prompt hash</th><th>tools hash</th><th>Thời điểm</th><th>CSV</th></tr></thead><tbody>${runRows||`<tr><td colspan="8" class="muted">Chưa có run</td></tr>`}</tbody></table></div>`;
}

function renderProgress(){
  const el = $("#t-progress"), items = DATA.progress;
  if(!items.length){ el.innerHTML = `<div class="empty">Không tìm thấy OutComeRequiredment.md</div>`; return; }
  const secs = []; items.forEach(it=>{ let s = secs.find(x=>x.name===it.section); if(!s){ s={name:it.section,items:[]}; secs.push(s);} s.items.push(it); });
  const done = items.filter(i=>i.done).length;
  el.innerHTML = `<div class="card"><h3>Tổng tiến độ</h3><div class="big">${done}/${items.length}</div><div class="prog"><i style="width:${done/items.length*100}%"></i></div></div>` +
    secs.map(s=>{ const d = s.items.filter(i=>i.done).length; return `<h2>${esc(s.name)} <span class="muted">${d}/${s.items.length}</span></h2><div class="prog"><i style="width:${d/s.items.length*100}%"></i></div><ul style="list-style:none;padding:0;margin:8px 0">${s.items.map(i=>`<li>${i.done?"✅":"⬜"} ${esc(i.text)}</li>`).join("")}</ul>`; }).join("");
}

function renderFiles(){
  $("#t-files").innerHTML = `<h2>system_prompt.md (hiện tại)</h2><pre>${esc(DATA.prompt)}</pre><h2>tools.yaml (hiện tại)</h2><pre>${esc(DATA.tools)}</pre>`;
}

/* ---------- So sánh 2 version ---------- */
let cmp = {a:null, b:null};
const FENCE = "```";
const splitLines = s => (s ?? "").split(/\r?\n/);
function diffLines(a, b){
  const n=a.length, m=b.length, dp=Array.from({length:n+1}, () => new Uint16Array(m+1));
  for(let i=n-1;i>=0;i--) for(let j=m-1;j>=0;j--) dp[i][j] = a[i]===b[j] ? dp[i+1][j+1]+1 : Math.max(dp[i+1][j], dp[i][j+1]);
  const out=[]; let i=0, j=0;
  while(i<n && j<m){
    if(a[i]===b[j]){ out.push([" ",a[i]]); i++; j++; }
    else if(dp[i+1][j] >= dp[i][j+1]) out.push(["-",a[i++]]);
    else out.push(["+",b[j++]]);
  }
  while(i<n) out.push(["-",a[i++]]);
  while(j<m) out.push(["+",b[j++]]);
  return out;
}
function diffOf(hashA, hashB){
  const ta = DATA.blobs[hashA], tb = DATA.blobs[hashB];
  if(ta==null || tb==null) return null;
  return diffLines(splitLines(ta), splitLines(tb));
}
function diffCount(d){ return [d.filter(x=>x[0]==="+").length, d.filter(x=>x[0]==="-").length]; }
function renderDiff(title, hashA, hashB){
  if(hashA===hashB) return `<h3>${title}</h3><p class="muted">Không đổi (hash <code>${esc(hashA)}</code>)</p>`;
  const d = diffOf(hashA, hashB);
  if(!d) return `<h3>${title}</h3><p><span class="pill p-warn">Thiếu snapshot</span> Không có nội dung cho hash <code>${esc(hashA)}</code> hoặc <code>${esc(hashB)}</code>. Chạy <code>python scripts/snapshot_version.py &lt;version&gt;</code> ngay sau khi sửa xong mỗi version.</p>`;
  const keep = new Array(d.length).fill(false);
  d.forEach((x,i)=>{ if(x[0]!==" ") for(let k=Math.max(0,i-2); k<=Math.min(d.length-1,i+2); k++) keep[k]=true; });
  let html="", gap=0;
  d.forEach((x,i)=>{
    if(keep[i]){
      if(gap){ html += `<span class="dl gap">… ${gap} dòng không đổi</span>`; gap=0; }
      const c = x[0]==="+" ? "add" : x[0]==="-" ? "del" : "";
      html += `<span class="dl ${c}">${x[0]===" " ? "  " : x[0]+" "}${esc(x[1])}</span>`;
    } else gap++;
  });
  if(gap) html += `<span class="dl gap">… ${gap} dòng không đổi</span>`;
  const [add, del] = diffCount(d);
  return `<h3>${title} <span class="muted"><code>${esc(hashA)}</code> → <code>${esc(hashB)}</code></span> <span class="pill p-pass">+${add}</span> <span class="pill p-fail">−${del}</span></h3><div class="diff">${html}</div>`;
}
function callStr(calls){
  if(!calls || !calls.length) return "(không gọi tool)";
  const s = calls.map(c=>`${c.name}(${Object.entries(c.args||{}).map(([k,v])=>k+"="+JSON.stringify(v)).join(", ")})`).join(" + ");
  return s.length>200 ? s.slice(0,200)+"…" : s;
}
function expectStr(e){
  if(!e) return "";
  if(e.no_tool) return "không gọi tool (" + (e.behavior||"") + ")";
  return (e.tool_calls||[]).map(c=>`${c.name}(${Object.entries(c.args||{}).map(([k,v])=>k+"="+JSON.stringify(v)).join(", ")})`).join(" + ");
}
function compareData(A, B){
  const cases = [];
  A.cases.forEach(ca=>{ const cb = B.cases.find(x=>x.id===ca.id); if(cb) cases.push({id:ca.id, a:ca, b:cb}); });
  return {
    fixed:      cases.filter(c=>!c.a.passed &&  c.b.passed),
    regressed:  cases.filter(c=> c.a.passed && !c.b.passed),
    stillFail:  cases.filter(c=>!c.a.passed && !c.b.passed),
    stillPass:  cases.filter(c=> c.a.passed &&  c.b.passed),
    onlyA: A.cases.filter(ca=>!B.cases.some(x=>x.id===ca.id)),
    onlyB: B.cases.filter(cb=>!A.cases.some(x=>x.id===cb.id)),
  };
}
function failTxt(c){ return c.passed ? "PASS" : `FAIL — ${(c.failures||[]).join("; ")}`; }
function markdownReport(A, B, g){
  const L = [];
  const tag = r => `${r.version} (${r.suite}, ${r.artifact_version})`;
  L.push(`## So sánh ${A.version} → ${B.version}`, "");
  L.push(`- ${tag(A)}`, `- ${tag(B)}`, "");
  L.push(`**Đã đổi:** prompt ${A.prompt_hash===B.prompt_hash?"không đổi":"ĐỔI"}, tools ${A.tools_hash===B.tools_hash?"không đổi":"ĐỔI"}`, "");
  L.push("| Metric | "+A.version+" | "+B.version+" | Δ |", "|---|---:|---:|---:|");
  METRICS.forEach(([k,l])=>{ const x=A.summary[k], y=B.summary[k]; L.push(`| ${l} | ${pct(x)} | ${pct(y)} | ${x==null||y==null?"–":(Math.round((y-x)*100)>0?"+":"")+Math.round((y-x)*100)+" điểm"} |`); });
  L.push("");
  const list = (title, arr, fn) => { L.push(`**${title} (${arr.length})**`); if(!arr.length) L.push("- không có"); arr.forEach(c=>L.push("- "+fn(c))); L.push(""); };
  list(`Sửa được (FAIL → PASS)`, g.fixed, c=>`${c.id}: trước lỗi ${c.a.failures.join("; ")}`);
  list(`Hồi quy (PASS → FAIL)`, g.regressed, c=>`${c.id}: ${c.b.failures.join("; ")}`);
  list(`Vẫn FAIL ở ${B.version}`, g.stillFail, c=>`${c.id} [${c.b.mismatch||c.b.failure_type||""}]: ${c.b.failures.join("; ")} — thực tế ${callStr(c.b.actual_calls)}`);
  [["Prompt", A.prompt_hash, B.prompt_hash], ["Tools", A.tools_hash, B.tools_hash]].forEach(([name,ha,hb])=>{
    if(ha===hb) return;
    const d = diffOf(ha, hb);
    L.push(`**Thay đổi ${name}** (${ha} → ${hb})`);
    if(!d){ L.push("(thiếu snapshot)", ""); return; }
    L.push(FENCE+"diff");
    d.filter(x=>x[0]!==" ").forEach(x=>L.push(x[0]+" "+x[1]));
    L.push(FENCE, "");
  });
  return L.join("\n");
}
function renderCompare(){
  const rs = runs(), el = $("#t-compare");
  if(rs.length<2){ el.innerHTML = `<div class="empty">Cần ít nhất 2 run (cùng suite) để so sánh. Hiện có ${rs.length}.</div>`; return; }
  if(cmp.a==null || cmp.a>=rs.length) cmp.a = rs.length-2;
  if(cmp.b==null || cmp.b>=rs.length) cmp.b = rs.length-1;
  const A = rs[cmp.a], B = rs[cmp.b], g = compareData(A, B);
  const opts = i => rs.map((r,k)=>`<option value="${k}" ${k===i?"selected":""}>${esc(r.version)} · ${esc(r.suite)} · ${esc(r.generated_at.slice(11))}</option>`).join("");
  const mrows = METRICS.map(([k,l])=>{
    const x=A.summary[k], y=B.summary[k];
    let d = `<span class="flat">–</span>`;
    if(x!=null && y!=null){ const p=Math.round((y-x)*100); d = p===0 ? `<span class="flat">0</span>` : `<span class="${p>0?"up":"down"}">${p>0?"▲ +":"▼ "}${p} điểm</span>`; }
    return `<tr><td>${l}</td><td>${pct(x)}</td><td>${pct(y)}</td><td>${d}</td></tr>`;
  }).join("");
  const diffRow = (c, cls, label) => `<tr><td><code>${esc(c.id)}</code> ${c.a.multiturn?`<span class="pill p-none">multi</span>`:""}</td><td><span class="pill ${cls}">${label}</span></td><td>${c.a.passed?`<span class="pill p-pass">PASS</span>`:`<span class="pill p-fail">FAIL</span> ${c.a.failures.map(esc).join("<br>")}`}<br><code>${esc(callStr(c.a.actual_calls))}</code></td><td>${c.b.passed?`<span class="pill p-pass">PASS</span>`:`<span class="pill p-fail">FAIL</span> ${c.b.failures.map(esc).join("<br>")}`}<br><code>${esc(callStr(c.b.actual_calls))}</code></td><td><code>${esc(expectStr(c.b.expect))}</code></td></tr>`;
  const rows = [
    ...g.regressed.map(c=>diffRow(c,"p-fail","HỒI QUY")),
    ...g.fixed.map(c=>diffRow(c,"p-pass","ĐÃ SỬA")),
    ...g.stillFail.map(c=>diffRow(c,"p-warn","VẪN FAIL")),
  ].join("");
  const failList = (R, other) => {
    const fails = R.cases.filter(c=>!c.passed);
    return `<div class="card"><h3>${esc(R.version)} đang bị lỗi (${fails.length}/${R.cases.length})</h3>` + (fails.length ? `<ul style="margin:6px 0;padding-left:18px">${fails.map(c=>`<li><code>${esc(c.id)}</code> <span class="pill p-fail">${esc(c.mismatch||c.failure_type||"")}</span><br><span class="muted">${c.failures.map(esc).join("; ")}</span></li>`).join("")}</ul>` : `<p class="muted">Không có lỗi</p>`) + `</div>`;
  };
  const md = markdownReport(A, B, g);
  el.innerHTML = `
    <div class="bar">
      <label>Version A (trước) <select id="cmpA">${opts(cmp.a)}</select></label>
      <label>Version B (sau) <select id="cmpB">${opts(cmp.b)}</select></label>
      <button class="btn" id="cmpSwap" type="button">⇄ Đảo</button>
    </div>
    <p class="muted"><code>${esc(A.artifact_version)}</code> → <code>${esc(B.artifact_version)}</code> · prompt ${A.prompt_hash===B.prompt_hash?"không đổi":"<b>ĐỔI</b>"} · tools ${A.tools_hash===B.tools_hash?"không đổi":"<b>ĐỔI</b>"}</p>
    <h2>Metric</h2>
    <div class="wrap"><table><thead><tr><th>Chỉ số</th><th>${esc(A.version)}</th><th>${esc(B.version)}</th><th>Thay đổi</th></tr></thead><tbody>${mrows}</tbody></table></div>
    <div class="grid" style="margin-top:12px">
      <div class="card"><h3>Đã sửa</h3><div class="big up">${g.fixed.length}</div></div>
      <div class="card"><h3>Hồi quy</h3><div class="big ${g.regressed.length?"down":""}">${g.regressed.length}</div></div>
      <div class="card"><h3>Vẫn FAIL</h3><div class="big">${g.stillFail.length}</div></div>
      <div class="card"><h3>Vẫn PASS</h3><div class="big">${g.stillPass.length}</div></div>
    </div>
    <h2>Mỗi version đang bị lỗi gì</h2>
    <div class="two">${failList(A)}${failList(B)}</div>
    <h2>Case thay đổi / còn lỗi</h2>
    ${rows ? `<div class="wrap"><table><thead><tr><th>Case</th><th>Trạng thái</th><th>${esc(A.version)}</th><th>${esc(B.version)}</th><th>Mong đợi</th></tr></thead><tbody>${rows}</tbody></table></div>` : `<div class="empty">Không có case nào đổi trạng thái hoặc còn lỗi.</div>`}
    ${g.onlyA.length||g.onlyB.length ? `<p class="muted">Case chỉ có ở một bên: A ${g.onlyA.length}, B ${g.onlyB.length} (bỏ qua khi so sánh).</p>` : ""}
    <h2>Khác biệt code</h2>
    ${renderDiff("system_prompt.md", A.prompt_hash, B.prompt_hash)}
    ${renderDiff("tools.yaml", A.tools_hash, B.tools_hash)}
    <h2>Bản markdown dán vào báo cáo</h2>
    <button class="btn" id="cmpCopy" type="button">Sao chép</button> <span class="muted" id="cmpCopied"></span>
    <textarea class="md" id="cmpMd" readonly>${esc(md)}</textarea>`;
  $("#cmpA").onchange = e => { cmp.a = +e.target.value; renderCompare(); };
  $("#cmpB").onchange = e => { cmp.b = +e.target.value; renderCompare(); };
  $("#cmpSwap").onclick = () => { [cmp.a, cmp.b] = [cmp.b, cmp.a]; renderCompare(); };
  $("#cmpCopy").onclick = async () => {
    const ta = $("#cmpMd"); let ok = false;
    try { await navigator.clipboard.writeText(ta.value); ok = true; } catch(e) { ta.select(); try { ok = document.execCommand("copy"); } catch(e2) {} }
    $("#cmpCopied").textContent = ok ? "Đã sao chép" : "Không sao chép được, hãy chọn và Ctrl+C";
  };
}

function renderAll(){ renderOverview(); renderMatrix(); renderCompare(); renderVersions(); renderProgress(); renderFiles(); }

function init(){
  $("#meta").textContent = `Tạo lúc ${DATA.built_at} · ${DATA.runs.length} run · dữ liệu đọc trực tiếp từ runs/, artifacts/ (chạy lại scripts/build_dashboard.py để cập nhật)`;
  const suites = [...new Set(DATA.runs.map(r=>r.suite))];
  $("#suiteSel").innerHTML = `<option value="all">Tất cả</option>` + suites.map(s=>`<option>${esc(s)}</option>`).join("");
  $("#suiteSel").onchange = e => { suite = e.target.value; sel = null; cmp = {a:null,b:null}; renderAll(); };
  $("#themeBtn").onclick = () => {
    const root = document.documentElement, dark = root.dataset.theme==="dark" || (!root.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
    root.dataset.theme = dark ? "light" : "dark";
  };
  buildTabs(); renderAll();
}
init();
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build analysis/dashboard.html from lab logs.")
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "runs")
    parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "dashboard.html")
    args = parser.parse_args()

    data = {
        "built_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "runs": load_runs(args.runs_dir),
        "version_log": load_version_log(ROOT / "artifacts" / "version_log.csv"),
        "progress": load_progress(REPO / "OutComeRequiredment.md"),
        "prompt": read_text(ROOT / "artifacts" / "system_prompt.md"),
        "tools": read_text(ROOT / "artifacts" / "tools.yaml"),
        "blobs": load_blobs(ROOT / "artifacts"),
    }
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.replace("__DATA__", payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(f"Wrote {args.output} ({len(data['runs'])} runs, {len(data['version_log'])} version rows, "
          f"{len(data['progress'])} checklist items)")


if __name__ == "__main__":
    main()
