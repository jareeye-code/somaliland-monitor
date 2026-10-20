"""Writes the posts: one result, a Top-N digest, or a period report. Somali, English or both.
Facts only come from the database (title, summary, source, counts). Optional AI polishing never adds facts."""
import os, re
from collections import Counter

TOPIC_SO = {"recognition": "Aqoonsi", "israel": "Israa'iil", "geography": "Juquraafi", "usa": "Mareykanka", "ethiopia": "Itoobiya",
            "uae": "Imaaraadka", "china_taiwan": "Shiinaha/Taiwan", "conference": "Shir", "somalia": "Soomaaliya",
            "security": "Amni", "economy": "Dhaqaale"}
HASHTAG = {"recognition": "#Recognition", "israel": "#Israel", "usa": "#USA", "ethiopia": "#Ethiopia", "uae": "#UAE",
           "geography": "#HornOfAfrica", "economy": "#Economy", "security": "#Security", "conference": "#Diplomacy"}
SENT_SO = {"positive": "wanaagsan", "neutral": "dhexdhexaad", "negative": "xun"}


def site_url():
    if os.environ.get("SITE_URL"):
        return os.environ["SITE_URL"].strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" in repo:
        owner, name = repo.split("/", 1)
        return f"https://{owner}.github.io/{name}/"
    return ""


def clip(s, n):
    s = re.sub(r"\s+", " ", (s or "")).strip()
    if len(s) <= n:
        return s
    cut = s[: max(1, n - 1)]
    if " " in cut[n // 2:]:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,;:-–—") + "…"


def pick(m, lang, field):
    if lang == "so":
        return (m.get(field + "_so") or m.get(field) or "") if field != "summary" else (m.get("summary_so") or m.get("summary_en") or "")
    return (m.get(field) or "") if field != "summary" else (m.get("summary_en") or "")


def tname(t, lang):
    return TOPIC_SO.get(t, t) if lang == "so" else t


def stats_of(rows):
    sent, topics = Counter(), Counter()
    for m in rows:
        sent[m.get("sentiment") or "neutral"] += 1
        for t in (m.get("topics") or "").split(","):
            if t: topics[t] += 1
    return {"total": len(rows), "sent": sent, "topics": topics}


def hashtags(items, limit=4):
    tags = ["#Somaliland"]
    c = Counter(t for m in items for t in (m.get("topics") or "").split(",") if t in HASHTAG)
    for t, _ in c.most_common():
        if HASHTAG[t] not in tags: tags.append(HASHTAG[t])
        if len(tags) >= limit: break
    return " ".join(tags)


def _stats_lines(stats, lang):
    s = stats["sent"]
    if lang == "so":
        l1 = f"{stats['total']} war la helay · wanaagsan {s['positive']} · dhexdhexaad {s['neutral']} · xun {s['negative']}"
        top = ", ".join(tname(t, lang) for t, _ in stats["topics"].most_common(4))
        return [l1] + ([f"Mawduucyada ugu badan: {top}"] if top else [])
    l1 = f"{stats['total']} mentions · positive {s['positive']} · neutral {s['neutral']} · negative {s['negative']}"
    top = ", ".join(tname(t, lang) for t, _ in stats["topics"].most_common(4))
    return [l1] + ([f"Top topics: {top}"] if top else [])


def _part(mode, items, label, stats, lang, n, summary_chars, footer_label, tag_line, title_len=110, level=0):
    items = items[:n]
    if mode == "item":
        m = items[0]
        lines = [f"📰 {clip(pick(m, lang, 'title'), 200)}"]
        if summary_chars:
            sm = clip(pick(m, lang, "summary"), summary_chars)
            if sm: lines.append(sm)
        src = m.get("source_name") or ""
        lines.append(("Ilaha: " if lang == "so" else "Source: ") + src + (f" · {m.get('day')}" if m.get("day") else ""))
    else:
        head = (f"📰 Somaliland warbaahinta — {label}" if lang == "so" else f"📰 Somaliland in the media — {label}")
        lines = [head]
        if stats and level < 2:
            sl = _stats_lines(stats, lang)
            lines += sl[:1] if level == 1 else sl
        lines.append("")
        for i, m in enumerate(items, 1):
            lines.append(f"{i}) {clip(pick(m, lang, 'title'), title_len)} — {m.get('source_name') or ''}")
    if footer_label:
        lines.append("")
        if mode == "item":
            lines.append("Maqaalka oo dhan:" if lang == "so" else "Read more:")
        else:
            lines.append("Dhammaan natiijooyinka:" if lang == "so" else "Full results:")
    lines.append(tag_line)
    return "\n".join(l for l in lines).strip()


def fit_text(connector, mode, items, label, stats, langs, link):
    """Builds the longest version that fits the platform limit. Returns (text, notes)."""
    notes = []
    reserve = connector.link_cost(link)
    footer_label = bool(link) and not connector.separate_link
    tag_line = hashtags(items)
    budget = connector.limit - reserve
    sep = "\n\n— — —\n\n"

    def build(langs_, n, sc, tl, lv):
        return sep.join(_part(mode, items, label, stats, lg, n, sc, footer_label, tag_line, tl, lv) for lg in langs_)

    tries = []
    max_n = 1 if mode == "item" else len(items)
    for lg in ([langs] if len(langs) > 1 else []) + [langs[:1]]:
        for n in range(max_n, 0, -1):
            if mode == "item":
                for sc in (400, 220, 0):
                    tries.append((lg, n, sc, 110, 0))
            else:
                for lv in (0, 1, 2):
                    for tl in (110, 80, 60):
                        tries.append((lg, n, 0, tl, lv))
    for lg, n, sc, tl, lv in tries:
        text = build(lg, n, sc, tl, lv)
        if len(text) <= budget:
            if len(langs) > 1 and len(lg) == 1:
                notes.append(f"{connector.label}: text too long for both languages - only {lg[0].upper()} was used")
            if mode != "item" and n < len(items):
                notes.append(f"{connector.label}: only the first {n} of {len(items)} results fit")
            return text, notes
    text = build(langs[:1], 1, 0, 60, 2)[: max(1, budget - 1)].rstrip() + "…"
    notes.append(f"{connector.label}: text was shortened to fit {connector.limit} characters")
    return text, notes


def polish(text, langs, limit_chars, ai_enabled=True):
    """Optional: Claude rewrites the post to read naturally. Falls back to the original text on any doubt."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not (ai_enabled and key):
        return text
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        names = {"so": "Somali (Af-Soomaali)", "en": "English"}
        r = client.messages.create(model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"), max_tokens=900,
            system=("You edit social-media posts for a neutral news-monitoring account about Somaliland. Rewrite the post so it reads naturally in "
                    + " and ".join(names[l] for l in langs) + ". Rules: keep every fact, number, source name and hashtag; do NOT add facts, opinions or "
                    "claims; keep a neutral tone and attribute statements to their source; keep emojis and line structure; never add links; "
                    f"stay under {limit_chars} characters. Output ONLY the finished post."),
            messages=[{"role": "user", "content": text}])
        new = r.content[0].text.strip()
        nums_old, nums_new = set(re.findall(r"\d+", text)), set(re.findall(r"\d+", new))
        if new and len(new) <= limit_chars and "http" not in new and nums_old <= nums_new and "#Somaliland" in new:
            return new
    except Exception as e:
        print("  [warn] AI polish skipped:", e)
    return text
