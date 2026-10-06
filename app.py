"""Web dashboard (pure Python standard library, works on Python 3.14).
Run:  python app.py   ->  http://127.0.0.1:8000
"""
import html, json, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import db

T = {
 "en": dict(title="Somaliland International Media Monitor", year="Year", month="Month", day="Day",
            search="Search", all="All", topic="Topic", stype="Type", mentions="mentions", summary="Summary",
            latest="Latest mentions", by="Mentions by", lang="Somali", source="Source", date="Date",
            sentiment="Sentiment", top="Top topics", export="Download CSV"),
 "so": dict(title="Kormeeraha Warbaahinta Caalamiga ee Somaliland", year="Sannad", month="Bil", day="Maalin",
            search="Raadi", all="Dhammaan", topic="Mawduuc", stype="Nooca", mentions="la sheegay", summary="Soo koobid",
            latest="Wararkii ugu dambeeyay", by="Tirada", lang="English", source="Ilaha", date="Taariikh",
            sentiment="Dareen", top="Mawduucyada ugu caansan", export="Soo deji CSV"),
}
e = html.escape

def page(q):
    g = lambda k, d="": q.get(k, [d])[0]
    lang = g("lang", "so"); t = T[lang]
    period = g("period", "month"); col = {"day": "day", "month": "month", "year": "year"}.get(period, "month")
    key = g("key"); topic = g("topic"); stype = g("stype"); text = g("q")
    con = db.connect()

    where, args = ["1=1"], []
    if key: where.append(f"{col}=?"); args.append(key)
    if topic: where.append("(',' || topics || ',') LIKE ?"); args.append(f"%,{topic},%")
    if stype: where.append("source_type=?"); args.append(stype)
    if text: where.append("(title LIKE ? OR snippet LIKE ? OR title_so LIKE ?)"); args += [f"%{text}%"] * 3
    W = " AND ".join(where)

    counts = con.execute(f"SELECT {col} k, COUNT(*) c FROM mentions WHERE {col}!='' GROUP BY {col} ORDER BY k DESC LIMIT 36").fetchall()
    mx = max([r["c"] for r in counts] or [1])
    bars = "".join(
        f'<a class="bar" href="?{urllib.parse.urlencode(dict(lang=lang, period=period, key=r["k"]))}">'
        f'<span class="k">{e(r["k"])}</span><span class="b" style="width:{int(r["c"]/mx*100)}%"></span>'
        f'<span class="c">{r["c"]}</span></a>' for r in counts)

    summ = ""
    if key:
        s = con.execute("SELECT * FROM summaries WHERE period=? AND period_key=?", (period, key)).fetchone()
        if s:
            body = s["summary_so"] if lang == "so" and s["summary_so"] else s["summary_en"]
            summ = f'<div class="card"><h3>{t["summary"]} — {e(key)} ({s["mention_count"]} {t["mentions"]})</h3><pre>{e(body or "")}</pre></div>'

    tc = {}
    for r in con.execute(f"SELECT topics FROM mentions WHERE {W}", args):
        for x in (r["topics"] or "").split(","):
            if x: tc[x] = tc.get(x, 0) + 1
    chips = "".join(f'<a class="chip" href="?{urllib.parse.urlencode(dict(lang=lang, period=period, key=key, topic=k))}">{e(k)} · {v}</a>'
                    for k, v in sorted(tc.items(), key=lambda x: -x[1]))

    rows = con.execute(f"SELECT * FROM mentions WHERE {W} ORDER BY day DESC, id DESC LIMIT 200", args).fetchall()
    trs = ""
    for r in rows:
        title = r["title_so"] if lang == "so" and r["title_so"] else r["title"]
        sbody = r["summary_so"] if lang == "so" and r["summary_so"] else r["summary_en"]
        sm = f'<details><summary>{t["summary"]}</summary><div>{e(sbody)}</div></details>' if sbody else ""
        trs += (f'<tr><td>{e(r["day"] or "")}</td><td><a href="{e(r["url"] or "#")}" target="_blank" rel="noopener">{e(title or "")}</a>{sm}</td>'
                f'<td>{e(r["source_name"] or "")}</td><td>{e(r["topics"] or "")}</td><td class="s-{e(r["sentiment"] or "")}">{e(r["sentiment"] or "")}</td></tr>')
    total = con.execute("SELECT COUNT(*) FROM mentions").fetchone()[0]
    con.close()

    other = "en" if lang == "so" else "so"
    sw = urllib.parse.urlencode({**{k: v[0] for k, v in q.items()}, "lang": other})
    tabs = "".join(f'<a class="tab{" on" if period == p else ""}" href="?lang={lang}&period={p}">{t[p]}</a>' for p in ("year", "month", "day"))
    return f"""<!doctype html><html lang="{lang}"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t['title']}</title><style>
body{{font:15px system-ui,sans-serif;margin:0;background:#f6f7f9;color:#1b1f24}}
header{{background:#0b5d3b;color:#fff;padding:16px 24px;display:flex;justify-content:space-between;align-items:center}}
header a{{color:#fff}} main{{max-width:1150px;margin:auto;padding:20px}}
.card{{background:#fff;border-radius:10px;padding:16px;margin-bottom:16px;box-shadow:0 1px 3px #0001}}
.tab{{padding:6px 14px;border-radius:20px;background:#e3e6ea;color:#222;text-decoration:none;margin-right:6px}} .tab.on{{background:#0b5d3b;color:#fff}}
.bar{{display:flex;align-items:center;gap:8px;text-decoration:none;color:inherit;margin:3px 0}} .k{{width:90px;font-size:13px}}
.b{{height:12px;background:#2e9e6b;border-radius:3px;display:inline-block}} .c{{font-size:12px;color:#666}}
.chip{{display:inline-block;background:#e8f3ee;border-radius:14px;padding:3px 10px;margin:2px;text-decoration:none;color:#0b5d3b;font-size:13px}}
table{{width:100%;border-collapse:collapse}} td{{padding:7px;border-bottom:1px solid #eee;vertical-align:top;font-size:14px}}
.s-positive{{color:#1a7f37}} .s-negative{{color:#c0392b}} pre{{white-space:pre-wrap;font:14px/1.5 system-ui}}
input{{padding:6px;border:1px solid #ccc;border-radius:6px}}
</style><header><b>{t['title']}</b><span>{total} {t['mentions']} · <a href="?{sw}">{t['lang']}</a> · <a href="/export.csv">{t['export']}</a></span></header>
<main>
<div class="card">{tabs}
<form style="display:inline;margin-left:12px"><input type="hidden" name="lang" value="{lang}"><input type="hidden" name="period" value="{period}">
<input name="q" value="{e(text)}" placeholder="{t['search']}…"><select name="stype"><option value="">{t['stype']}: {t['all']}</option>
{''.join(f'<option value="{x}"{" selected" if x==stype else ""}>{x}</option>' for x in ("news","social","video","conference"))}</select>
<button>{t['search']}</button></form></div>
<div class="card"><h3>{t['by']} {t[period]}</h3>{bars}</div>
{summ}
<div class="card"><h3>{t['top']}</h3>{chips}</div>
<div class="card"><h3>{t['latest']}</h3><table><tr><th>{t['date']}</th><th></th><th>{t['source']}</th><th>{t['topic']}</th><th>{t['sentiment']}</th></tr>{trs}</table></div>
</main></html>"""

def csv_export():
    import csv, io
    con = db.connect(); out = io.StringIO(); w = csv.writer(out)
    cur = con.execute("SELECT day,month,year,source_type,source_name,title,title_so,url,topics,sentiment,country FROM mentions ORDER BY day DESC")
    w.writerow([d[0] for d in cur.description]); w.writerows(cur.fetchall()); con.close()
    return out.getvalue().encode("utf-8-sig")

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/export.csv":
            b = csv_export(); self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=somaliland_mentions.csv")
        else:
            b = page(urllib.parse.parse_qs(u.query)).encode("utf-8"); self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass

if __name__ == "__main__":
    db.init()
    import os
    port = int(os.environ.get("PORT", "8000")); host = os.environ.get("HOST", "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")
    print(f"Dashboard: http://{host}:{port}")
    ThreadingHTTPServer((host, port), H).serve_forever()
