---
name: data-box
description: Get web data through a data-box server — turn a public URL into clean markdown, text, HTML or its links, and follow long-running jobs. Use when asked to "scrape this page", "get the content of", "pull the links from", "turn this URL into markdown", "what does this page say" (when you only need the data, not clicks), or "is data-box up". Also use to run your own data-box locally or on a server. For clicking, logging in or screenshots use browser-box instead.
allowed-tools: Bash, Read
---
> **In the Funding Affiliate Manager:** data-box is attached as the `data-box` MCP when `DATABOX_TOKEN` is set. Use `scrape` for an affiliate's site or a public profile when you only need the text; each call carries `max_cost_usd`.

# data-box — web data, one door

data-box is a data server: it gets web content for you and records what each call cost. **You are
the brain**; it fetches. Browsers (clicking, logins, screenshots) live in **browser-box**, a
separate server — use that when you need to *do* something on a page, not just read it.

## The tools

| Tool | Use it for | Cost |
|---|---|---|
| `scrape` | One public URL → `markdown` (default), `text`, `html` or `links` | free rung first; paid rungs only if configured, never past `max_cost_usd` (default $0.05) |
| `job` | Follow anything slow: `get`, `list`, `cancel`, `results` (page through items), `export` (csv/json/jsonl) | free |
| `status` | What is up, which sources are configured, recent spend | free |

**How `scrape` climbs.** It tries a free direct fetch first and stops at the first rung that
returns the real page. Then paid unblockers (Firecrawl, Bright Data, Decodo) and finally a real
browser (browser-box) — but only the rungs the server has keys for. `rungs_tried` shows every
rung, its cost and why it was left. If only the free rung is available and a page is blocked,
you get `blocked` saying what stopped it: that is an answer, not an error. Next move: open the
page with browser-box `read`.

**Money rules.** Every call takes `max_cost_usd`; a paid step that would exceed it never starts.
Pass `request_id` when you might retry — the same id returns the first job instead of paying
twice. Slow calls return a `job_id` after `wait_seconds`; poll it with `job(action="get")`.

**Refused on purpose:** loopback, private, link-local and `file:` targets, on every redirect.
Don't retry a refusal unchanged.

## Which sources a server has

Call `status`. Each source is listed with `configured: true/false` and what it is for:

| Source | Unlocks | Server env var(s) |
|---|---|---|
| direct fetch | scrape rung 0 | none (always on, free) |
| Firecrawl | scrape rung 1; later websearch, crawl, extract | `FIRECRAWL_API_KEY` |
| Bright Data | scrape rung 2 (Unlocker); datasets | `BRIGHTDATA_API_KEY` |
| Decodo | scrape rung 3 | `DECODO_SCRAPER_API_TOKEN` |
| Apify | Store actors (`sources`, `run`) | `APIFY_TOKEN` |
| browser-box | scrape's last rung: a real browser | `DATABOX_BROWSERBOX_URL`, `DATABOX_BROWSERBOX_TOKEN` |

Paid sources bill **the account whose key is on the server** — on your own data-box, that's you.
Some sources are still being wired into the rungs; `status` is the truth for your server.

## Running your own

```bash
git clone https://github.com/jbellsolutions/box-kit && cd box-kit
make up        # starts data-box (and browser-box) in Docker with fresh tokens
make env       # prints DATABOX_URL / DATABOX_TOKEN for your agents
```

Or without Docker, since data-box runs no browser:

```bash
cd box-kit/server/data-box
python3 -m venv .venv && .venv/bin/pip install -e .
export DATABOX_TOKEN="$(openssl rand -hex 32)"   # keep it; clients send it as a Bearer token
.venv/bin/data-box serve                          # http://127.0.0.1:8092/mcp
```

Then point the plugin at it: `DATABOX_URL=http://127.0.0.1:8092/mcp` and the same
`DATABOX_TOKEN`. Add paid keys to `server/data-box/.env` (or the server's environment) to switch sources on.
For a server others reach over the internet, put it behind HTTPS — see the kit's
`docs/SELF-HOST.md`.

Same tools over HTTP: `POST <server>/api/v1/<tool>` with the JSON arguments, `GET
/api/v1/status`, spec at `/openapi.json`. And a CLI: `data-box scrape --url https://example.com`.
