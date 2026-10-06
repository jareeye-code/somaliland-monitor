"""Per-article summaries: download the article page, extract text, summarize (English), translate (Somali).
Priority: articles about Israel / recognition / geography first. Only the summary is stored, not the full text."""
import re, requests
import config, db
from translate import to_somali

H = {"User-Agent": "Mozilla/5.0 (compatible; SomalilandMonitor/1.0)"}

def resolve_url(url):
    """Google News links are redirects; decode to the real article URL."""
    if url and "news.google.com" in url:
        try:
            from googlenewsdecoder import gnewsdecoder
            r = gnewsdecoder(url, interval=1)
            if r.get("status"): return r["decoded_url"]
        except Exception as e:
            print("  [warn] decode:", e)
    return url

def fetch_text(url):
    try:
        import trafilatura
        r = requests.get(url, headers=H, timeout=20)
        r.raise_for_status()
        return (trafilatura.extract(r.text, include_comments=False) or "").strip()
    except Exception as e:
        print(f"  [warn] fetch {str(url)[:70]}: {e}")
        return ""

def _extractive(text, n=3):
    sents = re.split(r"(?<=[.!?])\s+", text)
    sents = [s for s in sents if len(s) > 40]
    return " ".join(sents[:n])[:700]

def summarize(title, text):
    if config.ANTHROPIC_API_KEY:
        try:
            import anthropic
            c = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            r = c.messages.create(model=config.ANTHROPIC_MODEL, max_tokens=400,
                system=("Summarize this article about Somaliland in 3-4 factual sentences in English. "
                        "Say who said or did what, and note any position on recognition (e.g. Israel, USA, Ethiopia) "
                        "or on Somaliland's geography/strategic location. Do not add facts that are not in the text. "
                        "If the text is not really about Somaliland, say so in one sentence."),
                messages=[{"role": "user", "content": f"Title: {title}\n\n{text[:config.ARTICLE_MAX_CHARS]}"}])
            return r.content[0].text.strip()
        except Exception as e:
            print("  [warn] claude summary:", e)
    return _extractive(text)

def run_pending(con):
    rows = con.execute("""SELECT id,title,snippet,url,source_type FROM mentions
        WHERE summary_en IS NULL
        ORDER BY (topics LIKE '%israel%' OR topics LIKE '%recognition%' OR topics LIKE '%geography%') DESC, day DESC, id DESC
        LIMIT ?""", (config.ARTICLE_SUMMARIES_PER_RUN,)).fetchall()
    done = 0
    for r in rows:
        text, status = "", "snippet"
        if r["source_type"] == "news" and r["url"]:
            text = fetch_text(resolve_url(r["url"]))
            if len(text) > 400: status = "full_text"
        if status != "full_text":
            text = f"{r['title'] or ''}. {r['snippet'] or ''}"
        en = summarize(r["title"], text) if status == "full_text" else (r["snippet"] or r["title"] or "")[:500]
        if not en: status = "failed"
        so = to_somali(en) if en else None
        con.execute("UPDATE mentions SET summary_en=?, summary_so=?, summary_status=? WHERE id=?",
                    (en or "", so, status, r["id"]))
        con.commit(); done += 1
    print(f"[articles] summarized {done} (limit {config.ARTICLE_SUMMARIES_PER_RUN}/run)")
