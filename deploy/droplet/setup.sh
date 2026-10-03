#!/usr/bin/env bash
# Install / update the Funding Affiliate Manager on its DigitalOcean droplet (run as the `fam` user).
#
#   ./deploy/droplet/setup.sh            # idempotent: safe to re-run after every git pull
#
# Reads secrets from ~/.fam/agent.env (chmod 600, never in git). Renders ~/.hermes/config.yaml and
# ~/.hermes/.env from them, installs the GHL CLI (demo-location profile ONLY), the fam core, the vault,
# the Hermes cron routines, and the Slack gateway service. Hermes itself is installed separately with the
# pinned, checksum-verified v2026.8.31 installer (see docs/DEPLOY.md).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FAM_HOME="${FAM_HOME:-$HOME/.fam}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMES_PY="$HERMES_HOME/hermes-agent/venv/bin/python"
GHL_CLI_DIR="${GHL_CLI_DIR:-$HOME/ghl-cli}"
GHL_CLI_REF="${GHL_CLI_REF:-feat/affiliate-ops-commands}"
VAULT_DIR="${VAULT_DIR:-$HOME/fam-vault}"
ENV_FILE="$FAM_HOME/agent.env"
export PATH="$HOME/.local/bin:$PATH"

say()  { printf '\n\033[1m%s\033[0m\n' "$*"; }
fail() { printf '\nSetup stopped: %s\n' "$*" >&2; exit 1; }

say "1/8 Checking prerequisites"
command -v hermes >/dev/null || fail "Hermes is not installed (docs/DEPLOY.md step 2)"
hermes --version | grep -q "2026.8.31" || fail "expected Hermes v2026.8.31 (pinned)"
[ -x "$HERMES_PY" ] || fail "Hermes venv python not found at $HERMES_PY"
command -v npx >/dev/null || fail "Node/npx is required for the Orgo MCP"
[ -f "$ENV_FILE" ] || fail "missing $ENV_FILE — copy agent.example.env there and fill it in"
chmod 600 "$ENV_FILE"
set -a; . "$ENV_FILE"; set +a
: "${OPENROUTER_API_KEY:?OPENROUTER_API_KEY is required}"
FAM_GHL_MODE="${FAM_GHL_MODE:-mock}"
FAM_DEMO_MODE="${FAM_DEMO_MODE:-1}"
PRIMARY_MODEL="${PRIMARY_MODEL:-anthropic/claude-sonnet-5}"
FALLBACK_MODEL="${FALLBACK_MODEL:-anthropic/claude-haiku-4.5}"
ORGO_MCP_VERSION="${ORGO_MCP_VERSION:-1.1.1}"
ORGO_EXCLUDED_TOOLS="orgo_create_workspace, orgo_delete_workspace, orgo_create_computer, orgo_delete_computer, orgo_clone_computer, orgo_resize_computer, orgo_move_computer, orgo_stop_computer, orgo_get_vnc_password, orgo_publish_template, orgo_delete_template, orgo_build_template, orgo_cancel_build, orgo_test_run_template, orgo_stop_template_run, orgo_delete_file"
if [ "$FAM_GHL_MODE" = "live" ]; then
  [[ "${GHL_API_KEY:-}" == pit-* ]] || fail "FAM_GHL_MODE=live needs a location Private Integration Token (pit-...)"
  [ -n "${GHL_LOCATION_ID:-}" ] || fail "FAM_GHL_MODE=live needs GHL_LOCATION_ID"
fi

say "2/8 Installing the GoHighLevel CLI (demo location profile only)"
if [ ! -d "$GHL_CLI_DIR/.git" ]; then
  git clone -q https://github.com/jbellsolutions/gohighlevel-agency-cli.git "$GHL_CLI_DIR" \
    || fail "could not clone gohighlevel-agency-cli (private repo: run 'gh auth login' or add a deploy key)"
fi
if git -C "$GHL_CLI_DIR" fetch -q origin 2>/dev/null; then
  git -C "$GHL_CLI_DIR" checkout -q "$GHL_CLI_REF" && git -C "$GHL_CLI_DIR" pull -q --ff-only || true
else
  echo "  (no GitHub access from this box — using the existing checkout at $(git -C "$GHL_CLI_DIR" rev-parse --short HEAD))"
fi
[ -d "$GHL_CLI_DIR/.venv" ] || python3 -m venv "$GHL_CLI_DIR/.venv"
"$GHL_CLI_DIR/.venv/bin/pip" install -q -e "$GHL_CLI_DIR" "mcp>=1.2" >/dev/null
umask 077
if [ "$FAM_GHL_MODE" = "live" ]; then
  printf 'GHL_API_KEY=%s\nGHL_LOCATION_ID=%s\n' "$GHL_API_KEY" "$GHL_LOCATION_ID" > "$GHL_CLI_DIR/.env"
  rm -f "$GHL_CLI_DIR/profiles/registry.json"
  (cd "$GHL_CLI_DIR" && ./ghl profiles add mfm-demo --business funding --location-id "$GHL_LOCATION_ID" \
     --api-key "$GHL_API_KEY" --label "7FF Funding Affiliate Demo" --default >/dev/null) \
     || fail "could not register the mfm-demo GHL profile"
else
  printf '# FAM_GHL_MODE=mock — no GHL credentials on this box yet\n' > "$GHL_CLI_DIR/.env"
fi
umask 022

say "3/8 Installing the fam core into the Hermes venv"
"$HERMES_PY" -c "import mcp" 2>/dev/null || fail "the Hermes venv has no mcp package"
mkdir -p "$FAM_HOME/state" "$HERMES_HOME/scripts" "${FAM_CALL_INBOX:-$HOME/fam-inbox/calls}"
PYTHONPATH="$REPO_DIR/files/local-packages/fam/src" "$HERMES_PY" -m unittest discover -s "$REPO_DIR/tests" >/dev/null 2>&1 \
  || fail "unit tests failed — run: PYTHONPATH=files/local-packages/fam/src $HERMES_PY -m unittest discover -s tests -v"
cat > "$HOME/.local/bin/fam" <<SH
#!/usr/bin/env bash
set -a; . "$ENV_FILE"; set +a
export PYTHONPATH="$REPO_DIR/files/local-packages/fam/src" FAM_CONFIG_DIR="$REPO_DIR/config" \
  FAM_POLICY_PATH="$REPO_DIR/policies/permissions.json" FAM_STATE_DIR="$FAM_HOME/state" FAM_VAULT_DIR="$VAULT_DIR"
exec "$HERMES_PY" -m fam.cli "\$@"
SH
chmod 755 "$HOME/.local/bin/fam"
# Reply triage checks the inbox every 20 minutes but only wakes the model when an untriaged text shows up:
# Hermes runs this cheap script first and skips the agent run while its output (the pending ids) is unchanged.
cat > "$HERMES_HOME/scripts/fam-inbox-monitor.sh" <<SH
#!/usr/bin/env bash
exec "$HOME/.local/bin/fam" inbox --ids 2>/dev/null
SH
chmod 755 "$HERMES_HOME/scripts/fam-inbox-monitor.sh"
# Texts held back for the recipient's quiet hours go out when their window opens (no model involved).
cat > "$HERMES_HOME/scripts/fam-resume-paused.sh" <<SH
#!/usr/bin/env bash
exec "$HOME/.local/bin/fam" outbox resume
SH
chmod 755 "$HERMES_HOME/scripts/fam-resume-paused.sh"

say "4/8 Rendering Hermes config, persona, and gateway env"
[ -f "$HERMES_HOME/config.yaml" ] && [ ! -f "$HERMES_HOME/config.yaml.pre-fam" ] && cp "$HERMES_HOME/config.yaml" "$HERMES_HOME/config.yaml.pre-fam"
SLACK_ENABLED=false; [ -n "${SLACK_BOT_TOKEN:-}" ] && [ -n "${SLACK_APP_TOKEN:-}" ] && SLACK_ENABLED=true
TELEGRAM_ENABLED=false; [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && TELEGRAM_ENABLED=true
FAM_HOME="$FAM_HOME" REPO_DIR="$REPO_DIR" VAULT_DIR="$VAULT_DIR" HERMES_PY="$HERMES_PY" GHL_CLI_DIR="$GHL_CLI_DIR" \
SLACK_ENABLED="$SLACK_ENABLED" TELEGRAM_ENABLED="$TELEGRAM_ENABLED" PRIMARY_MODEL="$PRIMARY_MODEL" \
FALLBACK_MODEL="$FALLBACK_MODEL" ORGO_MCP_VERSION="$ORGO_MCP_VERSION" ORGO_EXCLUDED_TOOLS="$ORGO_EXCLUDED_TOOLS" \
FAM_GHL_MODE="$FAM_GHL_MODE" FAM_DEMO_MODE="$FAM_DEMO_MODE" \
python3 - "$REPO_DIR/hermes/config.template.yaml" "$HERMES_HOME/config.yaml" <<'PY'
import os, sys
src, dst = sys.argv[1], sys.argv[2]
text = open(src).read()
keys = ["PRIMARY_MODEL", "FALLBACK_MODEL", "REPO_DIR", "FAM_HOME", "VAULT_DIR", "HERMES_PYTHON", "GHL_CLI_DIR",
        "FAM_GHL_MODE", "FAM_DEMO_MODE", "GHL_API_KEY", "GHL_LOCATION_ID", "ORGO_MCP_VERSION", "ORGO_API_KEY",
        "ORGO_COMPUTER_ID", "ORGO_EXCLUDED_TOOLS", "SUPER_BROWSER_URL", "SUPER_BROWSER_TOKEN", "BROWSER_BOX_URL",
        "BROWSER_BOX_TOKEN", "DATABOX_URL", "DATABOX_TOKEN",
        "SLACK_ENABLED", "TELEGRAM_ENABLED", "SLACK_HOME_CHANNEL", "TELEGRAM_HOME_CHANNEL", "OPENROUTER_API_KEY",
        "FAM_DRAFT_MODEL", "FAM_FALLBACK_MODEL", "FAM_CALL_INBOX", "FAM_IGNORE_SMS_WINDOW"]
env = dict(os.environ, HERMES_PYTHON=os.environ["HERMES_PY"])
for key in keys:
    value = env.get(key, "")
    if key in ("BROWSER_BOX_URL", "DATABOX_URL"):
        # Accept the /mcp URL box-kit prints or the bare base URL. Unset → an unreachable
        # placeholder, so the MCP shows as down rather than half-configured.
        value = (value.strip().rstrip("/").removesuffix("/mcp") or "http://127.0.0.1:9") + "/mcp"
    if key == "SUPER_BROWSER_URL" and not value:
        value = "https://superbrowser.online/mcp/"
    text = text.replace(f"__{key}__", value.replace("\n", ""))
def drop_server(text, name):
    """Remove one `  name:` block under mcp_servers (2-space indent) through the next sibling."""
    out, skipping = [], False
    for line in text.splitlines():
        if line.startswith(f"  {name}:"):
            skipping = True
            continue
        if skipping and (line.startswith("  ") and not line.startswith("   ") and line.strip()) :
            skipping = False
        if not skipping:
            out.append(line)
    return "\n".join(out) + "\n"
# servers without credentials are left out entirely (never half-configured)
if not (env.get("ORGO_API_KEY") and env.get("ORGO_COMPUTER_ID")):
    text = drop_server(text, "orgo")
if not env.get("SUPER_BROWSER_TOKEN"):
    text = drop_server(text, "super-browser")
if not env.get("BROWSER_BOX_TOKEN"):
    text = drop_server(text, "browser-box")
if not env.get("DATABOX_TOKEN"):
    text = drop_server(text, "data-box")
if env.get("FAM_GHL_MODE") != "live":
    text = drop_server(text, "ghl")
left = [line for line in text.splitlines() if "__" in line and not line.lstrip().startswith("#")]
if any(tok in l for l in left for tok in ("__PRIMARY", "__REPO_DIR", "__GHL_", "__ORGO_", "__FAM_")):
    sys.exit("unrendered placeholders remain: " + "; ".join(left[:3]))
old = os.umask(0o077)
open(dst, "w").write(text)
os.umask(old)
os.chmod(dst, 0o600)
PY
install -m 600 "$REPO_DIR/files/SOUL.md" "$HERMES_HOME/SOUL.md"
install -m 600 "$REPO_DIR/files/AGENTS.md" "$HERMES_HOME/AGENTS.md"
umask 077
{
  echo "OPENROUTER_API_KEY=$OPENROUTER_API_KEY"
  [ -n "${SLACK_BOT_TOKEN:-}" ] && echo "SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN"
  [ -n "${SLACK_APP_TOKEN:-}" ] && echo "SLACK_APP_TOKEN=$SLACK_APP_TOKEN"
  [ -n "${SLACK_ALLOWED_USERS:-}" ] && echo "SLACK_ALLOWED_USERS=$SLACK_ALLOWED_USERS"
  [ -n "${SLACK_HOME_CHANNEL:-}" ] && echo "SLACK_HOME_CHANNEL=$SLACK_HOME_CHANNEL"
  [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && echo "TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN"
  [ -n "${TELEGRAM_ALLOWED_USERS:-}" ] && echo "TELEGRAM_ALLOWED_USERS=$TELEGRAM_ALLOWED_USERS"
  echo "GATEWAY_ALLOW_ALL_USERS=false"
} > "$HERMES_HOME/.env"
umask 022

say "5/8 Obsidian vault"
mkdir -p "$VAULT_DIR"
if [ ! -d "$VAULT_DIR/.git" ]; then
  cp -Rn "$REPO_DIR/vault-template/." "$VAULT_DIR/" 2>/dev/null || true
  git -C "$VAULT_DIR" init -q -b main
  git -C "$VAULT_DIR" -c user.name=funding-affiliate-manager -c user.email=fam@agents.usingaitoscale.com commit -q --allow-empty -m "vault: init"
fi
if [ -n "${VAULT_GIT_REMOTE:-}" ]; then
  git -C "$VAULT_DIR" remote get-url origin >/dev/null 2>&1 || git -C "$VAULT_DIR" remote add origin "$VAULT_GIT_REMOTE"
fi
install -m 755 "$REPO_DIR/deploy/droplet/vault-sync.sh" "$FAM_HOME/vault-sync.sh"
{ { crontab -l 2>/dev/null || true; } | { grep -v 'fam/vault-sync.sh' || true; }
  echo "*/15 * * * * VAULT_DIR=$VAULT_DIR $FAM_HOME/vault-sync.sh >> $FAM_HOME/vault-sync.log 2>&1"; } | crontab -

say "6/8 Scheduling routines (Hermes cron)"
existing="$(hermes cron list 2>/dev/null || true)"
# The old reply-triage job ran hourly on weekdays only, so a Friday-evening reply waited until Monday. Replace it.
legacy="$(awk '/^  [0-9a-f]+ \[/{id=$1} /Name: +FAM reply triage$/{print id}' <<<"$existing")"
for id in $legacy; do hermes cron remove "$id" >/dev/null && echo "  - FAM reply triage (weekday-only schedule)"; done
existing="$(hermes cron list 2>/dev/null || true)"
add_job() { # name schedule prompt-file [--monitor script] skills...
  local name="$1" schedule="$2" file="$3"; shift 3
  if grep -qF "Name:      $name" <<<"$existing"; then echo "  = $name"; return; fi
  local args=()
  if [ "${1:-}" = "--monitor" ]; then args+=(--monitor-script "$2"); shift 2; fi
  for s in "$@"; do args+=(--skill "$s"); done
  local deliver="local"; [ "$SLACK_ENABLED" = true ] && [ -n "${SLACK_HOME_CHANNEL:-}" ] && deliver="slack:$SLACK_HOME_CHANNEL"
  hermes cron create --name "$name" --deliver "$deliver" --workdir "$REPO_DIR" "${args[@]}" "$schedule" "$(cat "$REPO_DIR/routines/$file")" >/dev/null && echo "  + $name"
}
add_job "FAM daily tasks + sweep" "0 8 * * 1-5" daily-tasks-and-sweep.prompt affiliate-cadence ghl-affiliate-ops obsidian-memory
add_job "FAM reply triage every 20 min" "*/20 * * * *" reply-triage.prompt --monitor fam-inbox-monitor.sh affiliate-reply-triage
if ! grep -qF "Name:      FAM resume paused sends" <<<"$existing"; then
  hermes cron create --name "FAM resume paused sends" --deliver "$( [ "$SLACK_ENABLED" = true ] && [ -n "${SLACK_HOME_CHANNEL:-}" ] && echo "slack:$SLACK_HOME_CHANNEL" || echo local)" \
    --script fam-resume-paused.sh --no-agent "*/20 * * * *" >/dev/null && echo "  + FAM resume paused sends"
else
  echo "  = FAM resume paused sends"
fi
add_job "FAM call ingest" "45 9-19 * * 1-5" call-ingest.prompt obsidian-memory
add_job "FAM bi-weekly newsletter" "0 10 1,15 * *" biweekly-newsletter.prompt affiliate-newsletter
add_job "FAM monthly offer" "30 9 3 * *" monthly-offer.prompt affiliate-offers
add_job "FAM weekly scorecard" "0 16 * * 5" weekly-scorecard.prompt ghl-affiliate-ops

say "7/8 Gateway (it also runs the cron scheduler: without it no routine ever fires)"
hermes gateway install >/dev/null 2>&1 || true
hermes gateway restart >/dev/null 2>&1 || hermes gateway start >/dev/null 2>&1 || true
hermes gateway status 2>&1 | head -5 || true
hermes cron status 2>&1 | head -3 || true
if [ "$SLACK_ENABLED" != true ] && [ "$TELEGRAM_ENABLED" != true ]; then
  echo "  no Slack/Telegram tokens yet: routines run, and their output stays local (hermes cron runs)"
fi

say "8/8 Verifying"
"$HOME/.local/bin/fam" status | head -30
echo
echo "Funding Affiliate Manager is installed. Mode: FAM_GHL_MODE=$FAM_GHL_MODE, FAM_DEMO_MODE=$FAM_DEMO_MODE"
