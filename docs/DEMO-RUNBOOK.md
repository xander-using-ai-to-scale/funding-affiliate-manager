# Demo runbook: Funding Affiliate Manager

There are two ways to run the demo. **Mode A** works today: the agent runs on the droplet against the mock CRM. **Mode B** is the full show on the GoHighLevel demo sub-account, and it needs the human-only steps at the bottom first.

Leave the client-facing pages open in tabs:

- Workflow map + simulation: https://claude.ai/artifact/Ligihb8EmD6vb9oRvZhMoU
- Proposal (draft): https://claude.ai/artifact/LzTsAQzn3tnWpTeRJdkxEg

Both are private until you share them from the page's Share menu.

## Pre-flight (either mode)

```bash
ssh fam@104.131.176.19
fam status            # ghl_connected true, demo_mode true, external_writes_enabled true
hermes mcp list       # fam-core, fam-approvals (+ ghl/orgo/browsers once their keys exist)
```

- `demo_mode: true` means only contacts tagged `fam:test-contact` get real messages. Every other send is written as a `SIMULATED` note on the contact.
- If `stop_reason` is set, run `fam resume --actor Justin`.

## Mode A: mock CRM on the droplet (works now)

The mock CRM holds 150 synthetic affiliates plus the test contact "Demo Tester". Talk to the agent with `hermes` over SSH. Once the Slack app exists, you'll talk to it in #funding-affiliates instead.

| # | You say or do | What the audience sees |
|---|---|---|
| 1 | `hermes` → "Status check. What's my program look like today?" | GHL connected, demo mode on, cohort counts, and the 30/60/90-day silent numbers. |
| 2 | "Run the morning sweep and build today's list." | Lifecycle retags (quiet, dormant, dead, reactivated). Today's queue, with "check back" follow-ups first. |
| 3 | "Draft today's personal check-ins and give me the approval card." | Personalized drafts that reference each person's niche, source, last deal, and last words. One card with an action id and digest. |
| 4 | Approve: accept the `fam_action_approve` prompt in Hermes, or run `fam approve <action_id> <digest> --approver Justin` in a second terminal. | The agent can't approve its own sends. Only a human can. |
| 5 | "Send it." | Execute result: `mock` (test contact) vs `simulated` (everyone else). Last-touch dates update and due tasks close. |
| 6 | Second terminal: `fam sim inbound --text "Got a restaurant owner who needs about 80k, can I send you the file?"` → then in Hermes: "Check replies." | Classified `has_deal`. Manager alert, same-day CALL task, `deal:incoming`. A reply draft is queued for approval. |
| 7 | `fam sim inbound --text "Slammed with tax season, check back with me in two weeks"` → "Check replies." | Note, GHL task, `next_touch_date` 14 days out, and a `cadence_note`. `fam brief <contact_id>` shows it. |
| 8 | `fam sim inbound --text "Could you help me build a funnel page?"` → "Check replies." | `want:funnel` tag and a Growth Services card, plus a scoping task. |
| 9 | "Draft this cycle's newsletter and invite the quiet affiliates to Thursday's training." | Newsletter copy set into custom values. WF-6/WF-7 enrollments prepared, and one approval card. |
| 10 | "Turn on a standing approval for the bi-weekly touch: 100 a day for 30 days." → approve the prompt → `fam cadence run-standing` | Bulk cadence runs under a capped approval that expires. Show `fam status` → `standing_approvals`. |
| 11 | `fam stop "demo"` → try to send → `fam resume --actor Justin` | Kill switch: everything outbound is frozen until a human resumes it. |
| 12 | `ls ~/fam-vault/Daily ~/fam-vault/Affiliates \| head` | The Obsidian vault holds today's note, per-affiliate timelines, and campaign notes. |
| 13 | Workflow map tab → Simulation | 30 days, 253 affiliates: 67 replies, 17 deals, and 13 reactivated. On day 30, 16 are producing vs 1 in a no-outreach baseline. |

Step 3 always produces a fresh card. Approval requests expire after 12 hours (`approval_ttl_hours`), so don't reuse an old one from `fam actions`.

The weekday crons are live against the mock CRM: reply triage runs hourly at :15 from 9 to 18 ET, and the sweep runs at 8am. Each run spends OpenRouter credits and can leave an approval card. To pause them before the demo, run `hermes cron list` and then `hermes cron pause <id>`.

### Reset between runs (Mode A)

```bash
rm -f ~/.fam/state/mock-ghl.json ~/.fam/state/fam.sqlite3
fam sim seed --into-agent --count 150
```

## Mode B: live GoHighLevel demo sub-account

Complete the human-only steps first. Then:

1. Set these in `~/.fam/agent.env`: `FAM_GHL_MODE=live`, `GHL_API_KEY=pit-…`, `GHL_LOCATION_ID=…`. Keep `FAM_DEMO_MODE=1`.
2. Run `./deploy/droplet/setup.sh`, then `fam ghl bootstrap` (it prints a plan), then `fam ghl bootstrap --apply`.
3. Build the two pipelines and WF-1 to WF-9 in the GHL UI. Use the exact names in `config/pipelines.json` and `config/workflows.json`, or have the agent build them on its Orgo desktop. Then re-run `fam ghl bootstrap --apply` so the ids get mapped.
4. `fam sim seed --live --count 150 --test-email <yours> --test-phone <yours> --test-name "Justin"`
5. Run the same script as Mode A, with two differences:
   - Step 5: messages actually arrive on your phone and inbox. Everyone else gets a `SIMULATED` note in GHL.
   - Steps 6–8: reply from your phone instead of using `fam sim inbound`.
6. The Orgo moment: "Open GHL on your computer and show me the Affiliate Lifecycle pipeline." The agent takes a screenshot from its own desktop.

## Human-only steps that unlock Mode B

1. **Orgo**
   - Free a computer slot (buy one, or delete an unused computer).
   - Create a workspace-scoped API key in the Orgo dashboard.
   - Then the computer can be created, and `ORGO_API_KEY` / `ORGO_COMPUTER_ID` set.
   - Log into GHL, LinkedIn, and Skool once, over VNC.
2. **GHL:** create the sub-account "7FF Funding Affiliate Demo (synthetic data)" in the UI. The agency API returns 403 for this plan. Then create a Private Integration token in it.
3. **Slack:** create the app from `slack/manifest.json`. Put `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_HOME_CHANNEL`, and `SLACK_ALLOWED_USERS` in `agent.env`, then re-run `setup.sh`.
4. **SMS:** register A2P 10DLC on the demo number. Until then, demo over email.
