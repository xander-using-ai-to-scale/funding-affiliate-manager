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
