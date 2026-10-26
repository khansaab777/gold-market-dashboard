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
<title>Gold Market Structure Dashboard</title>
<style>
:root{
  --bg:#070b10;--panel:#101720;--panel2:#151f2a;--line:#283545;--text:#f5f8fc;--muted:#8fa1b6;
  --green:#3bd383;--red:#ff7070;--orange:#ffb44c;--blue:#6aa8ff;--gold:#f3ca66;--cyan:#63d4e5;
}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(circle at top,#101924 0,#080d13 46%,#070a0f 100%);color:var(--text);font-family:Inter,Segoe UI,Arial,sans-serif}
.wrap{max-width:1380px;margin:auto;padding:18px}
.top{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;align-items:flex-start}
.brand h1{margin:0;font-size:27px}.brand p{margin:5px 0 0;color:var(--muted);font-size:13px}
.controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
button{background:var(--panel2);border:1px solid var(--line);color:#fff;padding:9px 12px;border-radius:10px;cursor:pointer}
.status{font-size:12px;color:var(--muted)}
.source{display:inline-block;margin-top:8px;padding:5px 9px;border-radius:999px;background:rgba(106,168,255,.12);color:#acd0ff;font-size:11px}
.banner{display:none;margin-top:12px;padding:10px 12px;border-radius:11px;border:1px solid rgba(255,180,76,.35);background:rgba(255,180,76,.08);color:#ffd496;font-size:12px}
.hero{display:grid;grid-template-columns:repeat(5,1fr);gap:11px;margin-top:14px}
.card{background:linear-gradient(180deg,rgba(17,24,33,.98),rgba(13,19,27,.98));border:1px solid var(--line);border-radius:15px;padding:14px;box-shadow:0 8px 25px rgba(0,0,0,.2)}
.kicker{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.09em}
.value{font-size:23px;font-weight:760;margin-top:6px;font-variant-numeric:tabular-nums}
.sub{font-size:11px;color:var(--muted);margin-top:5px;line-height:1.35}
.tfgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:11px;margin-top:11px}
.tf-title{display:flex;justify-content:space-between;align-items:center;gap:8px}.tf-title h2{margin:0;font-size:20px}
.badge{display:inline-block;padding:5px 9px;border-radius:999px;font-size:11px;font-weight:700}
.bull{background:rgba(59,211,131,.13);color:var(--green)}.bear{background:rgba(255,112,112,.13);color:var(--red)}.neutral{background:rgba(255,180,76,.12);color:var(--orange)}
.row{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:12px}
.mini{background:#0d141d;border:1px solid #202c39;border-radius:11px;padding:10px}.mini .kicker{font-size:9px}.mini .value{font-size:17px}
.main{display:grid;grid-template-columns:1.65fr 1fr;gap:11px;margin-top:11px}.chartbox{height:465px}canvas{width:100%;height:100%;display:block}
.table{width:100%;border-collapse:collapse;margin-top:6px}.table th,.table td{padding:9px 7px;border-bottom:1px solid var(--line);font-size:12px;text-align:right;font-variant-numeric:tabular-nums}
.table th:first-child,.table td:first-child{text-align:left}
.alert{margin-top:10px;padding:11px;border-radius:11px;background:#0d141d;border:1px solid #233140}.alert strong{display:block;margin-bottom:4px}
.green{color:var(--green)}.red{color:var(--red)}.orange{color:var(--orange)}.blue{color:var(--blue)}
footer{font-size:11px;color:var(--muted);margin:15px 2px}
@media(max-width:1080px){.hero{grid-template-columns:repeat(3,1fr)}.tfgrid{grid-template-columns:1fr}.main{grid-template-columns:1fr}}
@media(max-width:650px){.hero{grid-template-columns:1fr 1fr}.wrap{padding:11px}.row{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div class="brand">
      <h1>Gold Market Structure Dashboard</h1>
      <p>M15 / H1 / H4 trend, support-resistance, liquidity pools and sweep detection</p>
      <div id="source" class="source">Connecting…</div>
    </div>
    <div class="controls">
      <button id="refresh">Refresh structure</button>
      <span id="status" class="status">Starting…</span>
    </div>
  </div>
  <div id="banner" class="banner"></div>

  <div class="hero">
    <div class="card"><div class="kicker">Live gold price</div><div id="spot" class="value">—</div><div class="sub">~2-second refresh</div></div>
    <div class="card"><div class="kicker">MTF bias</div><div id="mtfBias" class="value">—</div><div id="mtfSub" class="sub">M15 + H1 + H4 agreement</div></div>
    <div class="card"><div class="kicker">Nearest buy-side liquidity</div><div id="buyLiq" class="value">—</div><div id="buyLiqSub" class="sub">Equal highs / clustered highs</div></div>
    <div class="card"><div class="kicker">Nearest sell-side liquidity</div><div id="sellLiq" class="value">—</div><div id="sellLiqSub" class="sub">Equal lows / clustered lows</div></div>
    <div class="card"><div class="kicker">Latest liquidity event</div><div id="latestSweep" class="value">—</div><div id="latestSweepSub" class="sub">No event yet</div></div>
  </div>

  <div class="tfgrid" id="tfgrid"></div>

  <div class="main">
    <div class="card">
      <div class="kicker">M15 price structure + key levels</div>
      <div class="chartbox"><canvas id="chart"></canvas></div>
    </div>
    <div class="card">
      <div class="kicker">Liquidity map</div>
      <table class="table">
        <thead><tr><th>Type</th><th>Level</th><th>Distance</th><th>Status</th></tr></thead>
        <tbody id="liqTable"></tbody>
      </table>
      <div id="sweepAlert" class="alert"><strong>Liquidity sweep</strong><span>No recent sweep detected.</span></div>
      <div class="alert"><strong>Liquidity definition</strong><span class="sub">Buy-side liquidity = clustered/equal swing highs above price. Sell-side liquidity = clustered/equal swing lows below price. Sweep = price trades through a liquidity level and closes back through it.</span></div>
    </div>
  </div>
  <footer>Chart-inferred liquidity zones, not actual broker/exchange resting orders.</footer>
</div>

<script>
const $=id=>document.getElementById(id);
const fmt=x=>Number.isFinite(x)?x.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2}):"—";
let spot=NaN,m15=[],h1=[],structures={};

async function j(url){const r=await fetch(url,{cache:"no-store"});if(!r.ok)throw new Error("HTTP "+r.status);return await r.json()}

function aggregateH4(bars){
  const m=new Map();
  for(const p of bars){
    const d=new Date(p.t*1000),h=Math.floor(d.getUTCHours()/4)*4;
    const k=Date.UTC(d.getUTCFullYear(),d.getUTCMonth(),d.getUTCDate(),h)/1000;
    if(!m.has(k))m.set(k,{t:k,o:p.o,h:p.h,l:p.l,c:p.c});
    else{const b=m.get(k);b.h=Math.max(b.h,p.h);b.l=Math.min(b.l,p.l);b.c=p.c}
  }
  return [...m.values()].sort((a,b)=>a.t-b.t);
}
function ema(v,p){if(!v.length)return[];const a=2/(p+1),o=[v[0]];for(let i=1;i<v.length;i++)o.push(a*v[i]+(1-a)*o[i-1]);return o}
function atr(b,p=14){if(b.length<p+2)return NaN;const tr=[];for(let i=1;i<b.length;i++){const x=b[i],pc=b[i-1].c;tr.push(Math.max(x.h-x.l,Math.abs(x.h-pc),Math.abs(x.l-pc)))}return tr.slice(-p).reduce((a,c)=>a+c,0)/p}
function pivots(b,strength=3,lookback=180){
  const s=b.slice(-lookback),highs=[],lows=[];
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
  return{highs,lows}
}
function cluster(items,tol){
  const sorted=[...items].sort((a,b)=>a.v-b.v),cs=[];
  for(const x of sorted){
    let c=cs.find(c=>Math.abs(x.v-c.level)<=tol);
    if(!c){c={level:x.v,items:[x]};cs.push(c)}
    else{c.items.push(x);c.level=c.items.reduce((a,z)=>a+z.v,0)/c.items.length}
  }
  return cs.filter(c=>c.items.length>=2).map(c=>({level:c.level,touches:c.items.length,lastTime:Math.max(...c.items.map(x=>x.t))}))
}
function nearest(a,p,side){const f=a.filter(x=>side==="above"?x.level>p:x.level<p);if(!f.length)return null;return f.sort((x,y)=>Math.abs(x.level-p)-Math.abs(y.level-p))[0]}
function sweep(b,level,type){
  if(!level)return null;
  for(const x of b.slice(-12).reverse()){
    if(type==="BUY"&&x.h>level.level&&x.c<level.level)return{type:"BUY-SIDE SWEEP",bias:"BEARISH",time:x.t,level:level.level};
    if(type==="SELL"&&x.l<level.level&&x.c>level.level)return{type:"SELL-SIDE SWEEP",bias:"BULLISH",time:x.t,level:level.level};
  }
  return null;
}
function analyze(b,label){
  const s=b.slice().sort((a,c)=>a.t-c.t),cl=s.map(x=>x.c),e20=ema(cl,20),e50=ema(cl,50),A=atr(s),pv=pivots(s),lastH=pv.highs.slice(-2),lastL=pv.lows.slice(-2);
  let structure="MIXED";
  if(lastH.length>=2&&lastL.length>=2){
    if(lastH[1].v>lastH[0].v&&lastL[1].v>lastL[0].v)structure="HH/HL";
    else if(lastH[1].v<lastH[0].v&&lastL[1].v<lastL[0].v)structure="LH/LL";
  }
  let score=0,sl=e20.length>3?e20.at(-1)-e20.at(-3):0;
  if(e20.at(-1)>e50.at(-1)){score++;if(sl>0)score++}else if(e20.at(-1)<e50.at(-1)){score--;if(sl<0)score--}
  if(structure==="HH/HL")score+=2;if(structure==="LH/LL")score-=2;
  const trend=score>=2?"BULLISH":score<=-2?"BEARISH":"NEUTRAL";
  const p=Number.isFinite(spot)?spot:s.at(-1).c,tol=Math.max((A||0)*.18,p*.00035);
  const hc=cluster(pv.highs,tol),lc=cluster(pv.lows,tol),buy=nearest(hc,p,"above"),sell=nearest(lc,p,"below");
  const res=(pv.highs.filter(x=>x.v>p).sort((a,b)=>a.v-b.v)[0]||{}).v||null;
  const sup=(pv.lows.filter(x=>x.v<p).sort((a,b)=>b.v-a.v)[0]||{}).v||null;
  const sw=[sweep(s,buy,"BUY"),sweep(s,sell,"SELL")].filter(Boolean).sort((a,b)=>b.time-a.time)[0]||null;
  return{label,trend,score,structure,A,buyLiq:buy,sellLiq:sell,res,sup,sweep:sw,bars:s}
}
function card(x){
  const cls=x.trend==="BULLISH"?"bull":x.trend==="BEARISH"?"bear":"neutral",a=x.trend==="BULLISH"?"↑":x.trend==="BEARISH"?"↓":"↔";
  return `<div class="card"><div class="tf-title"><h2>${x.label}</h2><span class="badge ${cls}">${a} ${x.trend}</span></div><div class="sub">Structure: <b>${x.structure}</b> · ATR14: ${fmt(x.A)}</div><div class="row"><div class="mini"><div class="kicker">Support</div><div class="value">${x.sup?fmt(x.sup):"—"}</div></div><div class="mini"><div class="kicker">Resistance</div><div class="value">${x.res?fmt(x.res):"—"}</div></div><div class="mini"><div class="kicker">Sell-side liquidity</div><div class="value">${x.sellLiq?fmt(x.sellLiq.level):"—"}</div><div class="sub">${x.sellLiq?x.sellLiq.touches+" touches":"No cluster"}</div></div><div class="mini"><div class="kicker">Buy-side liquidity</div><div class="value">${x.buyLiq?fmt(x.buyLiq.level):"—"}</div><div class="sub">${x.buyLiq?x.buyLiq.touches+" touches":"No cluster"}</div></div></div></div>`
}
function allLiq(){
  const a=[];for(const x of Object.values(structures)){if(x.buyLiq)a.push({side:"BUY",tf:x.label,...x.buyLiq,d:Math.abs(x.buyLiq.level-spot),A:x.A});if(x.sellLiq)a.push({side:"SELL",tf:x.label,...x.sellLiq,d:Math.abs(x.sellLiq.level-spot),A:x.A})}
  return a.sort((a,b)=>a.d-b.d)
}
function latestSweep(){return Object.values(structures).map(x=>x.sweep?{...x.sweep,tf:x.label}:null).filter(Boolean).sort((a,b)=>b.time-a.time)[0]||null}
function render(){
  if(!structures.M15)return;
  $("tfgrid").innerHTML=["M15","H1","H4"].map(k=>card(structures[k])).join("");
  const sc=structures.M15.score+structures.H1.score+structures.H4.score,bias=sc>=4?"BULLISH":sc<=-4?"BEARISH":"MIXED";
  $("mtfBias").textContent=bias;$("mtfBias").className="value "+(bias==="BULLISH"?"green":bias==="BEARISH"?"red":"orange");$("mtfSub").textContent=`Combined score ${sc>0?"+":""}${sc}`;
  const liq=allLiq(),buy=liq.find(x=>x.side==="BUY"),sell=liq.find(x=>x.side==="SELL");
  $("buyLiq").textContent=buy?fmt(buy.level):"—";$("buyLiqSub").textContent=buy?`${buy.tf} · ${buy.touches} touches · ${fmt(buy.d)} away`:"No cluster";
  $("sellLiq").textContent=sell?fmt(sell.level):"—";$("sellLiqSub").textContent=sell?`${sell.tf} · ${sell.touches} touches · ${fmt(sell.d)} away`:"No cluster";
  const sw=latestSweep();
  if(sw){$("latestSweep").textContent=sw.type;$("latestSweep").className="value "+(sw.bias==="BULLISH"?"green":"red");$("latestSweepSub").textContent=`${sw.tf} · ${new Date(sw.time*1000).toLocaleString()} · ${fmt(sw.level)}`;$("sweepAlert").innerHTML=`<strong class="${sw.bias==="BULLISH"?"green":"red"}">${sw.type} (${sw.tf})</strong><span>${sw.bias} reaction: price swept ${fmt(sw.level)} and closed back through it.</span>`}
  else{$("latestSweep").textContent="NONE";$("latestSweep").className="value";$("latestSweepSub").textContent="No recent sweep";$("sweepAlert").innerHTML="<strong>Liquidity sweep</strong><span>No recent sweep detected.</span>"}
  $("liqTable").innerHTML=liq.slice(0,8).map(r=>`<tr><td>${r.side==="BUY"?"Buy-side":"Sell-side"} · ${r.tf}</td><td>${fmt(r.level)}</td><td>${fmt(r.d)}</td><td class="${r.A&&r.d<=.35*r.A?"orange":""}">${r.A&&r.d<=.35*r.A?"NEAR":"Waiting"}</td></tr>`).join("")||'<tr><td colspan="4">No clustered liquidity zones detected.</td></tr>';
  draw()
}
function draw(){
  const m=structures.M15;if(!m)return;const c=$("chart"),r=c.getBoundingClientRect(),dpr=devicePixelRatio||1;c.width=r.width*dpr;c.height=r.height*dpr;const ctx=c.getContext("2d");ctx.scale(dpr,dpr);const W=r.width,H=r.height,L=55,R=12,T=18,B=28,b=m.bars.slice(-100),lv=[m.sup,m.res,m.buyLiq?.level,m.sellLiq?.level].filter(Number.isFinite),vals=b.flatMap(x=>[x.h,x.l]).concat(lv,[spot]);let mn=Math.min(...vals),mx=Math.max(...vals),pad=(mx-mn)*.05||1;mn-=pad;mx+=pad;const xx=i=>L+i*(W-L-R)/Math.max(1,b.length-1),yy=v=>T+(mx-v)*(H-T-B)/(mx-mn);ctx.clearRect(0,0,W,H);ctx.font="11px Segoe UI";ctx.strokeStyle="#263240";ctx.fillStyle="#8497ac";for(let k=0;k<5;k++){const y=T+k*(H-T-B)/4;ctx.beginPath();ctx.moveTo(L,y);ctx.lineTo(W-R,y);ctx.stroke();ctx.fillText((mx-k*(mx-mn)/4).toFixed(1),4,y+4)}function line(v,col,label,d=[4,4]){if(!Number.isFinite(v))return;ctx.strokeStyle=col;ctx.setLineDash(d);ctx.beginPath();ctx.moveTo(L,yy(v));ctx.lineTo(W-R,yy(v));ctx.stroke();ctx.setLineDash([]);ctx.fillStyle=col;ctx.fillText(label,W-R-62,yy(v)-4)}line(m.res,"#ff7070","Resistance");line(m.sup,"#3bd383","Support");line(m.buyLiq?.level,"#ffb44c","Buy Liq",[2,4]);line(m.sellLiq?.level,"#63d4e5","Sell Liq",[2,4]);ctx.strokeStyle="#6aa8ff";ctx.lineWidth=1.8;ctx.beginPath();b.forEach((q,i)=>i?ctx.lineTo(xx(i),yy(q.c)):ctx.moveTo(xx(i),yy(q.c)));ctx.stroke();if(Number.isFinite(spot)){ctx.fillStyle="#f3ca66";ctx.beginPath();ctx.arc(W-R-3,yy(spot),4,0,Math.PI*2);ctx.fill();ctx.fillText("NOW",W-R-40,yy(spot)-7)}}
async function loadSpot(){try{const d=await j("/api/spot");if(!d.ok)throw new Error(d.error||"Spot unavailable");spot=Number(d.price);$("spot").textContent="$"+fmt(spot);$("source").textContent="Data source: "+d.source;$("status").textContent="Live "+new Date().toLocaleTimeString();if(m15.length&&h1.length){structures.M15=analyze(m15,"M15");structures.H1=analyze(h1,"H1");structures.H4=analyze(aggregateH4(h1),"H4");render()}}catch(e){$("status").textContent="Live retrying…"}}
async function loadStructure(){try{const[a,b]=await Promise.all([j("/api/m15"),j("/api/h1")]);if(!a.ok||!b.ok)throw new Error("Structure data unavailable");m15=a.bars;h1=b.bars;structures.M15=analyze(m15,"M15");structures.H1=analyze(h1,"H1");structures.H4=analyze(aggregateH4(h1),"H4");$("banner").style.display="none";render();$("status").textContent="Structure "+new Date().toLocaleTimeString()}catch(e){$("banner").textContent="Structure refresh failed: "+e.message;$("banner").style.display="block"}}
$("refresh").onclick=loadStructure;window.addEventListener("resize",draw);loadSpot();loadStructure();setInterval(loadSpot,2000);setInterval(loadStructure,60000);
</script>
</body>
</html>
"""

def get_json(url, timeout=12):
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
    if len(bars)<50:
        raise RuntimeError("Not enough history")
    return {"ok":True,"bars":bars,"price":price,"source":"Yahoo COMEX Gold futures","kind":"FUTURES","ts":int(time.time())}

def fetch_spot():
    try:
        d=get_json("https://xaus.com/api/v1/spot?compact=1",8)
        p=d.get("spot_usd_oz")
        if p is None: p=((d.get("xau") or {}).get("price"))
        p=float(p)
        if p>0:return {"ok":True,"price":p,"source":"XAU spot feed","kind":"SPOT","ts":int(time.time())}
    except Exception:
        pass
    try:
        d=fetch_yahoo("1m","1d")
        p=d.get("price") or d["bars"][-1]["c"]
        return {"ok":True,"price":float(p),"source":"Yahoo COMEX Gold futures","kind":"FUTURES","ts":int(time.time())}
    except Exception as e:
        return {"ok":False,"error":str(e),"ts":int(time.time())}

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
    def send_json(self,obj):
        self.send_bytes(json.dumps(obj).encode(),"application/json; charset=utf-8")
    def do_GET(self):
        p=urllib.parse.urlparse(self.path).path
        if p=="/api/spot": self.send_json(cached("spot",1.5,fetch_spot));return
        if p=="/api/m15": self.send_json(cached("m15",45,lambda:fetch_yahoo("15m","60d")));return
        if p=="/api/h1": self.send_json(cached("h1",45,lambda:fetch_yahoo("1h","6mo")));return
        if p in ("/","/dashboard.html"): self.send_bytes(HTML.encode());return
        self.send_bytes(b"Not found","text/plain",404)

def main():
    shown_host = "127.0.0.1" if HOST == "0.0.0.0" else HOST
    url=f"http://{shown_host}:{PORT}/"
    print("="*60)
    print("Gold Market Dashboard")
    print("Open:",url)
    print("="*60)
    srv=ThreadingHTTPServer((HOST,PORT),H)
    if os.environ.get("RENDER") is None:
        threading.Timer(1.0,lambda:webbrowser.open(url)).start()
    try:srv.serve_forever()
    except KeyboardInterrupt:pass
    finally:srv.server_close()

if __name__=="__main__":
    main()
