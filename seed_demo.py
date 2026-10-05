"""Optional: load a few FAKE sample rows so you can see the dashboard before the first real collection.
Delete them later with:  python seed_demo.py clear"""
import sys, db, analyze
db.init(); con = db.connect()
if len(sys.argv) > 1 and sys.argv[1] == "clear":
    con.execute("DELETE FROM mentions WHERE source_name LIKE 'DEMO%'"); con.execute("DELETE FROM summaries"); con.commit(); sys.exit()
demo = [("2026-10-03","DEMO news","Sample: Somaliland recognition debate continues in the region","news"),
        ("2026-10-02","DEMO social","Sample post: Berbera port and Red Sea location discussed","social"),
        ("2026-09-20","DEMO video","Sample: conference speech on Somaliland and Israel","video")]
for d, s, t, ty in demo:
    db.insert_mention(con, dict(source_type=ty, source_name=s, title=t, snippet=t, url="https://example.com/"+t[:20].replace(" ","-"),
        published_at=d, topics=analyze.tag(t), sentiment=analyze.sentiment(t)))
con.commit()
