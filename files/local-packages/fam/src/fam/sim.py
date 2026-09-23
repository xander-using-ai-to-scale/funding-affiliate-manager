"""Demo simulation: a synthetic affiliate program run day-by-day through the real engine.

    fam sim seed --count 250            # synthetic affiliates in the mock CRM
    fam sim run --days 30               # fast-forward 30 days of cadence, replies, deals, events
    -> sim-output/report.md + report.json + a separate Obsidian vault of everything the agent did

Everything runs through FamEngine — the same sweep, approvals, execution, triage, and
bookkeeping the live agent uses — against MockGHL, so no one receives anything.
The manager's approvals are simulated as "sim-manager" and recorded as such.
`--live` seeding into the real demo GHL location is supported for the live demo; only
contacts tagged fam:test-contact ever receive real messages there (demo mode).
"""

from __future__ import annotations

import json
import random
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from . import cadence
from .config import Settings
from .engine import FamEngine
from .ghl import MockGHL

FIRST = ["Alicia", "Marcus", "Priya", "Derek", "Tanya", "Luis", "Keisha", "Brandon", "Sofia", "Jamal", "Heather",
         "Victor", "Nadia", "Trevor", "Camila", "Andre", "Rachel", "Omar", "Jenna", "Malik", "Dana", "Carlos",
         "Brittany", "Kevin", "Yolanda", "Ethan", "Monique", "Raj", "Tiffany", "Grant", "Lena", "Terrence"]
LAST = ["Brooks", "Nguyen", "Patel", "Coleman", "Reyes", "Foster", "Hughes", "Ward", "Diaz", "Bennett", "Price",
        "Sanders", "Ortiz", "Myers", "Long", "Ross", "Jenkins", "Perry", "Powell", "Russell", "Sullivan", "Bell"]
SOURCES = [("skool", 30), ("linkedin", 15), ("referral", 15), ("webinar", 12), ("event", 6), ("facebook", 8),
           ("website", 8), ("legacy-import", 6)]
NICHES = {
    "skool": ["business coach", "credit repair pro", "online course creator"],
    "linkedin": ["fractional CFO", "commercial real-estate broker", "business consultant"],
    "referral": ["CPA", "bookkeeper", "insurance agent"],
    "webinar": ["marketing agency owner", "business coach", "real-estate investor"],
    "event": ["equipment dealer", "franchise consultant", "business broker"],
    "facebook": ["credit repair pro", "notary / loan signing agent", "side-hustle marketer"],
    "website": ["ISO / funding broker", "merchant services rep", "consultant"],
    "legacy-import": ["ISO / funding broker", "credit repair pro", "mortgage broker"],
}
REPLIES = [
    ("has_deal", "I actually have a client who needs about $150k for equipment — can I send you the file?"),
    ("has_deal", "Got a merchant for you, restaurant owner doing around 80k a month. How do I submit?"),
    ("check_back_later", "Slammed with tax season right now, check back with me in a few weeks."),
    ("check_back_later", "Not right now — can you follow up next month?"),
    ("wants_service", "Honestly I need a funnel page to capture leads. Can you help with that?"),
    ("wants_service", "I have about 2,000 old leads on my list I never worked. Can you help reactivate them?"),
    ("wants_service", "Could really use help with social content posts."),
    ("wants_service", "My GHL pipeline is a mess, could use CRM help."),
    ("commission_question", "When do commissions get paid out on funded deals?"),
    ("question", "How do I submit a deal again? Lost the link."),
    ("event_interest", "Yes — send me the training invite."),
    ("unsubscribe", "STOP"),
    ("general_reply", "Thanks, appreciate you checking in!"),
]
REPLY_WEIGHTS = [9, 6, 8, 6, 5, 4, 3, 3, 4, 4, 6, 2, 10]


def _pick_source(rng: random.Random) -> str:
    return rng.choices([s for s, _ in SOURCES], weights=[w for _, w in SOURCES])[0]


def synthetic_affiliates(count: int, today: date, seed: int = 7) -> list[dict[str, Any]]:
    """Contacts with a realistic spread of sources, tenure, silence, and production."""
    rng = random.Random(seed)
    rows = []
    buckets = [  # (share, days-silent range, lifecycle hint)
        (0.34, (0, 29), "aff:active"),
        (0.10, (30, 44), "aff:active"),
        (0.10, (45, 59), "aff:active"),
        (0.11, (60, 89), "aff:active"),
        (0.14, (90, 179), "aff:active"),
        (0.14, (180, 540), "aff:active"),
        (0.07, (0, 3), "aff:applied"),
    ]
    for i in range(count):
        roll, acc = rng.random(), 0.0
        bucket = buckets[-1]
        for b in buckets:
            acc += b[0]
            if roll <= acc:
                bucket = b
                break
        silent = rng.randint(*bucket[1])
        source = _pick_source(rng)
        first, last = rng.choice(FIRST), rng.choice(LAST)
        join = today - timedelta(days=max(silent + rng.randint(0, 200), 1) if bucket[2] != "aff:applied" else silent)
        producer = bucket[2] != "aff:applied" and rng.random() < 0.38
        deals = rng.choice([1, 1, 2, 2, 3, 4, 6, 9, 14]) if producer else 0
        last_reply = today - timedelta(days=silent)
        fields: dict[str, Any] = {
            "affiliate_id": f"AFF-{1000 + i}",
            "join_date": join.isoformat(),
            "source": source,
            "niche": rng.choice(NICHES[source]),
            "audience_size": rng.choice(["<500", "500-2k", "2k-10k", "10k+"]),
            "deals_submitted": deals,
            "last_touch_date": (today - timedelta(days=rng.randint(3, 40))).isoformat(),
            "last_touch_channel": rng.choice(["sms", "email"]),
            "last_offer_date": (today - timedelta(days=rng.randint(5, 45))).isoformat(),
            "preferred_channel": rng.choice(["", "", "sms", "email"]),
            "assigned_manager": "Funding Relationship Manager",
        }
        if bucket[2] != "aff:applied":
            fields["last_reply_date"] = last_reply.isoformat()
        if producer:
            deal_age = silent + rng.randint(0, 20) if rng.random() < 0.7 else rng.randint(0, 25)
            fields["last_deal_date"] = (today - timedelta(days=deal_age)).isoformat()
        if bucket[2] == "aff:active" and rng.random() < 0.06:
            fields["next_touch_date"] = (today + timedelta(days=rng.randint(0, 6))).isoformat()
            fields["cadence_note"] = rng.choice(["after tax season", "once her new office opens",
                                                 "when Q4 budget is set", "after his vacation"])
        tags = [f"src:{source}", bucket[2], "fam:synthetic"]
        rows.append({
            "firstName": first,
            "lastName": last,
            "email": f"{first}.{last}.{i}@example.com".lower(),
            "phone": f"+1555555{i:04d}",
            "tags": tags,
            "fields": fields,
        })
    return rows


def _custom_fields(settings: Settings, fields: dict[str, Any]) -> list[dict[str, Any]]:
    ids = settings.field_ids()
    return [{"id": ids[k], "field_value": v} for k, v in fields.items() if k in ids]


def seed(settings: Settings, count: int, today: date, test_contacts: list[dict[str, str]],
         backend: Any = None, seed_value: int = 7) -> dict[str, Any]:
    engine = FamEngine(settings=settings, backend=backend, today=today)
    if isinstance(engine.ghl, MockGHL):
        engine.ghl.reset()
    created = 0
    for row in synthetic_affiliates(count, today, seed_value):
        payload = {k: row[k] for k in ("firstName", "lastName", "email", "phone", "tags")}
        payload["customFields"] = _custom_fields(settings, row["fields"])
        engine.ghl.create_contact(payload)
        created += 1
    for tc in test_contacts:
        payload = {"firstName": tc.get("first_name", "Test"), "lastName": tc.get("last_name", "Contact"),
                   "email": tc.get("email", ""), "phone": tc.get("phone", ""),
                   "tags": ["fam:test-contact", "src:referral", "aff:active"]}
        payload["customFields"] = _custom_fields(settings, {
            "source": "referral", "join_date": (today - timedelta(days=120)).isoformat(),
            "last_reply_date": (today - timedelta(days=65)).isoformat(),
            "last_touch_date": (today - timedelta(days=20)).isoformat(), "deals_submitted": 2,
            "niche": "business coach", "assigned_manager": "Funding Relationship Manager"})
        engine.ghl.create_contact(payload)
        created += 1
    plan = cadence.sweep(engine.affiliates(), today, settings.cadence)
    return {"created": created, "cohorts": plan["cohorts"], "silent_30_plus": plan["silent_30_plus"],
            "silent_90_plus": plan["silent_90_plus"], "personal_due": len(plan["personal_queue"]),
            "bulk_due": plan["bulk_counts"]}


def draft(aff: cadence.Affiliate, item: dict[str, Any]) -> dict[str, Any]:
    """Deterministic drafts from the conversation playbook (the live agent personalizes with the model)."""
    first = aff.first_name or "there"
    niche = aff.fields.get("niche") or "your"
    kind = item["kind"]
    if kind == "scheduled_followup":
        note = item.get("context", {}).get("cadence_note") or "like you asked"
        sms = (f"Hey {first}, circling back {note} like you asked. Anything on your plate where funding "
               f"could help one of your {niche} clients?")
        subject = f"Circling back, {first}"
    else:
        sms = (f"Hey {first}, it's been a minute! How's business going? Anything I can help with — resources, "
               f"new programs, or help working your leads?")
        subject = f"{first}, quick check-in"
    if kind == "scheduled_followup":
        note = item.get("context", {}).get("cadence_note") or "when we last talked"
        body_email = (f"Hi {first},\n\nYou asked me to circle back {note}, so here I am. How are things looking "
                      f"now?\n\nIf any of your {niche} clients need working capital, I can walk you through the "
                      f"fastest way to send the file over. And if it's still not the right time, just tell me when "
                      f"and I'll put it on my calendar.")
    else:
        body_email = (f"Hi {first},\n\nIt's been a little while since we connected and I wanted to check in "
                      f"personally. How's business going on your side?\n\nIs there anything I can help with — "
                      f"resources for your {niche} clients, our newest funding programs, or even help reactivating "
                      f"your own leads?\n\nJust hit reply — I read every one.")
    if item["channel"] == "sms":
        return {"contact_id": aff.id, "channel": "sms", "body": sms, "kind": kind}
    return {"contact_id": aff.id, "channel": "email", "subject": subject, "body": body_email, "kind": kind}


def run(settings: Settings, days: int, start: date, out_dir: Path, seed_value: int = 11,
        manager: str = "sim-manager") -> dict[str, Any]:
    rng = random.Random(seed_value)
    backend = MockGHL(settings.state_dir / "mock-ghl.json")
    backend.autosave = False  # flushed once per simulated day
    if not backend.db["contacts"]:
        raise SystemExit("mock CRM is empty — run `fam sim seed` first")
    timeline: list[dict[str, Any]] = []
    samples: dict[str, list[Any]] = {"drafts": [], "triage": [], "approval_cards": []}
    pending_deals: list[tuple[date, str]] = []
    event_days = {9, 23}
    newsletter_days = {0, 14, 28}
    before = None
    initial_population = FamEngine(settings=settings, backend=backend, today=start).affiliates()
    for offset in range(days):
        day = start + timedelta(days=offset)
        backend.now_override = f"{day.isoformat()}T14:00:00+00:00"
        engine = FamEngine(settings=settings, backend=backend, today=day)
        stats: dict[str, Any] = {"day": day.isoformat()}
        plan = engine.sweep(apply_lifecycle=True, detail_limit=-1)
        if before is None:
            before = dict(plan["cohorts"])
        stats["lifecycle_changes"] = plan["lifecycle_applied"]
        stats["silent_90_plus"] = plan["silent_90_plus"]
        touched: list[tuple[str, str]] = []

        # 1) personal queue: draft -> one batch approval -> execute
        messages = []
        for item in plan["personal_queue"]:
            aff = engine.affiliate(item["contact_id"])
            messages.append(draft(aff, item))
        stats["personal_sent"] = 0
        if messages:
            action = engine.prepare_messages(messages, purpose="daily personal touches")
            card = engine.request_approval(action["action_id"])
            if len(samples["approval_cards"]) < 2:
                samples["approval_cards"].append(card["approval_card"])
            engine.approve(action["action_id"], action["action_digest"], manager)
            result = engine.execute(action["action_id"])
            stats["personal_sent"] = result["mock"] + result["simulated"]
            touched += [(m["contact_id"], "personal") for m in messages]
            if len(samples["drafts"]) < 6:
                samples["drafts"] += [{"kind": m["kind"], "channel": m["channel"], "body": m["body"]}
                                      for m in messages[: 6 - len(samples["drafts"])]]
        stats["tasks_worked"] = sum(1 for i in plan["personal_queue"] if i["kind"] == "scheduled_followup")

        # 2) bulk cadence (standing-approval path)
        stats["bulk_enrolled"] = {}
        for kind, items in plan["bulk_queue"].items():
            ids = [i["contact_id"] for i in items]
            action = engine.prepare_enrollment(kind, contact_ids=ids, purpose=f"cadence {kind}")
            engine.request_approval(action["action_id"])
            engine.approve(action["action_id"], action["action_digest"], manager)
            result = engine.execute(action["action_id"])
            stats["bulk_enrolled"][kind] = result["mock"] + result["simulated"]
            touched += [(cid, "bulk") for cid in ids]

        # 3) newsletter every two weeks, events twice a month
        if offset in newsletter_days:
            everyone = [a.id for a in engine.affiliates() if not a.is_dnc]
            action = engine.prepare_enrollment("newsletter", contact_ids=everyone, purpose="bi-weekly newsletter",
                                               custom_values={"newsletter_subject": f"Partner update — {day:%b %d}"})
            engine.request_approval(action["action_id"])
            engine.approve(action["action_id"], action["action_digest"], manager)
            sent = engine.execute(action["action_id"])
            stats["newsletter"] = sent["mock"] + sent["simulated"]
        if offset in event_days:
            invitees = [a.id for a in engine.affiliates() if not a.is_dnc and a.lifecycle in
                        {"aff:active", "aff:quiet", "aff:reactivated", "aff:producing"}]
            action = engine.prepare_enrollment("event_invite", contact_ids=invitees,
                                               purpose="How to get more leads — partner training",
                                               custom_values={"next_event_title": "How to get more funding leads"})
            engine.request_approval(action["action_id"])
            engine.approve(action["action_id"], action["action_digest"], manager)
            sent = engine.execute(action["action_id"])
            stats["event_invites"] = sent["mock"] + sent["simulated"]

        # 4) replies arrive (personal touches reply more than bulk)
        stats["replies"] = {}
        for cid, mode in touched:
            p = 0.22 if mode == "personal" else 0.07
            if rng.random() < p:
                intent, text = rng.choices(REPLIES, weights=REPLY_WEIGHTS)[0]
                backend.record_inbound(cid, "sms", text)
                outcome = engine.record_reply(cid, text)
                backend.mark_read(cid)
                stats["replies"][outcome["intent"]] = stats["replies"].get(outcome["intent"], 0) + 1
                if outcome["intent"] == "has_deal":
                    pending_deals.append((day + timedelta(days=rng.randint(1, 3)), cid))
                if len(samples["triage"]) < 8:
                    samples["triage"].append({"reply": text, "intent": outcome["intent"],
                                              "actions": outcome["actions_taken"],
                                              "alert": outcome["manager_alert"]})

        # 5) deals that came from "has a deal" replies get submitted
        stats["deals_recorded"] = 0
        for due_day, cid in list(pending_deals):
            if due_day <= day:
                engine.record_deal(cid, "submitted after affiliate replied to outreach (simulation)")
                pending_deals.remove((due_day, cid))
                stats["deals_recorded"] += 1
        timeline.append(stats)
        backend.flush()

    end = start + timedelta(days=days)
    baseline = cadence.sweep(initial_population, end, settings.cadence)["cohorts"]
    final_engine = FamEngine(settings=settings, backend=backend, today=end)
    after = cadence.sweep(final_engine.affiliates(), end, settings.cadence)["cohorts"]
    score = final_engine.scorecard()
    report = _report(timeline, before or {}, after, score, samples, days, len(backend.db["contacts"]))
    report["cohorts_no_agent"] = baseline
    report["assumptions"] = {"reply_rate_personal": 0.22, "reply_rate_bulk": 0.07,
                             "deal_follow_through": "every 'has a deal' reply is submitted 1–3 days later",
                             "manager": "approves each daily batch (simulated as sim-manager)"}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(report, indent=2, default=str))
    (out_dir / "report.md").write_text(_markdown(report))
    return report


def _report(timeline, before, after, score, samples, days, population) -> dict[str, Any]:
    totals: dict[str, Any] = {"personal_sent": 0, "bulk_enrolled": 0, "replies": 0, "deals_recorded": 0,
                              "tasks_worked": 0, "newsletter_sends": 0, "event_invites": 0, "reply_intents": {}}
    for d in timeline:
        totals["personal_sent"] += d.get("personal_sent", 0)
        totals["bulk_enrolled"] += sum(d.get("bulk_enrolled", {}).values())
        totals["deals_recorded"] += d.get("deals_recorded", 0)
        totals["tasks_worked"] += d.get("tasks_worked", 0)
        totals["newsletter_sends"] += d.get("newsletter", 0)
        totals["event_invites"] += d.get("event_invites", 0)
        for k, v in d.get("replies", {}).items():
            totals["replies"] += v
            totals["reply_intents"][k] = totals["reply_intents"].get(k, 0) + v
    scale = 10000 / max(population, 1)
    projection = {k: round(v * scale) for k, v in totals.items() if isinstance(v, int)}
    projection["manager_approvals_per_day"] = "1 batch card for personal touches + 1 per campaign"
    projection["personal_touches_per_day_at_cap"] = 40
    return {"days": days, "population": population, "cohorts_before": before, "cohorts_after": after,
            "totals": totals, "projection_10k": projection, "scorecard_end": score, "samples": samples,
            "timeline": timeline}


def _markdown(r: dict[str, Any]) -> str:
    t = r["totals"]
    lines = [
        f"# Funding Affiliate Manager — {r['days']}-day simulation",
        "",
        f"Synthetic program of **{r['population']} affiliates** run day-by-day through the real engine "
        "(sweep → approvals → execution → reply triage → deals) against a mock CRM. No one was contacted.",
        "",
        "## What the agent did",
        "",
        "| Metric | Simulation | Projected at 10,000 affiliates |",
        "|---|---:|---:|",
    ]
    labels = [("personal_sent", "Personal check-ins / follow-ups sent"),
              ("bulk_enrolled", "Cadence workflow enrollments (bi-weekly touch, monthly offer, reactivation)"),
              ("newsletter_sends", "Newsletter deliveries (every 2 weeks)"),
              ("event_invites", "Event / training invites"),
              ("tasks_worked", "“Check back with me” tasks worked on their due day"),
              ("replies", "Replies triaged"),
              ("deals_recorded", "Deals submitted after outreach")]
    for key, label in labels:
        lines.append(f"| {label} | {t[key]:,} | {r['projection_10k'].get(key, 0):,} |")
    lines += ["", "## Reply triage", "", "| Intent | Count |", "|---|---:|"]
    for k, v in sorted(t["reply_intents"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| {k} | {v} |")
    base = r.get("cohorts_no_agent", {})
    lines += ["", "## Lifecycle: with the agent vs. without", "",
              "Time passes either way. *Without the agent* is the same program aged "
              f"{r['days']} days with no outreach, replies, or deals.", "",
              "| Lifecycle | Day 0 | End — without agent | End — with agent |", "|---|---:|---:|---:|"]
    for k in sorted(set(r["cohorts_before"]) | set(r["cohorts_after"]) | set(base)):
        lines.append(f"| {k} | {r['cohorts_before'].get(k, 0)} | {base.get(k, 0)} | {r['cohorts_after'].get(k, 0)} |")
    if r.get("assumptions"):
        lines += ["", "Assumptions: " + "; ".join(f"{k.replace('_', ' ')} = {v}" for k, v in r["assumptions"].items())]
    lines += ["", "## Sample approval card", "", "```", (r["samples"]["approval_cards"] or ["(none)"])[0], "```",
              "", "## Sample drafts", ""]
    for d in r["samples"]["drafts"]:
        lines.append(f"- **{d['kind']} · {d['channel']}** — {d['body'][:300]}")
    lines += ["", "## Sample reply triage", ""]
    for s in r["samples"]["triage"]:
        lines.append(f"- “{s['reply']}” → **{s['intent']}** → {'; '.join(s['actions'])}"
                     + (f" · alert: {s['alert']}" if s["alert"] else ""))
    lines += ["", "## End-of-run scorecard", "", "```json", json.dumps(r["scorecard_end"], indent=2), "```", ""]
    return "\n".join(lines)


def sim_settings(base: Settings, out_dir: Path) -> Settings:
    """Isolated state + vault so a simulation never touches the live ledger or memory."""
    state = out_dir / "state"
    state.mkdir(parents=True, exist_ok=True)
    return replace(base, state_dir=state, vault_dir=out_dir / "vault", ghl_mode="mock", demo_mode=True)
