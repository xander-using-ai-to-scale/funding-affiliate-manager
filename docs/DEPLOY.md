# Deploy

## Infrastructure
| Piece | Where |
|---|---|
| Brain | DigitalOcean droplet `funding-affiliate-manager` (s-2vcpu-4gb, nyc3), user `fam` |
| Hands | Orgo workspace "Funding Affiliate Manager", one always-on Linux desktop (2 vCPU / 8 GB) |
| CRM | GHL sub-account "7FF Funding Affiliate Demo (synthetic data)", profile `mfm-demo` |
| Channel | Slack app "Funding Affiliate Manager" (socket mode, `slack/manifest.json`) in #funding-affiliates |
| Memory | `~/fam-vault` on the droplet, pushed to a private repo every 15 min |

## Steps (as `fam` on the droplet)
1. Base packages (root): `git python3-venv nodejs(22) ripgrep ffmpeg build-essential libatomic1`, plus a 2 GB swapfile and ufw allowing SSH only.
2. Hermes, pinned and checksum-verified. Download `scripts/install.sh` at commit `29112bef099274229cadff79cdff7bf7b99c4b77`, verify SHA256 `85ef536d455e51ab67aa74d79272efd49fe717597dbaadfd3cca179a905f4706`, then run it with `--skip-setup --branch v2026.8.31 --commit 29112bef… --force-commit`.
3. `git clone` this repo to `~/funding-affiliate-manager`.
4. `cp agent.example.env ~/.fam/agent.env && chmod 600 ~/.fam/agent.env`, then fill it in.
5. `./deploy/droplet/setup.sh`. This installs the GHL CLI (demo profile only), renders config, the vault, cron routines, and the gateway, then verifies.

## Going live on the demo location
1. Create the sub-account in the GHL UI. The agency API returned 403 for location creation on this plan.
2. In the sub-account: Settings → Private Integrations. Create a token with contacts, conversations, opportunities, workflows, locations/custom fields/values/tags, users, and calendars scopes.
3. Put `GHL_API_KEY`, `GHL_LOCATION_ID`, and `FAM_GHL_MODE=live` in `~/.fam/agent.env`, then run `./deploy/droplet/setup.sh`.
4. Run `fam ghl bootstrap` to see the plan, then `fam ghl bootstrap --apply`. This creates fields, tags, and custom values, maps pipelines and workflows by name, and writes `config/ghl-map.json`.
5. Build the two pipelines and WF-1…WF-9 in the GHL UI (or have the agent do it on its Orgo desktop) using the exact names in `config/pipelines.json` and `config/workflows.json`. Then run `fam ghl bootstrap --apply` again.
6. Seed: `fam sim seed --live --count 150 --test-email you@… --test-phone +1… --test-name "Justin Bell"`. Only the test contact ever gets a real message.

## Updating the droplet
1. Bring the new code over (`git pull` in `~/funding-affiliate-manager`, or the usual rsync, which leaves `~/.fam`, `~/fam-vault` and the venv alone).
2. `./deploy/droplet/setup.sh` again. It is idempotent and it:
   - re-renders `~/.hermes/config.yaml`, including the tool lockdown below;
   - replaces the old weekday-only "FAM reply triage" job with the 20-minute one and adds "FAM resume paused sends";
   - installs the two cron scripts in `~/.hermes/scripts/`;
   - starts the Hermes gateway, which is also what runs the cron scheduler.
3. Check: `hermes cron status` says the gateway is running, `hermes cron list` shows the jobs below with upcoming run times, and `fam status` shows `paused_batches` and `sends_to_settle` (both 0 on a fresh box).

## What runs on a schedule
| Job | When | Model? |
|---|---|---|
| FAM daily tasks + sweep | 08:00 weekdays | yes |
| FAM reply triage every 20 min | every 20 min, every day | only when an untriaged text is waiting (a monitor script, `fam inbox --ids`, gates it; pending texts re-wake it hourly) |
| FAM resume paused sends | every 20 min, every day | no (`fam outbox resume`: finishes approved batches as each recipient's send window opens; silent when there's nothing to send) |
| FAM call ingest | 09:45–19:45 weekdays | yes |
| FAM bi-weekly newsletter, monthly offer, weekly scorecard | as named | yes |

All times are America/New_York (`timezone` in the Hermes config). Cron jobs only fire while the gateway runs. Without Slack or Telegram tokens their output stays local (`hermes cron runs`).

## Safety settings to know
- **The agent has no shell, file or code-execution tools.** `agent.disabled_toolsets` in `hermes/config.template.yaml` removes them from every platform bundle, cron job and delegated child. It reads `knowledge/` and the vault through `fam_read`. Don't add those toolsets back: any of them would let it approve its own sends.
- **Human-only decisions live on `fam-approvals`:** approving a batch, standing approvals, lifting a stop, and settling a send whose outcome is unknown. Hermes asks the person before each one. The `fam` CLI has no approve or resume command.
- **Texts go out 9:00–20:00 in each recipient's own time zone** (`config/cadence.json`), checked per text. `FAM_IGNORE_SMS_WINDOW=1` in `~/.fam/agent.env` only works against the mock CRM, for demos at odd hours.
- **Email needs `mailing_address`** in `config/kickoff.json` (the company's postal address, confirmed with 7FF) before any live email goes out.
- **If a send's outcome is unknown** (a timeout), the agent says so. Check the partner's conversation in GoHighLevel, then settle it with `fam_outbox_settle` (sent / not_sent). `fam outbox` shows every message's state.
