from config import TOPICS, POSITIVE, NEGATIVE

def tag(text: str) -> str:
    t = (text or "").lower()
    found = [name for name, words in TOPICS.items() if any(w in t for w in words)]
    return ",".join(found)

def sentiment(text: str) -> str:
    t = (text or "").lower()
    p = sum(w in t for w in POSITIVE); n = sum(w in t for w in NEGATIVE)
    return "positive" if p > n else "negative" if n > p else "neutral"

def is_relevant(text: str) -> bool:
    return "somaliland" in (text or "").lower() or "somali land" in (text or "").lower()
