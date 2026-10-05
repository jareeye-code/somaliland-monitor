"""The agent: collect -> filter -> tag -> store -> translate -> summarize.
Usage:
  python agent.py once            # one collection cycle
  python agent.py loop            # repeat every COLLECT_EVERY_MINUTES
  python agent.py backfill 365d   # GDELT history (e.g. 30d, 6m, 1y -> use 'NNNd' / 'NNw' / 'NNm')
"""
import sys, time
import config, db, analyze, collectors, summarize
from translate import to_somali

def run_cycle(gdelt_span="7d"):
    db.init(); con = db.connect(); new = 0
    for q in config.QUERIES:
        for name, fn in collectors.ALL:
            kw = {"timespan": gdelt_span} if name == "gdelt" else {}
            try:
                for m in fn(q, **kw):
                    text = f"{m.get('title','')} {m.get('snippet','')}"
                    if not analyze.is_relevant(text): continue
                    m["topics"] = analyze.tag(text); m["sentiment"] = analyze.sentiment(text)
                    if db.insert_mention(con, m): new += 1
            except Exception as e:
                print(f"  [warn] {name}/{q}: {e}")
        con.commit()
        time.sleep(1)  # be polite to APIs
    print(f"[collect] {new} new mentions")
    translate_pending(con)
    con.close()
    summarize.build()
    print("[done]")

def translate_pending(con, limit=300):
    rows = con.execute("SELECT id,title,snippet FROM mentions WHERE title_so IS NULL ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    for r in rows:
        con.execute("UPDATE mentions SET title_so=?, snippet_so=? WHERE id=?",
                    (to_somali(r["title"]), to_somali((r["snippet"] or "")[:500]), r["id"]))
    con.commit(); print(f"[translate] {len(rows)} items")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "once"
    if cmd == "once": run_cycle()
    elif cmd == "backfill": run_cycle(sys.argv[2] if len(sys.argv) > 2 else "90d")
    elif cmd == "loop":
        while True:
            run_cycle(); time.sleep(config.COLLECT_EVERY_MINUTES * 60)
    else: print(__doc__)
