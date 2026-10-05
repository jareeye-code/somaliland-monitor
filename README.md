# Somaliland International Media Monitor

An agent that collects what the world says about Somaliland (news, social media, videos/conferences,
Israel recognition, geography/Berbera/Red Sea), stores it in an **SQL (SQLite) database**, builds
**daily / monthly / yearly summaries**, translates them to **Somali**, and shows everything on a
**Python dashboard**.

## Setup (Python 3.14)
    python -m venv .venv
    .venv\Scripts\activate          # Windows   (Linux/Mac: source .venv/bin/activate)
    pip install -r requirements.txt

## Optional keys (set as environment variables)
    ANTHROPIC_API_KEY   better Somali translation + smarter summaries (otherwise free Google translator)
    YOUTUBE_API_KEY     YouTube interviews/conference speeches (free quota)
    X_BEARER_TOKEN      X/Twitter posts (X's API is paid)

## Run
    python agent.py backfill 90d    # first run: pull the last 90 days of history (GDELT)
    python agent.py once            # one collection cycle
    python agent.py loop            # run automatically every hour
    python app.py                   # dashboard -> http://127.0.0.1:8000  (Somali/English switch, CSV export)
    python seed_demo.py             # (optional) fake demo rows to preview the dashboard; "clear" removes them

## Files
    schema.sql    database tables (mentions, summaries)      config.py   queries, topics, keys, schedule
    collectors.py Google News, GDELT, Reddit, YouTube, X     analyze.py  topic tags + sentiment
    translate.py  English -> Somali                          summarize.py day/month/year summaries
    agent.py      collect -> store -> translate -> summarize app.py      web dashboard

## Query the database directly (SQL)
    sqlite3 somaliland.db "SELECT month, COUNT(*) FROM mentions GROUP BY month;"
    sqlite3 somaliland.db "SELECT day,title FROM mentions WHERE topics LIKE '%israel%' ORDER BY day DESC;"

## Notes
- Edit QUERIES and TOPICS in config.py to track more people, countries, or keywords.
- Tagging/sentiment are keyword-based (fast, free); they are approximate, not a verdict.
- Respect each platform's terms of service. Social coverage is partial: Facebook, Instagram, TikTok and
  Telegram have no open search API, so they are not included.
