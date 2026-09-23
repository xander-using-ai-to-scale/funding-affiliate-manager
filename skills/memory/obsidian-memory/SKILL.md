---
name: obsidian-memory
description: "Use the Obsidian vault (~/fam-vault) as the agent's memory: daily notes, one note per affiliate, campaign/newsletter/event notes, reports. Read it to remember context about a person or a past campaign; write to it (via fam tools) so the manager can open Obsidian and see everything the agent did."
---

# Obsidian vault memory

Layout (created automatically):
- `Daily/YYYY-MM-DD.md` — timestamped log of sweeps, approvals, sends, replies, deals.
- `Affiliates/<Name> (<id6>).md` — frontmatter (GHL id, source, lifecycle) + a timeline of every touch, reply, and follow-up.
- `Campaigns/`, `Newsletters/`, `Events/`, `Reports/` — drafts and final copy.

Rules
- The `fam_*` tools write the vault for you; add context with `fam_note_add` (goes to GHL + the affiliate note) or `fam_campaign_note_save`.
- Before drafting to someone, read their affiliate note (`Affiliates/…`) — it remembers what they told us.
- Never store secrets, full contact lists, or sensitive financial documents in the vault.
- The vault is synced to a private git repo every 15 minutes so Justin can open it in Obsidian (`obsidian://open?vault=fam-vault`). Semantic search sits on top of these files later; the files stay the source of truth.
