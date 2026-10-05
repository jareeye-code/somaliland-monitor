import sqlite3, hashlib, pathlib
from config import DB_PATH

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init():
    con = connect()
    con.executescript(pathlib.Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))
    con.commit(); con.close()

def url_hash(url, title):
    return hashlib.sha256((url or title or "").strip().lower().encode()).hexdigest()

def insert_mention(con, m: dict) -> bool:
    """Returns True if newly inserted."""
    date = (m.get("published_at") or "")[:10]
    row = {
        "url_hash": url_hash(m.get("url"), m.get("title")),
        "source_type": m.get("source_type", "news"),
        "source_name": m.get("source_name"),
        "title": m.get("title"), "snippet": m.get("snippet"),
        "url": m.get("url"), "author": m.get("author"),
        "country": m.get("country"), "language": m.get("language"),
        "published_at": date, "day": date,
        "month": date[:7], "year": date[:4],
        "topics": m.get("topics"), "sentiment": m.get("sentiment"),
    }
    cols = ",".join(row); qs = ",".join("?" * len(row))
    try:
        con.execute(f"INSERT INTO mentions ({cols}) VALUES ({qs})", list(row.values()))
        return True
    except sqlite3.IntegrityError:
        return False
