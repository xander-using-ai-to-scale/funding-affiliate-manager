"""Regression tests for the pilot-blocking findings of the 2026-10-03 gap review (items 1–8).

Each proof script in docs/review/proofs/ showed a failure; each test here shows the fixed behavior.

    PYTHONPATH=files/local-packages/fam/src python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "files" / "local-packages" / "fam" / "src"))
os.environ.setdefault("FAM_CONFIG_DIR", str(ROOT / "config"))
os.environ.setdefault("FAM_POLICY_PATH", str(ROOT / "policies" / "permissions.json"))

from fam import cadence, cli, drafting, ghl, kickoff, sources, timezones  # noqa: E402
from fam.config import Settings  # noqa: E402
from fam.engine import FamEngine  # noqa: E402
from fam.errors import FamError, GHLError  # noqa: E402
from fam.ghl import MockGHL  # noqa: E402

TODAY = date(2026, 10, 5)
KICKOFF_BODY = "Hey there, it's Justin with 7 Figures Funding. Open to a quick call this week?"


def ago(days: int) -> str:
    return (TODAY - timedelta(days=days)).isoformat()


class Base(unittest.TestCase):
    backend = MockGHL

    def setUp(self):
        os.environ.pop("FAM_IGNORE_SMS_WINDOW", None)
        self.tmp = tempfile.TemporaryDirectory()
        base = Settings.load()
        self.settings = replace(base, state_dir=Path(self.tmp.name) / "state", vault_dir=Path(self.tmp.name) / "vault",
                                ghl_mode="mock", demo_mode=False,
                                kickoff={**base.kickoff, "default_sender": "Justin", "send_pause_seconds": 0})
        self.settings.state_dir.mkdir(parents=True)
        self.ghl = self.backend(self.settings.state_dir / "mock-ghl.json")
        self.engine = self.at(TODAY)

    def tearDown(self):
        self.tmp.cleanup()

    def at(self, day: date, hour: int = 15) -> FamEngine:
        self.ghl.now_override = f"{day.isoformat()}T{hour:02d}:00:00+00:00"
        return FamEngine(settings=self.settings, backend=self.ghl, today=day)

    def partner(self, first: str, phone: str = "+15555550100", last: str = "Smith", tags=None, **fields) -> str:
        ids = self.settings.field_ids()
        values = {"join_date": "2023-04-11", "last_reply_date": ago(200), "tier": "Executive", "deals_submitted": 3,
                  **fields}
        return self.ghl.create_contact({
            "firstName": first, "lastName": last, "email": f"{first.lower()}@example.com", "phone": phone,
            "tags": tags if tags is not None else ["aff:dormant", "fam:kickoff-pending"],
            "customFields": [{"id": ids[k], "field_value": v} for k, v in values.items() if k in ids]})["id"]

    def approve(self, engine: FamEngine, action: dict) -> None:
        engine.request_approval(action["action_id"])
        engine.approve(action["action_id"], action["action_digest"], "Justin")

    def kickoffs(self, ids: list[str]) -> dict:
        return self.engine.prepare_messages([{"contact_id": c, "channel": "sms", "kind": "kickoff", "body": KICKOFF_BODY}
                                             for c in ids], purpose="kickoff wave 1")

    def delivered(self) -> list[str]:
        return [m["contactId"] for m in self.ghl.db["outbox"]]


# ── 1. the agent can't approve its own sends ─────────────────────────────────
class SelfApproval(Base):
    def test_agent_has_no_shell_file_or_code_tools(self):
        text = (ROOT / "hermes" / "config.template.yaml").read_text()
        denied = next(line for line in text.splitlines() if "disabled_toolsets:" in line)
        for toolset in ("terminal", "code_execution", "file", "browser", "computer_use"):
            self.assertIn(toolset, denied)
        for line in (line for line in text.splitlines() if line.strip().startswith(("slack:", "telegram:"))
                     and "[" in line):
            for toolset in ("terminal", "code_execution", " file"):
                self.assertNotIn(toolset, line)

    def test_human_only_tools_live_only_on_the_approvals_surface(self):
        text = (ROOT / "hermes" / "config.template.yaml").read_text()
        core = next(line for line in text.splitlines() if "exclude: [fam_action_approve" in line)
        approvals = next(line for line in text.splitlines() if "include: [fam_action_approve" in line)
        for tool in ("fam_action_approve", "fam_standing_activate", "fam_resume_external_writes", "fam_outbox_settle"):
            self.assertIn(tool, core)
            self.assertIn(tool, approvals)

    def test_the_command_line_cannot_approve_or_lift_a_stop(self):
        for argv in (["approve", "act_x", "digest", "--approver", "Justin"], ["resume", "--actor", "Justin"]):
            with self.assertRaises(SystemExit), mock.patch("sys.stderr"):
                cli.main(argv)

    def test_file_reads_are_confined_to_knowledge_and_the_vault(self):
        self.assertIn("kickoff", self.engine.read_file("knowledge/funding")["files"][0] + " kickoff")
        playbook = self.engine.read_file("knowledge/funding/05-conversation-playbook.md")
        self.assertGreater(playbook["chars"], 100)
        for path in ("config/ghl-map.json", "vault/../state/fam.sqlite3", "knowledge/../../agent.example.env",
                     "/etc/passwd", "vault/.git/config", "vault/.trash/a/b/c/x.md"):
            with self.assertRaises(FamError, msg=path):
                self.engine.read_file(path)


# ── 2. a slow or failing GoHighLevel call never double-texts or loses a kickoff ─
class SlowSend(MockGHL):
    """GoHighLevel accepts the 2nd text, then the response never arrives (proof p2)."""
    calls = 0

    def send_message(self, *args, **kwargs):
        SlowSend.calls += 1
        result = super().send_message(*args, **kwargs)
        if SlowSend.calls == 2:
            raise TimeoutError("timed out")
        return result


class Idempotent(Base):
    backend = SlowSend

    def setUp(self):
        SlowSend.calls = 0
        super().setUp()

    def test_unknown_outcome_is_held_for_a_person_and_never_resent(self):
        ids = [self.partner(f"P{i}", f"+1555555010{i}") for i in range(4)]
        action = self.kickoffs(ids)
        self.approve(self.engine, action)
        result = self.engine.execute(action["action_id"])
        self.assertEqual((result["state"], result["mock"], result["unknown"]), ("needs_reconcile", 3, 1))
        self.assertEqual(len(self.delivered()), 4)  # GoHighLevel did deliver the 2nd one
        self.assertEqual(self.engine.store.get_action(action["action_id"])["state"], "needs_reconcile")
        # running it again sends nothing new
        again = self.engine.execute(action["action_id"])
        self.assertEqual(again["mock"], 0)
        self.assertEqual(len(self.delivered()), 4)
        # the unsettled partner is never put in another wave
        later = self.at(TODAY + timedelta(days=1))
        wave = kickoff.draft_wave(later, 250, drafter=drafting.TemplateDrafter())
        self.assertFalse(wave["ok"])
        # a person checks GoHighLevel and settles it
        later.settle(action["action_id"], 2, "sent", "Justin")
        self.assertEqual(later.store.get_action(action["action_id"])["state"], "executed")
        self.assertIn(cadence.KICKOFF_SENT, later.affiliate(ids[1]).tags)

    def test_a_rejected_send_is_a_plain_failure(self):
        class Rejects(MockGHL):
            def send_message(self, *a, **k):
                raise GHLError("GoHighLevel POST /conversations/messages returned HTTP 400", status=400)
        self.ghl = Rejects(self.settings.state_dir / "mock-ghl.json")
        self.engine = self.at(TODAY)
        cid = self.partner("Dana")
        action = self.kickoffs([cid])
        self.approve(self.engine, action)
        result = self.engine.execute(action["action_id"])
        self.assertEqual((result["state"], result["failed"]), ("executed_with_errors", 1))
        self.assertFalse(self.engine.store.kickoff_claimed([cid]))  # not delivered, so a later wave may retry

    def test_live_client_turns_timeouts_into_unknown_outcomes(self):
        live = ghl.LiveGHL(token="pit-test", location_id="loc1")
        live.MIN_INTERVAL_SECONDS = 0
        with mock.patch.object(ghl.request, "urlopen", side_effect=TimeoutError("read timed out")):
            with self.assertRaises(GHLError) as caught:
                live.send_message("c1", "sms", "hi")
        self.assertFalse(caught.exception.rejected)
        self.assertTrue(GHLError("bad request", status=400).rejected)
        self.assertFalse(GHLError("rate limited", status=429).rejected)


class Bookkeeping(Base):
    def test_a_failed_crm_update_after_delivery_never_causes_a_second_kickoff(self):
        class Flaky(MockGHL):
            fail = True

            def update_contact(self, cid, payload):
                if self.fail and "customFields" in payload:
                    raise GHLError("GoHighLevel PUT /contacts/x returned HTTP 429", status=429)
                return super().update_contact(cid, payload)
        self.ghl = Flaky(self.settings.state_dir / "mock-ghl.json")
        self.engine = self.at(TODAY)
        cid = self.partner("Dana")
        wave = kickoff.draft_wave(self.engine, 250, drafter=drafting.TemplateDrafter())
        self.approve(self.engine, wave["action"])
        result = self.engine.execute(wave["action"]["action_id"])
        self.assertEqual((result["mock"], result["failed"]), (1, 0))  # it went out; it isn't a failure
        self.assertEqual(self.engine.outbox_status()["bookkeeping_pending"], 1)
        self.ghl.fail = False
        later = self.at(TODAY + timedelta(days=1))
        self.assertFalse(kickoff.draft_wave(later, 250, drafter=drafting.TemplateDrafter())["ok"])
        self.ghl.remove_tags(cid, [cadence.KICKOFF_PENDING])  # tags lost entirely: enroll still won't re-queue her
        self.assertEqual(kickoff.enroll(later)["tagged"], 0)
        self.assertEqual(later.finish_bookkeeping()["finished"], 1)
        self.assertIn(cadence.KICKOFF_SENT, later.affiliate(cid).tags)
        self.assertEqual(len(self.delivered()), 1)


# ── 3. overlapping waves, expiry, and messages that went stale before sending ─
class Waves(Base):
    def test_a_second_wave_cannot_take_partners_held_by_an_open_one(self):
        for i in range(3):
            self.partner(f"P{i}", f"+1555555010{i}")
        first = kickoff.draft_wave(self.engine, 250, drafter=drafting.TemplateDrafter())
        later = self.at(TODAY + timedelta(days=1))
        second = kickoff.draft_wave(later, 250, drafter=drafting.TemplateDrafter())
        self.assertFalse(second["ok"])
        self.assertEqual(second["held_by_open_waves"], 3)
        self.approve(later, first["action"])
        later.execute(first["action"]["action_id"])
        self.assertEqual(sorted(self.delivered()), sorted(set(self.delivered())))
        self.assertEqual(len(self.delivered()), 3)

    def test_an_unapproved_wave_expires_and_frees_its_partners(self):
        for i in range(2):
            self.partner(f"P{i}", f"+1555555010{i}")
        first = kickoff.draft_wave(self.engine, 250, drafter=drafting.TemplateDrafter())
        old = (datetime.now(UTC) - timedelta(hours=72)).replace(microsecond=0).isoformat()
        self.engine.store.update_action(first["action"]["action_id"], created_at=old)
        second = kickoff.draft_wave(self.engine, 250, drafter=drafting.TemplateDrafter())
        self.assertTrue(second["ok"])
        self.assertEqual(self.engine.store.get_action(first["action"]["action_id"])["state"], "expired")
        with self.assertRaises(FamError):
            self.engine.approve(first["action"]["action_id"], first["action"]["action_digest"], "Justin")

    def test_a_kickoff_is_skipped_when_the_partner_wrote_first(self):
        a, b = self.partner("Ann", "+15555550101"), self.partner("Bob", "+15555550102")
        wave = kickoff.draft_wave(self.engine, 250, drafter=drafting.TemplateDrafter())
        self.approve(self.engine, wave["action"])
        self.engine.record_reply(a, "Hey! Mostly trucking clients these days.")
        result = self.engine.execute(wave["action"]["action_id"])
        self.assertEqual((result["mock"], result["skipped"]), (1, 1))
        self.assertEqual(self.delivered(), [b])

    def test_a_reply_is_skipped_when_they_wrote_again_after_it_was_drafted(self):
        cid = self.partner("Dana", tags=["aff:dormant", "fam:kickoff-done"])
        self.ghl.record_inbound(cid, "sms", "Mostly trucking clients.")
        action = self.engine.prepare_messages([{"contact_id": cid, "channel": "sms", "kind": "reply",
                                                "body": "Got it, Dana. What are you working toward this year?"}])
        self.approve(self.engine, action)
        self.ghl.now_override = f"{TODAY.isoformat()}T16:00:00+00:00"
        self.ghl.record_inbound(cid, "sms", "Actually, can you call me Thursday at 2pm?")
        result = self.engine.execute(action["action_id"])
        self.assertEqual(result["skipped"], 1)
        self.assertFalse(self.delivered())

    def test_a_reply_batch_can_be_cancelled_and_redrafted(self):
        cid = self.partner("Dana", tags=["aff:dormant", "fam:kickoff-done"])
        self.ghl.record_inbound(cid, "sms", "Mostly trucking clients.")
        reply = {"contact_id": cid, "channel": "sms", "kind": "reply"}
        first = self.engine.prepare_messages([{**reply, "body": "Got it, Dana. Mostly local?"}])
        with self.assertRaises(FamError):
            self.engine.prepare_messages([{**reply, "body": "Thanks, Dana. Mostly local?"}])
        self.engine.cancel_action(first["action_id"], "redraft")
        self.assertTrue(self.engine.prepare_messages([{**reply, "body": "Thanks, Dana. Mostly local?"}])["action_id"])

    def test_an_open_check_in_batch_never_blocks_answering_someone_who_wrote(self):
        cid = self.partner("Dana", tags=["aff:dormant", "fam:kickoff-done"])
        checkin = self.engine.prepare_messages([{"contact_id": cid, "channel": "sms", "body": "Hey Dana, quick one?"}])
        self.approve(self.engine, checkin)
        self.ghl.record_inbound(cid, "sms", "I have a client who needs $200k for trucks")
        row = self.engine.reply_inbox()[0]
        self.engine.record_reply(cid, row["last_message"], message_ids=row["message_ids"])
        reply = self.engine.prepare_messages([{"contact_id": cid, "channel": "sms", "kind": "reply",
                                               "body": "That's great, Dana. I'll give you a call today."}])
        self.assertEqual(self.engine.execute(checkin["action_id"])["skipped"], 1)  # the check-in no longer fits
        self.approve(self.engine, reply)
        self.assertEqual(self.engine.execute(reply["action_id"])["mock"], 1)
        self.assertEqual(len(self.delivered()), 1)


# ── 4. the stop switch and quiet hours, per message, in the recipient's time zone ─
class StopAndWindow(Base):
    def test_a_stop_mid_wave_stops_the_rest_and_resume_finishes_it(self):
        settings = self.settings

        class Stopper(MockGHL):
            calls = 0

            def send_message(self, *a, **k):
                Stopper.calls += 1
                if Stopper.calls == 2:  # the manager hits stop from another process
                    FamEngine(settings=settings, backend=self, today=TODAY).emergency_stop("wrong template!")
                return super().send_message(*a, **k)
        self.ghl = Stopper(self.settings.state_dir / "mock-ghl.json")
        self.engine = self.at(TODAY)
        ids = [self.partner(f"P{i}", f"+155555501{i:02d}") for i in range(6)]
        action = self.kickoffs(ids)
        self.approve(self.engine, action)
        result = self.engine.execute(action["action_id"])
        self.assertEqual((result["state"], result["mock"], result["pending"]), ("paused", 2, 4))
        with self.assertRaises(FamError):
            self.engine.execute(action["action_id"])
        self.engine.resume("Justin")  # a human lifts the stop (approvals surface)
        done = self.engine.execute(action["action_id"])
        self.assertEqual((done["state"], done["mock"]), ("executed", 4))
        self.assertEqual(sorted(self.delivered()), sorted(ids))

    def test_quiet_hours_are_the_recipients(self):
        ny, la, hi = (self.partner("Nia", "+12125550101"), self.partner("Lou", "+14155550102"),
                      self.partner("Kai", "+18085550103"))
        action = self.kickoffs([ny, la, hi])
        self.approve(self.engine, action)
        self.engine.clock = lambda: datetime(2026, 10, 5, 13, 0, tzinfo=UTC)  # 9:00 NY, 6:00 LA, 3:00 Honolulu
        first = self.engine.execute(action["action_id"])
        self.assertEqual((first["state"], first["mock"], first["deferred"]), ("paused", 1, 2))
        self.assertEqual(self.delivered(), [ny])
        self.engine.clock = lambda: datetime(2026, 10, 5, 22, 0, tzinfo=UTC)  # 18:00 NY, 15:00 LA, 12:00 Honolulu
        second = self.engine.execute(action["action_id"])
        self.assertEqual((second["state"], second["mock"]), ("executed", 2))
        self.assertEqual(sorted(self.delivered()), sorted([ny, la, hi]))

    def test_held_texts_go_out_on_their_own_when_the_window_opens(self):
        ny, la = self.partner("Nia", "+12125550101"), self.partner("Lou", "+14155550102")
        action = self.kickoffs([ny, la])
        self.approve(self.engine, action)
        self.engine.clock = lambda: datetime(2026, 10, 5, 13, 0, tzinfo=UTC)
        self.assertEqual(self.engine.execute(action["action_id"])["state"], "paused")
        self.assertEqual(self.engine.resume_paused()["resumed"], [])  # LA is still asleep: nothing to say
        self.engine.clock = lambda: datetime(2026, 10, 5, 17, 0, tzinfo=UTC)  # 10:00 in Los Angeles
        done = self.engine.resume_paused()["resumed"]
        self.assertEqual((done[0]["state"], done[0]["sent"]), ("executed", 1))
        self.assertEqual(sorted(self.delivered()), sorted([ny, la]))

    def test_a_send_cut_off_mid_flight_is_held_for_a_person(self):
        ids = [self.partner(f"P{i}", f"+1555555010{i}") for i in range(2)]
        action = self.kickoffs(ids)
        self.approve(self.engine, action)
        self.engine.store.use_approval(self.engine.store.get_action(action["action_id"])["approval_id"])
        self.engine.store.outbox_init(action["action_id"], action["preview"])
        self.engine.store.outbox_set(action["action_id"], 1, state="sending")
        with self.engine.store.connection() as conn:  # the run that claimed it was killed 20 minutes ago
            conn.execute("UPDATE outbox SET updated_at = '2000-01-01T00:00:00+00:00' WHERE n = 1")
        self.engine.store.update_action(action["action_id"], state="executing")
        result = self.engine.execute(action["action_id"])
        self.assertEqual((result["state"], result["mock"]), ("needs_reconcile", 1))
        self.assertEqual(len(self.engine.outbox_status()["unknown"]), 1)

    def test_unknown_area_codes_need_the_window_open_coast_to_coast(self):
        nine_am_eastern = datetime(2026, 10, 5, 13, 0, tzinfo=UTC)
        self.assertTrue(timezones.in_window("+12125550101", nine_am_eastern, 9, 20))
        self.assertFalse(timezones.in_window("+15555550100", nine_am_eastern, 9, 20))
        self.assertFalse(timezones.in_window("+15415550100", datetime(2026, 10, 5, 15, 30, tzinfo=UTC), 9, 20))

    def test_the_window_override_never_applies_to_a_real_text(self):
        os.environ["FAM_IGNORE_SMS_WINDOW"] = "1"
        try:
            self.engine.clock = lambda: datetime(2026, 10, 5, 4, 0, tzinfo=UTC)  # midnight in New York
            aff = self.engine.affiliate(self.partner("Nia", "+12125550101"))
            self.assertFalse(self.engine._send_window_open(aff, {"channel": "sms", "delivery": "live"}))
            self.assertTrue(self.engine._send_window_open(aff, {"channel": "sms", "delivery": "mock"}))
        finally:
            os.environ.pop("FAM_IGNORE_SMS_WINDOW", None)


# ── 5. the approver sees what the partner said ───────────────────────────────
class ReviewContext(Base):
    def test_review_and_card_show_their_text_the_reading_and_mismatches(self):
        cid = self.partner("Dana", tags=["aff:dormant", "fam:kickoff-sent"])
        self.ghl.send_message(cid, "sms", KICKOFF_BODY)
        self.ghl.record_inbound(cid, "sms", "Sounds good, Wednesday afternoon? <!channel> @here")
        action = self.engine.prepare_messages([{"contact_id": cid, "channel": "sms", "kind": "reply", "move": "question",
                                                "body": "Good question, Dana. Let me get you the exact answer today."}])
        card = self.engine.request_approval(action["action_id"])
        review = Path(card["review_file"]).read_text()
        self.assertIn("**They wrote**", review)
        self.assertIn("Wednesday afternoon", review)
        self.assertIn("**Read as:** book_call", review)
        self.assertIn("doesn't confirm it", review)
        self.assertIn("answers it like a question", review)
        self.assertIn("They wrote:", card["approval_card"])
        self.assertIn("⚠️", card["approval_card"])
        self.assertNotIn("<!channel>", card["approval_card"])
        self.assertNotIn("<!channel>", "".join(card["review_thread"]))
        self.assertIn("flagged", card["summary"])

    def test_a_big_wave_is_read_in_the_vault_not_pasted_into_slack(self):
        for i in range(40):
            self.partner(f"P{i}", f"+1555555{i:04d}")
        wave = kickoff.draft_wave(self.engine, 250, drafter=drafting.TemplateDrafter())
        card = self.engine.request_approval(wave["action"]["action_id"])
        self.assertEqual(card["review_thread"], [])
        self.assertIn("open the file in Obsidian", card["approval_card"])
        self.assertEqual(len(list((self.settings.vault_dir / "Reviews").glob("*.md"))), 1)


# ── 6. reply triage: the digest lines that went wrong ────────────────────────
class Triage(Base):
    def test_digest_lines_are_read_correctly(self):
        cases = {"Sounds good, Wednesday afternoon?": "book_call",
                 "Deals are typically $150k": "general_reply",
                 "Not a good time right now, maybe next quarter.": "check_back_later",
                 "I'd like to send you a deal a month": "will_send_deals",
                 "When do commissions get paid out on funded deals?": "commission_question",
                 "How do I submit a deal again? Lost the link.": "question",
                 "Slammed right now, can you check back with me in a few weeks?": "check_back_later",
                 "Busy today, try Thursday?": "book_call",
                 "not interested": "not_interested",
                 "I closed my business last year": "not_interested"}
        for text, intent in cases.items():
            self.assertEqual(cadence.classify_reply(text)["intent"], intent, text)
        self.assertEqual(cadence.classify_reply("Sounds good, Wednesday afternoon?")["proposed_time"],
                         "Wednesday afternoon")

    def test_next_moves(self):
        d = drafting.TemplateDrafter()
        kicked = [{"kind": "kickoff_sent", "summary": "Hey Dana... Open to a quick call this week?"}]
        p = {"first_name": "Dana", "history": kicked, "values": {},
             "open_questions": [{"slot": "goals", "question": "What are you working toward this year?"},
                                {"slot": "client_types", "question": "What kind of clients are you working with most "
                                                                     "these days?"}]}
        reply = d.reply(p, "Justin", "book_call", "Sounds good, Wednesday afternoon?")
        self.assertEqual(reply["move"], "confirm_time")
        self.assertTrue(reply["body"].startswith("Wednesday afternoon works"))
        self.assertEqual(d.reply(p, "Justin", "will_send_deals", "a deal a month")["move"], "ask_for_deal")
        deal = "Perfect timing. I actually have a client who needs about $50k for a line of credit. Can I send you the file?"
        self.assertEqual(cadence.classify_reply(deal)["intent"], "has_deal")
        self.assertEqual(d.next_move(p, "has_deal", deal)["move"], "has_deal")  # not the booking link
        self.assertNotIn("send the file", d.reply(p, "Justin", "has_deal", "I have a client who needs $200k")["body"])
        # they prefer text: discovery, not a call ask
        p_texter = {**p, "history": [{"kind": "reply", "summary": "x"}, {"kind": "reply", "summary": "y"},
                                     {"kind": "message_sent", "summary": "Got it, Dana. What's next?"}]}
        self.assertEqual(d.next_move(p_texter, "general_reply", "Texting is easier for me")["move"], "discover")
        # a question we just asked isn't asked again, and the opening line changes
        asked = [{"kind": "message_sent", "summary": "Great to hear from you, Dana! What are you working toward this year?"},
                 {"kind": "reply", "summary": "(general_reply) hey"}] + kicked
        move = d.next_move({**p, "history": asked}, "general_reply", "Hard to say")
        self.assertEqual(move.get("slot"), "client_types")
        body = d.reply({**p, "history": asked}, "Justin", "general_reply", "Hard to say")["body"]
        self.assertFalse(body.startswith("Great to hear from you"))

    def test_stop_help_and_wrong_numbers_are_not_replies(self):
        a, b, c = (self.partner("Ann", "+15555550101"), self.partner("Bob", "+15555550102"),
                   self.partner("Cy", "+15555550103"))
        wave = kickoff.draft_wave(self.engine, 250, drafter=drafting.TemplateDrafter())
        self.approve(self.engine, wave["action"])
        self.engine.execute(wave["action"]["action_id"])
        later = self.at(TODAY + timedelta(days=1))
        stop, wrong, help_ = (later.record_reply(a, "STOP"), later.record_reply(b, "wrong number"),
                              later.record_reply(c, "HELP"))
        for result in (stop, wrong, help_):
            self.assertFalse(result["counts_as_reply"])
            self.assertFalse(result["draft_reply"])
        for cid in (a, b, c):
            aff = later.affiliate(cid)
            self.assertFalse(aff.fields.get("last_reply_date", "").startswith(TODAY.isoformat()[:8] + "06"))
            self.assertNotEqual(aff.lifecycle, "aff:reactivated")
        self.assertIn(cadence.WRONG_NUMBER_TAG, later.affiliate(b).tags)
        self.assertIn(cadence.KICKOFF_DONE, later.affiliate(c).tags)  # no automated nudge after HELP
        self.assertEqual(sum(v["replied"] for v in later.graph.variant_stats().values()), 0)
        self.assertEqual(later.scorecard()["replied_last_30d"], 0)
        with self.assertRaises(FamError):  # no more texts to a wrong number
            later.prepare_messages([{"contact_id": b, "channel": "sms", "body": "Hey Bob, quick one?"}])


# ── 7. the inbox never drops a reply ─────────────────────────────────────────
class Inbox(Base):
    def test_a_reply_under_our_next_message_is_still_triaged(self):
        cid = self.partner("Dana")
        self.ghl.record_inbound(cid, "sms", "I have a client who needs $200k for trucks, can you call me?")
        self.ghl.send_message(cid, "sms", "Hey Dana, quick reminder about this month's webinar.")
        self.ghl.mark_read(cid)  # someone opened the thread in the GoHighLevel app
        rows = self.engine.reply_inbox()
        self.assertEqual([r["last_message"][:22] for r in rows], ["I have a client who ne"])
        self.engine.record_reply(cid, rows[0]["last_message"], message_ids=rows[0]["message_ids"])
        self.assertEqual(self.engine.reply_inbox(), [])

    def test_oldest_first_and_nothing_starves(self):
        ids = [self.partner(f"Q{i}", f"+155555502{i:02d}") for i in range(30)]
        for i, cid in enumerate(ids):
            self.ghl.now_override = f"{TODAY.isoformat()}T15:{i:02d}:00+00:00"
            self.ghl.record_inbound(cid, "sms", f"reply {i}")
        page = self.engine.reply_inbox_page(limit=25)
        self.assertEqual(page["rows"][0]["last_message"], "reply 0")
        self.assertEqual(page["remaining"], 5)
        for r in page["rows"]:
            self.engine.record_reply(r["contact"]["id"], r["last_message"], message_ids=r["message_ids"])
        rest = self.engine.reply_inbox_page(limit=25)
        self.assertEqual([r["last_message"] for r in rest["rows"]], [f"reply {i}" for i in range(25, 30)])

    def test_the_cron_monitor_output_is_stable(self):
        cid = self.partner("Dana")
        self.ghl.record_inbound(cid, "sms", "hey")
        ids = lambda: sorted(i for r in self.engine.reply_inbox_page(10**6)["rows"] for i in r["message_ids"])  # noqa: E731
        self.assertEqual(ids(), ids())
        self.assertEqual(len(ids()), 1)
        with mock.patch("sys.stdout") as out, mock.patch.object(cli, "FamEngine", lambda settings: self.engine):
            cli.main(["inbox", "--ids"])
        printed = "".join(c.args[0] for c in out.write.call_args_list)
        self.assertIn(ids()[0], printed)
        self.assertIn("retry 2026-10-05T18", printed)  # pending work re-wakes the agent hourly


# ── 8. opt-outs, HELP, quoted text, email compliance ─────────────────────────
class OptOut(Base):
    def test_the_opt_out_line_is_added_unless_that_exact_sentence_is_there(self):
        cid = self.partner("Dana", tags=["aff:dormant", "fam:kickoff-done"])
        action = self.engine.prepare_messages([{"contact_id": cid, "channel": "sms", "kind": "personal_checkin",
                                                "body": "Hey Dana, your team has been nonstop! Got 10 min this week?"}])
        self.assertTrue(action["preview"][0]["body"].endswith("Reply STOP to opt out."))

    def test_more_ways_to_say_stop_and_quoted_text(self):
        for text in ("Take me off your list", "lose my number", "Please don't contact me again", "no more texts"):
            self.assertEqual(cadence.classify_reply(text)["intent"], "unsubscribe", text)
        quoted = "Call me Tuesday\n\nOn Mon, Oct 5, 2026 at 9:02 AM Justin wrote:\n> Reply UNSUBSCRIBE and we'll stop"
        self.assertEqual(cadence.classify_reply(quoted)["intent"], "book_call")
        self.assertEqual(cadence.classify_reply("HELP")["intent"], "help")

    def test_email_carries_a_footer_and_live_email_needs_the_postal_address(self):
        cid = self.partner("Dana", phone="", tags=["aff:dormant", "fam:kickoff-done"])
        body = "Hey Dana, it's Justin. Open to a quick call this week?"
        action = self.engine.prepare_messages([{"contact_id": cid, "channel": "email", "subject": "Hi", "body": body}])
        self.assertIn("Reply UNSUBSCRIBE", action["preview"][0]["body"])
        live = FamEngine(settings=replace(self.settings, ghl_mode="live"), backend=self.ghl, today=TODAY)
        with self.assertRaises(FamError):
            live.prepare_messages([{"contact_id": cid, "channel": "email", "subject": "Hi", "body": body + " Thanks!"}])

    def test_an_email_opt_out_from_zoho_blocks_email_only(self):
        rec = sources.SourceRecord("zoho", "z1", "Erin", "Lee", "erin@example.com", "+15555550199",
                                   {"tier": "Executive"}, [], dnc=False, no_email=True)
        sources.import_records(self.engine, [rec])
        aff = next(a for a in self.engine.affiliates() if a.first_name == "Erin")
        self.assertFalse(aff.is_dnc)
        self.assertTrue(aff.no_email)
        self.assertEqual(kickoff.channel_for(aff), "sms")
        with self.assertRaises(FamError):
            self.engine.prepare_messages([{"contact_id": aff.id, "channel": "email", "subject": "Hi",
                                           "body": "Hey Erin, quick call this week?"}])


if __name__ == "__main__":
    unittest.main()
