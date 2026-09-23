"""Unit tests for the Funding Affiliate Manager core (stdlib unittest; no network).

    PYTHONPATH=files/local-packages/fam/src python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

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

from fam import cadence  # noqa: E402
from fam.config import DEFAULT_CADENCE, Settings  # noqa: E402
from fam.engine import FamEngine  # noqa: E402
from fam.errors import ApprovalRequired, FamError  # noqa: E402
from fam.ghl import LiveGHL, MockGHL  # noqa: E402

TODAY = date(2026, 9, 23)


def aff(**fields) -> cadence.Affiliate:
    tags = fields.pop("tags", ["aff:active", "src:skool"])
    return cadence.Affiliate(id="c1", name="Jane Doe", first_name="Jane", email="j@example.com",
                             phone="+15555550000", tags=tags, fields=fields)


def ago(days: int) -> str:
    return (TODAY - timedelta(days=days)).isoformat()


class CadenceRules(unittest.TestCase):
    rules = DEFAULT_CADENCE

    def kinds(self, a):
        return [d.kind for d in cadence.evaluate(a, TODAY, self.rules).due]

    def test_lifecycle_thresholds(self):
        cases = [(10, "aff:active"), (50, "aff:quiet"), (100, "aff:dormant"), (200, "aff:dead")]
        for silent, expected in cases:
            a = aff(join_date=ago(400), last_reply_date=ago(silent), last_touch_date=ago(20))
            self.assertEqual(cadence.target_lifecycle(a, TODAY, self.rules)[0], expected, silent)

    def test_recent_deal_is_producing(self):
        a = aff(join_date=ago(400), last_reply_date=ago(100), last_deal_date=ago(5))
        self.assertEqual(cadence.target_lifecycle(a, TODAY, self.rules)[0], "aff:producing")

    def test_sixty_day_silence_gets_personal_checkin(self):
        a = aff(join_date=ago(400), last_reply_date=ago(65), last_touch_date=ago(20))
        self.assertEqual(self.kinds(a), ["personal_checkin"])

    def test_scheduled_followup_beats_everything(self):
        a = aff(join_date=ago(400), last_reply_date=ago(65), last_touch_date=ago(2), next_touch_date=ago(0),
                cadence_note="after tax season")
        due = cadence.evaluate(a, TODAY, self.rules).due
        self.assertEqual(due[0].kind, "scheduled_followup")
        self.assertEqual(due[0].context["cadence_note"], "after tax season")

    def test_biweekly_and_monthly(self):
        a = aff(join_date=ago(400), last_reply_date=ago(10), last_touch_date=ago(15), last_offer_date=ago(10))
        self.assertEqual(self.kinds(a), ["biweekly_touch"])
        a = aff(join_date=ago(400), last_reply_date=ago(10), last_touch_date=ago(15), last_offer_date=ago(31))
        self.assertEqual(self.kinds(a), ["monthly_offer"])
        a = aff(join_date=ago(400), last_reply_date=ago(10), last_touch_date=ago(3))
        self.assertEqual(self.kinds(a), [])

    def test_dnc_gets_nothing(self):
        a = aff(join_date=ago(400), last_reply_date=ago(65), tags=["aff:active", "aff:dnc"])
        self.assertEqual(self.kinds(a), [])

    def test_channel_alternates(self):
        a = aff(join_date=ago(400), last_reply_date=ago(10), last_touch_date=ago(15), last_touch_channel="sms")
        self.assertEqual(cadence.evaluate(a, TODAY, self.rules).due[0].channel, "email")

    def test_classify(self):
        self.assertEqual(cadence.classify_reply("STOP")["intent"], "unsubscribe")
        self.assertEqual(cadence.classify_reply("I have a client who needs about $150k, can I send you the file?")
                         ["intent"], "has_deal")
        self.assertEqual(cadence.classify_reply("busy, check back with me next month")["intent"], "check_back_later")
        self.assertEqual(cadence.classify_reply("can you help me with a funnel page")["service"], "funnel")


class EngineFlows(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Settings.load()
        self.settings = replace(base, state_dir=Path(self.tmp.name) / "state", vault_dir=Path(self.tmp.name) / "vault",
                                ghl_mode="mock", demo_mode=True)
        self.settings.state_dir.mkdir(parents=True)
        self.ghl = MockGHL(self.settings.state_dir / "mock-ghl.json")
        self.engine = FamEngine(settings=self.settings, backend=self.ghl, today=TODAY)
        fields = [{"id": "join_date", "field_value": ago(300)}, {"id": "last_reply_date", "field_value": ago(70)},
                  {"id": "last_touch_date", "field_value": ago(20)}]
        self.synthetic = self.ghl.create_contact({"firstName": "Sam", "lastName": "Synthetic", "email": "s@example.com",
                                                  "phone": "+15555550001", "tags": ["aff:active", "fam:synthetic"],
                                                  "customFields": fields})["id"]
        self.tester = self.ghl.create_contact({"firstName": "Tess", "lastName": "Tester", "email": "t@example.com",
                                               "phone": "+15555550002", "tags": ["aff:active", "fam:test-contact"],
                                               "customFields": fields})["id"]

    def tearDown(self):
        self.tmp.cleanup()

    def batch(self):
        return self.engine.prepare_messages([
            {"contact_id": self.synthetic, "channel": "sms", "body": "Hey Sam, how's business?"},
            {"contact_id": self.tester, "channel": "email", "subject": "Hi", "body": "Hey Tess, how's business?"},
        ])

    def test_execute_requires_human_approval(self):
        action = self.batch()
        with self.assertRaises(ApprovalRequired):
            self.engine.execute(action["action_id"])
        self.engine.request_approval(action["action_id"])
        with self.assertRaises(FamError):
            self.engine.approve(action["action_id"], "wrong-digest", "Justin")
        self.engine.approve(action["action_id"], action["action_digest"], "Justin")
        result = self.engine.execute(action["action_id"])
        self.assertEqual((result["mock"], result["simulated"], result["failed"]), (1, 1, 0))
        with self.assertRaises(ApprovalRequired):
            self.engine.execute(action["action_id"])

    def test_demo_mode_only_reaches_test_contacts(self):
        action = self.batch()
        self.engine.request_approval(action["action_id"])
        self.engine.approve(action["action_id"], action["action_digest"], "Justin")
        self.engine.execute(action["action_id"])
        outbox = {m["contactId"] for m in self.ghl.db["outbox"]}
        self.assertEqual(outbox, {self.tester})
        notes = " ".join(n["body"] for n in self.ghl.list_notes(self.synthetic))
        self.assertIn("SIMULATED SMS", notes)
        synthetic = self.engine.affiliate(self.synthetic)
        self.assertEqual(synthetic.fields["last_touch_date"], TODAY.isoformat())

    def test_sms_gets_opt_out_and_lint_blocks_claims(self):
        action = self.batch()
        self.assertIn("Reply STOP", action["preview"][0]["body"])
        with self.assertRaises(FamError):
            self.engine.prepare_messages([{"contact_id": self.tester, "channel": "sms",
                                           "body": "Guaranteed approval, no credit check!"}])

    def test_stop_reply_sets_dnc_and_blocks_sends(self):
        out = self.engine.record_reply(self.synthetic, "STOP")
        self.assertEqual(out["intent"], "unsubscribe")
        with self.assertRaises(FamError):
            self.engine.prepare_messages([{"contact_id": self.synthetic, "channel": "sms", "body": "hi"}])

    def test_check_back_creates_task_and_next_touch(self):
        self.engine.record_reply(self.synthetic, "busy, check back with me in two weeks",
                                 follow_up_date=(TODAY + timedelta(days=14)).isoformat())
        a = self.engine.affiliate(self.synthetic)
        self.assertEqual(a.fields["next_touch_date"], (TODAY + timedelta(days=14)).isoformat())
        self.assertTrue(any(not t["completed"] for t in self.ghl.list_tasks(self.synthetic)))
        self.assertIn("aff:reactivated", a.tags)  # was 70 days silent -> quiet -> now reactivated by reply

    def test_kill_switch_blocks_execute(self):
        action = self.batch()
        self.engine.request_approval(action["action_id"])
        self.engine.approve(action["action_id"], action["action_digest"], "Justin")
        self.engine.emergency_stop("test")
        with self.assertRaises(FamError):
            self.engine.execute(action["action_id"])
        self.engine.resume("Justin")
        self.assertTrue(self.engine.execute(action["action_id"])["ok"])

    def test_standing_approval_runs_bulk_cadence(self):
        fields = [{"id": "join_date", "field_value": ago(300)}, {"id": "last_reply_date", "field_value": ago(5)},
                  {"id": "last_touch_date", "field_value": ago(16)}, {"id": "last_offer_date", "field_value": ago(5)}]
        cid = self.ghl.create_contact({"firstName": "Bea", "email": "b@example.com", "tags": ["aff:active"],
                                       "customFields": fields})["id"]
        skipped = self.engine.run_standing_cadence()["results"]["biweekly_touch"]
        self.assertEqual(skipped["skipped"], "no standing approval")
        self.engine.activate_standing("biweekly_touch", 100, 30, "Justin")
        ran = self.engine.run_standing_cadence()["results"]["biweekly_touch"]
        self.assertEqual(ran["simulated"], 1)
        self.assertEqual(self.engine.affiliate(cid).fields["last_touch_date"], TODAY.isoformat())
        with self.assertRaises(FamError):
            self.engine.activate_standing("newsletter", 100, 30, "Justin")

    def test_vault_records_the_day(self):
        self.engine.sweep(apply_lifecycle=True)
        daily = (self.settings.vault_dir / "Daily" / f"{TODAY.isoformat()}.md").read_text()
        self.assertIn("Daily sweep", daily)


class GuardRails(unittest.TestCase):
    def test_live_client_requires_location_token(self):
        with self.assertRaises(FamError):
            LiveGHL(token="not-a-pit", location_id="loc")

    def test_live_client_refuses_other_location(self):
        with self.assertRaises(FamError):
            LiveGHL(token="pit-abc", location_id="agency-real-location", expected_location_id="demo-location")

    def test_hermes_config_splits_approvals(self):
        text = (ROOT / "hermes" / "config.template.yaml").read_text()
        core = text.split("fam-core:")[1].split("fam-approvals:")[0]
        approvals = text.split("fam-approvals:")[1].split("\n  ghl:")[0]
        for tool in ("fam_action_approve", "fam_standing_activate", "fam_resume_external_writes"):
            self.assertIn(tool, core.split("exclude:")[1])
            self.assertIn(tool, approvals.split("include:")[1])
        self.assertIn("trust: full", core)
        self.assertIn("trust: untrusted", approvals)


if __name__ == "__main__":
    unittest.main()
