"""Connectors for social networks. Each connector posts ONE text (+ optional link) and returns the remote post id.
Credentials come from environment variables (GitHub Secrets). A connector without credentials is 'not connected'."""
import re, datetime
import os
import requests

TIMEOUT = 30


class PostError(Exception):
    pass


def fb_url(path):
    """Graph API address. Without FB_GRAPH_VERSION Meta uses the oldest version it still supports, so the call never breaks
    when a version is retired. To pin a version, add a repository secret FB_GRAPH_VERSION such as v26.0."""
    v = os.environ.get("FB_GRAPH_VERSION", "").strip().strip("/")
    return "https://graph.facebook.com/" + (v + "/" if v else "") + path


def _ok(r, what):
    if r.status_code >= 300:
        raise PostError(f"{what}: HTTP {r.status_code} {r.text[:300]}")
    return r


class Facebook:
    """Facebook PAGE (not a personal profile). Needs FB_PAGE_ID and a Page access token with pages_manage_posts."""
    name = "facebook"; label = "Facebook Page"; limit = 60000
    separate_link = True          # the link is sent as an attachment (shows a preview card), not inside the text
    def link_cost(self, link): return 0
    def configured(self): return bool(os.environ.get("FB_PAGE_ID") and os.environ.get("FB_PAGE_TOKEN"))
    def post(self, text, link=None):
        data = {"message": text, "access_token": os.environ["FB_PAGE_TOKEN"]}
        if link: data["link"] = link
        r = _ok(requests.post(fb_url(os.environ["FB_PAGE_ID"] + "/feed"), data=data, timeout=TIMEOUT), "Facebook")
        return r.json().get("id", "")


class Telegram:
    """Telegram channel or group. Needs TELEGRAM_BOT_TOKEN (from @BotFather) and TELEGRAM_CHAT_ID (@channelname or number); the bot must be admin."""
    name = "telegram"; label = "Telegram channel"; limit = 4000
    separate_link = False
    def link_cost(self, link): return len(link or "") + 1
    def configured(self): return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))
    def post(self, text, link=None):
        body = text + (("\n" + link) if link and link not in text else "")
        r = _ok(requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage",
                              json={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": body, "disable_web_page_preview": False}, timeout=TIMEOUT), "Telegram")
        return str(r.json().get("result", {}).get("message_id", ""))


class X:
    """X (Twitter). Needs X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET (user context, write permission)."""
    name = "x"; label = "X (Twitter)"; limit = 280
    separate_link = False
    def link_cost(self, link): return 24 if link else 0       # X counts every link as 23 characters
    def configured(self): return all(os.environ.get(k) for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"))
    def post(self, text, link=None):
        from requests_oauthlib import OAuth1
        auth = OAuth1(os.environ["X_API_KEY"], os.environ["X_API_SECRET"], os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"])
        body = text + (("\n" + link) if link and link not in text else "")
        r = _ok(requests.post("https://api.x.com/2/tweets", auth=auth, json={"text": body}, timeout=TIMEOUT), "X")
        return r.json().get("data", {}).get("id", "")


class LinkedIn:
    """LinkedIn profile or company page. Needs LINKEDIN_TOKEN (w_member_social / w_organization_social) and LINKEDIN_AUTHOR_URN."""
    name = "linkedin"; label = "LinkedIn"; limit = 3000
    separate_link = True
    def link_cost(self, link): return 0
    def configured(self): return bool(os.environ.get("LINKEDIN_TOKEN") and os.environ.get("LINKEDIN_AUTHOR_URN"))
    def post(self, text, link=None):
        content = {"shareCommentary": {"text": text}, "shareMediaCategory": "NONE"}
        if link:
            content["shareMediaCategory"] = "ARTICLE"
            content["media"] = [{"status": "READY", "originalUrl": link}]
        payload = {"author": os.environ["LINKEDIN_AUTHOR_URN"], "lifecycleState": "PUBLISHED",
                   "specificContent": {"com.linkedin.ugc.ShareContent": content},
                   "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}}
        r = _ok(requests.post("https://api.linkedin.com/v2/ugcPosts", json=payload, timeout=TIMEOUT,
                              headers={"Authorization": "Bearer " + os.environ["LINKEDIN_TOKEN"], "X-Restli-Protocol-Version": "2.0.0"}), "LinkedIn")
        return r.headers.get("X-RestLi-Id", "")


class Mastodon:
    """Mastodon account. Needs MASTODON_BASE_URL (e.g. https://mastodon.social) and MASTODON_TOKEN (write:statuses)."""
    name = "mastodon"; label = "Mastodon"; limit = 500
    separate_link = False
    def link_cost(self, link): return 24 if link else 0
    def configured(self): return bool(os.environ.get("MASTODON_BASE_URL") and os.environ.get("MASTODON_TOKEN"))
    def post(self, text, link=None):
        body = text + (("\n" + link) if link and link not in text else "")
        r = _ok(requests.post(os.environ["MASTODON_BASE_URL"].rstrip("/") + "/api/v1/statuses", data={"status": body}, timeout=TIMEOUT,
                              headers={"Authorization": "Bearer " + os.environ["MASTODON_TOKEN"]}), "Mastodon")
        return r.json().get("url", "")


class Bluesky:
    """Bluesky. Needs BLUESKY_HANDLE and BLUESKY_APP_PASSWORD (create an App Password in Bluesky settings)."""
    name = "bluesky"; label = "Bluesky"; limit = 300
    separate_link = False
    def link_cost(self, link): return len(link or "") + 1
    def configured(self): return bool(os.environ.get("BLUESKY_HANDLE") and os.environ.get("BLUESKY_APP_PASSWORD"))
    def post(self, text, link=None):
        body = text + (("\n" + link) if link and link not in text else "")
        s = _ok(requests.post("https://bsky.social/xrpc/com.atproto.server.createSession", timeout=TIMEOUT,
                              json={"identifier": os.environ["BLUESKY_HANDLE"], "password": os.environ["BLUESKY_APP_PASSWORD"]}), "Bluesky login").json()
        record = {"$type": "app.bsky.feed.post", "text": body,
                  "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")}
        facets = []
        for m in re.finditer(r"https?://[^\s]+", body):                      # make links clickable (offsets are in UTF-8 BYTES)
            start = len(body[:m.start()].encode("utf-8")); end = start + len(m.group(0).encode("utf-8"))
            facets.append({"index": {"byteStart": start, "byteEnd": end}, "features": [{"$type": "app.bsky.richtext.facet#link", "uri": m.group(0)}]})
        if facets: record["facets"] = facets
        r = _ok(requests.post("https://bsky.social/xrpc/com.atproto.repo.createRecord", timeout=TIMEOUT,
                              headers={"Authorization": "Bearer " + s["accessJwt"]},
                              json={"repo": s["did"], "collection": "app.bsky.feed.post", "record": record}), "Bluesky")
        return r.json().get("uri", "")


ALL = {c.name: c for c in (Facebook(), Telegram(), X(), LinkedIn(), Mastodon(), Bluesky())}


def select(platforms: str, publish: bool):
    """Returns (connectors, notes). 'all' = every connected platform (when publishing) or every platform (preview)."""
    notes, chosen = [], []
    wanted = [p.strip().lower() for p in (platforms or "").split(",") if p.strip()]
    if not wanted or wanted == ["all"]:
        wanted = [n for n, c in ALL.items() if (c.configured() or not publish)]
    for w in wanted:
        if w not in ALL:
            raise SystemExit(f"Unknown platform '{w}'. Choose from: {', '.join(ALL)} or 'all'.")
        c = ALL[w]
        if publish and not c.configured():
            notes.append(f"{c.label}: NOT CONNECTED (missing secrets) - skipped")
            continue
        if not publish and not c.configured():
            notes.append(f"{c.label}: not connected yet (preview only)")
        chosen.append(c)
    return chosen, notes


def check(c):
    """Tests the connection WITHOUT posting anything. Returns a short human-readable result."""
    try:
        if not c.configured():
            return "NOT CONNECTED - secrets missing"
        if c.name == "facebook":
            r = _ok(requests.get(fb_url(os.environ["FB_PAGE_ID"]), timeout=TIMEOUT,
                                 params={"fields": "name", "access_token": os.environ["FB_PAGE_TOKEN"]}), "Facebook")
            return "OK - page: " + r.json().get("name", "?")
        if c.name == "telegram":
            r = _ok(requests.get(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/getChat", timeout=TIMEOUT,
                                 params={"chat_id": os.environ["TELEGRAM_CHAT_ID"]}), "Telegram")
            return "OK - chat: " + str(r.json().get("result", {}).get("title") or r.json().get("result", {}).get("username"))
        if c.name == "mastodon":
            r = _ok(requests.get(os.environ["MASTODON_BASE_URL"].rstrip("/") + "/api/v1/accounts/verify_credentials", timeout=TIMEOUT,
                                 headers={"Authorization": "Bearer " + os.environ["MASTODON_TOKEN"]}), "Mastodon")
            return "OK - account: " + r.json().get("acct", "?")
        if c.name == "bluesky":
            r = _ok(requests.post("https://bsky.social/xrpc/com.atproto.server.createSession", timeout=TIMEOUT,
                                  json={"identifier": os.environ["BLUESKY_HANDLE"], "password": os.environ["BLUESKY_APP_PASSWORD"]}), "Bluesky")
            return "OK - handle: " + r.json().get("handle", "?")
        if c.name == "linkedin":
            r = _ok(requests.get("https://api.linkedin.com/v2/userinfo", timeout=TIMEOUT,
                                 headers={"Authorization": "Bearer " + os.environ["LINKEDIN_TOKEN"]}), "LinkedIn")
            return "OK - token accepted"
        if c.name == "x":
            from requests_oauthlib import OAuth1
            auth = OAuth1(os.environ["X_API_KEY"], os.environ["X_API_SECRET"], os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"])
            r = _ok(requests.get("https://api.x.com/2/users/me", auth=auth, timeout=TIMEOUT), "X")
            return "OK - account: @" + r.json().get("data", {}).get("username", "?")
        return "secrets present"
    except Exception as e:
        return "FAILED - " + str(e)[:300]
