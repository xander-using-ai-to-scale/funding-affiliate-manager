"""Build each partner's profile before the first message, from wherever their history lives.

Sources share one shape (`SourceRecord`: the partner, their record fields, and dated history items):
  * zoho         7FF's partner records in Zoho CRM, read-only (OAuth self-client; config/zoho-map.json holds
                 the module, the field names, and the related lists to read). Nothing is ever written to Zoho.
  * csv          any export: one partners file, plus an optional history file (date, kind, text).
  * ghl_history  partners already in GoHighLevel: their notes and past messages.

`import_records()` upserts each partner into GoHighLevel (tier, plan, dates, deals, source, niche), tags
the quiet ones `fam:kickoff-pending`, and builds the profile: plain fields go in without any model; one
extraction pass reads the history (only when there is history); every history item lands in the
partner's timeline with its date and source.
"""

from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Callable, Iterator
from urllib import error, parse, request

from . import cadence
from .cadence import KICKOFF_DONE, KICKOFF_PENDING, KICKOFF_SENT
from .errors import FamError

RECORD_FIELDS = ("tier", "plan", "join_date", "source", "niche", "deals_submitted", "last_deal_date",
                 "assigned_manager", "affiliate_id", "audience_size", "preferred_channel")


@dataclass
class SourceRecord:
    source: str
    external_id: str
    first_name: str
    last_name: str = ""
    email: str = ""
    phone: str = ""
    fields: dict[str, Any] = field(default_factory=dict)  # RECORD_FIELDS plus last_contact_date
    history: list[dict[str, str]] = field(default_factory=list)  # id, date, kind, text
    dnc: bool = False


def _digits(phone: str) -> str:
    return re.sub(r"\D", "", phone or "")[-10:]


def _tier(value: Any) -> str:
    text = str(value or "").strip()
    return next((t for t in cadence.TIERS if t.lower() == text.lower()), text)


# ── CSV ──────────────────────────────────────────────────────────────────────
class CsvSource:
    """partners.csv: external_id, first_name, last_name, email, phone, tier, plan, join_date, source, niche,
    deals_submitted, last_deal_date, last_contact_date, assigned_manager, dnc.
    history.csv (optional): external_id or email, date, kind, text."""

    name = "csv"

    def __init__(self, partners: Path, history: Path | None = None):
        self.partners, self.history = partners, history

    def records(self) -> Iterator[SourceRecord]:
        events: dict[str, list[dict[str, str]]] = {}
        if self.history and self.history.exists():
            with self.history.open(newline="") as handle:
                for i, row in enumerate(csv.DictReader(handle)):
                    key = (row.get("external_id") or row.get("email") or "").strip().lower()
                    events.setdefault(key, []).append({"id": f"h{i}", "date": (row.get("date") or "")[:10],
                                                       "kind": row.get("kind") or "note", "text": row.get("text") or ""})
        with self.partners.open(newline="") as handle:
            for row in csv.DictReader(handle):
                ext = (row.get("external_id") or row.get("email") or "").strip()
                fields = {k: row[k].strip() for k in (*RECORD_FIELDS, "last_contact_date") if (row.get(k) or "").strip()}
                yield SourceRecord("csv", ext, (row.get("first_name") or "").strip(), (row.get("last_name") or "").strip(),
                                   (row.get("email") or "").strip(), (row.get("phone") or "").strip(), fields,
                                   events.get(ext.lower(), []) + events.get((row.get("email") or "").strip().lower(), []),
                                   str(row.get("dnc") or "").strip().lower() in {"1", "true", "yes"})


# ── GoHighLevel history ──────────────────────────────────────────────────────
class GhlHistorySource:
    """Partners already in GoHighLevel: build their profile from notes and past messages."""

    name = "ghl_history"

    def __init__(self, engine: Any, contact_ids: list[str] | None = None):
        self.engine, self.contact_ids = engine, contact_ids

    def records(self) -> Iterator[SourceRecord]:
        affs = ([self.engine.affiliate(c) for c in self.contact_ids] if self.contact_ids
                else self.engine.affiliates())
        for aff in affs:
            history = [{"id": n.get("id", ""), "date": str(n.get("dateAdded") or "")[:10], "kind": "ghl_note",
                        "text": n.get("body", "")} for n in self.engine.ghl.list_notes(aff.id)
                       if not str(n.get("body", "")).startswith(("[SIMULATED", "Reply (", "Follow-up scheduled",
                                                                  "Task for the manager"))]
            for conv in self.engine.ghl.list_conversations(contact_id=aff.id, limit=3):
                for m in self.engine.ghl.list_messages(conv["id"], limit=20):
                    if m.get("direction") == "inbound" and (m.get("body") or "").strip():
                        history.append({"id": str(m.get("id", "")), "date": str(m.get("dateAdded") or "")[:10],
                                        "kind": "ghl_message", "text": m["body"]})
            yield SourceRecord("ghl_history", aff.id, aff.first_name, "", aff.email, aff.phone, {}, history,
                               aff.is_dnc)


# ── Zoho CRM (read-only) ─────────────────────────────────────────────────────
class ZohoSource:
    """Zoho CRM API v2, read-only. Needs ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET and ZOHO_REFRESH_TOKEN (a self-client
    with ZohoCRM.modules.READ). Field names come from config/zoho-map.json; confirm them on 7FF's org."""

    name = "zoho"

    def __init__(self, mapping: dict[str, Any], transport: Callable[[str, str, dict[str, Any]], dict[str, Any]] | None = None):
        self.map = mapping
        self.api = os.getenv("ZOHO_API_URL", "https://www.zohoapis.com").rstrip("/")
        self.accounts = os.getenv("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.com").rstrip("/")
        self.transport = transport or self._http
        self._token = ""

    def _http(self, method: str, url: str, params: dict[str, Any]) -> dict[str, Any]:
        url += ("?" + parse.urlencode(params)) if params else ""
        headers = {"Accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Zoho-oauthtoken {self._token}"
        try:
            with request.urlopen(request.Request(url, method=method, headers=headers), timeout=30) as resp:
                raw = resp.read(5_000_000)
        except error.HTTPError as exc:
            raise FamError(f"Zoho {method} returned HTTP {exc.code}") from exc
        except error.URLError as exc:
            raise FamError("Zoho could not be reached") from exc
        return json.loads(raw or b"{}") if raw else {}

    def _auth(self) -> None:
        creds = {k: os.getenv(f"ZOHO_{k.upper()}", "").strip() for k in ("client_id", "client_secret", "refresh_token")}
        if not all(creds.values()):
            raise FamError("Zoho needs ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET and ZOHO_REFRESH_TOKEN (read-only self-client)")
        token = self.transport("POST", f"{self.accounts}/oauth/v2/token", {**creds, "grant_type": "refresh_token"})
        self._token = token.get("access_token", "")
        if not self._token:
            raise FamError("Zoho did not return an access token")

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self._token:
            self._auth()
        return self.transport("GET", f"{self.api}/crm/v2/{path}", params or {})

    def records(self, limit: int = 0) -> Iterator[SourceRecord]:
        module, f = self.map.get("module", "Contacts"), self.map.get("fields", {})
        page, count = 1, 0
        while True:
            data = self._get(module, {"page": page, "per_page": 200})
            for row in data.get("data", []):
                fields = {key: row.get(api) for key, api in f.items()
                          if api and key in (*RECORD_FIELDS, "last_contact_date") and row.get(api) not in (None, "")}
                for key in ("join_date", "last_deal_date", "last_contact_date"):
                    if fields.get(key):
                        fields[key] = str(fields[key])[:10]
                if fields.get("source") and isinstance(fields["source"], str):
                    fields["source"] = fields["source"].strip().lower().replace(" ", "-")
                yield SourceRecord("zoho", str(row.get("id", "")), str(row.get(f.get("first_name", "First_Name")) or ""),
                                   str(row.get(f.get("last_name", "Last_Name")) or ""),
                                   str(row.get(f.get("email", "Email")) or ""), str(row.get(f.get("phone", "Mobile"))
                                                                                     or row.get("Phone") or ""),
                                   fields, self._history(module, str(row.get("id", ""))),
                                   bool(row.get(f.get("dnc", ""), False)) if f.get("dnc") else False)
                count += 1
                if limit and count >= limit:
                    return
            if not data.get("info", {}).get("more_records"):
                return
            page += 1

    def _history(self, module: str, record_id: str) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        for rel in self.map.get("related", ["Notes", "Deals", "Calls"]):
            try:
                rows = self._get(f"{module}/{record_id}/{rel}", {"per_page": 50}).get("data", [])
            except FamError:
                continue  # a related list the org doesn't have, or no permission: the record still imports
            for r in rows:
                if rel == "Notes":
                    text = " ".join(str(r.get(k) or "") for k in ("Note_Title", "Note_Content")).strip()
                    when = r.get("Created_Time")
                elif rel == "Deals":
                    text = f"Deal: {r.get('Deal_Name') or ''} ({r.get('Stage') or 'stage unknown'})"
                    when = r.get("Closing_Date") or r.get("Created_Time")
                else:
                    text = " ".join(str(r.get(k) or "") for k in ("Subject", "Description")).strip()
                    when = r.get("Call_Start_Time") or r.get("Created_Time")
                if text:
                    items.append({"id": f"{rel}:{r.get('id', '')}", "date": str(when or "")[:10],
                                  "kind": f"zoho_{rel.lower().rstrip('s')}", "text": text[:2000]})
        return items


# ── import ───────────────────────────────────────────────────────────────────
def _find_contact(engine: Any, rec: SourceRecord) -> dict[str, Any] | None:
    if rec.source == "ghl_history":
        return {"id": rec.external_id}
    for key in ("email", "phone"):
        value = getattr(rec, key)
        if not value:
            continue
        for c in engine.ghl.search_contacts(query=value, limit=5):
            if (key == "email" and (c.get("email") or "").lower() == value.lower()) or \
                    (key == "phone" and _digits(c.get("phone", "")) == _digits(value)):
                return c
    return None


def import_records(engine: Any, records: Any, *, mark_kickoff: bool = True, limit: int = 0) -> dict[str, Any]:
    """Upsert partners into GoHighLevel and build each profile. Returns counts and the kickoff queue size."""
    settings, today = engine.settings, engine.today()
    field_ids = settings.field_ids()
    taxonomy = json.loads((settings.config_dir / "tag-taxonomy.json").read_text())
    known_sources = {t[4:] for t in taxonomy.get("source", [])}
    report = {"records": 0, "created": 0, "updated": 0, "kickoff_pending": 0, "with_history": 0, "facts": 0}
    for rec in records:
        if limit and report["records"] >= limit:
            break
        report["records"] += 1
        fields = {k: v for k, v in rec.fields.items() if k in RECORD_FIELDS}
        if fields.get("tier"):
            fields["tier"] = _tier(fields["tier"])
        if rec.fields.get("last_contact_date"):
            fields["last_reply_date"] = str(rec.fields["last_contact_date"])[:10]
        tags = []
        if fields.get("source") in known_sources:
            tags.append(f"src:{fields['source']}")
        if fields.get("tier"):
            tags.append(f"tier:{str(fields['tier']).lower()}")
        payload_fields = [{"id": field_ids[k], "field_value": v} for k, v in fields.items() if k in field_ids]
        found = _find_contact(engine, rec)
        if found:
            if payload_fields:
                engine.ghl.update_contact(found["id"], {"customFields": payload_fields})
            if tags:
                engine.ghl.add_tags(found["id"], tags)
            contact_id = found["id"]
            report["updated"] += 1
        else:
            contact_id = engine.ghl.create_contact({"firstName": rec.first_name, "lastName": rec.last_name,
                                                    "email": rec.email, "phone": rec.phone, "tags": tags,
                                                    "customFields": payload_fields})["id"]
            report["created"] += 1
        if rec.dnc:
            engine.ghl.add_tags(contact_id, [cadence.DNC_TAG])
            engine.ghl.update_contact(contact_id, {"dnd": True})
        aff = engine.affiliate(contact_id)
        lifecycle, silent = cadence.target_lifecycle(aff, today, settings.cadence)
        quiet = silent is None or silent >= int(settings.cadence["quiet_after_days"])
        if (mark_kickoff and quiet and not aff.is_dnc and not aff.is_test_contact
                and not {KICKOFF_PENDING, KICKOFF_SENT, KICKOFF_DONE} & set(aff.tags)):
            engine.ghl.add_tags(contact_id, [KICKOFF_PENDING])
            aff = engine.affiliate(contact_id)
            report["kickoff_pending"] += 1
        facts: list[dict[str, str]] = [{"slot": k, "value": str(fields[k]), "source_type": rec.source,
                                        "observed_on": today.isoformat()} for k in ("tier", "niche") if fields.get(k)]
        history = sorted((h for h in rec.history if (h.get("text") or "").strip()), key=lambda h: h.get("date") or "")
        if history:
            report["with_history"] += 1
            text = "\n".join(f"{h.get('date', '')} ({h.get('kind', 'note')}): {h['text']}" for h in history)
            found_facts = engine.extractor.extract_text(text[:12000], {"name": aff.name})["facts"]
            last = history[-1].get("date") or today.isoformat()
            facts += [{**f, "source_type": f"{rec.source}_history" if rec.source != "ghl_history" else "ghl_note",
                       "source_ref": rec.external_id, "observed_on": last} for f in found_facts]
        interactions = [{"kind": "history", "at": h.get("date") or today.isoformat(),
                         "ref": f"{rec.source}:{rec.external_id}:{h.get('id') or i}",
                         "summary": f"{h.get('kind', 'note').replace('_', ' ')}: {h['text'][:240]}"}
                        for i, h in enumerate(history)]
        interactions.append({"kind": "profile_built", "ref": f"{rec.source}:{rec.external_id}:built:{today.isoformat()}",
                             "summary": f"profile built from {rec.source} ({len(history)} history items)"})
        out = engine.remember(aff, facts=facts, source_type=rec.source, source_ref=rec.external_id,
                              interaction=interactions)
        report["facts"] += len(out["facts_added"])
        engine.vault.affiliate(aff.name, aff.id, f"profile built from {rec.source}: {len(history)} history items, "
                               f"{len(out['facts_added'])} facts, {out['profile']['completeness']}% complete",
                               day=today.isoformat())
    engine.vault.log("Profiles built", f"- {report}", day=today.isoformat())
    engine.store.audit(actor=engine.actor, action="profiles.import", resource="partners", decision="autonomous",
                       result="ok", details=report)
    return report


def zoho_mapping(settings: Any) -> dict[str, Any]:
    path = settings.config_dir / "zoho-map.json"
    return json.loads(path.read_text()) if path.exists() else {}
