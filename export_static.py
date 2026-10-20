"""Exports the database to docs/index.html (+ data.json): the static dashboard for GitHub Pages.
Date-range pickers, auto day/month/year bars, and a "select results -> publish / share" panel."""
import json, pathlib, db

TEMPLATE = r'''<!doctype html>
<html lang="so"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Somaliland Media Monitor</title>
<style>
body{font:15px system-ui,sans-serif;margin:0;background:#f6f7f9;color:#1b1f24}
header{background:#0b5d3b;color:#fff;padding:14px 20px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;align-items:center}
main{max-width:1150px;margin:auto;padding:16px}
.card{background:#fff;border-radius:10px;padding:14px;margin-bottom:14px;box-shadow:0 1px 3px #0001}
.row{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:4px 0}
label{font-weight:600}
button,select,input{padding:6px 10px;border:1px solid #ccc;border-radius:6px;background:#fff;font:inherit}
input[type=date]{min-width:150px}
button{cursor:pointer}button.on{background:#0b5d3b;color:#fff;border-color:#0b5d3b}
.preset{background:#e8f3ee;border-color:#cfe6da;color:#0b5d3b}
.bar{display:flex;align-items:center;gap:8px;cursor:pointer;margin:3px 0}.k{width:90px;font-size:13px;flex:none}.b{height:12px;background:#2e9e6b;border-radius:3px;min-width:1px}
.stats{display:flex;flex-wrap:wrap;gap:10px}.stat{background:#eef5f1;border-radius:8px;padding:8px 14px}.stat b{font-size:20px;display:block}
.chip{display:inline-block;background:#e8f3ee;border-radius:14px;padding:3px 10px;margin:2px;cursor:pointer;font-size:13px;color:#0b5d3b}
.chip.on{background:#0b5d3b;color:#fff}
td{padding:6px;border-bottom:1px solid #eee;font-size:14px;vertical-align:top}table{width:100%;border-collapse:collapse}
pre{white-space:pre-wrap;font:14px/1.5 system-ui;margin:6px 0 10px}
.positive{color:#1a7f37}.negative{color:#c0392b}a{color:#0b5d3b}.muted{color:#666;font-size:13px}
details{margin:4px 0}summary{cursor:pointer}
textarea{width:100%;box-sizing:border-box;min-height:150px;padding:8px;border:1px solid #ccc;border-radius:6px;font:14px/1.45 system-ui}
.share a{display:inline-block;margin:3px 6px 3px 0;padding:6px 12px;border-radius:6px;background:#0b5d3b;color:#fff;text-decoration:none}
.pubcard{border:2px solid #0b5d3b}
</style></head><body>
<header><b id="t"></b><span><button id="lg"></button></span></header>
<main>
<div class="card">
  <div class="row">
    <label id="lFrom" for="from"></label><input type="date" id="from">
    <label id="lTo" for="to"></label><input type="date" id="to">
    <span id="presets"></span>
  </div>
  <div class="row"><select id="topic"></select><select id="type"></select><input id="q" placeholder="..."></div>
  <div class="muted" id="rangeNote"></div>
</div>
<div class="card" id="stats"></div>
<div class="card pubcard" id="pub" style="display:none"></div>
<div class="card"><h3 id="hBars" style="margin-top:0"></h3><div id="bars"></div></div>
<div class="card" id="sum"></div>
<div class="card"><h3 id="hList" style="margin-top:0"></h3><table id="tb"></table></div>
</main>
<script>
const L={
 so:{t:"Kormeeraha Warbaahinta Caalamiga ee Somaliland",from:"Laga bilaabo",to:"Ilaa",lg:"English",topic:"Mawduuc: dhammaan",type:"Nooca: dhammaan",
     q:"Raadi...",today:"Maanta",d7:"7 maalmood",d30:"30 maalmood",month:"Bishan",year:"Sannadkan",all:"Dhammaan",
     total:"Wadarta wararka",topics:"Mawduucyada",sources:"Ilaha ugu badan",sent:"Dareenka",bars:"Tirada wararka",
     byDay:"maalin kasta",byMonth:"bil kasta",byYear:"sannad kasta",click:"Riix baar si aad u aragto muddadaas",
     sum:"Soo koobid",noSum:"Weli ma jirto soo koobid la keydiyey muddadan.",sumDay:"soo koobidda maalinlaha ah",sumMonth:"soo koobidda bilaha ee muddadan",sumYear:"soo koobidda sannadaha ee muddadan",
     list:"Wararka",showing:"Waxaa la tusayaa",of:"ka mid ah",read:"Akhri soo koobidda",none:"Wax war ah looma helin muddadan.",
     range:"Muddada la doortay",days:"maalmood",selected:"La doortay",pubTitle:"Daabaci natiijooyinka la doortay",copyText:"Koobi qoraalka",copyIds:"Koobi ID-yada",clear:"Tirtir doorashada",shareOn:"Ku wadaag",agent:"Fur wakiilka daabacaadda (GitHub)",hint:"Daabacaad otomaatig ah: koobi ID-yada, kadibna ku dheji goobta ids ee wakiilka daabacaadda. Badhamada hoose waxay furaan daaqadda wadaagista ee shabakadaha bulshada (adiga ayaa gujinaya Post).",selAll:"Dooro dhammaan kuwa la muujiyey",positive:"Wanaagsan",negative:"Xun",neutral:"Dhexdhexaad"},
 en:{t:"Somaliland International Media Monitor",from:"From",to:"To",lg:"Soomaali",topic:"Topic: all",type:"Type: all",
     q:"Search...",today:"Today",d7:"Last 7 days",d30:"Last 30 days",month:"This month",year:"This year",all:"All time",
     total:"Total mentions",topics:"Topics",sources:"Top sources",sent:"Tone",bars:"Mentions",
     byDay:"per day",byMonth:"per month",byYear:"per year",click:"click a bar to zoom to that period",
     sum:"Summary",noSum:"No stored summary for this range yet.",sumDay:"daily summaries",sumMonth:"monthly summaries covering this range",sumYear:"yearly summaries covering this range",
     list:"Mentions",showing:"Showing",of:"of",read:"Read summary",none:"No mentions found in this range.",
     range:"Selected range",days:"days",selected:"Selected",pubTitle:"Publish selected results",copyText:"Copy text",copyIds:"Copy IDs",clear:"Clear selection",shareOn:"Share on",agent:"Open publishing agent (GitHub)",hint:"To publish automatically: copy the IDs and paste them in the ids box of the publishing agent. The buttons below only open the network's own share window (you press Post yourself).",selAll:"Select all shown",positive:"Positive",negative:"Negative",neutral:"Neutral"}
};
const TOPIC_SO={recognition:"Aqoonsi",israel:"Israa'iil",geography:"Juquraafi",usa:"Mareykanka",ethiopia:"Itoobiya",uae:"Imaaraadka",china_taiwan:"Shiinaha / Taiwan",conference:"Shir",somalia:"Soomaaliya",security:"Amni",economy:"Dhaqaale"};

let D={mentions:[],summaries:[]}, lang="so", topic="", type="", selected=new Set(), postDirty=false, lastKey="";
const $=id=>document.getElementById(id);
const esc=s=>String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const iso=d=>d.toISOString().slice(0,10);
const addDays=(s,n)=>{const d=new Date(s+"T00:00:00Z");d.setUTCDate(d.getUTCDate()+n);return iso(d)};
const daysBetween=(a,b)=>Math.round((new Date(b+"T00:00:00Z")-new Date(a+"T00:00:00Z"))/864e5);
const monthEnd=ym=>{const p=ym.split("-").map(Number);return iso(new Date(Date.UTC(p[0],p[1],0)))};
const todayStr=()=>{const n=new Date();return n.getFullYear()+"-"+String(n.getMonth()+1).padStart(2,"0")+"-"+String(n.getDate()).padStart(2,"0")};
const tname=k=>lang==="so"&&TOPIC_SO[k]?TOPIC_SO[k]:k;

function granFor(span){return span<=62?"day":span<=1100?"month":"year"}
function bucketKey(day,g){return g==="day"?day:g==="month"?day.slice(0,7):day.slice(0,4)}
function bucketRange(k,g){return g==="day"?[k,k]:g==="month"?[k+"-01",monthEnd(k)]:[k+"-01-01",k+"-12-31"]}
function bucketList(from,to,g){
  const out=[];
  if(g==="day"){for(let d=from;d<=to;d=addDays(d,1))out.push(d)}
  else if(g==="month"){let y=+from.slice(0,4),m=+from.slice(5,7);const ey=+to.slice(0,4),em=+to.slice(5,7);
    while(y<ey||(y===ey&&m<=em)){out.push(y+"-"+String(m).padStart(2,"0"));m++;if(m>12){m=1;y++}}}
  else{for(let y=+from.slice(0,4);y<=+to.slice(0,4);y++)out.push(String(y))}
  return out;
}
function getRange(){
  let f=$("from").value,t=$("to").value;
  if(!f&&!t){t=todayStr();f=addDays(t,-29)}
  if(!f)f=t; if(!t)t=f;
  if(f>t){const x=f;f=t;t=x}
  return [f,t];
}
function setRange(f,t){$("from").value=f;$("to").value=t;draw()}
function matches(m,q){
  if(topic&&(","+(m.topics||"")+",").indexOf(","+topic+",")<0)return false;
  if(type&&m.source_type!==type)return false;
  if(q&&((m.title||"")+" "+(m.title_so||"")).toLowerCase().indexOf(q)<0)return false;
  return true;
}
function topN(counter,n){return Object.entries(counter).sort((a,b)=>b[1]-a[1]).slice(0,n)}

function drawPresets(){
  const t=L[lang],td=todayStr();
  const defs=[["today",td,td],["d7",addDays(td,-6),td],["d30",addDays(td,-29),td],["month",td.slice(0,7)+"-01",td],["year",td.slice(0,4)+"-01-01",td]];
  let all=null;
  if(D.mentions.length){const ds=D.mentions.map(m=>m.day).filter(Boolean).sort();all=[ds[0],ds[ds.length-1]>td?ds[ds.length-1]:td]}
  $("presets").innerHTML=defs.map(d=>`<button class="preset" data-f="${d[1]}" data-t="${d[2]}">${t[d[0]]}</button>`).join(" ")+
    (all?` <button class="preset" data-f="${all[0]}" data-t="${all[1]}">${t.all}</button>`:"");
  $("presets").querySelectorAll("button").forEach(b=>b.onclick=()=>setRange(b.dataset.f,b.dataset.t));
}

function draw(){
  const t=L[lang];document.documentElement.lang=lang;
  $("t").textContent=t.t;$("lg").textContent=t.lg;$("lFrom").textContent=t.from;$("lTo").textContent=t.to;$("q").placeholder=t.q;
  $("topic").options[0].textContent=t.topic;$("type").options[0].textContent=t.type;
  [...$("topic").options].slice(1).forEach(o=>o.textContent=tname(o.value));
  drawPresets();
  const [from,to]=getRange();
  const span=daysBetween(from,to)+1;
  $("rangeNote").textContent=t.range+": "+from+"  →  "+to+"  ("+span+" "+t.days+")";
  const q=$("q").value.trim().toLowerCase();

  // everything inside the date range and the other filters
  const inRange=D.mentions.filter(m=>m.day&&m.day>=from&&m.day<=to);
  const rows=inRange.filter(m=>matches(m,q));

  // statistics
  const sent={positive:0,negative:0,neutral:0},tc={},sc={};
  rows.forEach(m=>{sent[m.sentiment]=(sent[m.sentiment]||0)+1;
    (m.topics||"").split(",").filter(Boolean).forEach(x=>tc[x]=(tc[x]||0)+1);
    if(m.source_name)sc[m.source_name]=(sc[m.source_name]||0)+1});
  $("stats").innerHTML=`<div class="stats"><div class="stat">${t.total}<b>${rows.length}</b></div>`+
    ["positive","neutral","negative"].map(k=>`<div class="stat ${k}">${t[k]}<b>${sent[k]||0}</b></div>`).join("")+`</div>`+
    `<div style="margin-top:8px"><b>${t.topics}:</b> `+topN(tc,10).map(([k,v])=>`<span class="chip ${topic===k?"on":""}" data-topic="${esc(k)}">${esc(tname(k))} · ${v}</span>`).join("")+`</div>`+
    `<div style="margin-top:6px"><b>${t.sources}:</b> <span class="muted">`+topN(sc,6).map(([k,v])=>esc(k)+" ("+v+")").join(", ")+`</span></div>`;
  $("stats").querySelectorAll("[data-topic]").forEach(c=>c.onclick=()=>{topic=topic===c.dataset.topic?"":c.dataset.topic;$("topic").value=topic;draw()});

  // bars: day / month / year automatically, depending on how long the range is
  const g=granFor(span),cnt={};
  rows.forEach(m=>{const k=bucketKey(m.day,g);cnt[k]=(cnt[k]||0)+1});
  const keys=bucketList(from,to,g),mx=Math.max(1,...keys.map(k=>cnt[k]||0));
  $("hBars").textContent=t.bars+" – "+(g==="day"?t.byDay:g==="month"?t.byMonth:t.byYear);
  $("bars").innerHTML=keys.map(k=>`<div class="bar" data-k="${k}"><span class="k">${k}</span><span class="b" style="width:${(cnt[k]||0)/mx*70}%"></span><span>${cnt[k]||0}</span></div>`).join("")+
    `<div class="muted" style="margin-top:6px">${t.click}</div>`;
  $("bars").querySelectorAll(".bar").forEach(b=>b.onclick=()=>{const r=bucketRange(b.dataset.k,g);setRange(r[0],r[1])});

  // stored summaries (made by the agent) that belong to this range
  const sp=span<=31?"day":span<=800?"month":"year";
  const fk=bucketKey(from,sp),tk=bucketKey(to,sp);
  const sums=D.summaries.filter(s=>s.period===sp&&s.period_key>=fk&&s.period_key<=tk).sort((a,b)=>a.period_key<b.period_key?1:-1).slice(0,40);
  const lab=sp==="day"?t.sumDay:sp==="month"?t.sumMonth:t.sumYear;
  $("sum").innerHTML=`<h3 style="margin-top:0">${t.sum} – ${lab}</h3>`+(sums.length?
    sums.map(s=>`<details ${sums.length===1?"open":""}><summary><b>${esc(s.period_key)}</b> (${s.mention_count})</summary><pre>${esc(lang==="so"&&s.summary_so?s.summary_so:s.summary_en)}</pre></details>`).join(""):
    `<div class="muted">${t.noSum}</div>`);

  // list
  $("hList").textContent=t.list+" – "+t.showing+" "+Math.min(rows.length,500)+" "+t.of+" "+rows.length;
  const head=`<tr><th style="width:28px"><input type="checkbox" id="selAll" title="${esc(t.selAll)}"></th><th colspan="4" class="muted" style="text-align:left;font-weight:400">${esc(t.selAll)}</th></tr>`;
  $("tb").innerHTML=rows.length?head+rows.slice(0,500).map(m=>{
    const title=lang==="so"&&m.title_so?m.title_so:m.title;
    const sm=(m.summary_so||m.summary_en)?`<details><summary>${t.read}</summary><div style="margin-top:4px;color:#333">${esc(lang==="so"&&m.summary_so?m.summary_so:m.summary_en)}</div></details>`:"";
    const cb=m.id!=null?`<input type="checkbox" class="sel" data-id="${esc(m.id)}" ${selected.has(String(m.id))?"checked":""}>`:"";
    return `<tr><td>${cb}</td><td>${esc(m.day)}</td><td><a href="${esc(m.url)}" target="_blank" rel="noopener">${esc(title)}</a>${sm}</td><td>${esc(m.source_name)}</td><td>${esc((m.topics||"").split(",").filter(Boolean).map(tname).join(", "))}</td><td class="${esc(m.sentiment)}">${esc(t[m.sentiment]||m.sentiment)}</td></tr>`}).join(""):
    `<tr><td class="muted">${t.none}</td></tr>`;
  $("tb").querySelectorAll(".sel").forEach(c=>c.onchange=()=>{c.checked?selected.add(c.dataset.id):selected.delete(c.dataset.id);drawPub()});
  const sa=$("selAll");if(sa){sa.checked=rows.slice(0,500).length>0&&rows.slice(0,500).every(m=>selected.has(String(m.id)));
    sa.onchange=()=>{rows.slice(0,500).forEach(m=>{if(m.id!=null)sa.checked?selected.add(String(m.id)):selected.delete(String(m.id))});
      $("tb").querySelectorAll(".sel").forEach(c=>c.checked=sa.checked);drawPub()}}
  drawPub();
}

function siteUrl(){return location.origin+location.pathname.replace(/index\.html$/,"")}
function agentUrl(){const h=location.hostname;if(h.endsWith(".github.io")){const repo=location.pathname.split("/")[1];if(repo)return "https://github.com/"+h.split(".")[0]+"/"+repo+"/actions/workflows/publish.yml"}return ""}
function copyTo(text,btn){
  const flash=()=>{const o=btn.textContent;btn.textContent="✔";setTimeout(()=>btn.textContent=o,1200)};
  const old=()=>{const ta=document.createElement("textarea");ta.value=text;document.body.appendChild(ta);ta.select();try{document.execCommand("copy")}catch(e){}document.body.removeChild(ta);flash()};
  if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(text).then(flash,old);else old();
}
function pickedItems(){
  return D.mentions.filter(m=>m.id!=null&&selected.has(String(m.id))).sort((a,b)=>(a.day<b.day?1:-1));
}
function buildPostText(items){
  const [from,to]=getRange();
  const head=lang==="so"?"📰 Somaliland warbaahinta":"📰 Somaliland in the media";
  const ttl=m=>lang==="so"&&m.title_so?m.title_so:m.title;
  if(items.length===1){const m=items[0];const sm=lang==="so"?(m.summary_so||m.summary_en):m.summary_en;
    return "📰 "+ttl(m)+(sm?"\n"+sm:"")+"\n"+(lang==="so"?"Ilaha: ":"Source: ")+(m.source_name||"")+" · "+m.day+"\n"+m.url+"\n#Somaliland"}
  const days=items.map(m=>m.day).sort();
  return head+" — "+days[0]+(days[0]!==days[days.length-1]?" → "+days[days.length-1]:"")+"\n\n"+
    items.slice(0,10).map((m,i)=>(i+1)+") "+ttl(m)+" — "+(m.source_name||"")).join("\n")+"\n\n"+siteUrl()+"\n#Somaliland"}
function drawPub(){
  const box=$("pub"),t=L[lang],items=pickedItems();
  if(!items.length){box.style.display="none";box.innerHTML="";lastKey="";return}
  box.style.display="block";
  const key=items.map(m=>m.id).join(",")+"|"+lang;
  if(key!==lastKey){lastKey=key;postDirty=false}
  const keep=$("postText")&&postDirty?$("postText").value:buildPostText(items);
  const link=items.length===1?items[0].url:siteUrl();
  const e=encodeURIComponent,tx=keep,short=tx.length>250?tx.slice(0,247)+"…":tx;
  const ag=agentUrl();
  box.innerHTML=`<h3 style="margin-top:0">${t.pubTitle} (${t.selected}: ${items.length})</h3>
   <div class="muted" style="margin-bottom:6px">IDs: <b id="idsOut">${items.map(m=>m.id).join(",")}</b></div>
   <textarea id="postText">${esc(keep)}</textarea>
   <div class="row"><button id="cpText">${t.copyText}</button><button id="cpIds">${t.copyIds}</button><button id="clr">${t.clear}</button>${ag?`<a href="${esc(ag)}" target="_blank" rel="noopener">${t.agent}</a>`:""}</div>
   <div class="share"><b>${t.shareOn}:</b>
    <a target="_blank" rel="noopener" data-n="fb" href="https://www.facebook.com/sharer/sharer.php?u=${e(link)}">Facebook</a>
    <a target="_blank" rel="noopener" data-n="x" href="https://twitter.com/intent/tweet?text=${e(short)}&url=${e(link)}">X</a>
    <a target="_blank" rel="noopener" data-n="tg" href="https://t.me/share/url?url=${e(link)}&text=${e(tx)}">Telegram</a>
    <a target="_blank" rel="noopener" data-n="wa" href="https://wa.me/?text=${e(tx)}">WhatsApp</a>
    <a target="_blank" rel="noopener" data-n="li" href="https://www.linkedin.com/sharing/share-offsite/?url=${e(link)}">LinkedIn</a></div>
   <div class="muted" style="margin-top:6px">${t.hint}</div>`;
  $("postText").oninput=()=>{postDirty=true};
  $("postText").onchange=()=>drawPub();
  $("cpText").onclick=ev=>copyTo($("postText").value,ev.target);
  $("cpIds").onclick=ev=>copyTo(items.map(m=>m.id).join(","),ev.target);
  $("clr").onclick=()=>{selected.clear();postDirty=false;draw()};
}

function init(){
  const tp=[...new Set(D.mentions.flatMap(m=>(m.topics||"").split(",")).filter(Boolean))].sort();
  const ty=[...new Set(D.mentions.map(m=>m.source_type).filter(Boolean))].sort();
  $("topic").innerHTML="<option value=''></option>"+tp.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join("");
  $("type").innerHTML="<option value=''></option>"+ty.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join("");
  $("topic").onchange=e=>{topic=e.target.value;draw()};$("type").onchange=e=>{type=e.target.value;draw()};
  $("q").oninput=draw;$("from").onchange=draw;$("to").onchange=draw;
  $("lg").onclick=()=>{lang=lang==="so"?"en":"so";draw()};
  // start with the 30 days that end on the newest mention (or today)
  const ds=D.mentions.map(m=>m.day).filter(Boolean).sort(),end=ds.length?ds[ds.length-1]:todayStr();
  $("to").value=end;$("from").value=addDays(end,-29);
  draw();
}
fetch("data.json").then(r=>r.json()).then(d=>{D=d;init()}).catch(()=>{init()});
</script></body></html>
'''

db.init(); con = db.connect()
rows = [dict(r) for r in con.execute(
    "SELECT id,day,month,year,source_type,source_name,title,title_so,url,topics,sentiment,country,summary_en,summary_so FROM mentions ORDER BY day DESC, id DESC LIMIT 20000")]
summ = [dict(r) for r in con.execute("SELECT period,period_key,summary_en,summary_so,mention_count FROM summaries")]
con.close()
out = pathlib.Path("docs"); out.mkdir(exist_ok=True)
(out / "data.json").write_text(json.dumps({"mentions": rows, "summaries": summ}, ensure_ascii=False), encoding="utf-8")
(out / "index.html").write_text(TEMPLATE, encoding="utf-8")
print("exported", len(rows), "mentions")
