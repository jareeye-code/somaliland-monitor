import os

DB_PATH = os.environ.get("SL_DB", "somaliland.db")

# Search queries used by every collector
QUERIES = [
    "Somaliland",
    "Somaliland recognition",
    "Israel Somaliland recognition",
    "Somaliland Berbera",
    "Somaliland Red Sea Gulf of Aden",
    "Somaliland Hargeisa",
    "Somaliland independence",
    "Somaliland Ethiopia sea access",
    "Somaliland United States recognition",
    "Somaliland conference",
    "Somaliland president Irro",
]

# Topic tagging rules (keyword -> topic)
TOPICS = {
    "recognition":  ["recognition", "recognize", "recognise", "recognized", "sovereign", "independence", "statehood"],
    "israel":       ["israel", "israeli", "netanyahu", "jerusalem", "tel aviv"],
    "geography":    ["berbera", "red sea", "gulf of aden", "bab el-mandeb", "bab al-mandab", "strategic", "port", "coast", "horn of africa", "geopolit", "location"],
    "usa":          ["united states", "u.s.", "washington", "congress", "senate", "trump", "pentagon"],
    "ethiopia":     ["ethiopia", "addis ababa", "abiy"],
    "uae":          ["uae", "emirates", "dp world", "abu dhabi"],
    "china_taiwan": ["taiwan", "china", "beijing"],
    "conference":   ["conference", "summit", "forum", "hearing", "panel", "speech", "address", "keynote", "interview"],
    "somalia":      ["mogadishu", "federal government", "somalia talks", "talks with somalia"],
    "security":     ["al-shabaab", "attack", "security", "military", "clashes", "las anod", "laascaanood"],
    "economy":      ["trade", "investment", "economy", "livestock", "remittance", "mining", "oil"],
}

POSITIVE = ["welcome", "support", "agreement", "recognize", "recognise", "partnership", "success", "praise", "deal", "historic", "boost"]
NEGATIVE = ["reject", "condemn", "violat", "clash", "attack", "oppose", "threat", "tension", "denounce", "crisis", "killed"]

# Optional API keys (leave blank to skip that collector)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
X_BEARER_TOKEN  = os.environ.get("X_BEARER_TOKEN", "")      # paid X API
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")  # summaries + Somali translation
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

COLLECT_EVERY_MINUTES = 60
USER_AGENT = "SomalilandMonitor/1.0 (research tool)"

# Per-article summaries
ARTICLE_SUMMARIES_PER_RUN = int(os.environ.get("ARTICLE_SUMMARIES_PER_RUN", "40"))  # cost/time limit per run
ARTICLE_MAX_CHARS = 6000      # text sent to the summarizer
