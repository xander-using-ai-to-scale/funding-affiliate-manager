"""The reactivation kickoff: one personal text to each quiet partner, in waves, then one nudge.

    fam kickoff enroll            tag every quiet partner already in GoHighLevel fam:kickoff-pending
    fam kickoff draft --size 250  draft the next wave (highest-value partners first), freeze it, write the
                                  review file, and post the approval card: a person reads every message
    fam kickoff nudge             one short follow-up to anyone who hasn't answered after nudge_after_days
    fam kickoff status            pending / sent / done, waves, and reply rate by variant

Drafting runs here, outside the agent loop, so each text pays only for its own short prompt (the cost
model assumes this). Texts are signed by the partner's manager and stay within two SMS segments.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from . import cadence, drafting
from .cadence import KICKOFF_DONE, KICKOFF_PENDING, KICKOFF_SENT, Affiliate

TIER_RANK = {"CEO": 0, "Executive": 1, "Apprentice": 2, "Free": 3}


def rank(aff: Affiliate) -> tuple:
    """Wave order: past producers first, then higher tier, then the most recent engagement, then tenure."""
    recent = aff.last_engagement()
    joined = aff.day("join_date")
    return (-aff.deals_submitted, TIER_RANK.get(aff.tier, 4), -(recent.toordinal() if recent else 0),
            joined.toordinal() if joined else 10**7, aff.id)


def enroll(engine: Any, min_silent_days: int | None = None) -> dict[str, Any]:
    """Tag quiet partners for the kickoff (partners imported through fam.sources are tagged on import)."""
    threshold = int(engine.settings.cadence["quiet_after_days"] if min_silent_days is None else min_silent_days)
    tagged = 0
    for aff in engine.affiliates():
        if aff.is_dnc or aff.is_test_contact or {KICKOFF_PENDING, KICKOFF_SENT, KICKOFF_DONE} & set(aff.tags):
            continue
        _, silent = cadence.target_lifecycle(aff, engine.today(), engine.settings.cadence)
        if silent is None or silent >= threshold:
            engine.ghl.add_tags(aff.id, [KICKOFF_PENDING])
            tagged += 1
    engine.vault.log("Kickoff enrollment", f"- tagged {tagged} quiet partners {KICKOFF_PENDING}",
                     day=engine.today().isoformat())
    return {"ok": True, "tagged": tagged}


def _wave_number(engine: Any) -> int:
    rows = engine.store.list_actions(limit=5000)
    return 1 + sum(1 for r in rows if r["kind"] == "send_messages"
                   and json.loads(r["payload_json"]).get("purpose", "").startswith("kickoff wave"))


def draft_wave(engine: Any, size: int = 0, drafter: Any = None, contact_ids: list[str] | None = None) -> dict[str, Any]:
    """Draft, freeze and post one wave for review. Nothing is sent until a person approves it."""
    cfg = engine.settings.kickoff
    size = int(size or cfg["wave_size"])
    drafter = drafter or drafting.open_drafter(cfg)
    pool = ([engine.affiliate(c) for c in contact_ids] if contact_ids
            else engine.affiliates(tags=[KICKOFF_PENDING]))
    pool = sorted((a for a in pool if KICKOFF_PENDING in a.tags and not a.is_dnc and (a.phone or a.email)), key=rank)
    messages, skipped, drafts = [], [], []
    for aff in pool[:size]:
        p = engine.profile_get(aff.id, aff=aff)
        sender = p["manager"] or cfg["default_sender"]
        variant = drafting.variant_for(aff.id, cfg.get("variants", ["A"]))
        d = drafter.kickoff(p, sender, variant)
        problems = drafting.check(d["body"], p, sender, kickoff=True, max_segments=int(cfg["max_segments"]))
        if problems:
            skipped.append({"contact_id": aff.id, "name": aff.name, "problems": problems})
            continue
        msg = {"contact_id": aff.id, "channel": "sms" if aff.phone else "email", "body": d["body"], "kind": "kickoff",
               "variant": variant}
        if msg["channel"] == "email":
            msg["subject"] = f"Your new partner manager at {cfg['company']}"
        messages.append(msg)
        drafts.append({"contact_id": aff.id, "name": aff.name, "variant": variant, "hook": d["hook"],
                       "drafter": d["drafter"], "segments": drafting.segments(d["body"]), "body": d["body"]})
    if not messages:
        return {"ok": False, "reason": "no partners waiting on a kickoff" if not skipped else "every draft failed checks",
                "skipped": skipped}
    wave = _wave_number(engine)
    action = engine.prepare_messages(messages, purpose=f"kickoff wave {wave}")
    card = engine.request_approval(action["action_id"])
    engine.vault.log(f"Kickoff wave {wave} drafted", f"- {len(messages)} texts ({drafter.name} drafter), "
                     f"{len(skipped)} held for a person · review: [[Reviews/{card.get('review_file', '').rsplit('/', 1)[-1].removesuffix('.md')}]]",
                     day=engine.today().isoformat())
    return {"ok": True, "wave": wave, "action": card, "drafts": drafts, "skipped": skipped,
            "remaining_after_wave": max(0, len(pool) - size)}


def nudge_due(engine: Any) -> list[Affiliate]:
    """Partners whose kickoff went out nudge_after_days ago (or more) and who haven't answered."""
    days = int(engine.settings.kickoff["nudge_after_days"])
    due = []
    for aff in engine.affiliates(tags=[KICKOFF_SENT]):
        if aff.is_dnc:
            continue
        sent = engine.graph.interactions(aff.id, ["kickoff_sent"], limit=1)
        if not sent:
            continue
        when = date.fromisoformat(sent[0]["at"][:10])
        replied = engine.graph.interactions(aff.id, ["reply", "call"], limit=1)
        if (engine.today() - when).days >= days and not (replied and replied[0]["at"] >= sent[0]["at"]):
            due.append(aff)
    return sorted(due, key=rank)


def draft_nudges(engine: Any, drafter: Any = None, limit: int = 0) -> dict[str, Any]:
    cfg = engine.settings.kickoff
    drafter = drafter or drafting.open_drafter(cfg)
    affs = nudge_due(engine)[: int(limit or cfg["batch_max"])]
    if not affs:
        return {"ok": False, "reason": "no nudges due"}
    messages = []
    for aff in affs:
        p = engine.profile_get(aff.id, aff=aff)
        body = drafter.nudge(p, p["manager"] or cfg["default_sender"])
        messages.append({"contact_id": aff.id, "channel": "sms" if aff.phone else "email", "body": body,
                         "kind": "kickoff_nudge", **({} if aff.phone else {"subject": "Following up"})})
    action = engine.prepare_messages(messages, purpose="kickoff nudges")
    return {"ok": True, "action": engine.request_approval(action["action_id"]), "nudges": len(messages)}


def status(engine: Any) -> dict[str, Any]:
    counts = {tag.split("-")[-1]: len(engine.affiliates(tags=[tag])) for tag in (KICKOFF_PENDING, KICKOFF_SENT,
                                                                                 KICKOFF_DONE)}
    waves = []
    for r in engine.store.list_actions(limit=5000):
        purpose = json.loads(r["payload_json"]).get("purpose", "")
        if r["kind"] == "send_messages" and purpose.startswith("kickoff"):
            waves.append({"action_id": r["action_id"], "purpose": purpose, "state": r["state"],
                          "messages": r["recipients"], "created_at": r["created_at"]})
    return {"partners": counts, "nudges_due": len(nudge_due(engine)), "waves": waves,
            "variants": engine.graph.variant_stats()}
