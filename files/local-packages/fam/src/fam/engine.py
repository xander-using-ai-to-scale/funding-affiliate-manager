"""The Funding Affiliate Manager operating core.

Three kinds of work, three levels of trust:

  READ            sweep, briefs, queues, reply inbox, scorecard       — always allowed
  CRM HYGIENE     lifecycle tags, notes, follow-up tasks, date fields — autonomous, audited, capped
  OUTBOUND        messages, workflow enrollments, broadcasts          — frozen, digested, approved once

Outbound follows the funding-director pattern: prepare (freeze + digest) ->
request approval (card for the manager) -> approve (ONLY via the untrusted
approvals MCP, so Hermes asks the human) -> execute (consumes the approval once).
Recurring bulk cadence can run under a bounded, expiring standing approval.

Demo mode (FAM_DEMO_MODE=1, the default): only contacts tagged `fam:test-contact`
receive real messages or enrollments. Everyone else is a simulated send, written to the
contact as a GHL note so the demo shows exactly what would have gone out.
"""

from __future__ import annotations

import os
import re
import secrets
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from . import cadence
from .cadence import Affiliate, affiliate_from_contact
from .config import Settings
from .errors import ApprovalRequired, FamError
from .ghl import GHLBackend, open_backend
from .store import Store, digest, now_iso, stable_json
from .vault import Vault

BANNED_PHRASES = (
    "guarantee",
    "100% approval",
    "no credit check",
    "instant approval",
    "risk-free",
    "risk free",
    "get rich",
    "can't lose",
    "cannot lose",
)
SERVICES = {"funnel", "reactivation", "email_campaigns", "social", "crm_help"}
MANAGER_TASK_PREFIXES = ("CALL ", "Answer ", "Scope ")  # human work; a sent touch never closes these
MANAGER_TASK_MARK = "[For the manager]"
SERVICE_LABELS = {"funnel": "a funnel page", "reactivation": "lead reactivation", "email_campaigns": "email campaigns",
                  "social": "social content", "crm_help": "CRM help"}
BULK_WORKFLOW_KEYS = {"onboarding", "biweekly_touch", "monthly_offer", "dormant_reactivation",
                      "dead_reactivation", "newsletter", "event_invite", "new_offer"}
STANDING_ALLOWED = {"onboarding", "biweekly_touch", "monthly_offer", "dormant_reactivation", "dead_reactivation"}
OFFER_KINDS = {"monthly_offer", "new_offer"}
LIFECYCLE_STAGE = {
    "aff:applied": "applied",
    "aff:onboarding": "onboarded",
    "aff:active": "active",
    "aff:producing": "producing",
    "aff:quiet": "quiet",
    "aff:dormant": "dormant",
    "aff:dead": "dormant",
    "aff:reactivated": "reactivated",
}


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(6)}"


class FamEngine:
    def __init__(self, settings: Settings | None = None, backend: GHLBackend | None = None,
                 today: date | None = None):
        self.settings = settings or Settings.load()
        self.ghl = backend or open_backend(self.settings)
        self.store = Store(self.settings.state_dir / "fam.sqlite3")
        self.tz = ZoneInfo(self.settings.cadence["timezone"])
        self.vault = Vault(self.settings.vault_dir, self.settings.cadence["timezone"])
        self._today = today
        self.actor = os.getenv("FAM_ACTOR", "funding-affiliate-manager")

    # ── clock ────────────────────────────────────────────────────────────────
    def today(self) -> date:
        return self._today or datetime.now(self.tz).date()

    def _local_hour(self) -> int:
        return datetime.now(self.tz).hour

    # ── status ───────────────────────────────────────────────────────────────
    def status(self) -> dict[str, Any]:
        s = self.settings
        result: dict[str, Any] = {
            "ghl_mode": s.ghl_mode,
            "demo_mode": s.demo_mode,
            "ghl_profile": s.profile or "(unset)",
            "configured_location_id": s.ghl_map.get("location_id", ""),
            "custom_fields_mapped": len(s.field_ids()),
            "workflows_mapped": sorted(k for k, v in s.ghl_map.get("workflows", {}).items() if v),
            "external_writes_enabled": self.store.get_flag("external_writes_enabled", "true") == "true",
            "stop_reason": self.store.get_flag("stop_reason", ""),
            "today": self.today().isoformat(),
            "sent_today": {
                "personal_messages": self.store.count(self.today().isoformat(), "personal_messages"),
                "enrollments": self.store.count(self.today().isoformat(), "enrollments"),
            },
            "pending_approvals": len(self.store.list_actions("approval_requested")),
            "standing_approvals": [r for r in self.store.list_standing() if not r["revoked_at"]],
            "vault": str(s.vault_dir),
        }
        try:
            location = self.ghl.location()
            result["ghl_connected"] = True
            result["ghl_location_name"] = location.get("name", "")
        except FamError as exc:
            result["ghl_connected"] = False
            result["ghl_error"] = str(exc)
        return result

    # ── reads ────────────────────────────────────────────────────────────────
    def affiliates(self, tags: list[str] | None = None, query: str = "", limit: int = 20000) -> list[Affiliate]:
        field_ids = self.settings.field_ids()
        out: list[Affiliate] = []
        page = 1
        while len(out) < limit:
            batch = self.ghl.search_contacts(query=query, tags=tags, limit=min(500, limit - len(out)), page=page)
            out.extend(affiliate_from_contact(c, field_ids) for c in batch)
            if len(batch) < 500:
                break
            page += 1
        return out

    def affiliate(self, contact_id: str) -> Affiliate:
        return affiliate_from_contact(self.ghl.get_contact(contact_id), self.settings.field_ids())

    def sweep(self, apply_lifecycle: bool = False, detail_limit: int = 25) -> dict[str, Any]:
        affiliates = self.affiliates()
        plan = cadence.sweep(affiliates, self.today(), self.settings.cadence)
        applied = 0
        if apply_lifecycle:
            by_id = {a.id: a for a in affiliates}
            for change in plan["lifecycle_changes"]:
                self._apply_lifecycle(by_id[change["contact_id"]], change["to"], "daily sweep")
                applied += 1
        plan["lifecycle_applied"] = applied
        self.vault.log(
            "Daily sweep",
            f"- affiliates: {plan['total_affiliates']}\n- cohorts: {plan['cohorts']}\n"
            f"- silent 30+: {plan['silent_30_plus']} · silent 90+: {plan['silent_90_plus']}\n"
            f"- personal touches due: {len(plan['personal_queue'])} (+{plan['personal_overflow']} overflow)\n"
            f"- bulk due: {plan['bulk_counts']}\n- lifecycle changes applied: {applied}",
            day=self.today().isoformat(),
        )
        self.store.audit(actor=self.actor, action="sweep", resource=self.today().isoformat(),
                         decision="read", result="ok",
                         details={"cohorts": plan["cohorts"], "applied": applied})
        if detail_limit >= 0:
            plan["personal_queue"] = plan["personal_queue"][:detail_limit]
            plan["bulk_queue"] = {k: v[:detail_limit] for k, v in plan["bulk_queue"].items()}
        return plan

    def affiliate_brief(self, contact_id: str) -> dict[str, Any]:
        aff = self.affiliate(contact_id)
        ev = cadence.evaluate(aff, self.today(), self.settings.cadence)
        notes = self.ghl.list_notes(contact_id)[-10:]
        tasks = [t for t in self.ghl.list_tasks(contact_id) if not t.get("completed")]
        messages: list[dict[str, Any]] = []
        for conv in self.ghl.list_conversations(contact_id=contact_id, limit=3):
            for m in self.ghl.list_messages(conv["id"], limit=10):
                messages.append({"direction": m.get("direction"), "type": m.get("messageType"),
                                 "date": m.get("dateAdded"), "body": (m.get("body") or "")[:500]})
        messages.sort(key=lambda m: m.get("date") or "", reverse=True)
        return {
            "affiliate": aff.summary(),
            "email": aff.email,
            "phone": aff.phone,
            "tags": aff.tags,
            "fields": aff.fields,
            "days_silent": ev.days_silent,
            "days_since_touch": ev.days_since_touch,
            "target_lifecycle": ev.target_lifecycle,
            "due_today": [d.to_dict() for d in ev.due],
            "open_tasks": tasks,
            "recent_notes": notes,
            "recent_messages": messages[:10],
            "drafting_rules": "Use knowledge/funding/05-conversation-playbook.md. Short, warm, peer-to-peer. "
                              "No guaranteed approvals, rates, or income claims.",
        }

    def daily_queue(self) -> dict[str, Any]:
        plan = self.sweep(apply_lifecycle=False, detail_limit=-1)
        queue = []
        for item in plan["personal_queue"]:
            open_tasks = [t for t in self.ghl.list_tasks(item["contact_id"]) if not t.get("completed")]
            queue.append({**item, "open_tasks": [{"id": t["id"], "title": t.get("title"),
                                                  "due": t.get("dueDate")} for t in open_tasks]})
        return {"date": plan["date"], "personal_queue": queue, "overflow": plan["personal_overflow"],
                "bulk_counts": plan["bulk_counts"]}

    def reply_inbox(self, limit: int = 25) -> list[dict[str, Any]]:
        rows = []
        for conv in self.ghl.list_conversations(unread_only=True, limit=limit):
            if conv.get("lastMessageDirection") not in (None, "", "inbound"):
                continue
            contact_id = conv.get("contactId", "")
            text = conv.get("lastMessageBody") or ""
            try:
                aff = self.affiliate(contact_id)
                who = aff.summary()
            except FamError:
                who = {"id": contact_id}
            rows.append({"contact": who, "conversation_id": conv.get("id"), "last_message": text[:600],
                         "received": conv.get("lastMessageDate"), "baseline": cadence.classify_reply(text)})
        return rows

    # ── CRM hygiene (autonomous, audited) ─────────────────────────────────────
    def _set_fields(self, contact_id: str, values: dict[str, Any]) -> None:
        payload = [{"id": self.settings.field_id(k), "field_value": v} for k, v in values.items()]
        self.ghl.update_contact(contact_id, {"customFields": payload})

    def _apply_lifecycle(self, aff: Affiliate, lifecycle: str, reason: str) -> None:
        if lifecycle not in cadence.LIFECYCLE_TAGS:
            raise FamError(f"unknown lifecycle tag {lifecycle}")
        stale = [t for t in aff.tags if t in cadence.LIFECYCLE_TAGS and t != lifecycle]
        if stale:
            self.ghl.remove_tags(aff.id, stale)
        self.ghl.add_tags(aff.id, [lifecycle])
        self._sync_lifecycle_stage(aff, lifecycle)
        self.vault.affiliate(aff.name, aff.id, f"lifecycle {aff.lifecycle or '—'} → {lifecycle} ({reason})",
                             source=aff.source, lifecycle=lifecycle, day=self.today().isoformat())
        self.store.audit(actor=self.actor, action="lifecycle.set", resource=aff.id, decision="autonomous",
                         result="ok", details={"from": aff.lifecycle, "to": lifecycle, "reason": reason})

    def _sync_lifecycle_stage(self, aff: Affiliate, lifecycle: str) -> None:
        try:
            pipeline = self.settings.pipeline("lifecycle")
        except FamError:
            return  # pipeline not built yet; tags remain the source of truth
        stage_key = LIFECYCLE_STAGE.get(lifecycle, "")
        stage_id = pipeline.get("stages", {}).get(stage_key, "")
        if stage_id:
            self.ghl.upsert_opportunity(pipeline_id=pipeline["id"], stage_id=stage_id, contact_id=aff.id,
                                        name=f"{aff.name} — affiliate")

    def set_lifecycle(self, contact_id: str, lifecycle: str, reason: str) -> dict[str, Any]:
        aff = self.affiliate(contact_id)
        self._apply_lifecycle(aff, lifecycle, reason)
        return {"ok": True, "contact_id": contact_id, "lifecycle": lifecycle}

    def add_note(self, contact_id: str, body: str) -> dict[str, Any]:
        if not body.strip():
            raise FamError("note body is empty")
        note = self.ghl.add_note(contact_id, body.strip())
        aff = self.affiliate(contact_id)
        self.vault.affiliate(aff.name, aff.id, f"note: {body.strip()[:200]}", day=self.today().isoformat())
        self.store.audit(actor=self.actor, action="note.add", resource=contact_id, decision="autonomous",
                         result="ok", details={"chars": len(body)})
        return {"ok": True, "note_id": note.get("id", "")}

    def schedule_followup(self, contact_id: str, due_date: str, note: str, title: str = "",
                          customer_touch: bool = True) -> dict[str, Any]:
        """A GHL task on the contact. customer_touch=True is a "check back with me" promise: it also sets
        next_touch_date/cadence_note so the agent drafts a touch that morning. False is internal work for
        the human (call, answer, scope) and never feeds an outbound message."""
        due = cadence.parse_day(due_date)
        if not due:
            raise FamError("due_date must be YYYY-MM-DD")
        if due < self.today():
            raise FamError("due_date is in the past")
        aff = self.affiliate(contact_id)
        assignee = self.settings.ghl_map.get("users", {}).get("manager", "")
        task = self.ghl.create_task(
            contact_id,
            title or f"Follow up with {aff.first_name} — {note[:60]}",
            datetime.combine(due, datetime.min.time(), self.tz).replace(hour=10).astimezone(UTC).isoformat(),
            body=note if customer_touch else f"{MANAGER_TASK_MARK} {note}",
            assigned_to=assignee,
        )
        if customer_touch:
            self._set_fields(contact_id, {"next_touch_date": due.isoformat(), "cadence_note": note[:250]})
            self.ghl.add_note(contact_id, f"Follow-up scheduled for {due.isoformat()}: {note}")
        else:
            self.ghl.add_note(contact_id, f"Task for the manager, due {due.isoformat()}: {note}")
        self.vault.affiliate(aff.name, aff.id, f"follow-up set for [[Daily/{due.isoformat()}]] — {note}",
                             day=self.today().isoformat())
        self.store.audit(actor=self.actor, action="followup.schedule", resource=contact_id,
                         decision="autonomous", result="ok", details={"due": due.isoformat()})
        return {"ok": True, "task_id": task.get("id", ""), "due": due.isoformat()}

    def queue_growth_service(self, contact_id: str, service: str, note: str = "") -> dict[str, Any]:
        if service not in SERVICES:
            raise FamError(f"service must be one of {sorted(SERVICES)}")
        aff = self.affiliate(contact_id)
        self.ghl.add_tags(contact_id, [f"want:{service.replace('_', '-')}"])
        opp: dict[str, Any] = {}
        try:
            pipeline = self.settings.pipeline("services")
            stage_id = pipeline.get("stages", {}).get("interested", "")
            if stage_id:
                opp = self.ghl.upsert_opportunity(pipeline_id=pipeline["id"], stage_id=stage_id,
                                                  contact_id=contact_id,
                                                  name=f"{aff.name} — {service.replace('_', ' ')}")
        except FamError:
            pass
        label = SERVICE_LABELS.get(service, service.replace("_", " "))
        self.schedule_followup(contact_id, self.today().isoformat(), f"Scope {label} for {aff.name}. {note}",
                               title=f"Scope {label} for {aff.first_name}", customer_touch=False)
        self.vault.log("Growth service queued", f"- {self.vault.affiliate_link(aff.name, aff.id)} wants **{label}**"
                       f" {('— ' + note) if note else ''}", day=self.today().isoformat())
        return {"ok": True, "service": service, "opportunity_id": opp.get("id", "")}

    def record_reply(self, contact_id: str, text: str, intent: str = "", follow_up_date: str = "",
                     summary: str = "") -> dict[str, Any]:
        """Apply the outcome of one inbound reply to the CRM. The model passes its own intent;
        the keyword baseline fills in when it doesn't, and STOP is always honored."""
        aff = self.affiliate(contact_id)
        baseline = cadence.classify_reply(text)
        if baseline["intent"] == "unsubscribe":
            intent = "unsubscribe"
        intent = intent or baseline["intent"]
        today = self.today()
        taken: list[str] = []
        self._set_fields(contact_id, {"last_reply_date": today.isoformat()})
        taken.append("last_reply_date=today")
        alert = ""
        if intent == "unsubscribe":
            self.ghl.add_tags(contact_id, [cadence.DNC_TAG])
            self.ghl.update_contact(contact_id, {"dnd": True})
            self.ghl.add_note(contact_id, f"Opted out: {text[:200]}")
            taken.append("DNC + dnd set")
            alert = f"{aff.name} opted out. No further outreach."
        else:
            was, _ = cadence.target_lifecycle(aff, today, self.settings.cadence)
            if aff.lifecycle in {"aff:quiet", "aff:dormant", "aff:dead"} or was in {"aff:quiet", "aff:dormant",
                                                                                    "aff:dead"}:
                self._apply_lifecycle(aff, "aff:reactivated", f"replied: {intent}")
                taken.append("lifecycle → aff:reactivated")
            self.ghl.add_note(contact_id, f"Reply ({intent}): {summary or text[:400]}")
            if intent == "has_deal":
                self.ghl.add_tags(contact_id, ["deal:incoming"])
                self.schedule_followup(contact_id, today.isoformat(),
                                       f"Has a deal to send — call today. They said: {text[:160]}",
                                       title=f"CALL {aff.first_name} — has a deal", customer_touch=False)
                taken.append("deal:incoming + same-day call task")
                alert = f"🔥 {aff.name} has a deal. Same-day call task created."
            elif intent == "check_back_later":
                due = cadence.parse_day(follow_up_date) or today + timedelta(days=14)
                self.schedule_followup(contact_id, due.isoformat(), summary or f"They asked: {text[:160]}")
                taken.append(f"follow-up task {due.isoformat()}")
            elif intent == "wants_service":
                self.queue_growth_service(contact_id, baseline.get("service", "crm_help"), text[:160])
                taken.append(f"growth service queued: {baseline.get('service', 'crm_help')}")
                alert = f"{aff.name} wants help with {SERVICE_LABELS.get(baseline.get('service', 'crm_help'), 'CRM help')}."
            elif intent in {"commission_question", "question"}:
                self.schedule_followup(contact_id, today.isoformat(), f"Answer: {text[:180]}",
                                       title=f"Answer {aff.first_name}'s question", customer_touch=False)
                taken.append("answer task today")
                alert = f"{aff.name} asked: {text[:140]}"
            elif intent == "event_interest":
                self.ghl.add_tags(contact_id, ["want:event"])
                taken.append("want:event")
        self.vault.affiliate(aff.name, aff.id, f"replied ({intent}): {text[:160]}", day=today.isoformat())
        self.vault.log("Reply triaged", f"- {self.vault.affiliate_link(aff.name, aff.id)} — **{intent}** — "
                       f"{'; '.join(taken)}", day=today.isoformat())
        self.store.audit(actor=self.actor, action="reply.record", resource=contact_id, decision="autonomous",
                         result="ok", details={"intent": intent, "taken": taken})
        return {"ok": True, "intent": intent, "baseline": baseline, "actions_taken": taken, "manager_alert": alert}

    def record_deal(self, contact_id: str, note: str = "") -> dict[str, Any]:
        aff = self.affiliate(contact_id)
        today = self.today().isoformat()
        self._set_fields(contact_id, {"last_deal_date": today, "deals_submitted": aff.deals_submitted + 1})
        self.ghl.remove_tags(contact_id, ["deal:incoming"])
        for task in self.ghl.list_tasks(contact_id):
            if not task.get("completed") and str(task.get("title", "")).startswith("CALL "):
                self.ghl.complete_task(contact_id, task["id"])
        self._apply_lifecycle(aff, "aff:producing", "deal submitted")
        self.ghl.add_note(contact_id, f"Deal submitted {today}. {note}")
        self.vault.log("Deal recorded", f"- {self.vault.affiliate_link(aff.name, aff.id)} submitted a deal. {note}",
                       day=today)
        return {"ok": True, "deals_submitted": aff.deals_submitted + 1}

    # ── outbound: prepare ────────────────────────────────────────────────────
    def _lint(self, text: str) -> None:
        lowered = text.lower()
        hits = [p for p in BANNED_PHRASES if p in lowered]
        if hits:
            raise FamError(f"message contains non-compliant language: {hits} — see knowledge/funding/"
                           "06-compliance-guardrails.md")
        if re.search(r"\b\d{1,2}(\.\d+)?\s?%\s*(apr|interest|rate)", lowered):
            raise FamError("message states a specific rate; rates only from a sourced 7FF program card")

    def _freeze(self, kind: str, payload: dict[str, Any], recipients: int, summary: str) -> dict[str, Any]:
        payload = {**payload, "location_id": self.ghl.location_id, "prepared_for": self.today().isoformat()}
        payload_hash = digest({"kind": kind, "payload": payload})
        existing = self.store.find_action(kind, payload_hash)
        if existing:
            return self._action_view(existing)
        row = {"action_id": _new_id("act"), "kind": kind, "payload_json": stable_json(payload),
               "payload_hash": payload_hash, "recipients": recipients, "state": "prepared",
               "summary": summary, "created_at": now_iso(), "updated_at": now_iso()}
        self.store.insert_action(row)
        self.store.audit(actor=self.actor, action=f"{kind}.prepare", resource=row["action_id"],
                         decision="approval-required", result="prepared",
                         details={"recipients": recipients, "summary": summary})
        return self._action_view(row)

    def _action_view(self, row: dict[str, Any]) -> dict[str, Any]:
        import json as _json
        payload = _json.loads(row["payload_json"])
        view = {k: row[k] for k in ("action_id", "kind", "state", "recipients", "summary", "created_at")}
        view["action_digest"] = row["payload_hash"]
        view["demo_mode"] = self.settings.demo_mode
        if row["kind"] == "send_messages":
            view["preview"] = [{"contact_id": m["contact_id"], "name": m.get("name", ""), "channel": m["channel"],
                                "subject": m.get("subject", ""), "body": " ".join(m["body"].split())[:280],
                                "delivery": m.get("delivery", "")}
                               for m in payload["messages"][:8]]
        else:
            view["workflow_key"] = payload.get("workflow_key", "")
            view["sample_contacts"] = payload.get("names", [])[:8]
            if payload.get("custom_values"):
                view["custom_values"] = {k: str(v)[:280] for k, v in payload["custom_values"].items()}
        if row.get("result_json"):
            view["result"] = _json.loads(row["result_json"])
        return view

    def _delivery_mode(self, aff: Affiliate) -> str:
        if self.settings.ghl_mode == "mock":
            return "mock" if (not self.settings.demo_mode or aff.is_test_contact) else "simulated"
        return "live" if (not self.settings.demo_mode or aff.is_test_contact) else "simulated"

    def prepare_messages(self, messages: list[dict[str, Any]], purpose: str = "personal touches") -> dict[str, Any]:
        """Freeze a batch of individually drafted messages for one manager approval."""
        if not messages:
            raise FamError("no messages to prepare")
        cap = int(self.settings.cadence["batch_approval_max"])
        if len(messages) > cap:
            raise FamError(f"batch has {len(messages)} messages; max per approval is {cap}")
        frozen = []
        seen = set()
        for m in messages:
            contact_id = str(m.get("contact_id", "")).strip()
            channel = str(m.get("channel", "")).lower()
            body = str(m.get("body", "")).strip()
            kind = str(m.get("kind", "personal_checkin"))
            if not contact_id or contact_id in seen:
                raise FamError(f"missing or duplicate contact_id: {contact_id!r}")
            seen.add(contact_id)
            if channel not in {"sms", "email"}:
                raise FamError(f"{contact_id}: channel must be sms or email")
            if not body:
                raise FamError(f"{contact_id}: empty body")
            self._lint(body + " " + str(m.get("subject", "")))
            aff = self.affiliate(contact_id)
            if aff.is_dnc:
                raise FamError(f"{aff.name} is do-not-contact")
            segments = 0
            if channel == "sms":
                if not aff.phone:
                    raise FamError(f"{aff.name} has no phone for SMS")
                body = cadence.sms_normalize(body)
                if kind != "reply" and "stop" not in body.lower():
                    body = body.rstrip() + " Reply STOP to opt out."
                if len(body) > 480:
                    raise FamError(f"{aff.name}: SMS longer than 480 characters")
                segments = cadence.sms_segments(body)["segments"]
            if channel == "email" and not aff.email:
                raise FamError(f"{aff.name} has no email")
            frozen.append({"contact_id": contact_id, "name": aff.name, "channel": channel, "kind": kind,
                           "subject": str(m.get("subject", ""))[:150], "body": body,
                           "delivery": self._delivery_mode(aff), "segments": segments})
        real = sum(1 for m in frozen if m["delivery"] in {"live", "mock"})
        summary = f"{len(frozen)} {purpose} ({real} real, {len(frozen) - real} simulated)"
        billed = sum(m["segments"] for m in frozen)
        if billed:
            summary += f" · {billed} SMS segment{'s' if billed != 1 else ''}"
        return self._freeze("send_messages", {"messages": frozen, "purpose": purpose}, len(frozen), summary)

    def prepare_enrollment(self, workflow_key: str, contact_ids: list[str] | None = None,
                           from_sweep_kind: str = "", purpose: str = "",
                           custom_values: dict[str, str] | None = None) -> dict[str, Any]:
        """Freeze a bulk workflow enrollment (cadence, newsletter, event, new offer)."""
        if workflow_key not in BULK_WORKFLOW_KEYS:
            raise FamError(f"workflow_key must be one of {sorted(BULK_WORKFLOW_KEYS)}")
        workflow_id = self.settings.workflow_id(workflow_key)
        if from_sweep_kind:
            plan = cadence.sweep(self.affiliates(), self.today(), self.settings.cadence)
            contact_ids = [i["contact_id"] for i in plan["bulk_queue"].get(from_sweep_kind, [])]
        ids = sorted(dict.fromkeys(contact_ids or []))
        if not ids:
            raise FamError("no contacts to enroll")
        cap = int(self.settings.cadence["daily_bulk_enroll_cap"])
        already = self.store.count(self.today().isoformat(), "enrollments")
        if already + len(ids) > cap:
            raise FamError(f"enrolling {len(ids)} would exceed today's cap ({already}/{cap})")
        names, deliveries = [], {}
        amap = {a.id: a for a in self.affiliates()} if len(ids) > 25 else {}
        for cid in ids:
            aff = amap.get(cid) or self.affiliate(cid)
            if aff.is_dnc:
                continue
            names.append(aff.name)
            deliveries[cid] = self._delivery_mode(aff)
        ids = [cid for cid in ids if cid in deliveries]
        if custom_values:
            for value in custom_values.values():
                self._lint(str(value))
        real = sum(1 for v in deliveries.values() if v in {"live", "mock"})
        summary = (f"enroll {len(ids)} in {workflow_key} ({real} real, {len(ids) - real} simulated)"
                   + (f" — {purpose}" if purpose else ""))
        payload = {"workflow_key": workflow_key, "workflow_id": workflow_id, "contact_ids": ids,
                   "deliveries": deliveries, "names": names, "purpose": purpose,
                   "custom_values": custom_values or {}}
        return self._freeze("enroll_workflow", payload, len(ids), summary)

    # ── outbound: approve / execute ──────────────────────────────────────────
    def request_approval(self, action_id: str) -> dict[str, Any]:
        row = self.store.get_action(action_id)
        if not row:
            raise FamError(f"unknown action {action_id}")
        if row["state"] not in {"prepared", "approval_requested"}:
            raise FamError(f"action is {row['state']}, not awaiting approval")
        self.store.update_action(action_id, state="approval_requested")
        view = self._action_view({**row, "state": "approval_requested"})
        lines = [f"*Approval needed* — {row['summary']}",
                 f"action `{action_id}` · digest `{row['payload_hash']}` · demo mode: {self.settings.demo_mode}"]
        for i, p in enumerate(view.get("preview", []), 1):
            subj = f" — _{p['subject']}_" if p.get("subject") else ""
            lines.append(f"{i}. {p['name']} ({p['channel']}, {p['delivery']}){subj}: {p['body'][:180]}")
        if view.get("sample_contacts"):
            lines.append("Contacts: " + ", ".join(view["sample_contacts"]) +
                         (" …" if row["recipients"] > len(view["sample_contacts"]) else ""))
        for key, value in (view.get("custom_values") or {}).items():
            lines.append(f"{key}: {value}")
        lines.append(f"Reply *approve {action_id}* to send, or tell me what to change.")
        view["approval_card"] = "\n".join(lines)
        return view

    def approve(self, action_id: str, action_digest: str, approver: str) -> dict[str, Any]:
        """Record a human approval. Exposed ONLY on the untrusted approvals MCP."""
        row = self.store.get_action(action_id)
        if not row:
            raise FamError(f"unknown action {action_id}")
        if row["state"] != "approval_requested":
            raise FamError(f"action is {row['state']}; request approval first")
        if action_digest != row["payload_hash"]:
            raise FamError("digest does not match the frozen action — re-read the approval card")
        if not approver.strip():
            raise FamError("approver name is required")
        ttl = int(self.settings.cadence["approval_ttl_hours"])
        approval = {"approval_id": _new_id("apr"), "action_id": action_id, "digest": action_digest,
                    "approver": approver.strip(), "created_at": now_iso(),
                    "expires_at": (datetime.now(UTC) + timedelta(hours=ttl)).replace(microsecond=0).isoformat()}
        self.store.insert_approval(approval)
        self.store.update_action(action_id, state="approved", approval_id=approval["approval_id"])
        self.store.audit(actor=approver, action=f"{row['kind']}.approve", resource=action_id, decision="human",
                         result="approved", details={"expires_at": approval["expires_at"]})
        return {"ok": True, "action_id": action_id, "approval_id": approval["approval_id"],
                "expires_at": approval["expires_at"]}

    def _require_writes_enabled(self) -> None:
        if self.store.get_flag("external_writes_enabled", "true") != "true":
            raise FamError(f"external writes are stopped: {self.store.get_flag('stop_reason', '')}")

    def execute(self, action_id: str) -> dict[str, Any]:
        import json as _json
        self._require_writes_enabled()
        row = self.store.get_action(action_id)
        if not row:
            raise FamError(f"unknown action {action_id}")
        if row["state"] != "approved":
            raise ApprovalRequired(f"action is {row['state']}; it needs a human approval first")
        approval = self.store.get_approval(row["approval_id"])
        if not approval or approval["digest"] != row["payload_hash"]:
            raise FamError("approval does not match this action")
        if approval["expires_at"] < now_iso():
            self.store.update_action(action_id, state="approval_requested")
            raise FamError("approval expired — request a fresh one")
        payload = _json.loads(row["payload_json"])
        if payload.get("location_id") != self.ghl.location_id:
            raise FamError("action was prepared for a different GHL location")
        if row["kind"] == "send_messages":
            has_real_sms = any(m["channel"] == "sms" and m["delivery"] == "live" for m in payload["messages"])
            start, end = self.settings.cadence["sms_window_start_hour"], self.settings.cadence["sms_window_end_hour"]
            if has_real_sms and not (start <= self._local_hour() < end) and not os.getenv("FAM_IGNORE_SMS_WINDOW"):
                raise FamError(f"outside the SMS send window ({start}:00–{end}:00 {self.settings.cadence['timezone']})")
        if not self.store.use_approval(approval["approval_id"]):
            raise FamError("approval was already used")
        self.store.update_action(action_id, state="executing")
        if row["kind"] == "send_messages":
            result = self._execute_messages(payload)
        elif row["kind"] == "enroll_workflow":
            result = self._execute_enrollment(payload)
        else:
            raise FamError(f"unknown action kind {row['kind']}")
        state = "executed" if not result["failed"] else "executed_with_errors"
        self.store.update_action(action_id, state=state, result_json=stable_json(result))
        self.store.audit(actor=self.actor, action=f"{row['kind']}.execute", resource=action_id,
                         decision=f"approved:{approval['approver']}", result=state,
                         details={k: v for k, v in result.items() if k != "per_contact"})
        return {"ok": True, "action_id": action_id, "state": state, **result}

    def _touch_bookkeeping(self, aff: Affiliate, channel: str, kind: str) -> None:
        values: dict[str, Any] = {"last_touch_date": self.today().isoformat(), "last_touch_channel": channel}
        if kind in OFFER_KINDS:
            values["last_offer_date"] = self.today().isoformat()
        if kind == "scheduled_followup":
            values["next_touch_date"] = ""
            for task in self.ghl.list_tasks(aff.id):
                due = cadence.parse_day(task.get("dueDate"))
                manager_work = (str(task.get("title", "")).startswith(MANAGER_TASK_PREFIXES)
                                or str(task.get("body", "")).startswith(MANAGER_TASK_MARK))
                if not task.get("completed") and due and due <= self.today() and not manager_work:
                    self.ghl.complete_task(aff.id, task["id"])
        self._set_fields(aff.id, values)

    def _execute_messages(self, payload: dict[str, Any]) -> dict[str, Any]:
        counts = {"live": 0, "mock": 0, "simulated": 0, "failed": 0}
        per_contact = []
        for m in payload["messages"]:
            try:
                aff = self.affiliate(m["contact_id"])
                if aff.is_dnc:
                    raise FamError("contact opted out after approval")
                if m["delivery"] == "simulated":
                    self.ghl.add_note(aff.id, f"[SIMULATED {m['channel'].upper()} — demo mode, not delivered]\n"
                                              f"{m.get('subject', '')}\n{m['body']}".strip())
                else:
                    self.ghl.send_message(aff.id, m["channel"], m["body"], m.get("subject", ""))
                self._touch_bookkeeping(aff, m["channel"], m.get("kind", ""))
                self.vault.affiliate(aff.name, aff.id, f"{m['delivery']} {m['channel']} ({m.get('kind', '')}): "
                                     f"{m['body'][:140]}", day=self.today().isoformat())
                counts[m["delivery"]] += 1
                per_contact.append({"contact_id": aff.id, "delivery": m["delivery"], "ok": True})
            except FamError as exc:
                counts["failed"] += 1
                per_contact.append({"contact_id": m["contact_id"], "ok": False, "error": str(exc)})
        self.store.bump(self.today().isoformat(), "personal_messages",
                        counts["live"] + counts["mock"] + counts["simulated"])
        self.vault.log("Messages sent", f"- {payload['purpose']}: live {counts['live']}, mock {counts['mock']}, "
                       f"simulated {counts['simulated']}, failed {counts['failed']}", day=self.today().isoformat())
        return {**counts, "per_contact": per_contact}

    def _execute_enrollment(self, payload: dict[str, Any]) -> dict[str, Any]:
        counts = {"live": 0, "mock": 0, "simulated": 0, "failed": 0}
        per_contact = []
        key = payload["workflow_key"]
        if payload.get("custom_values"):
            update = getattr(self.ghl, "update_custom_value_by_name", None)
            if update is None:
                raise FamError("custom value updates are not supported by this backend")
            for name, value in payload["custom_values"].items():
                update(name, value)
        kind = {"monthly_offer": "monthly_offer", "new_offer": "new_offer"}.get(key, key)
        channel = "workflow"
        # one paged read instead of a GET per contact — keeps 10k-affiliate runs inside GHL rate limits
        amap = {a.id: a for a in self.affiliates()} if len(payload["contact_ids"]) > 25 else {}
        for cid in payload["contact_ids"]:
            delivery = payload["deliveries"].get(cid, "simulated")
            try:
                aff = amap.get(cid) or self.affiliate(cid)
                if aff.is_dnc:
                    raise FamError("contact opted out after approval")
                if delivery == "simulated":
                    self.ghl.add_note(cid, f"[SIMULATED ENROLLMENT — demo mode] workflow: {key}")
                else:
                    self.ghl.enroll_workflow(cid, payload["workflow_id"])
                if key == "onboarding" and aff.lifecycle == "aff:applied":
                    self._apply_lifecycle(aff, "aff:onboarding", "onboarding sequence started")
                if key not in {"event_invite"}:
                    self._touch_bookkeeping(aff, channel, kind)
                counts[delivery] += 1
                per_contact.append({"contact_id": cid, "delivery": delivery, "ok": True})
            except FamError as exc:
                counts["failed"] += 1
                per_contact.append({"contact_id": cid, "ok": False, "error": str(exc)})
        self.store.bump(self.today().isoformat(), "enrollments",
                        counts["live"] + counts["mock"] + counts["simulated"])
        self.vault.log("Workflow enrollment", f"- {key}: live {counts['live']}, mock {counts['mock']}, "
                       f"simulated {counts['simulated']}, failed {counts['failed']}"
                       + (f" — {payload['purpose']}" if payload.get("purpose") else ""),
                       day=self.today().isoformat())
        return {**counts, "per_contact": per_contact}

    # ── standing approvals for recurring bulk cadence ─────────────────────────
    def activate_standing(self, workflow_key: str, max_per_day: int, days: int, approver: str) -> dict[str, Any]:
        """Human-approve recurring cadence enrollments. Approvals MCP only."""
        if workflow_key not in STANDING_ALLOWED:
            raise FamError(f"standing approvals are limited to {sorted(STANDING_ALLOWED)}")
        if not 1 <= max_per_day <= int(self.settings.cadence["daily_bulk_enroll_cap"]):
            raise FamError("max_per_day is out of range")
        if not 1 <= days <= 90:
            raise FamError("standing approvals last 1–90 days")
        if not approver.strip():
            raise FamError("approver name is required")
        row = {"standing_id": _new_id("std"), "workflow_key": workflow_key, "max_per_day": max_per_day,
               "approver": approver.strip(), "created_at": now_iso(),
               "expires_at": (datetime.now(UTC) + timedelta(days=days)).replace(microsecond=0).isoformat()}
        self.store.insert_standing(row)
        self.store.audit(actor=approver, action="standing.activate", resource=row["standing_id"], decision="human",
                         result="active", details={"workflow_key": workflow_key, "max_per_day": max_per_day,
                                                   "days": days})
        return {"ok": True, **row}

    def revoke_standing(self, standing_id: str, reason: str) -> dict[str, Any]:
        ok = self.store.revoke_standing(standing_id, reason)
        self.store.audit(actor=self.actor, action="standing.revoke", resource=standing_id, decision="autonomous",
                         result="revoked" if ok else "not-found", details={"reason": reason})
        return {"ok": ok}

    def run_standing_cadence(self) -> dict[str, Any]:
        """Execute today's bulk cadence under active standing approvals (the cron path)."""
        self._require_writes_enabled()
        plan = cadence.sweep(self.affiliates(), self.today(), self.settings.cadence)
        results: dict[str, Any] = {}
        for kind, items in plan["bulk_queue"].items():
            standing = self.store.active_standing(kind)
            if not standing:
                results[kind] = {"skipped": "no standing approval", "due": len(items)}
                continue
            ids = [i["contact_id"] for i in items][: int(standing["max_per_day"])]
            if not ids:
                continue
            action = self.prepare_enrollment(kind, contact_ids=ids, purpose=f"standing approval {standing['standing_id']}")
            self.store.update_action(action["action_id"], state="approval_requested")
            approval = {"approval_id": _new_id("apr"), "action_id": action["action_id"],
                        "digest": action["action_digest"], "approver": f"standing:{standing['standing_id']}",
                        "created_at": now_iso(),
                        "expires_at": (datetime.now(UTC) + timedelta(hours=1)).replace(microsecond=0).isoformat()}
            self.store.insert_approval(approval)
            self.store.update_action(action["action_id"], state="approved", approval_id=approval["approval_id"])
            results[kind] = self.execute(action["action_id"])
            results[kind].pop("per_contact", None)
        return {"date": self.today().isoformat(), "results": results}

    # ── kill switch ──────────────────────────────────────────────────────────
    def emergency_stop(self, reason: str) -> dict[str, Any]:
        self.store.set_flag("external_writes_enabled", "false")
        self.store.set_flag("stop_reason", reason or "stopped")
        self.store.audit(actor=self.actor, action="external_writes.stop", resource="all", decision="stop",
                         result="stopped", details={"reason": reason})
        self.vault.log("EMERGENCY STOP", f"All outbound frozen: {reason}", day=self.today().isoformat())
        return {"ok": True, "external_writes_enabled": False, "reason": reason}

    def resume(self, actor: str) -> dict[str, Any]:
        self.store.set_flag("external_writes_enabled", "true")
        self.store.set_flag("stop_reason", "")
        self.store.audit(actor=actor, action="external_writes.resume", resource="all", decision="human",
                         result="resumed", details={})
        return {"ok": True, "external_writes_enabled": True}

    # ── reporting ────────────────────────────────────────────────────────────
    def scorecard(self) -> dict[str, Any]:
        today = self.today()
        affs = self.affiliates()
        plan = cadence.sweep(affs, today, self.settings.cadence)

        def within(key: str, days: int) -> int:
            return sum(1 for a in affs if (d := a.day(key)) and (today - d).days <= days)

        by_source: dict[str, int] = {}
        for a in affs:
            by_source[a.source] = by_source.get(a.source, 0) + 1
        total = len(affs) or 1
        replied_30 = within("last_reply_date", 30)
        touched_30 = within("last_touch_date", 30)
        return {
            "date": today.isoformat(),
            "affiliates": len(affs),
            "by_source": dict(sorted(by_source.items(), key=lambda kv: -kv[1])),
            "cohorts": plan["cohorts"],
            "submitted_deal_last_30d": within("last_deal_date", 30),
            "replied_last_30d": replied_30,
            "touched_last_30d": touched_30,
            "reply_rate_30d": round(replied_30 / max(touched_30, 1), 3),
            "active_rate": round((plan["cohorts"].get("aff:active", 0) + plan["cohorts"].get("aff:producing", 0)
                                  + plan["cohorts"].get("aff:reactivated", 0)) / total, 3),
            "silent_90_plus": plan["silent_90_plus"],
            "dnc": sum(1 for a in affs if a.is_dnc),
            "open_growth_services": sum(1 for a in affs if any(t.startswith("want:") for t in a.tags)),
        }

    def save_campaign_note(self, title: str, body: str, kind: str = "campaign") -> dict[str, Any]:
        self._lint(body)
        path = self.vault.campaign(title, body, kind=kind, day=self.today().isoformat())
        return {"ok": True, "path": str(path)}
