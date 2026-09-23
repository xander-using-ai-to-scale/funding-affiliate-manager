#!/usr/bin/env bash
# Commit and push the Obsidian vault so the manager can open it in Obsidian. Runs every 15 minutes.
set -euo pipefail
VAULT_DIR="${VAULT_DIR:-$HOME/fam-vault}"
cd "$VAULT_DIR"
git add -A
if ! git diff --cached --quiet; then
  git -c user.name=funding-affiliate-manager -c user.email=fam@agents.usingaitoscale.com \
    commit -q -m "vault: $(date +%Y-%m-%dT%H:%M)"
fi
if git remote get-url origin >/dev/null 2>&1; then
  git pull -q --rebase origin main 2>/dev/null || true
  git push -q origin main
fi
