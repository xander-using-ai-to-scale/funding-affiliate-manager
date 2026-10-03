import tempfile, collections
from common import *
from fam import kickoff, drafting, cadence
import fam.ghl as ghl
# (1) non-repliers after kickoff + nudge: where does the cadence put them?
with tempfile.TemporaryDirectory() as tmp:
    s, g = make(tmp)
    ids = [partner(s, g, f"P{i}", f"+155555501{i:02d}", last_reply_date=ago(d), deals_submitted=dl)
           for i, (d, dl) in enumerate([(400, 0), (400, 2), (120, 0), (120, 3), (70, 0), (50, 0)])]
    e = engine(s, g)
    w = kickoff.draft_wave(e, 250, drafter=drafting.TemplateDrafter()); a = w["action"]
    e.approve(a["action_id"], a["action_digest"], "Justin"); e.execute(a["action_id"])
    e = engine(s, g, TODAY + timedelta(days=5))
    n = kickoff.draft_nudges(e, drafter=drafting.TemplateDrafter()); a = n["action"]
    e.approve(a["action_id"], a["action_digest"], "Justin"); e.execute(a["action_id"])
    day = TODAY + timedelta(days=20)
    e = engine(s, g, day)
    plan = cadence.sweep(e.affiliates(), day, s.cadence)
    print("tags:", collections.Counter(t for c in ids for t in g.get_contact(c)["tags"] if t.startswith("fam:")))
    print("20 days after the kickoff, bulk queue:", plan["bulk_counts"], "| personal queue:", [i["kind"] for i in plan["personal_queue"]])
# (2) cost of the first lifecycle sweep after an import (import sets no lifecycle tags)
class Count(ghl.MockGHL):
    c = collections.Counter()
    def __getattribute__(self, name):
        attr = super().__getattribute__(name)
        if callable(attr) and not name.startswith("_") and name not in ("flush",): Count.c[name] += 1
        return attr
with tempfile.TemporaryDirectory() as tmp:
    s, _ = make(tmp); g = Count(s.state_dir/"mock-ghl.json")
    ids_ = s.field_ids()
    for i in range(40):
        g.create_contact({"firstName": f"P{i}", "phone": f"+1555555{i:04d}", "tags": [],
                          "customFields": [{"id": ids_["last_reply_date"], "field_value": ago(300)}]})
    e = engine(s, g); Count.c.clear()
    r = e.sweep(apply_lifecycle=True)
    print(f"first sweep applied {r['lifecycle_applied']} changes with {sum(Count.c.values())} GHL calls ({dict(Count.c)})")
# (3) a quoted email footer opts the partner out
print("email reply with quoted footer ->", cadence.classify_reply(
    "Sounds good, call me Tuesday.\n\nOn Mon, Justin wrote:\n> Hi Dana ... \n> To unsubscribe from these emails click here"))
