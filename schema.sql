CREATE TABLE IF NOT EXISTS mentions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    url_hash      TEXT UNIQUE NOT NULL,
    source_type   TEXT NOT NULL,      -- news | social | video | conference
    source_name   TEXT,               -- e.g. Reuters, reddit, youtube
    title         TEXT,
    snippet       TEXT,
    url           TEXT,
    author        TEXT,
    country       TEXT,
    language      TEXT,
    published_at  TEXT,               -- ISO date YYYY-MM-DD
    day           TEXT,               -- YYYY-MM-DD
    month         TEXT,               -- YYYY-MM
    year          TEXT,               -- YYYY
    topics        TEXT,               -- comma separated tags
    sentiment     TEXT,               -- positive | neutral | negative
    title_so      TEXT,               -- Somali translation
    snippet_so    TEXT,
    summary_en    TEXT,               -- per-article summary (English)
    summary_so    TEXT,               -- per-article summary (Somali)
    summary_status TEXT,              -- full_text | snippet | failed
    collected_at  TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_day   ON mentions(day);
CREATE INDEX IF NOT EXISTS idx_month ON mentions(month);
CREATE INDEX IF NOT EXISTS idx_year  ON mentions(year);

CREATE TABLE IF NOT EXISTS summaries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    period     TEXT NOT NULL,         -- day | month | year
    period_key TEXT NOT NULL,         -- 2026-10-05 | 2026-10 | 2026
    summary_en TEXT,
    summary_so TEXT,
    mention_count INTEGER,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(period, period_key)
);
