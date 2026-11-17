"""Render an analysis result as a self-contained HTML page with English charts."""
from __future__ import annotations

import html
import json

A_COL, B_COL = "#2a78d6", "#eb6834"

_PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Behavioral Chat report — __TITLE__</title>
<style>
:root{--bg:#fbfbf9;--card:#fff;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--line:#e1e0d9;--border:rgba(11,11,11,.1)}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--card:#1c1c1b;--ink:#f0efec;--ink2:#c3c2b7;--muted:#898781;--line:#2c2c2a;--border:rgba(255,255,255,.1)}}
body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,"Segoe UI",Vazirmatn,Tahoma,sans-serif;line-height:1.6}
.wrap{max-width:960px;margin:0 auto;padding:28px 20px 60px}h1{font-size:23px;font-weight:500;margin:0}
h2{font-size:18px;font-weight:500;margin:0 0 8px}.sub{color:var(--ink2);font-size:14px}
section{background:var(--card);border:.5px solid var(--border);border-radius:12px;padding:18px 20px;margin-top:16px}
.legend{display:flex;gap:14px;font-size:12px;color:var(--ink2);margin:4px 0 8px}.sw{width:10px;height:10px;border-radius:2px;display:inline-block;margin-right:5px}
.row .top{display:flex;justify-content:space-between;font-size:13px;margin-bottom:3px}.row .top i{font-style:normal;color:var(--ink2)}
.bar{display:flex;height:13px;gap:2px;margin-bottom:10px}.chart{position:relative;height:260px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,400px),1fr));gap:18px}
table{width:100%;border-collapse:collapse;font-size:13px}td,th{padding:5px 6px;border-bottom:.5px solid var(--line);text-align:left}
th{font-weight:500;color:var(--muted)}.note{font-size:13px;color:var(--ink2)}
</style></head><body><div class="wrap">
<h1>__TITLE__</h1><div class="sub">__SUB__</div>
<section><h2>Every factor, for both people</h2>
<div class="legend"><span><i class="sw" style="background:__A_COL__"></i>__A__</span><span><i class="sw" style="background:__B_COL__"></i>__B__</span></div>
<div id="splits"></div></section>
<section><h2>Conversation volume and trend</h2><div class="chart"><canvas id="vol"></canvas></div>
<p class="note">Messages per day, by week. Dashed lines extend the recent trend; they are not a prediction.</p></section>
<section class="grid"><div><h2>Warm behaviours per week</h2><div class="chart"><canvas id="warm"></canvas></div></div>
<div><h2>Tension behaviours per week</h2><div class="chart"><canvas id="tense"></canvas></div></div></section>
<section><h2>Alignment and balance</h2><div class="chart"><canvas id="al"></canvas></div>
<p class="note">Alignment: share of warm messages out of warm + tension messages (both people). Balance: how even the two people's
messages, questions and warm messages were (100 = even). Dotted lines show scenario levels: same pattern, early pattern returns,
tension drops 80%.</p></section>
<section><h2>Replies slower than one hour</h2><div class="chart" style="height:220px"><canvas id="slow"></canvas></div></section>
<section class="grid"><div><h2>Emerging words: __A__</h2><table id="ewA"></table></div><div><h2>Emerging words: __B__</h2><table id="ewB"></table></div></section>
<section><h2>Method and limits</h2><p class="note">__METHOD__</p></section>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.js"></script>
<script>
const D=__DATA__, A=D.meta.participants[0], B=D.meta.participants[1], AC="__A_COL__", BC="__B_COL__";
const dark=matchMedia('(prefers-color-scheme: dark)').matches, grid=dark?'#2c2c2a':'#e1e0d9', ink='#898781';
Chart.defaults.color=ink;Chart.defaults.font.size=11;
const cats=D.meta.categories, W=D.weekly, L=W.labels.map(l=>{const i=l.indexOf(' ');return [l.slice(0,i),l.slice(i+1)]}), n=L.length;
const keys=["messages","characters","questions","media_total","restarts_after_silence",...Object.keys(cats)];
const names={messages:"Messages",characters:"Characters written",questions:"Questions asked",media_total:"Photos, videos & media",restarts_after_silence:"Restarts after a silence"};
document.getElementById('splits').innerHTML=keys.map(k=>{const a=D.totals[A][k]||0,b=D.totals[B][k]||0,t=a+b||1;
 return `<div class="row"><div class="top"><span>${names[k]||cats[k].label}</span><i>${a.toLocaleString()} · ${b.toLocaleString()}</i></div>
 <div class="bar"><div style="width:${a/t*100}%;background:${AC};border-radius:4px 0 0 4px"></div><div style="width:${b/t*100}%;background:${BC};border-radius:0 4px 4px 0"></div></div></div>`}).join('');
const sum=(p,g)=>Array.from({length:n},(_,i)=>Object.keys(cats).filter(c=>cats[c].group===g).reduce((s,c)=>s+(W[p][c]?W[p][c][i]:0),0));
const opt=(extra={})=>({responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{position:'bottom'}},
 scales:{x:{grid:{display:false},ticks:{maxRotation:0,autoSkip:true}},y:{beginAtZero:true,grid:{color:grid},border:{display:false},...extra}}});
const line=(label,data,col,dash)=>({label,data,borderColor:col,backgroundColor:col,borderWidth:2,pointRadius:2.5,tension:.25,borderDash:dash||[]});
const proj=(p)=>{const pr=D.trend[p].projection||[];return pr.length?Array(n-1).fill(null).concat([W[p].messages_per_day[n-1]],pr):[]};
const L2=L.concat((D.trend[A].projection||[]).map((_,i)=>['W'+(n+i+1),'trend']));
new Chart(document.getElementById('vol'),{type:'line',data:{labels:L2,datasets:[line(A,W[A].messages_per_day,AC),line(A+' trend',proj(A),AC,[6,4]),line(B,W[B].messages_per_day,BC),line(B+' trend',proj(B),BC,[6,4])]},options:opt()});
new Chart(document.getElementById('warm'),{type:'line',data:{labels:L,datasets:[line(A,sum(A,'warm'),AC),line(B,sum(B,'warm'),BC)]},options:opt()});
new Chart(document.getElementById('tense'),{type:'line',data:{labels:L,datasets:[line(A,sum(A,'tension'),AC,[6,4]),line(B,sum(B,'tension'),BC,[6,4])]},options:opt()});
const S=D.scenarios, flat=v=>v==null?[]:Array(n).fill(v);
new Chart(document.getElementById('al'),{type:'line',data:{labels:L,datasets:[line('Alignment',W.alignment,'#52514e'),line('Balance',W.balance,'#898781',[2,3]),
 {...line('Same pattern',flat(S.same_pattern),'#1baf7a',[3,4]),pointRadius:0},{...line('Early pattern returns',flat(S.early_pattern_returns),'#c98500',[3,4]),pointRadius:0},
 {...line('Tension drops 80%',flat(S.tension_drops_80pct),'#6250d6',[3,4]),pointRadius:0}]},options:opt({min:0,max:100})});
new Chart(document.getElementById('slow'),{type:'line',data:{labels:L,datasets:[line(A,W[A].slow_reply_pct,AC),line(B,W[B].slow_reply_pct,BC)]},options:opt({ticks:{callback:v=>v+'%'}})});
const ew=(id,p)=>{const r=D.emerging_words[p]||[];document.getElementById(id).innerHTML='<tr><th>Word</th><th>First seen</th><th>Uses</th></tr>'+
 (r.length?r.map(w=>`<tr><td>${w.word.replace(/</g,'&lt;')}</td><td>${w.first_seen}</td><td>${w.total}</td></tr>`).join(''):'<tr><td colspan="3">None</td></tr>')};
ew('ewA',A);ew('ewB',B);
</script></body></html>"""


def render_html(result: dict, title: str | None = None) -> str:
    m = result["meta"]
    a, b = m["participants"]
    title = title or f"{a} & {b}"
    sub = (f"{m['start'][:10]} – {m['end'][:10]} · {m['messages_analyzed']:,} messages · "
           f"{m['relationship_type']} · keyword-based, approximate")
    method = " ".join(result["method"].values())
    data = json.dumps({k: result[k] for k in ("meta", "totals", "weekly", "trend", "scenarios", "emerging_words")},
                      ensure_ascii=False).replace("</", "<\\/")
    out = _PAGE
    for key, val in {
        "__TITLE__": html.escape(title), "__SUB__": html.escape(sub), "__A__": html.escape(a),
        "__B__": html.escape(b), "__A_COL__": A_COL, "__B_COL__": B_COL, "__METHOD__": html.escape(method),
    }.items():
        out = out.replace(key, val)
    return out.replace("__DATA__", data)
