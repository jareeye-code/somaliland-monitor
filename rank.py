"""Chooses the best results to publish: important topics first, trusted sources, summaries available, newest first,
no near-duplicate headlines and at most 2 per source."""
import re

TOPIC_WEIGHT = {"recognition": 4, "israel": 4, "usa": 3, "geography": 3, "ethiopia": 2, "uae": 2, "conference": 2,
                "china_taiwan": 2, "economy": 1, "security": 1, "somalia": 1}
BIG_SOURCES = ("reuters", "bbc", "aljazeera", "apnews", "ap news", "associated press", "cnn", "nytimes", "washingtonpost", "ft.com",
               "theguardian", "voanews", "dw.com", "france24", "axios", "politico", "bloomberg", "timesofisrael", "jpost", "haaretz",
               "foreignpolicy", "economist", "africanews", "theeastafrican", "hiiraan", "garoweonline", "horseedmedia")
TYPE_WEIGHT = {"news": 2, "video": 1, "social": 0}


STOP = {"the", "and", "for", "with", "from", "that", "this", "have", "has", "was", "are", "will", "say", "says", "said", "after", "over",
        "into", "about", "somaliland", "somalia", "news", "piece", "report", "reports", "new", "amid", "its", "his", "her", "their"}


def _norm(t):
    """Headline -> set of word stems (first 5 letters), without filler words, so 'announces' = 'announced'."""
    words = re.findall(r"[a-z0-9\u00c0-\u024f]{3,}", (t or "").lower())
    return {w[:5] for w in words if w not in STOP}


def _similar(a, b):
    if not a or not b:
        return False
    small = min(len(a), len(b))
    if small < 3:
        return a == b
    return len(a & b) / small >= 0.6


def score(m):
    s = sum(TOPIC_WEIGHT.get(t, 0) for t in (m.get("topics") or "").split(",") if t)
    src = ((m.get("source_name") or "") + " " + (m.get("url") or "")).lower()
    if any(b in src for b in BIG_SOURCES): s += 3
    s += TYPE_WEIGHT.get(m.get("source_type"), 0)
    if m.get("summary_en"): s += 1
    if m.get("sentiment") in ("positive", "negative"): s += 0.5
    return s


def top_items(rows, n, max_per_source=2):
    """rows: list of dict. Returns the n best, most important first."""
    ordered = sorted(rows, key=lambda m: (score(m), m.get("day") or "", m.get("id") or 0), reverse=True)
    chosen, per_source, seen = [], {}, []
    for m in ordered:
        words = _norm(m.get("title"))
        if any(_similar(words, w) for w in seen):
            continue                                              # near-duplicate headline
        src = (m.get("source_name") or "").lower()
        if per_source.get(src, 0) >= max_per_source:
            continue
        chosen.append(m); seen.append(words); per_source[src] = per_source.get(src, 0) + 1
        if len(chosen) >= n: break
    return chosen
