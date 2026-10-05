"""Builds day / month / year summaries (English + Somali)."""
from collections import Counter
import config, db
from translate import to_somali

def _extractive(rows, label):
    n = len(rows)
    topics = Counter(t for r in rows for t in (r["topics"] or "").split(",") if t)
    sents = Counter(r["sentiment"] for r in rows)
    types = Counter(r["source_type"] for r in rows)
    srcs = Counter(r["source_name"] for r in rows).most_common(5)
    top = ", ".join(f"{k} ({v})" for k, v in topics.most_common(5)) or "none"
    heads = "\n".join(f"- {r['title']} [{r['source_name']}]" for r in rows[:8])
    return (f"{label}: {n} mentions of Somaliland. Types: {dict(types)}. "
            f"Sentiment: {dict(sents)}. Main topics: {top}. "
            f"Top sources: {', '.join(f'{s} ({c})' for s, c in srcs)}.\nKey headlines:\n{heads}")

def _claude_summary(rows, label):
    import anthropic
    c = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    items = "\n".join(f"- [{r['source_name']}] {r['title']} | topics={r['topics']} | {r['sentiment']}" for r in rows[:60])
    r = c.messages.create(model=config.ANTHROPIC_MODEL, max_tokens=700,
        system=("You are an analyst tracking Somaliland's international profile. Summarize the items in 5-8 sentences: "
                "who said what, notable statements on recognition (esp. Israel/US/Ethiopia), geography/strategic location "
                "(Berbera, Red Sea), conferences/speeches, and overall tone. Be factual; do not invent."),
        messages=[{"role": "user", "content": f"Period {label}:\n{items}"}])
    return r.content[0].text.strip()

def build(period="all"):
    con = db.connect()
    for per, col in (("day", "day"), ("month", "month"), ("year", "year")):
        keys = [r[0] for r in con.execute(f"SELECT DISTINCT {col} FROM mentions WHERE {col}!='' ORDER BY 1")]
        for k in keys:
            rows = con.execute(f"SELECT * FROM mentions WHERE {col}=? ORDER BY id DESC", (k,)).fetchall()
            old = con.execute("SELECT mention_count, summary_so FROM summaries WHERE period=? AND period_key=?", (per, k)).fetchone()
            if old and old["mention_count"] == len(rows) and old["summary_so"]:
                continue  # unchanged
            try:
                en = _claude_summary(rows, k) if config.ANTHROPIC_API_KEY and per != "day" else _extractive(rows, k)
            except Exception as e:
                print("  [warn] summary:", e); en = _extractive(rows, k)
            so = to_somali(en)
            con.execute("""INSERT INTO summaries(period,period_key,summary_en,summary_so,mention_count)
                           VALUES (?,?,?,?,?)
                           ON CONFLICT(period,period_key) DO UPDATE SET summary_en=excluded.summary_en,
                           summary_so=excluded.summary_so, mention_count=excluded.mention_count,
                           updated_at=CURRENT_TIMESTAMP""", (per, k, en, so, len(rows)))
            con.commit()
    con.close()
