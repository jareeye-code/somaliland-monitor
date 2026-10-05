"""Collectors: each yields dicts with title/snippet/url/published_at/source_*.
Free, no-key: Google News RSS, GDELT, Reddit.  Optional: YouTube, X."""
import re, html, time, urllib.parse, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import requests
import config

H = {"User-Agent": config.USER_AGENT}

def _get(url, **kw):
    try:
        r = requests.get(url, headers=H, timeout=25, **kw)
        r.raise_for_status(); return r
    except Exception as e:
        print(f"  [warn] {url[:80]}... -> {e}"); return None

def _clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()

def _iso(dt): return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")

# ---------- Google News RSS (media + articles) ----------
def google_news(query, lang="en", country="US"):
    url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(query) +
           f"&hl={lang}&gl={country}&ceid={country}:{lang}")
    r = _get(url)
    if not r: return
    root = ET.fromstring(r.content)
    for it in root.iter("item"):
        try: d = _iso(parsedate_to_datetime(it.findtext("pubDate")))
        except Exception: d = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        src = it.find("source")
        yield dict(source_type="news", source_name=src.text if src is not None else "Google News",
                   title=_clean(it.findtext("title")), snippet=_clean(it.findtext("description")),
                   url=it.findtext("link"), published_at=d, language=lang)

# ---------- GDELT (global media archive, 100+ languages, history) ----------
def gdelt(query, timespan="7d", maxrecords=100):
    url = ("https://api.gdeltproject.org/api/v2/doc/doc?query=" + urllib.parse.quote(f'"{query}"') +
           f"&mode=artlist&format=json&sort=datedesc&maxrecords={maxrecords}&timespan={timespan}")
    r = _get(url)
    if not r: return
    try: arts = r.json().get("articles", [])
    except Exception: return
    for a in arts:
        sd = a.get("seendate", "")  # 20261005T120000Z
        d = f"{sd[:4]}-{sd[4:6]}-{sd[6:8]}" if len(sd) >= 8 else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        yield dict(source_type="news", source_name=a.get("domain"), title=a.get("title"),
                   snippet="", url=a.get("url"), published_at=d,
                   country=a.get("sourcecountry"), language=a.get("language"))

# ---------- Reddit (public search JSON; social) ----------
def reddit(query, limit=50):
    url = f"https://www.reddit.com/search.json?q={urllib.parse.quote(query)}&sort=new&limit={limit}"
    r = _get(url)
    if not r: return
    for c in r.json().get("data", {}).get("children", []):
        p = c["data"]
        d = _iso(datetime.fromtimestamp(p["created_utc"], timezone.utc))
        yield dict(source_type="social", source_name=f"reddit r/{p.get('subreddit')}",
                   title=p.get("title"), snippet=_clean(p.get("selftext", ""))[:600],
                   url="https://reddit.com" + p.get("permalink", ""), author=p.get("author"),
                   published_at=d, language="en")

# ---------- YouTube (optional key; interviews, conferences, speeches) ----------
def youtube(query, max_results=25):
    if not config.YOUTUBE_API_KEY: return
    r = _get("https://www.googleapis.com/youtube/v3/search", params=dict(
        part="snippet", q=query, type="video", order="date", maxResults=max_results,
        key=config.YOUTUBE_API_KEY))
    if not r: return
    for it in r.json().get("items", []):
        s = it["snippet"]
        yield dict(source_type="video", source_name="youtube:" + s.get("channelTitle", ""),
                   title=html.unescape(s.get("title", "")), snippet=s.get("description", ""),
                   url="https://www.youtube.com/watch?v=" + it["id"]["videoId"],
                   author=s.get("channelTitle"), published_at=s.get("publishedAt", "")[:10])

# ---------- X / Twitter (optional, requires paid API bearer token) ----------
def x_posts(query, max_results=50):
    if not config.X_BEARER_TOKEN: return
    try:
        r = requests.get("https://api.x.com/2/tweets/search/recent", timeout=25,
                         headers={**H, "Authorization": f"Bearer {config.X_BEARER_TOKEN}"},
                         params={"query": f"{query} -is:retweet", "max_results": min(max_results, 100),
                                 "tweet.fields": "created_at,author_id,lang"})
        r.raise_for_status()
    except Exception as e:
        print("  [warn] X:", e); return
    for t in r.json().get("data", []):
        yield dict(source_type="social", source_name="x.com", title=t["text"][:140], snippet=t["text"],
                   url=f"https://x.com/i/web/status/{t['id']}", author=t.get("author_id"),
                   published_at=t.get("created_at", "")[:10], language=t.get("lang"))

ALL = [("google_news", google_news), ("gdelt", gdelt), ("reddit", reddit),
       ("youtube", youtube), ("x", x_posts)]
