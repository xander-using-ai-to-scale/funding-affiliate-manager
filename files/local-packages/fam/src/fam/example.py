"""One partner's journey through the relationship graph, run through the real code and frozen to disk.

    fam example partner-journey --out examples/partner-journey [--model]

Dana Reyes is fictional. Her Zoho-style record, her texts and the call transcript are written for this
example; everything the system produces from them (the profile, the kickoff text, our replies, the facts,
the call note, the tasks, the revenue plan) comes from the same code the agent runs, against a mock CRM
and a separate vault. With --model, drafting and extraction use FAM_DRAFT_MODEL through OpenRouter;
without it, the framework templates and keyword rules (deterministic).

Output: steps.json (each step's inputs, outputs, profile snapshot and graph), notes/step-N.md (the
partner note after each step), vault/ (the whole Obsidian vault), and the call file it ingested.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from . import calls, drafting, extract, kickoff, sources
from .config import Settings
from .engine import FamEngine
from .ghl import MockGHL

START = date(2026, 10, 5)
SENDER = "Justin"
CALENDAR = "https://example.com/book/justin"
RECORD = sources.SourceRecord(
    source="zoho", external_id="ZX-10482", first_name="Dana", last_name="Reyes",
    email="dana.reyes@example.com", phone="+15555550142",
    fields={"tier": "Executive", "plan": "Executive Partner, annual", "join_date": "2023-04-11",
            "source": "linkedin", "niche": "business consultant", "deals_submitted": 7,
            "last_deal_date": "2025-06-18", "last_contact_date": "2025-11-02", "assigned_manager": SENDER},
    history=[
        {"id": "n1", "date": "2023-04-12", "kind": "zoho_note",
         "text": "Onboarding call. Dana consults for small trucking and logistics companies. Mostly work with "
                 "owner-operators who are growing their fleets."},
        {"id": "d1", "date": "2024-08-20", "kind": "zoho_deal", "text": "Lone Star Freight, equipment (funded)"},
        {"id": "d2", "date": "2025-06-18", "kind": "zoho_deal", "text": "Ramirez Hauling, working capital (funded)"},
        {"id": "n2", "date": "2025-11-02", "kind": "zoho_note",
         "text": "Dana asked how to find the new partner portal. Said things got slow after summer."},
    ])
REPLIES = [
    (1, "Hey Justin! Good to hear from you. Honestly it's been a slow year on my end. Most of my clients are small "
        "trucking companies and they always need equipment, usually around $150k. Texting is best, mornings."),
    (2, "I want to get back to sending a couple deals a month. What would help is a simple page I can send my "
        "clients to so they can apply."),
    (2, "Sure, Thursday morning works."),
]
CALL = {
    "source": "readai", "id": "rai-7f3c2", "title": "Dana Reyes x Justin, partner call",
    "start_time": "2026-10-08T10:00:00", "duration_minutes": 24,
    "participants": [{"name": "Justin", "email": "justin@example.com"},
                     {"name": "Dana Reyes", "email": "dana.reyes@example.com"}],
    "transcript": {"speaker_blocks": [
        {"speaker": {"name": "Justin"}, "start_time": 0, "words": "Hey Dana, thanks for making time. Quick heads up, I "
         "record my calls so I don't lose track of what we talk about. That okay?"},
        {"speaker": {"name": "Dana Reyes"}, "start_time": 9, "words": "Totally fine."},
        {"speaker": {"name": "Justin"}, "start_time": 12, "words": "Great. So tell me where things are at."},
        {"speaker": {"name": "Dana Reyes"}, "start_time": 16, "words": "So most of my clients are small trucking "
         "companies and a few logistics outfits, mostly in Texas and Oklahoma. They grow in spurts, so it's "
         "usually equipment, a truck or two at a time, or working capital to cover payroll in a slow month."},
        {"speaker": {"name": "Justin"}, "start_time": 41, "words": "What size deals are we usually talking?"},
        {"speaker": {"name": "Dana Reyes"}, "start_time": 45, "words": "Trucks run $100k to $250k, so usually "
         "around $150k."},
        {"speaker": {"name": "Justin"}, "start_time": 52, "words": "And what got in the way of sending deals this "
         "year?"},
        {"speaker": {"name": "Dana Reyes"}, "start_time": 57, "words": "Honestly I haven't sent any because the "
         "portal changed and I didn't know who to call anymore. And it was a slow summer."},
        {"speaker": {"name": "Justin"}, "start_time": 70, "words": "That's on us. I'm your person now, text me "
         "anytime."},
        {"speaker": {"name": "Dana Reyes"}, "start_time": 76, "words": "My goal is to get back to two deals a month "
         "by the end of the year. I'd love to have a simple page I can put in my email signature so clients can "
         "apply without me in the middle."},
        {"speaker": {"name": "Justin"}, "start_time": 95, "words": "We can do that. I'll set up a funnel page draft "
         "for you next week, and I'll send you the new submission link and the equipment program summary by "
         "Friday."},
        {"speaker": {"name": "Dana Reyes"}, "start_time": 110, "words": "Perfect. Actually I have one now, Martinez "
         "Trucking needs two trucks. I'll send you the file tomorrow."},
        {"speaker": {"name": "Justin"}, "start_time": 121, "words": "Love it. I'll watch for it."},
        {"speaker": {"name": "Dana Reyes"}, "start_time": 125, "words": "Mornings are best to reach me, I'm on the "
         "road most afternoons."},
    ]},
}


def _graph(engine: FamEngine, contact_id: str, p: dict[str, Any]) -> dict[str, Any]:
    """The partner's corner of the graph: hubs, facts, calls and open loops linked to her."""
    nodes = [{"id": "partner", "label": p["name"], "type": "partner"}]
    links = []
    with engine.store.connection() as conn:
        for r in conn.execute("SELECT hub_type, hub FROM edges WHERE contact_id = ? ORDER BY hub_type, hub",
                              (contact_id,)):
            nid = f"hub:{r['hub_type']}:{r['hub']}"
            nodes.append({"id": nid, "label": r["hub"], "type": f"hub-{r['hub_type']}"})
            links.append({"source": "partner", "target": nid})
    labels = {k: s.get("label", k) for k, s in engine.graph.slots.items()}
    for f in p["facts"]:
        if f["slot"] in {"tier", "niche", "open_loop"}:
            continue
        nid = f"fact:{f['id']}"
        nodes.append({"id": nid, "label": f["value"], "type": "fact", "slot": labels.get(f["slot"], f["slot"]),
                      "source": f["source_type"]})
        links.append({"source": "partner", "target": nid})
    for loop in p["open_loops"]:
        nid = f"loop:{loop['id']}"
        nodes.append({"id": nid, "label": loop["text"], "type": "loop"})
        links.append({"source": "partner", "target": nid})
    for i, call in enumerate(engine.graph.interactions(contact_id, ["call"])):
        nid = f"call:{i}"
        nodes.append({"id": nid, "label": f"Call {call['at']}", "type": "call"})
        links.append({"source": "partner", "target": nid})
    return {"nodes": nodes, "links": links}


def _snapshot(engine: FamEngine, contact_id: str) -> dict[str, Any]:
    aff = engine.affiliate(contact_id)
    p = engine.profile_get(contact_id, aff=aff)
    note = engine.vault.partner_path(aff.name, aff.id).read_text()
    keep = ("completeness", "summary", "values", "open_loops", "next_question", "next_step", "revenue_plan",
            "filled_slots", "tier", "joined", "deals", "manager", "kickoff")
    return {"profile": {k: p.get(k) for k in keep},
            "facts": [{k: f[k] for k in ("slot", "value", "source_type", "observed_on")} for f in p["facts"]],
            "graph": _graph(engine, contact_id, p), "note": note,
            "ghl_fields": {k: aff.fields.get(k) for k in ("tier", "profile_completeness", "next_step",
                                                           "profile_summary", "obsidian_note")}}


def _approve_and_send(engine: FamEngine, action_id: str, digest: str) -> dict[str, Any]:
    engine.approve(action_id, digest, SENDER)
    return engine.execute(action_id)


def partner_journey(base: Settings, out: Path, use_model: bool = False) -> dict[str, Any]:
    if out.exists():
        shutil.rmtree(out)
    (out / "notes").mkdir(parents=True)
    settings = replace(base, state_dir=out / "state", vault_dir=out / "vault", ghl_mode="mock", demo_mode=False,
                       kickoff={**base.kickoff, "calendar_link": CALENDAR, "default_sender": SENDER,
                                "send_pause_seconds": 0})
    settings.state_dir.mkdir(parents=True)
    backend = MockGHL(settings.state_dir / "mock-ghl.json")
    drafter = drafting.open_drafter(settings.kickoff, use_model=use_model)
    extractor = extract.open_extractor([s["key"] for s in settings.profile_schema["slots"]], use_model=use_model)
    steps: list[dict[str, Any]] = []

    def engine_on(day: date) -> FamEngine:
        backend.now_override = f"{day.isoformat()}T15:00:00+00:00"
        e = FamEngine(settings=settings, backend=backend, today=day)
        e.extractor = extractor
        return e

    def step(n: int, title: str, day: date, engine: FamEngine, cid: str, **data: Any) -> None:
        snap = _snapshot(engine, cid)
        (out / "notes" / f"step-{n}.md").write_text(snap["note"])
        steps.append({"n": n, "title": title, "day": day.isoformat(), **data, **snap})

    # 1. The record, before anyone texts her
    day = START
    engine = engine_on(day)
    imported = sources.import_records(engine, [RECORD])
    cid = backend.search_contacts(query=RECORD.email, limit=1)[0]["id"]
    step(1, "The record becomes a profile", day, engine, cid, input={"record": {
        "source": "Zoho (synthetic)", "fields": RECORD.fields, "history": RECORD.history}}, output=imported)

    # 2. The kickoff text, reviewed and sent
    wave = kickoff.draft_wave(engine, 1, drafter=drafter)
    action = wave["action"]
    review = Path(action["review_file"]).read_text()
    sent = _approve_and_send(engine, action["action_id"], action["action_digest"])
    step(2, "The kickoff text", day, engine, cid, output={
        "draft": wave["drafts"][0], "approval_card": action["approval_card"],
        "review_file": re.sub(r"^---.*?---\n", "", review, flags=re.S), "sent": {k: sent[k] for k in ("mock", "live")}})

    # 3-5. The conversation
    for n, (offset, text) in enumerate(REPLIES, 3):
        day = START + timedelta(days=offset)
        engine = engine_on(day)
        backend.record_inbound(cid, "sms", text)
        inbox = next(r for r in engine.reply_inbox(limit=50) if r["contact"]["id"] == cid)
        result = engine.record_reply(cid, inbox["last_message"], message_ids=inbox["message_ids"])
        p = engine.profile_get(cid)
        draft = drafter.reply(p, SENDER, result["intent"], inbox["last_message"])
        out_msg: dict[str, Any] = {"triage": {k: result[k] for k in ("intent", "actions_taken", "facts_added",
                                                                   "completeness", "manager_alert")},
                                   "reply": draft}
        if draft["body"]:
            prepared = engine.prepare_messages([{"contact_id": cid, "channel": "sms", "body": draft["body"],
                                                 "kind": "reply"}], purpose="conversation replies")
            engine.request_approval(prepared["action_id"])
            _approve_and_send(engine, prepared["action_id"], prepared["action_digest"])
        if draft.get("move") == "book":
            out_msg["pre_call_brief"] = engine.pre_call_brief(cid, "first call since the kickoff")["brief"]
        title = {3: "Her first reply", 4: "What she wants", 5: "She books a call"}[n]
        step(n, title, day, engine, cid, input={"text": text}, output=out_msg)

    # 6. The call, recorded and transcribed by her video recorder, lands in the call inbox
    day = START + timedelta(days=3)
    engine = engine_on(day)
    inbox = out / "state" / "call-inbox"
    inbox.mkdir()
    (inbox / "dana-reyes-2026-10-08.json").write_text(json.dumps(CALL, indent=2))
    (out / "call-transcript.json").write_text(json.dumps(CALL, indent=2))
    polled = calls.poll_drop(engine, inbox)
    call_note = next((out / "vault" / "Calls").glob("*.md")).read_text()
    tasks = [{"title": t["title"], "due": t["dueDate"][:10]} for t in backend.list_tasks(cid) if not t.get("completed")]
    step(6, "The call", day, engine, cid, input={"transcript": CALL["transcript"]["speaker_blocks"],
                                                 "recorder": "Read.ai-style export (synthetic)"},
         output={"ingest": polled["results"][0], "call_note": re.sub(r"^---.*?---\n", "", call_note, flags=re.S),
                 "open_tasks": tasks})

    # 7. The revenue plan
    plan = engine.write_revenue_plan(cid, drafter=drafter)
    step(7, "Her revenue plan", day, engine, cid, output={"plan": plan["plan"]})

    usage = {who: dict(getattr(getattr(obj, "client", None), "usage", None) or {}) for who, obj in
             (("drafting", drafter), ("extraction", extractor)) if getattr(obj, "client", None)}
    meta = {"partner": "Dana Reyes (fictional)", "start": START.isoformat(), "drafter": drafter.name,
            "extractor": extractor.name, "model": getattr(getattr(drafter, "client", None), "model", ""),
            "model_usage": usage or None, "steps": len(steps),
            # times the framework template or the keyword rules stood in because a model answer failed a check
            "fallbacks": {"drafting": list(getattr(drafter, "fallbacks", [])),
                          "extraction": list(getattr(extractor, "fallbacks", []))}}
    (out / "steps.json").write_text(json.dumps({"meta": meta, "steps": steps}, indent=2, default=str))
    return {"ok": True, "out": str(out), **meta,
            "completeness": [s["profile"]["completeness"] for s in steps]}
