"""Tests for the relationship graph: profiles, the kickoff, replies, calls (stdlib unittest; no network).

    PYTHONPATH=files/local-packages/fam/src python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "files" / "local-packages" / "fam" / "src"))
os.environ.setdefault("FAM_CONFIG_DIR", str(ROOT / "config"))
os.environ.setdefault("FAM_POLICY_PATH", str(ROOT / "policies" / "permissions.json"))

from fam import cadence, calls, drafting, extract, kickoff, sources  # noqa: E402
from fam.config import Settings  # noqa: E402
from fam.engine import FamEngine  # noqa: E402
from fam.errors import FamError  # noqa: E402
from fam.ghl import MockGHL  # noqa: E402

TODAY = date(2026, 10, 5)


def ago(days: int) -> str:
    return (TODAY - timedelta(days=days)).isoformat()


class Relationships(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Settings.load()
        self.settings = replace(base, state_dir=Path(self.tmp.name) / "state", vault_dir=Path(self.tmp.name) / "vault",
                                ghl_mode="mock", demo_mode=False,
                                kickoff={**base.kickoff, "default_sender": "Justin", "send_pause_seconds": 0})
        self.settings.state_dir.mkdir(parents=True)
        self.ghl = MockGHL(self.settings.state_dir / "mock-ghl.json")
        self.engine = self.at(TODAY)
        ids = self.settings.field_ids()
        fields = {"join_date": "2023-04-11", "last_reply_date": ago(200), "tier": "Executive", "deals_submitted": 3,
                  "niche": "CPA", "assigned_manager": "Justin"}
        self.cid = self.ghl.create_contact({
            "firstName": "Dana", "lastName": "Reyes", "email": "dana@example.com", "phone": "+15555550142",
            "tags": ["aff:dormant", "src:linkedin"],
            "customFields": [{"id": ids[k], "field_value": v} for k, v in fields.items() if k in ids]})["id"]

    def tearDown(self):
        self.tmp.cleanup()

    def at(self, day: date) -> FamEngine:
        self.ghl.now_override = f"{day.isoformat()}T15:00:00+00:00"
        return FamEngine(settings=self.settings, backend=self.ghl, today=day)

    def send(self, messages, exclude=None):
        action = self.engine.prepare_messages(messages, purpose="test batch")
        card = self.engine.request_approval(action["action_id"])
        self.engine.approve(action["action_id"], action["action_digest"], "Justin", exclude=exclude)
        return card, self.engine.execute(action["action_id"])

    def notes(self):
        return sorted((self.settings.vault_dir / "Partners").glob("*.md"))

    # ── the partner note ─────────────────────────────────────────────────────
    def test_note_survives_rename_and_keeps_manager_notes(self):
        self.engine.facts_record(self.cid, [{"slot": "goals", "value": "two deals a month"}])
        path = self.notes()[0]
        text = path.read_text().replace("_Yours. The agent reads this section and never edits it._",
                                        "Loves golf. Call before 10am.")
        path.write_text(text)
        self.ghl.update_contact(self.cid, {"firstName": "Danielle"})
        out = self.engine.facts_record(self.cid, [{"slot": "channel", "value": "text"}])
        notes = self.notes()
        self.assertEqual(len(notes), 1, [n.name for n in notes])
        self.assertTrue(notes[0].name.startswith("Danielle Reyes ("))
        body = notes[0].read_text()
        self.assertIn("Loves golf. Call before 10am.", body)
        self.assertIn(f"profile_completeness: {out['completeness']}", body)
        self.assertEqual(body.count("ghl_contact_id:"), 1)
        self.assertTrue(body.rstrip().split("\n## ")[-1].startswith("Timeline"))

    def test_hub_links_make_the_graph(self):
        self.engine.facts_record(self.cid, [{"slot": "deal_types", "value": "equipment financing"}])
        note = self.notes()[0].read_text()
        for link in ("[[Tiers/Executive|Executive]]", "[[Niches/CPA|CPA]]", "[[Managers/Justin|Justin]]",
                     "[[Sources/LinkedIn|LinkedIn]]", "[[Products/Equipment financing|Equipment financing]]"):
            self.assertIn(link, note)
        self.assertTrue((self.settings.vault_dir / "Niches" / "CPA.md").exists())

    def test_profile_get_returns_values_facts_and_next_question(self):
        self.engine.facts_record(self.cid, [{"slot": "client_types", "value": "small trucking companies"},
                                            {"slot": "deal_size", "value": "around $150k"}], source_type="manual")
        p = self.engine.profile_get(self.cid)
        self.assertEqual(p["values"]["client_types"], ["small trucking companies"])
        self.assertIn({"slot": "deal_size", "value": "around $150k", "source_type": "manual"},
                      [{k: f[k] for k in ("slot", "value", "source_type")} for f in p["facts"]])
        self.assertEqual(p["tier"], "Executive")
        self.assertEqual(p["next_question"]["slot"], "goals")
        self.assertGreater(p["completeness"], 0)

    def test_never_store_drops_account_numbers(self):
        out = self.engine.facts_record(self.cid, [{"slot": "note", "value": "routing 021000021 acct 123456789012"}])
        self.assertEqual(out["facts_added"], [])

    def test_reindex_rebuilds_facts_from_the_vault(self):
        self.engine.facts_record(self.cid, [{"slot": "goals", "value": "two deals a month"}])
        with self.engine.store.connection() as conn:
            conn.execute("DELETE FROM facts")
        self.engine.graph.reindex()
        self.assertIn("two deals a month", self.engine.profile_get(self.cid)["values"]["goals"])

    # ── replies ──────────────────────────────────────────────────────────────
    def test_stop_variants(self):
        for text in ("STOP", "Stop.", "stop!", "CANCEL", "Quit", "UNSUBSCRIBE", "please stop texting me", "STOP please",
                     "Remove me", "End"):
            self.assertEqual(cadence.classify_reply(text)["intent"], "unsubscribe", text)
        for text in ("I can stop by Friday to drop off the file", "Is there an end date on the promo?"):
            self.assertNotEqual(cadence.classify_reply(text)["intent"], "unsubscribe", text)

    def test_reply_facts_are_recorded_once_per_message(self):
        text = "Most of my clients are small trucking companies. Usually around $150k for equipment."
        first = self.engine.record_reply(self.cid, text, message_ids=["m1"])
        self.assertGreaterEqual(len(first["facts_added"]), 2)
        again = self.engine.record_reply(self.cid, text, message_ids=["m1"])
        self.assertTrue(again["duplicate"])
        self.assertEqual(len(self.engine.graph.facts(self.cid)),
                         len([f for f in self.engine.graph.facts(self.cid)]))
        values = self.engine.profile_get(self.cid)["values"]
        self.assertEqual(values["deal_size"], ["around $150k"])
        self.assertIn("equipment financing", values["deal_types"])

    def test_inbox_reads_every_new_text_and_skips_handled_ones(self):
        self.ghl.send_message(self.cid, "sms", "Hey Dana, it's Justin.")
        self.ghl.record_inbound(self.cid, "sms", "Hey Justin!")
        self.ghl.record_inbound(self.cid, "sms", "Most of my clients are restaurants.")
        rows = self.engine.reply_inbox(limit=50)
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]["message_ids"]), 2)
        self.assertIn("Hey Justin!", rows[0]["last_message"])
        self.assertIn("restaurants", rows[0]["last_message"])
        self.engine.record_reply(self.cid, rows[0]["last_message"], message_ids=rows[0]["message_ids"])
        self.assertEqual(self.engine.reply_inbox(limit=50), [])
        for m in self.ghl.db["messages"]:  # GoHighLevel shows the conversation unread again
            m["unread"] = m["direction"] == "inbound"
        self.assertEqual(self.engine.reply_inbox(limit=50), [])

    def test_identity_question_goes_to_the_manager(self):
        out = self.engine.record_reply(self.cid, "Is this a real person or a bot?")
        self.assertEqual(out["intent"], "identity_question")
        self.assertFalse(out["draft_reply"])
        tasks = [t for t in self.ghl.list_tasks(self.cid) if t["title"].startswith("Reply personally")]
        self.assertEqual(len(tasks), 1)
        with self.assertRaises(FamError):
            self.engine.prepare_messages([{"contact_id": self.cid, "channel": "sms", "body": "Hey Dana!",
                                           "kind": "reply"}])
        self.ghl.complete_task(self.cid, tasks[0]["id"])
        self.engine.prepare_messages([{"contact_id": self.cid, "channel": "sms", "body": "Hey Dana!", "kind": "reply"}])

    def test_partner_texts_never_mention_ai(self):
        for body in ("Hi Dana, I'm Justin's AI assistant.", "This text was drafted by our team's assistant.", "I'm a real person!"):
            with self.assertRaises(FamError, msg=body):
                self.engine.prepare_messages([{"contact_id": self.cid, "channel": "sms", "body": body}])
        self.assertTrue(drafting.check("Hey Dana, our AI found a program for you. Call?", {}, "Justin"))

    def test_we_do_not_ask_for_a_call_twice_in_a_row(self):
        d = drafting.TemplateDrafter()
        history = [{"kind": "reply", "summary": "texting is easier"},
                   {"kind": "message_sent", "summary": "Would a quick 15-minute call this week be easier?"},
                   {"kind": "reply", "summary": "my clients are restaurants"},
                   {"kind": "reply", "summary": "hey!"},
                   {"kind": "kickoff_sent", "summary": "Hey Dana... Open to a quick call this week?"}]
        p = {"history": history, "next_question": {"slot": "goals", "question": "What are you working toward?"}}
        self.assertEqual(d.next_move(p, "general_reply", "Texting is easier for me right now")["move"], "discover")
        p["history"] = history[1:]
        self.assertEqual(d.next_move(p, "general_reply", "Sure, sounds good")["move"], "book")
        # they named a time: confirm it, never send them off to pick a time again
        move = d.next_move(p, "general_reply", "Sure, Thursday works")
        self.assertEqual((move["move"], move["time"]), ("confirm_time", "Thursday"))

    # ── the kickoff ──────────────────────────────────────────────────────────
    def test_kickoff_drafts_fit_two_segments_and_three_are_refused(self):
        p = {"first_name": "Bartholomew", "joined": "2019-01-01", "deals": 12, "tier": "Executive",
             "niche": "commercial real-estate broker", "source": "linkedin"}
        for variant in drafting.VARIANTS:
            d = drafting.TemplateDrafter().kickoff(p, "Christopher", variant)
            self.assertLessEqual(drafting.segments(d["body"]), 2, d["body"])
            self.assertEqual(drafting.check(d["body"], p, "Christopher", kickoff=True), [])
        long = ("Hey Dana, it's Justin with 7 Figures Funding. " * 7) + "Open to a quick call this week?"
        with self.assertRaises(FamError):
            self.engine.prepare_messages([{"contact_id": self.cid, "channel": "sms", "body": long, "kind": "kickoff"}])

    def test_kickoff_wave_review_and_approve_with_exceptions(self):
        ids = [self.cid]
        for i in range(3):
            ids.append(self.ghl.create_contact({"firstName": f"P{i}", "lastName": "Partner", "phone": f"+1555555990{i}",
                                                "email": f"p{i}@example.com", "tags": ["aff:dormant"]})["id"])
        self.assertEqual(kickoff.enroll(self.engine)["tagged"], 4)
        wave = kickoff.draft_wave(self.engine, 10)
        self.assertTrue(wave["ok"])
        review = Path(wave["action"]["review_file"]).read_text()
        for d in wave["drafts"]:
            self.assertIn(d["body"], review)
            self.assertLessEqual(d["segments"], 2)
        self.assertEqual(wave["drafts"][0]["contact_id"], self.cid)  # past producer goes first
        self.engine.approve(wave["action"]["action_id"], wave["action"]["action_digest"], "Justin", exclude=[2])
        result = self.engine.execute(wave["action"]["action_id"])
        self.assertEqual((result["mock"], result["held_back"]), (3, 1))
        held = wave["drafts"][1]["contact_id"]
        self.assertNotIn(held, {m["contactId"] for m in self.ghl.db["outbox"]})
        self.assertIn(cadence.KICKOFF_PENDING, self.engine.affiliate(held).tags)
        self.assertIn(cadence.KICKOFF_SENT, self.engine.affiliate(self.cid).tags)
        self.engine.record_reply(self.cid, "Hey Justin! Good to hear from you.")
        self.assertIn(cadence.KICKOFF_DONE, self.engine.affiliate(self.cid).tags)
        self.assertEqual(self.engine.graph.variant_stats()[wave["drafts"][0]["variant"]]["replied"], 1)

    def test_kickoff_partners_skip_bulk_workflows(self):
        self.ghl.add_tags(self.cid, [cadence.KICKOFF_PENDING])
        plan = cadence.sweep(self.engine.affiliates(), TODAY, self.settings.cadence)
        bulk = [i["contact_id"] for items in plan["bulk_queue"].values() for i in items]
        self.assertNotIn(self.cid, bulk)

    def test_import_builds_profile_and_tags_quiet_partners(self):
        rec = sources.SourceRecord(source="zoho", external_id="Z1", first_name="Lee", last_name="Ortiz",
                                   email="lee@example.com", phone="+15555550199",
                                   fields={"tier": "CEO", "join_date": "2022-01-05", "niche": "fractional CFO",
                                           "last_contact_date": ago(300), "deals_submitted": 2},
                                   history=[{"id": "n1", "date": "2024-02-01", "kind": "zoho_note",
                                             "text": "Most of my clients are software startups."}])
        out = sources.import_records(self.engine, [rec])
        self.assertEqual((out["created"], out["kickoff_pending"], out["with_history"]), (1, 1, 1))
        cid = self.ghl.search_contacts(query="lee@example.com", limit=1)[0]["id"]
        p = self.engine.profile_get(cid)
        self.assertEqual(p["values"]["client_types"], ["software startups"])
        self.assertIn("tier:ceo", self.engine.affiliate(cid).tags)
        again = sources.import_records(self.engine, [rec])
        self.assertEqual((again["created"], again["updated"]), (0, 1))

    # ── calls ────────────────────────────────────────────────────────────────
    def call_file(self, email: str) -> dict:
        return {"source": "recorder", "id": "v1", "start_time": f"{TODAY.isoformat()}T15:00:00",
                "participants": [{"name": "Justin"}, {"name": "Dana Reyes", "email": email}],
                "segments": [
                    {"speaker": "Justin", "start": 0, "text": "I record my calls so I don't lose track. Okay?"},
                    {"speaker": "Dana Reyes", "start": 5, "text": "Sure. Most of my clients are small trucking "
                                                                  "companies, usually around $150k for equipment."},
                    {"speaker": "Justin", "start": 20, "text": "I'll set up a funnel page draft for you next week, "
                                                               "and I'll send you the submission link by Friday."},
                    {"speaker": "Dana Reyes", "start": 30, "text": "I'll send you the file for my client tomorrow."}]}

    def test_call_ingest_matches_partner_and_turns_commitments_into_tasks(self):
        inbox = Path(self.tmp.name) / "calls"
        inbox.mkdir()
        (inbox / "dana.json").write_text(json.dumps(self.call_file("dana@example.com")))
        (inbox / "stranger.json").write_text(json.dumps({**self.call_file("nobody@example.com"), "id": "v2",
                                                         "participants": [{"name": "Justin"},
                                                                          {"name": "Pat Stranger",
                                                                           "email": "nobody@example.com"}]}))
        out = calls.poll_drop(self.engine, inbox)
        by_file = {r["file"]: r for r in out["results"]}
        self.assertTrue(by_file["dana.json"]["ok"])
        self.assertTrue(by_file["stranger.json"].get("unmatched"))
        self.assertTrue((inbox / "unmatched" / "stranger.json").exists())
        commitments = by_file["dana.json"]["commitments"]
        self.assertEqual([c["owner"] for c in commitments], ["us", "us", "partner"])
        self.assertEqual(commitments[2]["what"], "send us the file for their client tomorrow")
        titles = [t["title"] for t in self.ghl.list_tasks(self.cid)]
        self.assertEqual(sum(t.startswith("Follow through for Dana") for t in titles), 2)
        p = self.engine.profile_get(self.cid)
        self.assertIn("small trucking companies", p["values"]["client_types"])
        self.assertEqual(p["values"]["deal_size"], ["around $150k"])
        self.assertEqual(len(p["open_loops"]), 3)
        again = calls.poll_drop(self.engine, inbox)
        self.assertEqual(again["results"], [])
        self.engine.record_deal(self.cid, "the file arrived")
        self.assertEqual(len(self.engine.profile_get(self.cid)["open_loops"]), 2)

    def test_phone_call_from_ghl_transcription(self):
        sentences = [{"sentenceIndex": 0, "mediaChannel": 1, "startTime": 0, "transcript": "Hey Dana, it's Justin."},
                     {"sentenceIndex": 1, "mediaChannel": 2, "startTime": 4,
                      "transcript": "Mornings are best to reach me. My clients are mostly in Texas."}]
        self.ghl.record_call(self.cid, "outbound", 600, sentences)
        out = calls.poll_ghl(self.engine)
        self.assertEqual(out["calls"], 1)
        self.assertEqual(self.engine.profile_get(self.cid)["values"]["best_time"], ["mornings"])
        self.assertEqual(calls.poll_ghl(self.engine)["calls"], 0)

    def test_commitments_split_into_separate_promises(self):
        t = calls.CallTranscript("drop", "x", TODAY.isoformat(), 10, [{"name": "Justin"}, {"name": "Dana"}],
                                 [{"speaker": "Justin", "start": 0, "text": "I'll set up a funnel page draft for you "
                                   "next week, and I'll send you the program summary by Friday."}])
        out = extract.RuleExtractor().extract_call(t, {"first_name": "Dana"}, ["Justin"], today=TODAY)
        self.assertEqual([c["what"] for c in out["commitments"]],
                         ["set up a funnel page draft for Dana next week",
                          "send Dana the program summary by Friday"])

    def test_model_facts_are_put_in_the_profiles_terms(self):
        got = extract.tidy([{"slot": "deal_types", "value": "Equipment; working capital"},
                            {"slot": "channel", "value": "A simple page in her email signature so clients can apply"},
                            {"slot": "channel", "value": "texting"},
                            {"slot": "best_time", "value": "Mornings; on the road most afternoons"},
                            {"slot": "deal_size", "value": "Trucks run $100k to $250k, usually around $150k"},
                            {"slot": "client_types", "value": "Small trucking companies; logistics outfits"}])
        self.assertEqual(got, [{"slot": "deal_types", "value": "equipment financing"},
                               {"slot": "deal_types", "value": "working capital"},
                               {"slot": "channel", "value": "text"}, {"slot": "best_time", "value": "mornings"},
                               {"slot": "deal_size", "value": "around $150k"},
                               {"slot": "client_types", "value": "small trucking companies"},
                               {"slot": "client_types", "value": "logistics outfits"}])
        self.assertNotIn("niche", extract.ModelExtractor(["niche", "goals", "open_loop"], client=object()).slots)

    def test_typical_amount_beats_the_first_one_mentioned(self):
        self.assertEqual(extract._money("Trucks run $100k to $250k, so usually around $150k."), "around $150k")


if __name__ == "__main__":
    unittest.main()
