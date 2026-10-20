# Social-media publishing agent - setup and use

The agent never posts anything by itself until YOU switch it on. Every run is a PREVIEW unless you untick "Preview only".

## 1. Quickest way (no setup at all): share buttons
On the website, tick the results you want. A green panel appears with the ready-made post text (you can edit it) and buttons
**Facebook / X / Telegram / WhatsApp / LinkedIn**. Each button opens that network's own share window with the text -
you press Post yourself. Nothing is stored anywhere.

## 2. The publishing agent (posts for you, from GitHub's servers)

### Connect the platforms (do only the ones you want)
Add each value in GitHub: **Settings > Secrets and variables > Actions > New repository secret**.
Then run **Actions > Publish to social media > Run workflow > mode = check_connections** - it tests every connection WITHOUT posting.
(Platform websites change their menus from time to time; the names below are what to look for.)

| Platform | Secrets to add | How to get them |
|---|---|---|
| **Facebook Page** (not a personal profile) | `FB_PAGE_ID`, `FB_PAGE_TOKEN` | developers.facebook.com > My Apps > Create app (type Business). Open Tools > Graph API Explorer, choose your app, press "Get Page Access Token", allow `pages_show_list`, `pages_manage_posts`, `pages_read_engagement` and select your Page. To get a token that does not expire: exchange the user token for a long-lived one (`/oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=TOKEN`), then call `/me/accounts` with it - the answer lists your Page `id` (= FB_PAGE_ID) and its `access_token` (= FB_PAGE_TOKEN). You must be an admin of the app and the Page. |
| **Telegram** channel | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | In Telegram talk to @BotFather: /newbot, copy the token. Create a channel, add the bot as ADMINISTRATOR (allowed to post). Chat id = `@yourchannelname` for a public channel. |
| **X (Twitter)** | `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_SECRET` | developer.x.com > create a project/app > set App permissions to **Read and write** > Keys and tokens: generate API key/secret and Access token/secret for your account. X decides which plan allows posting - check their current plans. |
| **LinkedIn** | `LINKEDIN_TOKEN`, `LINKEDIN_AUTHOR_URN` | linkedin.com/developers > create app > add product "Share on LinkedIn" > create an OAuth token with `w_member_social` (company pages: `w_organization_social`). Author = `urn:li:person:XXXX` (or `urn:li:organization:XXXX`). LinkedIn tokens expire (about 60 days) and must be renewed. |
| **Mastodon** | `MASTODON_BASE_URL`, `MASTODON_TOKEN` | Your server > Preferences > Development > New application, scope `write:statuses`, copy the access token. Base URL like `https://mastodon.social`. |
| **Bluesky** | `BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD` | Bluesky > Settings > Privacy and security > App passwords > Add. Handle like `name.bsky.social`. |

Not supported (no safe public posting API): personal Facebook profiles and groups, WhatsApp channels, TikTok, Instagram (needs pictures).
Optional: `ANTHROPIC_API_KEY` (already used by the collector) lets Claude polish the wording. It may never add facts, numbers or links; if the
polished text breaks a rule, the plain text is used.

### Publish manually (what you asked for)
1. On the website tick the results you want -> press **Copy IDs** (or use the top-N option instead of IDs).
2. **Actions > Publish to social media > Run workflow** and choose:
   - `mode`: **items** = one post per chosen result | **digest** = ONE post listing the Top N | **report** = statistics + top results
   - `ids`: paste the IDs (leave empty to let the agent pick the Top 3/5/10 of the chosen dates)
   - `period` / custom dates, `top`, `platforms` (e.g. `facebook,telegram` or `all`), `lang` (Somali / English / both)
   - `dry_run` ticked = PREVIEW. Open the finished run > **Summary**: you see the exact text for every platform.
3. Happy? Run again with **dry_run unticked** - now it really posts. Results already posted on a platform are skipped next time (log in the database).

### Switch on automatic publishing (next step, only when you are ready)
Settings > Secrets and variables > Actions > **Variables** tab:
`AUTO_PUBLISH = true`, `AUTO_TOP = 3` (or 5), `AUTO_PLATFORMS = facebook,telegram`, `AUTO_LANG = both`.
Every day at 06:30 UTC the agent publishes ONE digest with the Top results of yesterday that have not been published yet.
Turn it off again: set `AUTO_PUBLISH` to `false` (or delete the variable).

## How the Top results are chosen
Score = topic importance (recognition, Israel, USA, geography/Red Sea, Ethiopia, UAE, conferences...) + trusted/major source + news over social posts
+ has a summary. Near-duplicate headlines are removed and at most 2 results per source are used.
Edit the weights at the top of `rank.py` to change what counts as important.

## What a post contains
Only: headline, a short summary (if available), source name, date, hashtags and a link (to the article, or to your website for digests).
Posts that are too long for a platform are shortened automatically (X 280 characters, Bluesky 300, Mastodon 500 ...).
Test it yourself: `python publish.py --mode digest --top 3 --platforms all --no-ai` shows previews for every platform.
