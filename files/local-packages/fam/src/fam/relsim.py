"""Relationship simulation: a quiet partner program brought back one conversation at a time.

    fam sim relationships --count 250 --days 30 --start 2026-10-05 --out sim-output/relationships

Synthetic partners arrive the way 7FF's will: a Zoho-style record (tier, plan, join date, deals, and for
some a few notes) imported through fam.sources, every one of them quiet and tagged for the kickoff. Then,
day by day, through the real engine and the framework templates (no model, no network, deterministic):

  * kickoff waves of personal texts, every one in a review file, approved by a simulated manager
  * one nudge for anyone who hasn't answered after five days
  * partners answer in their own words; the inbox reads every new text, triage records the facts
  * our replies follow the framework: one discovery question at a time, then the call ask, then the link
  * booked calls happen; half are phone calls transcribed in GoHighLevel, half are video calls whose
    transcript lands in the call inbox; commitments become tasks; then the revenue plan
  * "is this a bot?" goes to the manager, who answers personally; STOP in any form is honored

Each synthetic partner has a hidden truth (who their clients are, what they need, deal size, goals...)
and a persona (engaged, warm, needs a nudge, check back later, has a deal, silent, opt-out, asks who
is texting). Replies are written from the truth, so the report can say how much of what partners said
ended up in their profile.

Output: report.json, report.md, partners/<before|after>.md for one sample partner, and the vault.
"""

from __future__ import annotations

import json
import random
import re
import shutil
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from . import calls, drafting, extract, kickoff, sources
from .config import Settings
from .engine import FamEngine
from .errors import FamError
from .ghl import MockGHL
from .graph import SOURCE_LABELS

SENDER = "Justin"
MANAGER = "sim-manager"
CALENDAR = "https://example.com/book/justin"
WAVE = 40
FIRST = ["Alicia", "Marcus", "Priya", "Derek", "Tanya", "Luis", "Keisha", "Brandon", "Sofia", "Jamal", "Heather",
         "Victor", "Nadia", "Trevor", "Camila", "Andre", "Rachel", "Omar", "Jenna", "Malik", "Carlos", "Brittany",
         "Kevin", "Yolanda", "Ethan", "Monique", "Raj", "Tiffany", "Grant", "Lena", "Terrence", "Gina"]
LAST = ["Brooks", "Nguyen", "Patel", "Coleman", "Foster", "Hughes", "Ward", "Diaz", "Bennett", "Price", "Sanders",
        "Ortiz", "Myers", "Long", "Ross", "Jenkins", "Perry", "Powell", "Russell", "Sullivan", "Bell", "Vance"]
TIERS = [("CEO", 5), ("Executive", 17), ("Apprentice", 33), ("Free", 45)]
PLANS = {"CEO": "CEO Partner, annual", "Executive": "Executive Partner, annual", "Apprentice": "Apprentice, monthly",
         "Free": "Free partner"}
SOURCES = [("skool", 30), ("linkedin", 15), ("referral", 15), ("webinar", 12), ("event", 6), ("facebook", 8),
           ("website", 8), ("legacy-import", 6)]
NICHES = {  # niche -> the clients they serve
    "business consultant": ["small trucking companies", "restaurant owners", "home service contractors"],
    "CPA": ["dental practices", "small manufacturers", "family-owned retailers"],
    "bookkeeper": ["construction subcontractors", "salons and spas", "cleaning companies"],
    "insurance agent": ["auto repair shops", "landscaping companies", "trucking companies"],
    "commercial real-estate broker": ["restaurant groups", "medical practices", "retail franchisees"],
    "equipment dealer": ["construction companies", "farm operations", "trucking companies"],
    "business coach": ["e-commerce brands", "agency owners", "service businesses"],
    "fractional CFO": ["software startups", "manufacturers", "healthcare clinics"],
    "credit repair pro": ["new business owners", "self-employed contractors", "first-time founders"],
    "ISO / funding broker": ["restaurants", "retail shops", "trucking companies"],
    "merchant services rep": ["restaurants", "retail shops", "salons"],
}
NEEDS = [  # how a partner says it -> the deal type the profile should record
    ("equipment, a truck or two at a time", "equipment financing"), ("new equipment", "equipment financing"),
    ("working capital to cover payroll", "working capital"), ("cash flow in the slow season", "working capital"),
    ("inventory before the busy season", "inventory financing"), ("a line of credit", "a line of credit"),
    ("SBA loans", "SBA loans"), ("money to open a second location", "expansion capital"),
    ("credit cards to get started", "business credit cards"),
]
GOALS = ["get back to sending a deal a month", "close two deals a month by the end of the year",
         "build a second income stream from referrals", "add funding as a service for my clients",
         "grow my referral income this year"]
HELP = ["a simple page I can send my clients to", "help working my old leads", "a faster way to submit deals",
        "a short list of which programs fit my clients", "posts I can share with my audience"]
BLOCKERS = ["the portal changed", "I didn't know who to call anymore", "my last client got declined",
            "I lost the submission link"]
STATES = ["Texas", "Florida", "Georgia", "Ohio", "Arizona", "California", "North Carolina", "Illinois", "Colorado",
          "Tennessee", "New York", "Oklahoma"]
SIZES = [25, 50, 75, 100, 150, 250]
PERSONAS = [("engaged", 6), ("warm", 8), ("nudge", 5), ("later", 4), ("has_deal", 2), ("silent", 70),
            ("stop", 3), ("identity", 2)]
STOPS = ["STOP", "Stop.", "UNSUBSCRIBE", "please stop texting me", "Remove me"]
ASK_WHO = ["Is this a real person or a bot?", "Is this really {sender}?", "Am I talking to a bot?"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
# Ways a partner states each slot. Some are phrasings the keyword rules miss on purpose: the report says
# how much of what partners said reached their profile, and that number should be honest.
SAY = {
    "client_types": ["Most of my clients are {client}.", "I mostly work with {client} these days.",
                     "Mainly {client}.", "These days it's a lot of {client}."],
    "deal_types": ["Usually it's {need}.", "Mostly {need}, sometimes {need2}.", "They always seem to need {need}."],
    "deal_size": ["Usually around ${size}k.", "Deals are typically ${size}k or so.",
                  "Anywhere from ${lo}k to ${hi}k, usually about ${size}k."],
    "regions": ["Mostly in {state}.", "Most of them are in {state} and {state2}.", "All over the country really."],
    "goals": ["My goal this year is to {goal}.", "I want to {goal}.", "Honestly I'd love to {goal}.",
              "Trying to {goal}, that's the plan."],
    "needs": ["What would help is {help}.", "I could really use {help}.", "Honestly {help} would make a big difference."],
    "channel": {"text": ["Texting is best.", "Text is best for me."], "phone call": ["Call me, I'm bad at texting."],
                "email": ["Email me, I'm in meetings all day."]},
    "best_time": ["{time_cap} are best to reach me.", "Best to catch me in the {time}.", "{time_cap} are easier for me."],
    "blockers": ["Honestly I haven't sent anything because {blocker}.", "I haven't sent anything lately because {blocker}."],
}
OPENERS = ["Hey {sender}! Good to hear from you.", "Hi {sender}, thanks for reaching out.",
           "Hey, nice to meet you {sender}.", "Thanks {sender}!"]
YES_CALL = ["Sure, {day} morning works.", "Yes, let's do it. I'm free {day}.", "Sounds good, {day} afternoon?"]
NO_CALL = "Texting is easier for me right now, let's keep it here for now."


@dataclass
class Partner:
    cid: str
    first: str
    last: str
    email: str
    phone: str
    persona: str
    truth: dict[str, Any]
    started_as: str = ""
    stated: dict[str, str] = field(default_factory=dict)   # slot -> the truth value they said out loud
    replies: int = 0
    answered_kickoff: bool = False
    call_on: str = ""
    called: bool = False
    deal_on: str = ""
    quiet_after: int = 99   # warm partners stop answering after this many replies


def _truth(rng: random.Random, niche: str) -> dict[str, Any]:
    need, need2 = rng.sample(NEEDS, 2)
    size = rng.choice(SIZES)
    region = rng.random()
    regions = (["nationwide"] if region < 0.15 else rng.sample(STATES, 2) if region < 0.45 else [rng.choice(STATES)])
    time = rng.choice(["mornings", "afternoons", "evenings"])
    return {"client": rng.choice(NICHES[niche]), "need": need, "need2": need2, "size": size,
            "lo": max(10, size // 2), "hi": size * 2, "regions": regions, "goal": rng.choice(GOALS),
            "help": rng.choice(HELP), "channel": rng.choices(["text", "phone call", "email"], [7, 2, 1])[0],
            "time": time, "blocker": rng.choice(BLOCKERS)}


def _say(rng: random.Random, p: Partner, slot: str) -> str:
    t = p.truth
    if slot == "channel":
        line = rng.choice(SAY["channel"][t["channel"]])
    elif slot == "regions":
        line = SAY["regions"][2 if t["regions"] == ["nationwide"] else 1 if len(t["regions"]) > 1 else 0]
    else:
        line = rng.choice(SAY[slot])
    p.stated.setdefault(slot, line)
    return line.format(client=t["client"], need=t["need"][0], need2=t["need2"][0], size=t["size"], lo=t["lo"],
                       hi=t["hi"], state=t["regions"][0], state2=(t["regions"] + [""])[1], goal=t["goal"],
                       help=t["help"], time=t["time"], time_cap=t["time"].capitalize(), blocker=t["blocker"])


def _records(count: int, today: date, rng: random.Random) -> tuple[list[sources.SourceRecord], dict[str, dict]]:
    records, hidden = [], {}
    for i in range(count):
        first, last = rng.choice(FIRST), rng.choice(LAST)
        source = rng.choices([s for s, _ in SOURCES], [w for _, w in SOURCES])[0]
        niche = rng.choice(list(NICHES))
        tier = rng.choices([t for t, _ in TIERS], [w for _, w in TIERS])[0]
        joined = today - timedelta(days=rng.randint(420, 1800))
        silent = rng.randint(95, max(96, (today - joined).days - 30))
        producer = rng.random() < (0.55 if tier in {"CEO", "Executive"} else 0.25)
        deals = rng.choice([1, 1, 2, 3, 4, 7, 11]) if producer else 0
        fields: dict[str, Any] = {"tier": tier, "plan": PLANS[tier], "join_date": joined.isoformat(), "source": source,
                                  "niche": niche, "deals_submitted": deals, "assigned_manager": SENDER,
                                  "last_contact_date": (today - timedelta(days=silent)).isoformat()}
        if producer:
            fields["last_deal_date"] = (today - timedelta(days=silent + rng.randint(0, 120))).isoformat()
        truth = _truth(rng, niche)
        history = []
        if rng.random() < 0.35:  # a third have notes worth reading; the rest are thin records
            history.append({"id": "n1", "date": (joined + timedelta(days=2)).isoformat(), "kind": "zoho_note",
                            "text": f"Onboarding call. {niche.capitalize()}. Said most of my clients are "
                                    f"{truth['client']}."})
            if producer:
                history.append({"id": "d1", "date": fields["last_deal_date"], "kind": "zoho_deal",
                                "text": f"{truth['need'][1].capitalize()} for a client (funded)"})
        email = f"{first}.{last}.{i}@example.com".lower()
        records.append(sources.SourceRecord(source="zoho", external_id=f"ZX-{20000 + i}", first_name=first,
                                            last_name=last, email=email, phone=f"+1555444{i:04d}", fields=fields,
                                            history=history))
        hidden[email] = {"truth": truth, "persona": rng.choices([p for p, _ in PERSONAS], [w for _, w in PERSONAS])[0]}
    return records, hidden


class Sim:
    def __init__(self, settings: Settings, out: Path, start: date, days: int, count: int, seed: int = 21):
        self.settings, self.out, self.start, self.days, self.count = settings, out, start, days, count
        self.rng = random.Random(seed)
        self.backend = MockGHL(settings.state_dir / "mock-ghl.json")
        self.backend.autosave = False
        self.drafter = drafting.TemplateDrafter(settings.kickoff["company"], CALENDAR,
                                                int(settings.kickoff["max_segments"]))
        self.extractor = extract.RuleExtractor()
        self.partners: dict[str, Partner] = {}
        self.queue: list[tuple[str, str, str]] = []  # (day, contact_id, text) waiting to arrive
        self.personal: list[tuple[str, str]] = []    # (day, contact_id): the manager answers "who is this?"
        self.timeline: list[dict[str, Any]] = []
        self.samples: dict[str, Any] = {"kickoffs": {}, "nudge": "", "conversations": [], "review_file": "",
                                        "approval_card": "", "call_note": "", "brief": "", "plan": "",
                                        "identity": {}, "stop": []}
        self.totals = {k: 0 for k in ("kickoffs_sent", "kickoffs_held_back", "nudges_sent", "replies_in",
                                      "texts_in", "replies_sent", "discovery_questions", "call_asks", "calls_booked",
                                      "calls_held", "calls_phone", "calls_video", "commitments", "manager_tasks",
                                      "revenue_plans", "deals", "opt_outs", "identity_escalations",
                                      "duplicates_skipped", "drafts_blocked", "relisted",
                                      "triaged_twice")}
        self.day = start
        self.engine = self._engine(start)

    def _engine(self, day: date) -> FamEngine:
        self.backend.now_override = f"{day.isoformat()}T14:00:00+00:00"
        engine = FamEngine(settings=self.settings, backend=self.backend, today=day)
        engine.extractor = self.extractor
        return engine

    def later(self, cid: str, text: str, lo: int, hi: int) -> None:
        when = (self.day + timedelta(days=self.rng.randint(lo, hi))).isoformat()
        if len(text) > 90 and ". " in text and self.rng.random() < 0.3:  # some people send it as two texts
            first, rest = text.split(". ", 1)
            self.queue += [(when, cid, first + "."), (when, cid, rest)]
        else:
            self.queue.append((when, cid, text))

    # ── what a partner does after hearing from us ────────────────────────────
    def respond(self, p: Partner, kind: str, move: str = "", slot: str = "") -> None:
        r, persona = self.rng.random(), p.persona
        if p.replies >= p.quiet_after or persona in {"stop"} and p.replies:
            return
        opener = self.rng.choice(OPENERS).format(sender=SENDER)
        if kind == "kickoff":
            if persona == "stop":
                self.later(p.cid, self.rng.choice(STOPS), 0, 1)
            elif persona == "identity":
                self.later(p.cid, self.rng.choice(ASK_WHO).format(sender=SENDER), 0, 1)
            elif persona == "has_deal" and r < 0.9:
                self.later(p.cid, f"Perfect timing. I actually have a client who needs about ${p.truth['size']}k for "
                                  f"{p.truth['need'][0]}. Can I send you the file?", 0, 1)
            elif persona == "later" and r < 0.85:
                self.later(p.cid, f"{opener} Slammed right now, can you check back with me in a few weeks?", 0, 2)
            elif persona == "engaged" and r < 0.85:
                slots = self.rng.sample(["client_types", "deal_types", "deal_size", "regions", "channel"], 2)
                self.later(p.cid, " ".join([opener] + [_say(self.rng, p, s) for s in slots]), 0, 1)
            elif persona == "warm" and r < 0.7:
                self.later(p.cid, f"{opener} {_say(self.rng, p, self.rng.choice(['client_types', 'deal_types']))}", 1, 3)
        elif kind == "nudge":
            if persona == "nudge" and r < 0.7 or persona in {"engaged", "warm"} and r < 0.45:
                p.persona = "warm" if persona == "nudge" else persona
                self.later(p.cid, f"Sorry, crazy week! {_say(self.rng, p, 'client_types')}", 0, 2)
            elif persona == "silent" and r < 0.05:
                self.later(p.cid, "Not a good time right now, maybe next quarter.", 0, 2)
        elif kind == "reply":
            eager = 0.9 if persona in {"engaged", "has_deal"} else 0.6 if persona in {"warm", "identity"} else 0.3
            if move == "discover" and slot and r < eager:
                extra = self.rng.random() < 0.3
                pool = [s for s in ("deal_size", "regions", "best_time", "blockers") if s != slot and s not in p.stated]
                said = [_say(self.rng, p, slot)] + ([_say(self.rng, p, pool[0])] if extra and pool else [])
                self.later(p.cid, " ".join(said), 0, 1)
            elif move == "call_ask":
                yes = 0.85 if persona in {"engaged", "has_deal"} else 0.35
                if r < yes:
                    self.later(p.cid, self.rng.choice(YES_CALL).format(day=self.rng.choice(WEEKDAYS)), 0, 1)
                elif r < yes + 0.3:
                    self.later(p.cid, NO_CALL, 0, 1)
        elif kind == "personal" and r < 0.8:  # after the manager answered them personally
            p.persona = "warm"
            self.later(p.cid, f"Thanks for getting back to me, {SENDER}. {_say(self.rng, p, 'client_types')}", 0, 1)

    # ── one manager approval for a batch, as the manager would do it ─────────
    def _sendable(self, m: dict[str, Any]) -> bool:
        """The engine's own send checks, per message, so one bad draft can't sink the day's batch."""
        try:
            aff = self.engine.affiliate(m["contact_id"])
            if aff.is_dnc or self.engine._personal_reply_pending(aff):
                raise FamError("blocked")
            self.engine._lint(m["body"])
            self.engine._lint_voice(m["body"])
            return True
        except FamError:
            self.totals["drafts_blocked"] += 1
            return False

    def send(self, messages: list[dict[str, Any]], purpose: str, hold_back: list[int] | None = None) -> dict[str, Any]:
        sendable = [m for m in messages if self._sendable(m)]
        if not sendable:
            return {"sent": [], "held": []}
        action = self.engine.prepare_messages(sendable, purpose=purpose)
        card = self.engine.request_approval(action["action_id"])
        if not self.samples["approval_card"] and purpose.startswith("kickoff"):
            self.samples["approval_card"] = card["approval_card"]
        self.engine.approve(action["action_id"], action["action_digest"], MANAGER, exclude=hold_back or [])
        result = self.engine.execute(action["action_id"])
        sent = [r["contact_id"] for r in result["per_contact"] if r.get("ok") and not r.get("held_back")]
        held = [r["contact_id"] for r in result["per_contact"] if r.get("held_back")]
        return {"sent": sent, "held": held, "card": card}

    # ── the day ──────────────────────────────────────────────────────────────
    def run_day(self, day: date) -> None:
        self.day = day
        self.engine = engine = self._engine(day)
        iso = day.isoformat()
        stats: dict[str, Any] = {"day": iso}
        # 1. kickoff wave
        wave = kickoff.draft_wave(engine, WAVE, drafter=self.drafter)
        if wave.get("ok"):
            action = wave["action"]
            hold = [2] if not self.samples["review_file"] else []  # wave 1: the reviewer holds one back to edit
            if not self.samples["review_file"]:
                self.samples["review_file"] = Path(action["review_file"]).read_text()
                self.samples["approval_card"] = action["approval_card"]
            engine.approve(action["action_id"], action["action_digest"], MANAGER, exclude=hold)
            result = engine.execute(action["action_id"])
            stats["kickoffs"] = result["mock"]
            self.totals["kickoffs_sent"] += result["mock"]
            self.totals["kickoffs_held_back"] += result["held_back"]
            sent = {r["contact_id"] for r in result["per_contact"] if r.get("ok") and not r.get("held_back")}
            for d in wave["drafts"]:
                key = f"{d['variant']}/{d['hook']}"
                if d["contact_id"] in sent and key not in self.samples["kickoffs"]:
                    self.samples["kickoffs"][key] = {"variant": d["variant"], "hook": d["hook"], "body": d["body"],
                                                     "segments": d["segments"]}
                if d["contact_id"] in sent:
                    self.respond(self.partners[d["contact_id"]], "kickoff")
        # 2. nudges
        due = kickoff.nudge_due(engine)
        if due:
            msgs = [{"contact_id": a.id, "channel": "sms", "kind": "kickoff_nudge",
                     "body": self.drafter.nudge(engine.profile_get(a.id, aff=a), SENDER)} for a in due]
            out = self.send(msgs, "kickoff nudges")
            stats["nudges"] = len(out["sent"])
            self.totals["nudges_sent"] += len(out["sent"])
            self.samples["nudge"] = self.samples["nudge"] or (msgs[0]["body"] if out["sent"] else "")
            for cid in out["sent"]:
                self.respond(self.partners[cid], "nudge")
        # 3. the manager answers anyone who asked who they're texting with, personally (outside the agent)
        for when, cid in [x for x in self.personal if x[0] <= iso]:
            self.personal.remove((when, cid))
            p = self.partners[cid]
            for t in self.backend.list_tasks(cid):
                if not t.get("completed") and str(t.get("title", "")).startswith("Reply personally"):
                    self.backend.complete_task(cid, t["id"])
            self.backend.send_message(cid, "sms", f"Hey {p.first}, {SENDER} here, I read every one of these myself. "
                                                  "Happy to jump on a quick call anytime if that's easier.")
            self.samples["identity"].setdefault("manager_replied", iso)
            self.respond(p, "personal")
        # 4. partners' texts arrive (some send two in a row)
        arriving = [x for x in self.queue if x[0] <= iso]
        for item in arriving:
            self.queue.remove(item)
            self.backend.record_inbound(item[1], "sms", item[2])
            self.totals["texts_in"] += 1
        # 5. triage every conversation with something new, then reply in one approved batch
        replies, moves = [], {}
        rows = engine.reply_inbox(limit=2000)
        for row in rows:
            cid = row["contact"]["id"]
            p = self.partners[cid]
            result = engine.record_reply(cid, row["last_message"], message_ids=row["message_ids"])
            if result.get("duplicate"):
                self.totals["duplicates_skipped"] += 1
                continue
            p.replies += 1
            self.totals["replies_in"] += 1
            intent = result["intent"]
            if intent == "unsubscribe":
                self.totals["opt_outs"] += 1
                self.samples["stop"].append(row["last_message"])
                continue
            if intent == "identity_question":
                self.totals["identity_escalations"] += 1
                self.totals["manager_tasks"] += 1
                self.personal.append(((day + timedelta(days=1)).isoformat(), cid))
                if not self.samples["identity"]:
                    self.samples["identity"] = {"text": row["last_message"], "alert": result["manager_alert"],
                                                "actions": result["actions_taken"], "draft": "none (manager replies)"}
                continue
            if intent == "has_deal":
                self.totals["manager_tasks"] += 1
                p.deal_on = p.deal_on or (day + timedelta(days=self.rng.randint(1, 3))).isoformat()
            prof = engine.profile_get(cid)
            draft = self.drafter.reply(prof, SENDER, intent, row["last_message"])
            if not draft["body"]:
                continue
            move = draft["move"]
            moves[cid] = (move, (prof.get("next_question") or {}).get("slot", "") if move == "discover" else "")
            replies.append({"contact_id": cid, "channel": "sms", "kind": "reply", "body": draft["body"], "move": move})
            if len(self.samples["conversations"]) < 400:
                self.samples["conversations"].append({"cid": cid, "day": iso, "in": row["last_message"],
                                                      "intent": intent, "facts": result["facts_added"],
                                                      "move": move, "out": draft["body"]})
            if move in {"book", "confirm_time"}:
                p.call_on = (day + timedelta(days=self.rng.randint(1, 3))).isoformat()
                self.totals["calls_booked"] += 1
                brief = engine.pre_call_brief(cid, "first call since the kickoff")["brief"]
                self.samples["brief"] = self.samples["brief"] or brief
        # GoHighLevel sometimes keeps a handled conversation unread: flag some again and read the inbox twice
        for row in rows:
            if self.rng.random() < 0.1:
                for msg in self.backend.db["messages"]:
                    if msg["contactId"] == row["contact"]["id"] and msg["direction"] == "inbound":
                        msg["unread"] = True
                self.totals["relisted"] += 1
        self.totals["triaged_twice"] += len(engine.reply_inbox(limit=2000))
        if replies:
            out = self.send(replies, "conversation replies")
            stats["replies_sent"] = len(out["sent"])
            self.totals["replies_sent"] += len(out["sent"])
            for cid in out["sent"]:
                move, slot = moves[cid]
                self.totals["discovery_questions"] += move == "discover"
                self.totals["call_asks"] += move == "call_ask"
                self.respond(self.partners[cid], "reply", move, slot)
        # 6. calls happen, alternating phone (GoHighLevel transcription) and video (call inbox)
        for p in [p for p in self.partners.values() if p.call_on == iso and not p.called]:
            self.call(engine, p)
        # 7. deals arrive
        for p in [p for p in self.partners.values() if p.deal_on == iso]:
            engine.record_deal(p.cid, "submitted after the relationship kickoff (simulation)")
            self.totals["deals"] += 1
        self.backend.flush()
        g = engine.graph.stats()
        talking = [p for p in self.partners.values() if p.replies and p.persona not in {"stop"}]
        stats.update(avg_completeness=g["avg_completeness"], facts=g["facts"], calls=g["calls"],
                     plans=g["revenue_plans"], buckets=g["completeness_buckets"],
                     talking=len(talking),
                     avg_completeness_talking=round(sum(engine.graph.profile(engine.affiliate(p.cid), day)["completeness"]
                                                        for p in talking) / max(len(talking), 1), 1))
        self.timeline.append(stats)

    def call(self, engine: FamEngine, p: Partner) -> None:
        p.called = True
        self.totals["calls_held"] += 1
        t = p.truth
        convo = [
            (SENDER, f"Hey {p.first}, thanks for making time. Quick heads up, I record my calls so I don't lose track "
                     "of what we talk about. That okay?"),
            (p.first, "Totally fine."),
            (SENDER, "Tell me about your clients and what they usually need."),
            (p.first, f"{_say(self.rng, p, 'client_types')} {_say(self.rng, p, 'deal_types')} "
                      f"{_say(self.rng, p, 'deal_size')}"),
            (SENDER, "Where are most of them?"),
            (p.first, _say(self.rng, p, "regions")),
            (SENDER, "What's gotten in the way of sending deals?"),
            (p.first, f"{_say(self.rng, p, 'blockers')} {_say(self.rng, p, 'goals')}"),
            (SENDER, "What would make this worth your time?"),
            (p.first, _say(self.rng, p, "needs")),
            (SENDER, f"Done. I'll send you the submission link and a one-page program summary by Friday, and I'll "
                     f"check in next week."),
        ]
        if self.rng.random() < 0.5:
            convo.append((p.first, "Great. I'll send you a file for one of my clients tomorrow."))
            p.deal_on = p.deal_on or (self.day + timedelta(days=self.rng.randint(2, 6))).isoformat()
        convo.append((p.first, _say(self.rng, p, "best_time")))
        name = f"{p.first} {p.last}"
        if self.totals["calls_held"] % 2:
            self.totals["calls_phone"] += 1
            self.backend.record_call(p.cid, "outbound", 60 * self.rng.randint(12, 28),
                                     [{"sentenceIndex": i, "mediaChannel": 1 if who == SENDER else 2,
                                       "startTime": i * 8, "transcript": said} for i, (who, said) in enumerate(convo)])
            result = calls.poll_ghl(engine, contact_id=p.cid)["results"][0]
        else:
            self.totals["calls_video"] += 1
            inbox = self.settings.state_dir / "call-inbox"
            inbox.mkdir(exist_ok=True)
            (inbox / f"{p.cid}.json").write_text(json.dumps({
                "source": "recorder", "id": f"vid-{p.cid}", "start_time": f"{self.day.isoformat()}T15:00:00",
                "duration_minutes": self.rng.randint(15, 30),
                "participants": [{"name": SENDER}, {"name": name, "email": p.email}],
                "segments": [{"speaker": SENDER if who == SENDER else name, "start": i * 8, "text": said}
                             for i, (who, said) in enumerate(convo)]}))
            result = calls.poll_drop(engine, inbox)["results"][0]
        self.totals["commitments"] += len(result.get("commitments", []))
        self.totals["manager_tasks"] += sum(1 for c in result.get("commitments", []) if c["owner"] == "us")
        plan = engine.write_revenue_plan(p.cid, drafter=self.drafter)
        self.totals["revenue_plans"] += 1
        if not self.samples["call_note"]:
            notes = sorted((self.settings.vault_dir / "Calls").glob("*.md"))
            self.samples["call_note"] = notes[0].read_text() if notes else ""
            self.samples["plan"] = plan["plan"]


def _accuracy(sim: Sim, engine: FamEngine) -> dict[str, Any]:
    """Of the facts partners said out loud, how many reached their profile, and correctly."""
    out: dict[str, dict[str, int]] = {}
    for p in sim.partners.values():
        if not p.stated:
            continue
        values = engine.graph.profile(engine.affiliate(p.cid), sim.day)["values"]
        t = p.truth
        expect = {"client_types": [t["client"]], "deal_types": [t["need"][1], t["need2"][1]],
                  "deal_size": [f"${t['size']}k"], "regions": t["regions"], "goals": [t["goal"]],
                  "needs": [t["help"]] + [label for pat, label in extract.GROWTH if re.search(pat, t["help"])],
                  "channel": [t["channel"]], "best_time": [t["time"]], "blockers": [t["blocker"]]}
        for slot in p.stated:
            row = out.setdefault(slot, {"said": 0, "captured": 0, "correct": 0})
            row["said"] += 1
            got = values.get(slot, [])
            if got:
                row["captured"] += 1
                if any(e.lower() in v.lower() or v.lower() in e.lower() for e in expect[slot] for v in got):
                    row["correct"] += 1
    total = {k: sum(r[k] for r in out.values()) for k in ("said", "captured", "correct")}
    return {"by_slot": dict(sorted(out.items())), "total": total,
            "capture_rate": round(total["captured"] / max(total["said"], 1), 3),
            "correct_rate": round(total["correct"] / max(total["said"], 1), 3)}


def run(base: Settings, out: Path, start: date, days: int = 30, count: int = 250, seed: int = 21) -> dict[str, Any]:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    settings = replace(base, state_dir=out / "state", vault_dir=out / "vault", ghl_mode="mock", demo_mode=False,
                       kickoff={**base.kickoff, "calendar_link": CALENDAR, "default_sender": SENDER,
                                "send_pause_seconds": 0})
    settings.state_dir.mkdir(parents=True)
    sim = Sim(settings, out, start, days, count, seed)
    records, hidden = _records(count, start, sim.rng)
    imported = sources.import_records(sim.engine, records)
    for c in sim.backend.db["contacts"].values():
        h = hidden[c["email"]]
        sim.partners[c["id"]] = Partner(c["id"], c.get("firstName", ""), c.get("lastName", ""), c["email"],
                                        c.get("phone", ""), h["persona"], h["truth"], h["persona"],
                                        quiet_after=sim.rng.randint(2, 4) if h["persona"] == "warm" else 99)
    sim.backend.flush()
    start_stats = sim.engine.graph.stats()
    day0 = {cid: sim.engine.vault.partner_path(sim.engine.affiliate(cid).name, cid).read_text() for cid in sim.partners}
    for offset in range(days):
        sim.run_day(start + timedelta(days=offset))
    end = sim.engine
    # the sample partner: someone who talked and held a call, whose record came with notes
    talked = sorted((p for p in sim.partners.values() if p.called),
                    key=lambda p: (-len(p.stated), -end.affiliate(p.cid).deals_submitted, p.cid))
    sample = next((p for p in talked if "Onboarding call" in day0[p.cid]),
                  talked[0] if talked else next(iter(sim.partners.values())))
    sample_aff = end.affiliate(sample.cid)
    (out / "partners").mkdir()
    (out / "partners" / "before.md").write_text(day0[sample.cid])
    (out / "partners" / "after.md").write_text(end.vault.partner_path(sample_aff.name, sample.cid).read_text())
    personas: dict[str, int] = {}
    for p in sim.partners.values():
        personas[p.started_as] = personas.get(p.started_as, 0) + 1
    report = {
        "meta": {"partners": count, "days": days, "start": start.isoformat(), "seed": seed, "sender": SENDER,
                 "wave_size": WAVE, "drafter": sim.drafter.name, "extractor": sim.extractor.name,
                 "nudge_after_days": settings.kickoff["nudge_after_days"]},
        "import": imported, "graph_start": start_stats, "graph_end": end.graph.stats(),
        "totals": sim.totals, "variants": end.graph.variant_stats(), "accuracy": _accuracy(sim, end),
        "kickoff_status": {k: v for k, v in kickoff.status(end).items() if k != "waves"},
        "personas": dict(sorted(personas.items())),
        "sample_partner": {"name": sample_aff.name, "contact_id": sample.cid, "persona": sample.persona,
                           "before": day0[sample.cid],
                           "after": end.vault.partner_path(sample_aff.name, sample.cid).read_text(),
                           "conversation": [c for c in sim.samples["conversations"] if c["cid"] == sample.cid]},
        "samples": {k: v for k, v in sim.samples.items() if k != "conversations"},
        "timeline": sim.timeline,
        "assumptions": {
            "personas (share of partners)": ", ".join(f"{k} {v}%" for k, v in PERSONAS),
            "replies": "written from each partner's hidden truth; some phrasings are ones the keyword rules miss",
            "drafting": "framework templates and keyword rules (no model); the live agent drafts with the model",
            "manager": "approves every batch (simulated); holds one kickoff back in wave 1 to edit it",
            "calls": "every booked call happens 1-3 days later; odd calls by phone, even calls by video recorder",
            "variants": "a synthetic partner's reply does not depend on the kickoff wording, so the variant table "
                        "shows the tracking works, not which copy wins; real replies decide that",
        },
    }
    (out / "report.json").write_text(json.dumps(report, indent=2, default=str))
    (out / "report.md").write_text(_markdown(report))
    return report


def _markdown(r: dict[str, Any]) -> str:
    t, m, g0, g1, acc = r["totals"], r["meta"], r["graph_start"], r["graph_end"], r["accuracy"]
    last = r["timeline"][-1]
    lines = [
        f"# Relationship simulation: {m['partners']} quiet partners, {m['days']} days",
        "",
        f"Synthetic partners imported from Zoho-style records, then run day by day through the real engine from "
        f"{m['start']}: kickoff waves of {m['wave_size']}, one nudge after {m['nudge_after_days']} days, replies, "
        "calls, revenue plans. Every message was approved by a (simulated) manager. No one was contacted.",
        "",
        "## The graph",
        "",
        "| | Day 0 (records only) | Day " + str(m["days"]) + " |",
        "|---|---:|---:|",
        f"| Average profile completeness, all partners | {g0['avg_completeness']}% | {g1['avg_completeness']}% |",
        f"| Average completeness, partners who wrote back | n/a | {last['avg_completeness_talking']}% |",
        f"| Facts in the graph | {g0['facts']:,} | {g1['facts']:,} |",
        f"| Links to hub notes (tier, niche, manager, source, product) | {g0['hub_links']:,} | {g1['hub_links']:,} |",
        f"| Calls on file | {g0['calls']} | {g1['calls']} |",
        f"| Revenue plans | {g0['revenue_plans']} | {g1['revenue_plans']} |",
        "",
        "Facts by where they came from: " + ", ".join(f"{SOURCE_LABELS.get(k, k)} {v}"
                                                      for k, v in sorted(g1["facts_by_source"].items())),
        "",
        "## What happened",
        "",
        "| | Count |",
        "|---|---:|",
    ]
    labels = [("kickoffs_sent", "Kickoff texts sent"), ("kickoffs_held_back", "Kickoffs the reviewer held back"),
              ("nudges_sent", "Nudges"), ("texts_in", "Texts from partners"),
              ("replies_in", "Conversations triaged (several texts in a row count once)"),
              ("replies_sent", "Our replies sent"), ("discovery_questions", "Discovery questions asked"),
              ("call_asks", "Call asks"), ("calls_booked", "Calls booked"),
              ("calls_held", "Calls held and ingested"), ("calls_phone", "  by phone (GoHighLevel transcript)"),
              ("calls_video", "  by video (recorder export in the call inbox)"),
              ("commitments", "Commitments pulled from calls"), ("revenue_plans", "Revenue plans written"),
              ("deals", "Deals submitted"), ("opt_outs", "Opt-outs honored"),
              ("identity_escalations", "\"Is this a bot?\" handed to the manager"),
              ("drafts_blocked", "Drafts the engine refused")]
    lines += [f"| {label} | {t[k]:,} |" for k, label in labels]
    lines += ["", "## Kickoff variants", "", "| Variant | Sent | Replied | Calls | Reply rate |",
              "|---|---:|---:|---:|---:|"]
    lines += [f"| {k} | {v['sent']} | {v['replied']} | {v['calls']} | {v['reply_rate']:.0%} |"
              for k, v in r["variants"].items()]
    lines += ["", "## How much of what partners said reached their profile", "",
              f"Keyword rules only (the live agent extracts with the model): **{acc['capture_rate']:.0%}** of stated "
              f"facts captured, **{acc['correct_rate']:.0%}** captured correctly.", "",
              "| Slot | Said | Captured | Correct |", "|---|---:|---:|---:|"]
    lines += [f"| {k} | {v['said']} | {v['captured']} | {v['correct']} |" for k, v in acc["by_slot"].items()]
    lines += ["", "## Sample kickoffs", ""]
    lines += [f"- **{k}** ({v['segments']} segments): {v['body']}" for k, v in sorted(r["samples"]["kickoffs"].items())]
    lines += ["", f"Nudge: {r['samples']['nudge']}", "", "## Sample partner", "",
              f"{r['sample_partner']['name']} ({r['sample_partner']['persona']}). Notes before and after are in "
              "partners/before.md and partners/after.md.", ""]
    for c in r["sample_partner"]["conversation"]:
        lines += [f"- {c['day']} **them:** {c['in']}",
                  f"  - triage: {c['intent']}; facts: {', '.join(f['slot'] for f in c['facts']) or 'none'}",
                  f"  - **us** ({c['move']}): {c['out']}"]
    if r["samples"]["identity"]:
        i = r["samples"]["identity"]
        lines += ["", "## \"Is this a bot?\"", "", f"- They wrote: {i.get('text')}",
                  f"- Agent: {'; '.join(i.get('actions', []))}. Draft: {i.get('draft')}",
                  f"- Manager replied personally on {i.get('manager_replied', 'n/a')}"]
    lines += ["", "## Assumptions", ""] + [f"- {k}: {v}" for k, v in r["assumptions"].items()] + [""]
    return "\n".join(lines)
