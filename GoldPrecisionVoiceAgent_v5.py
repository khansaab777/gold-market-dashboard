import json
import os
import time
import threading
import webbrowser
import urllib.request
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "10000"))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

_cache = {}
_lock = threading.Lock()

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Gold Precision Dashboard</title>
<style>
:root{
  --bg:#06090d;--panel:#0d141c;--panel2:#111b26;--line:#233244;--text:#f6f8fb;--muted:#8da0b6;
  --green:#39d98a;--red:#ff6b74;--orange:#ffb454;--blue:#67a8ff;--gold:#f0ca65;--cyan:#58d4e7;--violet:#ab8cff;
}
*{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at top,#111a25 0,#080d13 45%,#05080c 100%);color:var(--text);font-family:Inter,Segoe UI,Arial,sans-serif}
.wrap{max-width:1480px;margin:auto;padding:16px}
.top{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;flex-wrap:wrap}
.brand h1{margin:0;font-size:28px}.brand p{margin:5px 0 0;color:var(--muted);font-size:13px}
.controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
button{background:var(--panel2);border:1px solid var(--line);color:#fff;padding:9px 12px;border-radius:10px;cursor:pointer}
button.active{border-color:var(--blue);box-shadow:0 0 0 1px rgba(103,168,255,.25) inset}
.status,.source{font-size:11px;color:var(--muted)}
.source{display:inline-block;margin-top:8px;padding:5px 9px;border-radius:999px;background:rgba(103,168,255,.11);color:#a9ceff}
.banner{display:none;margin-top:12px;padding:10px 12px;border-radius:11px;border:1px solid rgba(255,180,84,.35);background:rgba(255,180,84,.08);color:#ffd49a;font-size:12px}
.card{background:linear-gradient(180deg,rgba(15,23,33,.99),rgba(11,17,24,.99));border:1px solid var(--line);border-radius:15px;padding:14px;box-shadow:0 8px 24px rgba(0,0,0,.22)}
.kicker{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.10em}
.value{font-size:23px;font-weight:780;margin-top:6px;font-variant-numeric:tabular-nums}
.sub{font-size:11px;color:var(--muted);margin-top:5px;line-height:1.4}
.green{color:var(--green)}.red{color:var(--red)}.orange{color:var(--orange)}.blue{color:var(--blue)}.cyan{color:var(--cyan)}
.hero{display:grid;grid-template-columns:1.25fr repeat(5,1fr);gap:10px;margin-top:13px}
.actionCard{border-width:1px;position:relative;overflow:hidden}.actionCard:before{content:"";position:absolute;inset:0 0 auto 0;height:3px;background:var(--orange)}
.actionBig{font-size:38px;font-weight:900;letter-spacing:.025em;margin-top:4px}
.scoreBar{height:7px;border-radius:99px;background:#1c2835;margin-top:10px;overflow:hidden}.scoreBar span{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--orange),var(--green))}
.main{display:grid;grid-template-columns:2fr .9fr;gap:10px;margin-top:10px}
.chartCard{padding:12px}.chartTop{display:flex;justify-content:space-between;gap:10px;align-items:center;flex-wrap:wrap}
.legend{display:flex;gap:12px;flex-wrap:wrap;color:var(--muted);font-size:11px}.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:4px}
.chartbox{height:560px;position:relative;margin-top:8px}
canvas{width:100%;height:100%;display:block}
.ohlc{position:absolute;left:10px;top:8px;background:rgba(6,9,13,.82);border:1px solid #223143;border-radius:9px;padding:7px 9px;font-size:11px;color:#c6d2df;pointer-events:none}
.sideStack{display:grid;gap:10px}
.checks{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:10px}
.check{padding:8px 9px;border-radius:9px;background:#0b121a;border:1px solid #203040;font-size:11px}
.check.ok{border-color:rgba(57,217,138,.45);color:#9ce9c2}.check.no{border-color:rgba(255,107,116,.35);color:#ffb1b6}
.planGrid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}.plan{background:#0b121a;border:1px solid #203040;border-radius:10px;padding:9px}.plan .value{font-size:17px}
.tfgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px}
.tfhead{display:flex;justify-content:space-between;align-items:center;gap:8px}.tfhead h2{margin:0;font-size:19px}.badge{padding:5px 8px;border-radius:999px;font-size:10px;font-weight:800}
.bull{background:rgba(57,217,138,.13);color:var(--green)}.bear{background:rgba(255,107,116,.13);color:var(--red)}.neutral{background:rgba(255,180,84,.12);color:var(--orange)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;margin-top:10px}.stat{background:#0b121a;border:1px solid #203040;border-radius:9px;padding:8px}.stat .value{font-size:15px}
.table{width:100%;border-collapse:collapse;margin-top:8px}.table th,.table td{padding:8px 6px;border-bottom:1px solid var(--line);font-size:11px;text-align:right;font-variant-numeric:tabular-nums}.table th:first-child,.table td:first-child{text-align:left}
.alert{margin-top:8px;padding:10px;border:1px solid #223244;border-radius:10px;background:#0b121a;font-size:12px;line-height:1.45}
footer{margin:14px 2px 2px;color:var(--muted);font-size:10px;line-height:1.5}
.agentFab{position:fixed;right:20px;bottom:20px;width:64px;height:64px;border-radius:50%;border:1px solid rgba(103,168,255,.55);background:linear-gradient(145deg,#17283a,#0e1823);color:#fff;font-size:26px;display:grid;place-items:center;cursor:pointer;box-shadow:0 12px 35px rgba(0,0,0,.45);z-index:30}
.agentFab.listening{border-color:var(--red);box-shadow:0 0 0 5px rgba(255,107,116,.13),0 12px 35px rgba(0,0,0,.45)}
.agentPanel{position:fixed;right:20px;bottom:94px;width:min(390px,calc(100vw - 24px));max-height:72vh;background:rgba(9,14,20,.985);border:1px solid #2a3a4d;border-radius:17px;box-shadow:0 20px 60px rgba(0,0,0,.55);z-index:29;display:none;overflow:hidden}
.agentPanel.open{display:flex;flex-direction:column}.agentHead{display:flex;justify-content:space-between;align-items:center;padding:12px 13px;border-bottom:1px solid #233244}.agentHead strong{font-size:14px}.agentHead span{font-size:10px;color:var(--muted)}
.agentLog{padding:11px;overflow:auto;min-height:220px;max-height:420px}.msg{max-width:90%;padding:9px 10px;border-radius:12px;margin:6px 0;font-size:12px;line-height:1.45;white-space:pre-wrap}.msg.user{margin-left:auto;background:#17304a;border:1px solid #254d72}.msg.agent{background:#111b26;border:1px solid #233244}.msg.alertMsg{background:rgba(255,180,84,.08);border-color:rgba(255,180,84,.35)}
.agentQuick{display:flex;gap:6px;flex-wrap:wrap;padding:0 11px 9px}.chip{padding:6px 8px;border:1px solid #27394c;border-radius:999px;background:#0d1620;color:#b9c8d8;font-size:10px;cursor:pointer}.chip:hover{border-color:#4a6c8e}
.agentInput{display:grid;grid-template-columns:1fr auto auto;gap:7px;padding:10px;border-top:1px solid #233244}.agentInput input{min-width:0;background:#0c141d;border:1px solid #27394c;border-radius:10px;color:#fff;padding:9px 10px}.agentInput button{padding:8px 10px}.agentSettings{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:8px 11px;border-top:1px solid #1d2a38;color:var(--muted);font-size:10px}.agentSettings select{background:#0c141d;color:#fff;border:1px solid #27394c;border-radius:8px;padding:5px}.toggle{display:flex;gap:5px;align-items:center}.agentPulse{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--green);margin-right:5px}
@media(max-width:680px){.agentFab{right:12px;bottom:12px}.agentPanel{right:12px;bottom:84px}.agentLog{max-height:46vh}}
@media(max-width:1120px){.hero{grid-template-columns:repeat(3,1fr)}.main{grid-template-columns:1fr}.tfgrid{grid-template-columns:1fr}.chartbox{height:470px}}
@media(max-width:680px){.wrap{padding:10px}.hero{grid-template-columns:1fr 1fr}.actionCard{grid-column:1/-1}.chartbox{height:420px}.stats{grid-template-columns:1fr 1fr}.checks{grid-template-columns:1fr}.planGrid{grid-template-columns:1fr 1fr}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div class="brand">
      <h1>Gold Precision Dashboard</h1>
      <p>High-confirmation market structure engine — fewer signals, stronger filters</p>
      <div id="source" class="source">Connecting signal feed…</div>
    </div>
    <div class="controls">
      <button class="tfbtn active" data-tf="M15">M15 Chart</button>
      <button class="tfbtn" data-tf="H1">H1 Chart</button>
      <button class="tfbtn" data-tf="H4">H4 Chart</button>
      <button id="refresh">Refresh structure</button>
      <span id="status" class="status">Starting…</span>
    </div>
  </div>
  <div id="banner" class="banner"></div>

  <div class="hero">
    <div class="card actionCard" id="actionCard">
      <div class="kicker">CURRENT ACTION</div>
      <div id="action" class="actionBig orange">WAIT</div>
      <div id="actionWhy" class="sub">Waiting for closed-candle confirmation.</div>
      <div class="scoreBar"><span id="scoreFill"></span></div>
      <div id="scoreText" class="sub">0 / 100 confirmation</div>
    </div>
    <div class="card"><div class="kicker">Signal feed price</div><div id="signalPrice" class="value">—</div><div id="signalAge" class="sub">COMEX Gold futures</div></div>
    <div class="card"><div class="kicker">H4 / H1 bias</div><div id="htfBias" class="value">—</div><div id="htfSub" class="sub">Higher-timeframe agreement</div></div>
    <div class="card"><div class="kicker">M15 structure event</div><div id="structureEvent" class="value">—</div><div id="structureEventSub" class="sub">BOS / CHOCH</div></div>
    <div class="card"><div class="kicker">Liquidity event</div><div id="liqEvent" class="value">—</div><div id="liqEventSub" class="sub">Sweep + reclaim</div></div>
    <div class="card"><div class="kicker">Trend strength</div><div id="adxHero" class="value">—</div><div id="adxHeroSub" class="sub">M15 ADX / DI</div></div>
  </div>

  <div class="main">
    <div class="card chartCard">
      <div class="chartTop">
        <div>
          <div class="kicker">Professional candlestick chart</div>
          <div id="chartTitle" class="value" style="font-size:18px">M15 structure</div>
        </div>
        <div class="legend">
          <span><i class="dot" style="background:#67a8ff"></i>EMA20</span>
          <span><i class="dot" style="background:#ab8cff"></i>EMA50</span>
          <span><i class="dot" style="background:#f0ca65"></i>EMA200</span>
          <span><i class="dot" style="background:#ff7070"></i>Resistance</span>
          <span><i class="dot" style="background:#39d98a"></i>Support</span>
        </div>
      </div>
      <div class="chartbox">
        <canvas id="chart"></canvas>
        <div id="ohlc" class="ohlc">Move over chart for OHLC</div>
      </div>
    </div>

    <div class="sideStack">
      <div class="card">
        <div class="kicker">High-confirmation checklist</div>
        <div id="checks" class="checks"></div>
        <div id="filterNote" class="alert">Signal requires closed-candle confirmation. No forced trade when filters conflict.</div>
      </div>

      <div class="card">
        <div class="kicker">Trade plan — only when confirmed</div>
        <div class="planGrid">
          <div class="plan"><div class="kicker">Entry</div><div id="entry" class="value">—</div></div>
          <div class="plan"><div class="kicker">Invalidation / SL</div><div id="sl" class="value">—</div></div>
          <div class="plan"><div class="kicker">TP1</div><div id="tp1" class="value">—</div></div>
          <div class="plan"><div class="kicker">TP2</div><div id="tp2" class="value">—</div></div>
        </div>
        <div id="rr" class="sub">R:R appears after a confirmed setup.</div>
      </div>

      <div class="card">
        <div class="kicker">Nearest liquidity map</div>
        <table class="table">
          <thead><tr><th>Pool</th><th>Level</th><th>Touches</th><th>Distance</th></tr></thead>
          <tbody id="liqTable"></tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="tfgrid" id="tfgrid"></div>

  <footer>
    Signal engine uses one consistent COMEX Gold futures feed for structure and decision logic, and evaluates the setup from completed candles to reduce intrabar noise. Liquidity is chart-inferred swing/stop liquidity, not actual resting exchange orders. BUY/SELL is a rule-based technical signal, not a guarantee or personalized financial advice. Voice-agent answers are generated from the dashboard state and rule engine, not from a general-purpose LLM.
  </footer>
</div>

<button id="agentFab" class="agentFab" title="Gold Voice Agent">🎙️</button>
<div id="agentPanel" class="agentPanel">
  <div class="agentHead"><div><strong><span class="agentPulse"></span>Gold Voice Agent</strong><div><span>Dashboard-aware assistant</span></div></div><button id="agentClose">✕</button></div>
  <div id="agentLog" class="agentLog"></div>
  <div class="agentQuick">
    <button class="chip" data-q="Abhi buy ya sell?">Buy ya sell?</button>
    <button class="chip" data-q="Signal kyun?">Signal kyun?</button>
    <button class="chip" data-q="M15 H1 H4 trend batao">MTF trend</button>
    <button class="chip" data-q="Liquidity kahan hai?">Liquidity</button>
    <button class="chip" data-q="Entry SL TP batao">Entry / SL / TP</button>
    <button class="chip" data-q="Full summary">Full summary</button>
  </div>
  <div class="agentInput"><input id="agentText" placeholder="Type or use mic…"><button id="agentSend">Send</button><button id="agentMic">🎤</button></div>
  <div class="agentSettings">
    <label class="toggle"><input id="speakToggle" type="checkbox" checked> Speak answers</label>
    <label class="toggle"><input id="alertToggle" type="checkbox"> Proactive alerts</label>
    <label>Alert quality <select id="alertGrade"><option value="80" selected>A / A+ (80+)</option><option value="90">A+ only (90+)</option><option value="75">All confirmed (75+)</option></select></label>
    <label>Mic language <select id="voiceLang"><option value="ur-PK" selected>Urdu</option><option value="hi-IN">Hindi</option><option value="en-US">English</option></select></label>
  </div>
</div>

<script>
const $=id=>document.getElementById(id);
const fmt=x=>Number.isFinite(x)?x.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2}):"—";
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
let m15=[],h1=[],structures={},signalPrice=NaN,currentTF="M15",lastChartGeom=null;
let lastEvaluation=null,lastAlertKey="",recognition=null,isListening=false;

async function j(url){const r=await fetch(url,{cache:"no-store"});if(!r.ok)throw new Error("HTTP "+r.status);return await r.json()}

function aggregateH4(bars){
  const m=new Map();
  for(const p of bars){
    const d=new Date(p.t*1000),h=Math.floor(d.getUTCHours()/4)*4,k=Date.UTC(d.getUTCFullYear(),d.getUTCMonth(),d.getUTCDate(),h)/1000;
    if(!m.has(k))m.set(k,{t:k,o:p.o,h:p.h,l:p.l,c:p.c});
    else{const b=m.get(k);b.h=Math.max(b.h,p.h);b.l=Math.min(b.l,p.l);b.c=p.c}
  }
  return [...m.values()].sort((a,b)=>a.t-b.t);
}
function ema(vals,p){
  if(!vals.length)return[];
  const a=2/(p+1),out=[vals[0]];
  for(let i=1;i<vals.length;i++)out.push(a*vals[i]+(1-a)*out[i-1]);
  return out;
}
function atr(bars,p=14){
  if(bars.length<p+2)return NaN;
  const tr=[];
  for(let i=1;i<bars.length;i++){const b=bars[i],pc=bars[i-1].c;tr.push(Math.max(b.h-b.l,Math.abs(b.h-pc),Math.abs(b.l-pc)))}
  return tr.slice(-p).reduce((a,b)=>a+b,0)/p;
}
function adx(bars,p=14){
  if(bars.length<2*p+3)return {adx:NaN,plus:NaN,minus:NaN};
  const tr=[],pdm=[],mdm=[];
  for(let i=1;i<bars.length;i++){
    const up=bars[i].h-bars[i-1].h,down=bars[i-1].l-bars[i].l;
    pdm.push(up>down&&up>0?up:0);mdm.push(down>up&&down>0?down:0);
    tr.push(Math.max(bars[i].h-bars[i].l,Math.abs(bars[i].h-bars[i-1].c),Math.abs(bars[i].l-bars[i-1].c)));
  }
  let smTR=tr.slice(0,p).reduce((a,b)=>a+b,0),smP=pdm.slice(0,p).reduce((a,b)=>a+b,0),smM=mdm.slice(0,p).reduce((a,b)=>a+b,0);
  const dx=[];let plus=0,minus=0;
  for(let i=p;i<tr.length;i++){
    if(i>p){smTR=smTR-smTR/p+tr[i];smP=smP-smP/p+pdm[i];smM=smM-smM/p+mdm[i]}
    plus=smTR?100*smP/smTR:0;minus=smTR?100*smM/smTR:0;
    const den=plus+minus;dx.push(den?100*Math.abs(plus-minus)/den:0);
  }
  if(dx.length<p)return {adx:NaN,plus,minus};
  let A=dx.slice(0,p).reduce((a,b)=>a+b,0)/p;
  for(let i=p;i<dx.length;i++)A=(A*(p-1)+dx[i])/p;
  return {adx:A,plus,minus};
}
function pivots(bars,strength=3,lookback=260){
  const s=bars.slice(-lookback),highs=[],lows=[];
  for(let i=strength;i<s.length-strength;i++){
    let hi=true,lo=true;
    for(let k=1;k<=strength;k++){
      if(s[i].h<=s[i-k].h||s[i].h<=s[i+k].h)hi=false;
      if(s[i].l>=s[i-k].l||s[i].l>=s[i+k].l)lo=false;
      if(!hi&&!lo)break;
    }
    if(hi)highs.push({t:s[i].t,v:s[i].h});
    if(lo)lows.push({t:s[i].t,v:s[i].l});
  }
  return {highs,lows};
}
function clusters(items,tol){
  const sorted=[...items].sort((a,b)=>a.v-b.v),cs=[];
  for(const x of sorted){
    let c=cs.find(z=>Math.abs(x.v-z.level)<=tol);
    if(!c){c={level:x.v,items:[x]};cs.push(c)}
    else{c.items.push(x);c.level=c.items.reduce((a,z)=>a+z.v,0)/c.items.length}
  }
  return cs.filter(c=>c.items.length>=2).map(c=>({level:c.level,touches:c.items.length,first:Math.min(...c.items.map(x=>x.t)),last:Math.max(...c.items.map(x=>x.t))}));
}
function nearest(arr,price,side){
  const f=arr.filter(x=>side==="above"?x.level>price:x.level<price);
  if(!f.length)return null;
  return f.sort((a,b)=>Math.abs(a.level-price)-Math.abs(b.level-price))[0];
}
function latestSweep(bars,highClusters,lowClusters,lookback=16){
  const recent=bars.slice(-lookback),events=[];
  for(const b of recent){
    for(const c of highClusters){
      if(c.last>=b.t)continue;
      if(b.h>c.level&&b.c<c.level)events.push({type:"BUY-SIDE SWEEP",bias:"BEARISH",level:c.level,time:b.t,reclaim:true});
    }
    for(const c of lowClusters){
      if(c.last>=b.t)continue;
      if(b.l<c.level&&b.c>c.level)events.push({type:"SELL-SIDE SWEEP",bias:"BULLISH",level:c.level,time:b.t,reclaim:true});
    }
  }
  return events.sort((a,b)=>b.time-a.time)[0]||null;
}
function structureEvent(bars,pv){
  if(bars.length<5)return {type:"NONE",bias:"NEUTRAL",level:null,time:null};
  const last=bars.at(-1),priorH=pv.highs.filter(x=>x.t<last.t).at(-1),priorL=pv.lows.filter(x=>x.t<last.t).at(-1);
  const prevHighs=pv.highs.filter(x=>x.t<last.t).slice(-2),prevLows=pv.lows.filter(x=>x.t<last.t).slice(-2);
  let prevTrend="MIXED";
  if(prevHighs.length>=2&&prevLows.length>=2){
    if(prevHighs[1].v>prevHighs[0].v&&prevLows[1].v>prevLows[0].v)prevTrend="BULLISH";
    if(prevHighs[1].v<prevHighs[0].v&&prevLows[1].v<prevLows[0].v)prevTrend="BEARISH";
  }
  if(priorH&&last.c>priorH.v)return {type:prevTrend==="BEARISH"?"BULLISH CHOCH":"BULLISH BOS",bias:"BULLISH",level:priorH.v,time:last.t};
  if(priorL&&last.c<priorL.v)return {type:prevTrend==="BULLISH"?"BEARISH CHOCH":"BEARISH BOS",bias:"BEARISH",level:priorL.v,time:last.t};
  return {type:"NONE",bias:"NEUTRAL",level:null,time:last.t};
}
function analyze(raw,label){
  // Drop the last bar because it may still be forming; signal logic uses completed candles.
  const s=raw.slice().sort((a,b)=>a.t-b.t).slice(0,-1);
  const closes=s.map(x=>x.c),e20=ema(closes,20),e50=ema(closes,50),e200=ema(closes,200),A=atr(s),D=adx(s),pv=pivots(s);
  const last=s.at(-1),lastH=pv.highs.slice(-2),lastL=pv.lows.slice(-2);
  let structure="MIXED";
  if(lastH.length>=2&&lastL.length>=2){
    if(lastH[1].v>lastH[0].v&&lastL[1].v>lastL[0].v)structure="HH/HL";
    else if(lastH[1].v<lastH[0].v&&lastL[1].v<lastL[0].v)structure="LH/LL";
  }
  const slope50=e50.length>4?e50.at(-1)-e50.at(-4):0;
  let trend="NEUTRAL",score=0;
  if(last.c>e200.at(-1))score+=2;else score-=2;
  if(e20.at(-1)>e50.at(-1)){score+=1;if(slope50>0)score+=1}else if(e20.at(-1)<e50.at(-1)){score-=1;if(slope50<0)score-=1}
  if(structure==="HH/HL")score+=2;if(structure==="LH/LL")score-=2;
  if(D.adx>=18){if(D.plus>D.minus)score+=1;else if(D.minus>D.plus)score-=1}
  if(score>=3)trend="BULLISH";else if(score<=-3)trend="BEARISH";
  const tol=Math.max((A||0)*0.16,last.c*0.00030),hc=clusters(pv.highs,tol),lc=clusters(pv.lows,tol);
  const buyLiq=nearest(hc,last.c,"above"),sellLiq=nearest(lc,last.c,"below");
  const res=(pv.highs.filter(x=>x.v>last.c).sort((a,b)=>a.v-b.v)[0]||{}).v||null;
  const sup=(pv.lows.filter(x=>x.v<last.c).sort((a,b)=>b.v-a.v)[0]||{}).v||null;
  const sweep=latestSweep(s,hc,lc,label==="M15"?20:12);
  const event=structureEvent(s,pv);
  return {label,bars:s,close:last.c,e20,e50,e200,A,D,pv,structure,trend,score,hc,lc,buyLiq,sellLiq,res,sup,sweep,event};
}
function ageText(t){
  if(!t)return "—";const sec=Math.max(0,Math.floor(Date.now()/1000-t));
  if(sec<60)return sec+" sec ago";const m=Math.floor(sec/60);if(m<60)return m+" min ago";const h=Math.floor(m/60);if(h<24)return h+" hr ago";return Math.floor(h/24)+" day ago";
}
function tfCard(x){
  const cls=x.trend==="BULLISH"?"bull":x.trend==="BEARISH"?"bear":"neutral";
  return `<div class="card">
    <div class="tfhead"><h2>${x.label}</h2><span class="badge ${cls}">${x.trend}</span></div>
    <div class="sub">Closed-candle structure: <b>${x.structure}</b></div>
    <div class="stats">
      <div class="stat"><div class="kicker">ADX</div><div class="value">${Number.isFinite(x.D.adx)?x.D.adx.toFixed(1):"—"}</div></div>
      <div class="stat"><div class="kicker">EMA200 side</div><div class="value ${x.close>x.e200.at(-1)?"green":"red"}">${x.close>x.e200.at(-1)?"ABOVE":"BELOW"}</div></div>
      <div class="stat"><div class="kicker">Support</div><div class="value">${fmt(x.sup)}</div></div>
      <div class="stat"><div class="kicker">Resistance</div><div class="value">${fmt(x.res)}</div></div>
    </div>
    <div class="sub" style="margin-top:9px">Event: <b>${x.event.type}</b>${x.sweep?` · ${x.sweep.type} ${ageText(x.sweep.time)}`:""}</div>
  </div>`;
}
function evaluateSignal(){
  const M=structures.M15,H=structures.H1,F=structures.H4;
  if(!M||!H||!F)return null;
  const dir=(H.trend===F.trend&&H.trend!=="NEUTRAL")?H.trend:"NEUTRAL";
  const checks=[];
  const htfAligned=dir!=="NEUTRAL";
  const m15Trend=M.trend===dir;
  const eventAligned=M.event.bias===dir;
  const sweepAligned=M.sweep&&M.sweep.bias===dir&&((Date.now()/1000-M.sweep.time)<=4*3600);
  const emaAligned=dir==="BULLISH"?M.close>M.e200.at(-1)&&H.close>H.e200.at(-1):dir==="BEARISH"?M.close<M.e200.at(-1)&&H.close<H.e200.at(-1):false;
  const adxAligned=M.D.adx>=18&&H.D.adx>=18&&(dir==="BULLISH"?M.D.plus>M.D.minus:M.D.minus>M.D.plus);
  const structureAligned=dir==="BULLISH"?M.structure==="HH/HL"||eventAligned:M.structure==="LH/LL"||eventAligned;
  const entry=M.close;
  const recentLows=M.pv.lows.filter(x=>x.t<M.bars.at(-1).t).slice(-3),recentHighs=M.pv.highs.filter(x=>x.t<M.bars.at(-1).t).slice(-3);
  let sl=NaN,tp1=NaN,tp2=NaN,risk=NaN,roomOK=false,opposing=null;
  if(dir==="BULLISH"){
    const swing=recentLows.length?Math.min(...recentLows.map(x=>x.v)):entry-M.A;
    sl=swing-0.20*M.A;risk=entry-sl;opposing=M.buyLiq?.level||M.res;
    tp1=entry+1.5*risk;tp2=entry+2.5*risk;
    roomOK=Number.isFinite(opposing)?opposing-entry>=1.20*risk:true;
    if(Number.isFinite(opposing)){tp1=Math.min(tp1,opposing);tp2=Math.max(tp1,Math.min(tp2,opposing+0.5*risk))}
  } else if(dir==="BEARISH"){
    const swing=recentHighs.length?Math.max(...recentHighs.map(x=>x.v)):entry+M.A;
    sl=swing+0.20*M.A;risk=sl-entry;opposing=M.sellLiq?.level||M.sup;
    tp1=entry-1.5*risk;tp2=entry-2.5*risk;
    roomOK=Number.isFinite(opposing)?entry-opposing>=1.20*risk:true;
    if(Number.isFinite(opposing)){tp1=Math.max(tp1,opposing);tp2=Math.min(tp1,Math.max(tp2,opposing-0.5*risk))}
  }
  let score=0;
  if(htfAligned)score+=25;
  if(m15Trend)score+=15;
  if(eventAligned)score+=15;
  if(sweepAligned)score+=20;
  if(emaAligned)score+=10;
  if(adxAligned)score+=10;
  if(roomOK)score+=5;
  checks.push(["H4 + H1 same direction",htfAligned],["M15 trend aligned",m15Trend],["M15 BOS/CHOCH aligned",eventAligned],["Recent liquidity sweep + reclaim",!!sweepAligned],["Price on correct EMA200 side",emaAligned],["ADX + DI confirm strength",adxAligned],["Enough room to target",roomOK]);
  // Strict permission: score alone is not enough. Require HTF, EMA, ADX and either sweep or structure event.
  const core=htfAligned&&emaAligned&&adxAligned&&structureAligned&&(sweepAligned||eventAligned);
  let action="WAIT";
  if(core&&score>=75)action=dir==="BULLISH"?"BUY":"SELL";
  const grade=score>=90?"A+":score>=80?"A":score>=70?"B":score>=55?"C":"NO TRADE";
  return {dir,score,action,grade,checks,entry,sl,tp1,tp2,risk,roomOK,sweepAligned,eventAligned};
}
function renderSignal(){
  const S=evaluateSignal();if(!S)return;
  lastEvaluation=S;
  const cls=S.action==="BUY"?"green":S.action==="SELL"?"red":"orange";
  $("action").textContent=S.action;$("action").className="actionBig "+cls;
  $("actionCard").style.borderColor=S.action==="BUY"?"rgba(57,217,138,.55)":S.action==="SELL"?"rgba(255,107,116,.55)":"#233244";
  $("actionWhy").textContent=S.action==="WAIT"?"No forced trade — one or more core confirmations are missing.":`${S.grade} setup · closed-candle confirmation active.`;
  $("scoreFill").style.width=clamp(S.score,0,100)+"%";$("scoreText").textContent=`${S.score} / 100 confirmation · Grade ${S.grade}`;
  $("htfBias").textContent=S.dir;$("htfBias").className="value "+(S.dir==="BULLISH"?"green":S.dir==="BEARISH"?"red":"orange");
  $("htfSub").textContent=`H4 ${structures.H4.trend} · H1 ${structures.H1.trend}`;
  $("structureEvent").textContent=structures.M15.event.type;$("structureEvent").className="value "+(structures.M15.event.bias==="BULLISH"?"green":structures.M15.event.bias==="BEARISH"?"red":"orange");
  $("structureEventSub").textContent=structures.M15.event.level?`Level ${fmt(structures.M15.event.level)}`:"No fresh break on last closed M15 candle";
  const sw=structures.M15.sweep;
  $("liqEvent").textContent=sw?sw.type:"NONE";$("liqEvent").className="value "+(sw?.bias==="BULLISH"?"green":sw?.bias==="BEARISH"?"red":"orange");
  $("liqEventSub").textContent=sw?`${ageText(sw.time)} · level ${fmt(sw.level)}`:"No recent confirmed sweep";
  const D=structures.M15.D;$("adxHero").textContent=Number.isFinite(D.adx)?D.adx.toFixed(1):"—";$("adxHero").className="value "+(D.adx>=22?"green":D.adx>=18?"orange":"red");
  $("adxHeroSub").textContent=`+DI ${fmt(D.plus)} · -DI ${fmt(D.minus)}`;
  $("checks").innerHTML=S.checks.map(c=>`<div class="check ${c[1]?"ok":"no"}">${c[1]?"✓":"✕"} ${c[0]}</div>`).join("");
  if(S.action==="WAIT"){
    $("entry").textContent=$("sl").textContent=$("tp1").textContent=$("tp2").textContent="—";$("rr").textContent="Trade plan hidden until a high-confirmation BUY/SELL setup is active.";
  }else{
    $("entry").textContent=fmt(S.entry);$("sl").textContent=fmt(S.sl);$("tp1").textContent=fmt(S.tp1);$("tp2").textContent=fmt(S.tp2);
    const rr1=S.risk>0?Math.abs(S.tp1-S.entry)/S.risk:NaN,rr2=S.risk>0?Math.abs(S.tp2-S.entry)/S.risk:NaN;
    $("rr").textContent=`Approx R:R — TP1 ${Number.isFinite(rr1)?rr1.toFixed(2):"—"}R · TP2 ${Number.isFinite(rr2)?rr2.toFixed(2):"—"}R`;
  }
}
function allLiquidity(){
  const a=[];for(const x of Object.values(structures)){
    if(x.buyLiq)a.push({side:"BUY",tf:x.label,...x.buyLiq,d:Math.abs(x.buyLiq.level-x.close)});
    if(x.sellLiq)a.push({side:"SELL",tf:x.label,...x.sellLiq,d:Math.abs(x.sellLiq.level-x.close)});
  }
  return a.sort((a,b)=>a.d-b.d);
}
function renderLiquidity(){
  const rows=allLiquidity().slice(0,8);
  $("liqTable").innerHTML=rows.map(r=>`<tr><td>${r.side==="BUY"?"Buy-side":"Sell-side"} · ${r.tf}</td><td>${fmt(r.level)}</td><td>${r.touches}</td><td>${fmt(r.d)}</td></tr>`).join("")||'<tr><td colspan="4">No clustered liquidity pools detected.</td></tr>';
}
function render(){
  if(!structures.M15)return;
  $("tfgrid").innerHTML=["M15","H1","H4"].map(k=>tfCard(structures[k])).join("");
  $("signalPrice").textContent="$"+fmt(signalPrice);
  $("signalAge").textContent="COMEX Gold futures · signal calculations use the same feed";
  renderSignal();renderLiquidity();draw();
}
function chartModel(){
  return structures[currentTF]||structures.M15;
}
function draw(){
  const m=chartModel();if(!m)return;
  const c=$("chart"),rect=c.getBoundingClientRect(),dpr=devicePixelRatio||1;c.width=rect.width*dpr;c.height=rect.height*dpr;
  const ctx=c.getContext("2d");ctx.scale(dpr,dpr);const W=rect.width,H=rect.height,L=62,R=18,T=18,B=34;
  const bars=m.bars.slice(-100),start=m.bars.length-bars.length,e20=m.e20.slice(start),e50=m.e50.slice(start),e200=m.e200.slice(start);
  const levels=[m.sup,m.res,m.buyLiq?.level,m.sellLiq?.level].filter(Number.isFinite);
  const vals=bars.flatMap(b=>[b.h,b.l]).concat(levels,e200.filter(Number.isFinite));
  let mn=Math.min(...vals),mx=Math.max(...vals),pad=(mx-mn)*.05||1;mn-=pad;mx+=pad;
  const plotW=W-L-R,plotH=H-T-B,step=plotW/Math.max(1,bars.length),body=Math.max(2,Math.min(9,step*.58));
  const xx=i=>L+(i+.5)*step,yy=v=>T+(mx-v)*plotH/(mx-mn);
  ctx.clearRect(0,0,W,H);ctx.font="11px Segoe UI";ctx.strokeStyle="#203040";ctx.fillStyle="#8194aa";ctx.lineWidth=1;
  for(let k=0;k<6;k++){const y=T+k*plotH/5;ctx.beginPath();ctx.moveTo(L,y);ctx.lineTo(W-R,y);ctx.stroke();ctx.fillText((mx-k*(mx-mn)/5).toFixed(1),5,y+4)}
  function hline(v,col,label,dash=[4,4]){if(!Number.isFinite(v))return;ctx.strokeStyle=col;ctx.setLineDash(dash);ctx.beginPath();ctx.moveTo(L,yy(v));ctx.lineTo(W-R,yy(v));ctx.stroke();ctx.setLineDash([]);ctx.fillStyle=col;ctx.fillText(label,W-R-66,yy(v)-4)}
  hline(m.res,"#ff7070","Resistance");hline(m.sup,"#39d98a","Support");hline(m.buyLiq?.level,"#ffb454","Buy Liq",[2,4]);hline(m.sellLiq?.level,"#58d4e7","Sell Liq",[2,4]);
  for(let i=0;i<bars.length;i++){
    const b=bars[i],up=b.c>=b.o,col=up?"#39d98a":"#ff6b74",x=xx(i);
    ctx.strokeStyle=col;ctx.beginPath();ctx.moveTo(x,yy(b.h));ctx.lineTo(x,yy(b.l));ctx.stroke();
    ctx.fillStyle=col;const y1=yy(Math.max(b.o,b.c)),y2=yy(Math.min(b.o,b.c));ctx.fillRect(x-body/2,y1,body,Math.max(1,y2-y1));
  }
  function plot(arr,col){
    ctx.strokeStyle=col;ctx.lineWidth=1.5;ctx.beginPath();let started=false;
    arr.forEach((v,i)=>{if(!Number.isFinite(v))return;const x=xx(i),y=yy(v);if(!started){ctx.moveTo(x,y);started=true}else ctx.lineTo(x,y)});ctx.stroke();
  }
  plot(e20,"#67a8ff");plot(e50,"#ab8cff");plot(e200,"#f0ca65");
  // Last completed candle marker
  const last=bars.at(-1);if(last){ctx.fillStyle="#f0ca65";ctx.fillText("CLOSED",Math.max(L,xx(bars.length-1)-48),yy(last.c)-8)}
  // Bottom time labels
  const idxs=[0,Math.floor((bars.length-1)/2),bars.length-1];ctx.fillStyle="#8194aa";
  idxs.forEach(i=>{if(i<0||!bars[i])return;const d=new Date(bars[i].t*1000),s=currentTF==="M15"?d.toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"}):d.toLocaleDateString();ctx.fillText(s,Math.max(L,Math.min(W-R-70,xx(i)-28)),H-10)});
  lastChartGeom={bars,L,R,T,B,W,H,step,xx,yy};
  $("chartTitle").textContent=`${currentTF} · Candles + EMA20/50/200 + structure levels`;
}
function updateHover(ev){
  if(!lastChartGeom)return;
  const rect=$("chart").getBoundingClientRect(),x=ev.clientX-rect.left,g=lastChartGeom;
  let i=Math.floor((x-g.L)/g.step);i=clamp(i,0,g.bars.length-1);const b=g.bars[i];if(!b)return;
  $("ohlc").textContent=`${new Date(b.t*1000).toLocaleString()}  O ${fmt(b.o)}  H ${fmt(b.h)}  L ${fmt(b.l)}  C ${fmt(b.c)}`;
}

function agentAdd(text,who="agent",extra=""){
  const log=$("agentLog"),d=document.createElement("div");d.className=`msg ${who} ${extra}`;d.textContent=text;log.appendChild(d);log.scrollTop=log.scrollHeight;
}
function speakAgent(text){
  if(!$("speakToggle").checked||!("speechSynthesis" in window))return;
  speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.lang=$("voiceLang").value;u.rate=1.02;u.pitch=1;speechSynthesis.speak(u);
}
function n(v){return Number.isFinite(v)?fmt(v):"available nahi"}
function setupExplain(S){
  if(!S)return "Dashboard data abhi load ho raha hai.";
  const missing=S.checks.filter(x=>!x[1]).map(x=>x[0]);
  if(S.action!=="WAIT")return `${S.action} setup active hai. Confirmation ${S.score}/100, grade ${S.grade}. Core filters aligned hain. Entry ${n(S.entry)}, SL ${n(S.sl)}, TP1 ${n(S.tp1)}, TP2 ${n(S.tp2)}.`;
  return `Abhi WAIT hai. Confirmation ${S.score}/100, grade ${S.grade}. Missing confirmation: ${missing.length?missing.join(", "):"core rule gate"}.`;
}
function trendSummary(){
  if(!structures.M15)return "Trend data abhi load ho raha hai.";
  return `M15 ${structures.M15.trend}, H1 ${structures.H1.trend}, H4 ${structures.H4.trend}. M15 structure ${structures.M15.structure}, H1 structure ${structures.H1.structure}, H4 structure ${structures.H4.structure}.`;
}
function liquiditySummary(){
  if(!structures.M15)return "Liquidity data abhi load ho raha hai.";
  const rows=allLiquidity();const buy=rows.find(x=>x.side==="BUY"),sell=rows.find(x=>x.side==="SELL"),sw=structures.M15.sweep;
  let s=`Nearest buy-side liquidity ${buy?n(buy.level)+" on "+buy.tf:"nahi mili"}. Nearest sell-side liquidity ${sell?n(sell.level)+" on "+sell.tf:"nahi mili"}.`;
  if(sw)s+=` Latest M15 event ${sw.type} at ${n(sw.level)}, ${ageText(sw.time)}.`;else s+=" Recent M15 liquidity sweep nahi hai.";
  return s;
}
function srSummary(){
  if(!structures.M15)return "S/R data abhi load ho raha hai.";
  return `M15 support ${n(structures.M15.sup)}, resistance ${n(structures.M15.res)}. H1 support ${n(structures.H1.sup)}, resistance ${n(structures.H1.res)}. H4 support ${n(structures.H4.sup)}, resistance ${n(structures.H4.res)}.`;
}
function adxSummary(){
  if(!structures.M15)return "ADX data abhi load ho raha hai.";const d=structures.M15.D;
  return `M15 ADX ${Number.isFinite(d.adx)?d.adx.toFixed(1):"N/A"}. Plus DI ${n(d.plus)}, minus DI ${n(d.minus)}. ${d.adx>=22?"Trend strength strong hai.":d.adx>=18?"Trend strength moderate hai.":"Trend weak hai."}`;
}
function fullAgentSummary(){
  const S=lastEvaluation||evaluateSignal();
  return `Gold signal price ${n(signalPrice)}. ${trendSummary()} ${liquiditySummary()} ${setupExplain(S)}`;
}
function agentAnswer(q){
  const x=(q||"").toLowerCase().trim(),S=lastEvaluation||evaluateSignal();
  if(!x)return "Sawal bolo ya type karo.";
  if(/buy|sell|action|trade lena|kharid|bech/.test(x))return setupExplain(S);
  if(/kyun|why|reason|confirm/.test(x))return setupExplain(S);
  if(/trend|direction|m15|h1|h4/.test(x)&&!/sl|tp|entry/.test(x))return trendSummary();
  if(/liquid|sweep|stop hunt|stop-hunt/.test(x))return liquiditySummary();
  if(/support|resistance|s\/r/.test(x))return srSummary();
  if(/adx|strength|di\b/.test(x))return adxSummary();
  if(/entry|sl|stop loss|tp|target/.test(x)){
    if(!S||S.action==="WAIT")return `Abhi confirmed trade nahi hai, isliye Entry/SL/TP hide hain. ${setupExplain(S)}`;
    return `${S.action}: Entry ${n(S.entry)}, SL ${n(S.sl)}, TP1 ${n(S.tp1)}, TP2 ${n(S.tp2)}. Confirmation ${S.score}/100.`;
  }
  if(/price|rate|gold kitna/.test(x))return `Signal feed Gold price ${n(signalPrice)} hai.`;
  if(/summary|haal|situation|market/.test(x))return fullAgentSummary();
  if(/alert/.test(x))return `Proactive alerts ${$("alertToggle").checked?"ON":"OFF"} hain. Current minimum score ${$("alertGrade").value}+ hai.`;
  return `Main dashboard ke live signal context par jawab deta hoon. Tum pooch sakte ho: abhi buy ya sell, signal kyun, trend, liquidity, sweep, support resistance, ADX, ya Entry SL TP.`;
}
function askAgent(q){
  if(!q)return;agentAdd(q,"user");const a=agentAnswer(q);agentAdd(a,"agent");speakAgent(a);$("agentText").value="";
}
function openAgent(){$("agentPanel").classList.add("open");if(!$("agentLog").children.length)agentAdd("Bhai, Gold Voice Agent ready hai. Poocho: abhi buy ya sell?","agent")}
function setupRecognition(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR)return false;
  recognition=new SR();recognition.continuous=false;recognition.interimResults=false;
  recognition.onstart=()=>{isListening=true;$("agentFab").classList.add("listening");$("agentMic").textContent="⏹"};
  recognition.onend=()=>{isListening=false;$("agentFab").classList.remove("listening");$("agentMic").textContent="🎤"};
  recognition.onerror=e=>agentAdd(`Mic issue: ${e.error}. Text box use kar sakte ho.`,"agent");
  recognition.onresult=e=>{const q=e.results[0][0].transcript;$("agentText").value=q;askAgent(q)};return true;
}
function toggleMic(){openAgent();if(!recognition&&!setupRecognition()){agentAdd("Is browser mein voice recognition available nahi. Chrome/Edge ya text input use karo.","agent");return}if(isListening){recognition.stop();return}recognition.lang=$("voiceLang").value;try{recognition.start()}catch(e){}}
async function enableAlerts(){
  if(!$("alertToggle").checked)return;
  if("Notification" in window&&Notification.permission==="default")await Notification.requestPermission();
  agentAdd("Proactive setup alerts ON. Dashboard open rehne par A/A+ setup change hote hi alert milega.","agent","alertMsg");
}
function proactiveCheck(){
  const S=lastEvaluation;if(!S||!$("alertToggle").checked||S.action==="WAIT")return;
  const min=Number($("alertGrade").value||80);if(S.score<min)return;
  const key=`${S.action}|${S.score}|${structures.M15?.bars?.at(-1)?.t||0}`;if(key===lastAlertKey)return;lastAlertKey=key;
  const msg=`Gold ${S.action} setup. Score ${S.score}/100, grade ${S.grade}. Entry ${n(S.entry)}, SL ${n(S.sl)}, TP1 ${n(S.tp1)}, TP2 ${n(S.tp2)}.`;
  agentAdd(msg,"agent","alertMsg");speakAgent(msg);
  if("Notification" in window&&Notification.permission==="granted")new Notification(`Gold ${S.action} · ${S.grade}`,{body:`Score ${S.score}/100 · Entry ${n(S.entry)} · SL ${n(S.sl)} · TP1 ${n(S.tp1)}`});
}

async function loadStructure(){
  try{
    const[a,b]=await Promise.all([j("/api/m15"),j("/api/h1")]);if(!a.ok||!b.ok)throw new Error("Signal history unavailable");
    m15=a.bars;h1=b.bars;signalPrice=Number(a.price||m15.at(-1)?.c);
    structures.M15=analyze(m15,"M15");structures.H1=analyze(h1,"H1");structures.H4=analyze(aggregateH4(h1),"H4");
    $("source").textContent="Signal source: Yahoo COMEX Gold futures · internally consistent feed";
    $("banner").style.display="none";render();proactiveCheck();$("status").textContent="Updated "+new Date().toLocaleTimeString();
  }catch(e){$("banner").textContent="Structure refresh failed: "+e.message+". Last valid values remain on screen.";$("banner").style.display="block";$("status").textContent="Retrying…"}
}
document.querySelectorAll(".tfbtn").forEach(b=>b.onclick=()=>{document.querySelectorAll(".tfbtn").forEach(x=>x.classList.remove("active"));b.classList.add("active");currentTF=b.dataset.tf;draw()});
$("refresh").onclick=loadStructure;$("chart").addEventListener("mousemove",updateHover);window.addEventListener("resize",draw);
$("agentFab").onclick=()=>{$("agentPanel").classList.contains("open")?$("agentPanel").classList.remove("open"):openAgent()};
$("agentClose").onclick=()=>$("agentPanel").classList.remove("open");$("agentMic").onclick=toggleMic;
$("agentSend").onclick=()=>askAgent($("agentText").value);$("agentText").addEventListener("keydown",e=>{if(e.key==="Enter")askAgent($("agentText").value)});
document.querySelectorAll(".chip").forEach(c=>c.onclick=()=>askAgent(c.dataset.q));$("alertToggle").addEventListener("change",enableAlerts);
loadStructure();setInterval(loadStructure,60000);
</script>
</body>
</html>
"""

def get_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept":"application/json,text/plain,*/*","Cache-Control":"no-cache"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))

def normalize_yahoo(payload):
    r = (((payload or {}).get("chart") or {}).get("result") or [None])[0]
    if not r:
        return [], None
    ts = r.get("timestamp") or []
    q = ((((r.get("indicators") or {}).get("quote") or [{}])[0]) or {})
    opens, highs, lows, closes = q.get("open") or [], q.get("high") or [], q.get("low") or [], q.get("close") or []
    out=[]
    for i,t in enumerate(ts):
        try:
            o,h,l,c=float(opens[i]),float(highs[i]),float(lows[i]),float(closes[i])
            if min(o,h,l,c)<=0: continue
            out.append({"t":int(t),"o":o,"h":h,"l":l,"c":c})
        except Exception:
            pass
    meta=r.get("meta") or {}
    try: price=float(meta.get("regularMarketPrice"))
    except Exception: price=None
    return out,price

def fetch_yahoo(interval, rng):
    url=("https://query1.finance.yahoo.com/v8/finance/chart/GC%3DF"
         f"?range={urllib.parse.quote(rng)}&interval={urllib.parse.quote(interval)}&includePrePost=false")
    d=get_json(url,15)
    bars,price=normalize_yahoo(d)
    if len(bars)<80:
        raise RuntimeError(f"Not enough {interval} history")
    return {"ok":True,"bars":bars,"price":price,"source":"Yahoo COMEX Gold futures","kind":"FUTURES","ts":int(time.time())}

def cached(key, ttl, fn):
    now=time.time()
    with _lock:
        x=_cache.get(key)
        if x and now-x["time"]<ttl:return x["data"]
    d=fn()
    if d.get("ok"):
        with _lock:_cache[key]={"time":now,"data":d}
    return d

class H(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send_bytes(self,data,ctype="text/html; charset=utf-8",status=200):
        self.send_response(status);self.send_header("Content-Type",ctype);self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
    def send_json(self,obj): self.send_bytes(json.dumps(obj).encode(),"application/json; charset=utf-8")
    def do_GET(self):
        p=urllib.parse.urlparse(self.path).path
        if p=="/api/m15": self.send_json(cached("m15",45,lambda:fetch_yahoo("15m","60d")));return
        if p=="/api/h1": self.send_json(cached("h1",45,lambda:fetch_yahoo("1h","6mo")));return
        # Serve the dashboard for every non-API route so shared/mobile links do not 404.
        self.send_bytes(HTML.encode())

def main():
    shown_host="127.0.0.1" if HOST=="0.0.0.0" else HOST
    url=f"http://{shown_host}:{PORT}/"
    print("="*68);print("Gold Precision Dashboard");print("Open:",url);print("="*68)
    srv=ThreadingHTTPServer((HOST,PORT),H)
    if os.environ.get("RENDER") is None and HOST in ("127.0.0.1","localhost"):
        threading.Timer(1.0,lambda:webbrowser.open(url)).start()
    try:srv.serve_forever()
    except KeyboardInterrupt:pass
    finally:srv.server_close()

if __name__=="__main__":
    main()
