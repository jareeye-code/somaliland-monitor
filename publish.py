"""Social-media publishing agent for the Somaliland Monitor.

Examples
  python publish.py --check                                   # which platforms are connected? (posts nothing)
  python publish.py --mode digest --period last_7_days --top 5 --platforms facebook,telegram          # PREVIEW only
  python publish.py --mode digest --period last_7_days --top 5 --platforms facebook,telegram --publish # really post
  python publish.py --mode items --ids 12,15 --platforms all --lang so --publish                      # exactly these results
  python publish.py --mode report --period this_month --platforms facebook --lang both --publish      # statistics + top results
Nothing is posted unless --publish is given."""
import argparse, os, sys, time, datetime
import db, rank, compose, social

COLS = "id,title,title_so,snippet,summary_en,summary_so,url,source_name,source_type,topics,sentiment,day"


def ensure_table(con):
    con.execute("""CREATE TABLE IF NOT EXISTS published (
        id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, platform TEXT, mention_id INTEGER, post_text TEXT,
        remote_id TEXT, status TEXT, error TEXT, posted_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    con.commit()


def period_range(period, f, t, today=None):
    today = today or datetime.date.today()
    d = datetime.timedelta
    if period == "today": return today, today
    if period == "yesterday": return today - d(days=1), today - d(days=1)
    if period == "last_7_days": return today - d(days=6), today
    if period == "last_30_days": return today - d(days=29), today
    if period == "this_month": return today.replace(day=1), today
    if period == "this_year": return today.replace(month=1, day=1), today
    if period == "custom":
        if not (f and t): raise SystemExit("Custom period needs --from and --to (YYYY-MM-DD).")
        a, b = datetime.date.fromisoformat(f), datetime.date.fromisoformat(t)
        return (a, b) if a <= b else (b, a)
    raise SystemExit("Unknown period: " + period)


def rows_to_dicts(cur):
    return [dict(r) for r in cur.fetchall()]


def load_range(con, a, b):
    return rows_to_dicts(con.execute(f"SELECT {COLS} FROM mentions WHERE day BETWEEN ? AND ? ORDER BY day DESC, id DESC", (a.isoformat(), b.isoformat())))


def load_ids(con, ids):
    q = ",".join("?" * len(ids))
    rows = rows_to_dicts(con.execute(f"SELECT {COLS} FROM mentions WHERE id IN ({q})", ids))
    order = {i: k for k, i in enumerate(ids)}
    return sorted(rows, key=lambda r: order[r["id"]])


def already_published(con, platform_names):
    q = ",".join("?" * len(platform_names))
    return {r[0] for r in con.execute(f"SELECT DISTINCT mention_id FROM published WHERE status='ok' AND platform IN ({q})", list(platform_names))}


def log_post(con, kind, platform, mention_ids, text, remote_id, status, error=""):
    for i, mid in enumerate(mention_ids or [None]):
        con.execute("INSERT INTO published (kind, platform, mention_id, post_text, remote_id, status, error) VALUES (?,?,?,?,?,?,?)",
                    (kind, platform, mid, text if i == 0 else "", remote_id, status, error))
    con.commit()


def label_for(a, b):
    return a.isoformat() if a == b else f"{a.isoformat()} → {b.isoformat()}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["digest", "report", "items"], default="digest",
                    help="digest = Top-N list in ONE post | report = statistics + top results | items = one post per chosen result")
    ap.add_argument("--period", default="last_7_days", choices=["today", "yesterday", "last_7_days", "last_30_days", "this_month", "this_year", "custom"])
    ap.add_argument("--from", dest="date_from", default="")
    ap.add_argument("--to", dest="date_to", default="")
    ap.add_argument("--top", type=int, default=5, help="how many top results (digest/report)")
    ap.add_argument("--ids", default="", help="comma separated result IDs chosen on the website (overrides --top)")
    ap.add_argument("--platforms", default="all", help="facebook,telegram,x,linkedin,mastodon,bluesky or all")
    ap.add_argument("--lang", choices=["so", "en", "both"], default="both")
    ap.add_argument("--no-ai", action="store_true", help="do not use Claude to polish the text")
    ap.add_argument("--publish", action="store_true", help="REALLY post. Without this flag you only get a preview.")
    ap.add_argument("--repost", action="store_true", help="allow results that were already published on that platform")
    ap.add_argument("--check", action="store_true", help="test the connections, post nothing")
    ap.add_argument("--max-items-posts", type=int, default=10, help="safety limit for --mode items")
    a = ap.parse_args(argv)

    if a.check:
        print("Connection check (nothing is posted):")
        for c in social.ALL.values():
            print(f"  {c.label:18} {social.check(c)}")
        return 0

    db.init(); con = db.connect(); ensure_table(con)
    connectors, notes = social.select(a.platforms, a.publish)
    for n in notes: print("NOTE:", n)
    if not connectors:
        print("No platform selected/connected. Run with --check to see what is connected."); return 1
    names = [c.name for c in connectors]
    langs = ["so", "en"] if a.lang == "both" else [a.lang]

    # ---------- choose the results ----------
    ids = [int(x) for x in a.ids.replace(" ", "").split(",") if x.isdigit()]
    start, end = period_range(a.period, a.date_from, a.date_to)
    range_rows = load_range(con, start, end)
    if ids:
        items = load_ids(con, ids)
        missing = set(ids) - {m["id"] for m in items}
        if missing: print("NOTE: these IDs were not found:", sorted(missing))
        if items:
            days = sorted(m["day"] for m in items if m.get("day"))
            start, end = datetime.date.fromisoformat(days[0]), datetime.date.fromisoformat(days[-1])
    else:
        if a.mode == "items":
            print("Mode 'items' needs --ids (the numbers you copy from the website)."); return 1
        pool = range_rows
        if not a.repost:
            done = already_published(con, names)
            pool = [m for m in pool if m["id"] not in done]
        items = rank.top_items(pool, a.top if a.mode == "digest" else min(a.top, 5))
    if a.mode != "items" and not a.repost:
        done = already_published(con, names)
        dup = [m["id"] for m in items if m["id"] in done]
        if ids and dup: print("NOTE: already published on at least one selected platform (use --repost to publish again):", dup)
    if not items:
        print("Nothing new to publish for this selection."); return 0
    label = label_for(start, end)
    stats = compose.stats_of(range_rows if not ids else items)
    link_site = compose.site_url()

    # ---------- build the posts ----------
    posts = []          # (connector, kind, [mention ids], text, link)
    for c in connectors:
        if a.mode == "items":
            for m in items[: a.max_items_posts]:
                text, nn = compose.fit_text(c, "item", [m], label, None, langs, m.get("url"))
                notes += nn
                text = compose.polish(text, langs, c.limit - c.link_cost(m.get("url")), not a.no_ai)
                posts.append((c, "item", [m["id"]], text, m.get("url")))
        else:
            kind = "report" if a.mode == "report" else "digest"
            text, nn = compose.fit_text(c, "digest", items, label, stats if a.mode == "report" else (stats if len(range_rows) else None), langs, link_site or None)
            notes += nn
            text = compose.polish(text, langs, c.limit - c.link_cost(link_site or None), not a.no_ai)
            posts.append((c, kind, [m["id"] for m in items], text, link_site or None))

    # ---------- preview ----------
    out = [f"# {'PUBLISHED' if a.publish else 'PREVIEW (nothing posted)'} - {label}", ""]
    for c, kind, mids, text, link in posts:
        out += [f"## {c.label}  ({len(text) + c.link_cost(link)}/{c.limit} characters)", "", "```", text, "```",
                f"Link: {link or '-'}", f"Results: {mids}", ""]
    for n in sorted(set(notes)): out.append(f"- {n}")
    preview = "\n".join(out)
    print(preview)

    # ---------- publish ----------
    failures = 0
    if a.publish:
        print("\nPublishing...")
        for c, kind, mids, text, link in posts:
            try:
                remote = c.post(text, link)
                log_post(con, kind, c.name, mids, text, remote, "ok")
                print(f"  OK   {c.label}: {remote}")
                time.sleep(3)
            except Exception as e:
                failures += 1
                log_post(con, kind, c.name, mids, text, "", "error", str(e)[:500])
                print(f"  FAIL {c.label}: {e}")
        preview += "\n\n## Result\n" + ("All posts were published." if not failures else f"{failures} post(s) failed - see the log.")
    open("publish_preview.md", "w", encoding="utf-8").write(preview)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f: f.write(preview + "\n")
    con.close()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
