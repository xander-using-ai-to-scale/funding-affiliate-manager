"""`fam` — command line for the operator, cron, and the demo.

    fam status | sweep [--apply] | queue | brief ID | inbox | scorecard | actions [--state S]
    fam approve ACTION DIGEST --approver NAME [--except 4,17]   (a human at the terminal)
    fam execute ACTION
    fam cadence run-standing                      (cron: bulk cadence under standing approvals)
    fam stop "reason" | fam resume --actor NAME
    fam ghl bootstrap [--apply]                   (live location setup; dry-run by default)
    fam sim seed [--count 250] [--live --test-email E --test-phone P --test-name N]
    fam sim run [--days 30] [--out sim-output]
    fam sim inbound --text "..." [--contact ID] [--channel sms]   (mock CRM: play an affiliate replying)
    fam sim relationships [--days 30] [--out sim-output/relationships]   (kickoff → replies → calls → profiles)

  Relationship graph
    fam profile ID                                 the partner's profile
    fam graph query [--tier T] [--slot S --contains X] [--hub H] [--min N]
    fam graph stats | fam graph reindex            (rebuild the facts index from the vault)
    fam import csv PARTNERS.csv [--history H.csv] | fam import zoho [--limit N] | fam import ghl [--no-kickoff]
    fam kickoff enroll | draft [--size N] [--model|--template] | nudge | status
    fam calls ingest [--ghl] [--file F --contact ID]   (default: the call inbox folder)
    fam plan ID                                    draft and save the partner's revenue plan
    fam example partner-journey [--out examples/partner-journey] [--model]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from . import cadence
from .config import Settings
from .engine import FamEngine
from .errors import FamError


def _print(value) -> None:
    print(json.dumps(value, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="fam", description="Funding Affiliate Manager")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sp = sub.add_parser("sweep")
    sp.add_argument("--apply", action="store_true", help="apply lifecycle tag/stage changes")
    sub.add_parser("queue")
    sp = sub.add_parser("brief")
    sp.add_argument("contact_id")
    sub.add_parser("inbox")
    sub.add_parser("scorecard")
    sp = sub.add_parser("actions")
    sp.add_argument("--state", default="")
    sp = sub.add_parser("approve")
    sp.add_argument("action_id")
    sp.add_argument("digest")
    sp.add_argument("--approver", required=True)
    sp.add_argument("--except", dest="exclude", default="", help="message numbers to hold back, e.g. 4,17")
    sp = sub.add_parser("profile")
    sp.add_argument("contact_id")
    sp = sub.add_parser("graph")
    sp.add_argument("what", choices=["query", "stats", "reindex"])
    sp.add_argument("--tier", default="")
    sp.add_argument("--niche", default="")
    sp.add_argument("--slot", default="")
    sp.add_argument("--contains", default="")
    sp.add_argument("--hub", default="")
    sp.add_argument("--min", type=int, default=0)
    sp.add_argument("--limit", type=int, default=50)
    sp = sub.add_parser("import")
    sp.add_argument("source", choices=["csv", "zoho", "ghl"])
    sp.add_argument("path", nargs="?", default="")
    sp.add_argument("--history", default="")
    sp.add_argument("--limit", type=int, default=0)
    sp.add_argument("--no-kickoff", action="store_true", help="don't tag quiet partners for the kickoff")
    sp = sub.add_parser("kickoff")
    sp.add_argument("what", choices=["enroll", "draft", "nudge", "status"])
    sp.add_argument("--size", type=int, default=0)
    group = sp.add_mutually_exclusive_group()
    group.add_argument("--model", action="store_true", help="draft with FAM_DRAFT_MODEL (default when it is set)")
    group.add_argument("--template", action="store_true", help="draft from the framework templates only")
    sp = sub.add_parser("calls")
    sp.add_argument("what", choices=["ingest"])
    sp.add_argument("--ghl", action="store_true", help="GoHighLevel phone calls instead of the call inbox")
    sp.add_argument("--file", default="")
    sp.add_argument("--contact", default="")
    sp = sub.add_parser("plan")
    sp.add_argument("contact_id")
    sp = sub.add_parser("example")
    sp.add_argument("what", choices=["partner-journey"])
    sp.add_argument("--out", default="examples/partner-journey")
    sp.add_argument("--model", action="store_true", help="real model drafts and extraction (needs FAM_DRAFT_MODEL)")
    sp = sub.add_parser("execute")
    sp.add_argument("action_id")
    sp = sub.add_parser("cadence")
    sp.add_argument("what", choices=["run-standing"])
    sp = sub.add_parser("stop")
    sp.add_argument("reason")
    sp = sub.add_parser("resume")
    sp.add_argument("--actor", required=True)
    sp = sub.add_parser("ghl")
    sp.add_argument("what", choices=["bootstrap"])
    sp.add_argument("--apply", action="store_true")
    sp = sub.add_parser("sim")
    sp.add_argument("what", choices=["seed", "run", "inbound", "relationships"])
    sp.add_argument("--count", type=int, default=250)
    sp.add_argument("--days", type=int, default=30)
    sp.add_argument("--out", default="sim-output")
    sp.add_argument("--start", default="")
    sp.add_argument("--live", action="store_true", help="seed the real demo location instead of the mock CRM")
    sp.add_argument("--into-agent", action="store_true",
                    help="seed the agent's own mock CRM (FAM_GHL_MODE=mock) so it can be demoed in Slack")
    sp.add_argument("--test-email", default="")
    sp.add_argument("--test-phone", default="")
    sp.add_argument("--test-name", default="")
    sp.add_argument("--contact", default="", help="inbound: contact id (default: the first fam:test-contact)")
    sp.add_argument("--text", default="", help="inbound: the reply text")
    sp.add_argument("--channel", default="sms", choices=["sms", "email"])
    args = p.parse_args(argv)

    try:
        settings = Settings.load()
        if args.cmd == "example":
            from . import example
            _print(example.partner_journey(settings, Path(args.out).resolve(), use_model=args.model))
            return 0
        if args.cmd == "sim" and args.what == "relationships":
            from . import relsim
            start = date.fromisoformat(args.start) if args.start else date.today()
            out = Path(args.out if args.out != "sim-output" else "sim-output/relationships").resolve()
            relsim.run(settings, out, start=start, days=args.days, count=args.count)
            print((out / "report.md").read_text())
            print(f"\nreport: {out / 'report.md'}\nvault:  {out / 'vault'}")
            return 0
        if args.cmd == "sim":
            from . import sim
            start = date.fromisoformat(args.start) if args.start else date.today()
            out = Path(args.out).resolve()
            if args.what == "inbound":
                if settings.ghl_mode != "mock":
                    raise FamError("sim inbound only writes to the mock CRM; in live mode, reply from the test phone")
                if not args.text.strip():
                    raise FamError("--text is required")
                from .ghl import open_backend
                backend = open_backend(settings)
                contact_id = args.contact
                if not contact_id:
                    tests = backend.search_contacts(tags=[cadence.TEST_CONTACT_TAG], limit=1)
                    if not tests:
                        raise FamError("no fam:test-contact in the mock CRM; pass --contact")
                    contact_id = tests[0]["id"]
                _print(backend.record_inbound(contact_id, args.channel, args.text.strip()))
                return 0
            if args.what == "seed":
                tests = []
                if args.test_email or args.test_phone:
                    first, _, last = (args.test_name or "Test Contact").partition(" ")
                    tests.append({"email": args.test_email, "phone": args.test_phone,
                                  "first_name": first, "last_name": last or "Contact"})
                if args.into_agent:
                    if settings.ghl_mode != "mock":
                        raise FamError("--into-agent is for FAM_GHL_MODE=mock; use --live for the real demo location")
                    if not tests:
                        tests = [{"email": "demo.tester@example.com", "phone": "+15550000001",
                                  "first_name": "Demo", "last_name": "Tester"}]
                    _print(sim.seed(settings, args.count, start, tests))
                elif args.live:
                    if settings.ghl_mode != "live":
                        raise FamError("--live needs FAM_GHL_MODE=live and a bootstrapped ghl-map.json")
                    _print(sim.seed(settings, args.count, start, tests))
                else:
                    if not tests:
                        tests = [{"email": f"test{i}@example.com", "phone": f"+1555000000{i}",
                                  "first_name": "Demo", "last_name": f"Tester{i}"} for i in (1, 2, 3)]
                    _print(sim.seed(sim.sim_settings(settings, out), args.count, start, tests))
            else:
                report = sim.run(sim.sim_settings(settings, out), args.days, start, out)
                print((out / "report.md").read_text())
                print(f"\nreport: {out / 'report.md'}\nvault:  {out / 'vault'}")
                del report
            return 0
        if args.cmd == "ghl":
            from .bootstrap import bootstrap
            _print(bootstrap(settings, dry_run=not args.apply))
            return 0
        engine = FamEngine(settings=settings)
        if args.cmd == "status":
            _print(engine.status())
        elif args.cmd == "sweep":
            _print(engine.sweep(apply_lifecycle=args.apply))
        elif args.cmd == "queue":
            _print(engine.daily_queue())
        elif args.cmd == "brief":
            _print(engine.affiliate_brief(args.contact_id))
        elif args.cmd == "inbox":
            _print(engine.reply_inbox())
        elif args.cmd == "scorecard":
            _print(engine.scorecard())
        elif args.cmd == "actions":
            _print([engine._action_view(r) for r in engine.store.list_actions(args.state)])
        elif args.cmd == "approve":
            held = [int(x) for x in args.exclude.replace(" ", "").split(",") if x]
            _print(engine.approve(args.action_id, args.digest, args.approver, held))
        elif args.cmd == "profile":
            _print(engine.profile_get(args.contact_id))
        elif args.cmd == "graph":
            if args.what == "stats":
                _print(engine.graph.stats())
            elif args.what == "reindex":
                _print(engine.graph.reindex())
            else:
                _print(engine.graph.query(tier=args.tier, niche=args.niche, slot=args.slot, contains=args.contains,
                                          hub=args.hub, min_completeness=args.min, limit=args.limit))
        elif args.cmd == "import":
            from . import sources
            if args.source == "csv":
                if not args.path:
                    raise FamError("fam import csv PARTNERS.csv [--history HISTORY.csv]")
                src = sources.CsvSource(Path(args.path), Path(args.history) if args.history else None).records()
            elif args.source == "zoho":
                src = sources.ZohoSource(sources.zoho_mapping(settings)).records(limit=args.limit)
            else:
                src = sources.GhlHistorySource(engine).records()
            _print(sources.import_records(engine, src, mark_kickoff=not args.no_kickoff, limit=args.limit))
        elif args.cmd == "kickoff":
            from . import drafting, kickoff
            use = True if args.model else False if args.template else None
            drafter = drafting.open_drafter(settings.kickoff, use_model=use)
            if args.what == "enroll":
                _print(kickoff.enroll(engine))
            elif args.what == "draft":
                result = kickoff.draft_wave(engine, args.size, drafter=drafter)
                if result.get("ok"):
                    print(result["action"]["approval_card"] + "\n")
                _print({k: v for k, v in result.items() if k not in {"action", "drafts"}})
            elif args.what == "nudge":
                result = kickoff.draft_nudges(engine, drafter=drafter)
                print(result["action"]["approval_card"] if result.get("ok") else json.dumps(result))
            else:
                _print(kickoff.status(engine))
        elif args.cmd == "calls":
            from . import calls
            if args.file:
                _print(calls.ingest(engine, calls.parse_file(Path(args.file).expanduser()), contact_id=args.contact))
            elif args.ghl:
                _print(calls.poll_ghl(engine, contact_id=args.contact))
            else:
                _print(calls.poll_drop(engine))
        elif args.cmd == "plan":
            _print(engine.write_revenue_plan(args.contact_id))
        elif args.cmd == "execute":
            _print(engine.execute(args.action_id))
        elif args.cmd == "cadence":
            _print(engine.run_standing_cadence())
        elif args.cmd == "stop":
            _print(engine.emergency_stop(args.reason))
        elif args.cmd == "resume":
            _print(engine.resume(args.actor))
        return 0
    except FamError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
