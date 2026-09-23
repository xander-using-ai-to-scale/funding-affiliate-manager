"""Obsidian vault memory: daily notes, one note per affiliate, campaign notes.

The vault is plain markdown with wiki-links so Justin (or the client's manager)
can open it in Obsidian and see exactly what the agent did and remembers.
Semantic search can be layered on top; these files stay the source of truth.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def _slug(text: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|#^\[\]]", "", text).strip()
    return re.sub(r"\s+", " ", cleaned)[:80] or "untitled"


class Vault:
    def __init__(self, root: Path, timezone: str = "America/New_York"):
        self.root = root
        self.tz = ZoneInfo(timezone)
        for folder in ("Daily", "Affiliates", "Campaigns", "Events", "Newsletters", "Reports"):
            (self.root / folder).mkdir(parents=True, exist_ok=True)

    def _now(self) -> datetime:
        return datetime.now(self.tz)

    def affiliate_link(self, name: str, contact_id: str) -> str:
        return f"[[Affiliates/{_slug(name)} ({contact_id[-6:]})|{name}]]"

    def daily_path(self, day: str = "") -> Path:
        day = day or self._now().date().isoformat()
        return self.root / "Daily" / f"{day}.md"

    def log(self, title: str, body: str = "", day: str = "") -> Path:
        path = self.daily_path(day)
        if not path.exists():
            path.write_text(
                f"---\ntype: daily\ndate: {path.stem}\n---\n# {path.stem} — Funding Affiliate Manager\n\n"
            )
        stamp = self._now().strftime("%H:%M")
        with path.open("a") as handle:
            handle.write(f"\n### {stamp} — {title}\n")
            if body.strip():
                handle.write(body.rstrip() + "\n")
        return path

    def affiliate(self, name: str, contact_id: str, line: str, *, source: str = "", lifecycle: str = "",
                  day: str = "") -> Path:
        path = self.root / "Affiliates" / f"{_slug(name)} ({contact_id[-6:]}).md"
        if not path.exists():
            path.write_text(
                "---\n"
                f"type: affiliate\nghl_contact_id: {contact_id}\nsource: {source or 'unknown'}\n"
                f"lifecycle: {lifecycle or 'unknown'}\n---\n"
                f"# {name}\n\n## Timeline\n"
            )
        day = day or self._now().date().isoformat()
        with path.open("a") as handle:
            handle.write(f"- {day} [[Daily/{day}]] — {line}\n")
        return path

    def campaign(self, title: str, body: str, kind: str = "campaign", day: str = "") -> Path:
        day = day or self._now().date().isoformat()
        folder = {"newsletter": "Newsletters", "event": "Events", "report": "Reports"}.get(kind, "Campaigns")
        path = self.root / folder / f"{day} {_slug(title)}.md"
        path.write_text(f"---\ntype: {kind}\ndate: {day}\n---\n# {title}\n\n{body.rstrip()}\n")
        self.log(f"{kind.title()} saved", f"[[{folder}/{path.stem}]]", day=day)
        return path
