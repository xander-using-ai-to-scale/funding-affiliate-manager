# A FamError AFTER a successful send marks the message "failed" and the kickoff tags are left wrong:
#  case A (429 on the field update, before the tag move): still fam:kickoff-pending -> next wave texts them again
#  case B (429 on add_tags after remove_tags): no kickoff tag at all -> never nudged, and `fam kickoff enroll` re-queues them
import tempfile
from common import *
from fam import kickoff, drafting
from fam.errors import FamError
import fam.ghl as ghl
def run(case):
    class Flaky(ghl.MockGHL):
        fail = True
        def update_contact(self, cid, payload):
            if case == "A" and self.fail and "customFields" in payload:
                raise FamError("GoHighLevel PUT /contacts/x returned HTTP 429")
            return super().update_contact(cid, payload)
        def add_tags(self, cid, tags):
            if case == "B" and self.fail and "fam:kickoff-sent" in tags:
                raise FamError("GoHighLevel POST /contacts/x/tags returned HTTP 429")
            return super().add_tags(cid, tags)
    with tempfile.TemporaryDirectory() as tmp:
        s, _ = make(tmp); g = Flaky(s.state_dir/"mock-ghl.json")
        cid = partner(s, g, "Dana", "+15555550100")
        e = engine(s, g)
        w = kickoff.draft_wave(e, 250, drafter=drafting.TemplateDrafter()); a = w["action"]
        e.approve(a["action_id"], a["action_digest"], "Justin"); r = e.execute(a["action_id"])
        g.fail = False
        print(f"case {case}: result {({k: r[k] for k in ('mock','failed')})}, delivered={len(g.db['outbox'])}, tags={[t for t in g.get_contact(cid)['tags'] if t.startswith('fam:')]}")
        e = engine(s, g, TODAY + timedelta(days=1))
        if case == "B":
            print("   enroll re-tags:", kickoff.enroll(e))
        w = kickoff.draft_wave(e, 250, drafter=drafting.TemplateDrafter())
        if w.get("ok"):
            a = w["action"]; e.approve(a["action_id"], a["action_digest"], "Justin"); e.execute(a["action_id"])
        print(f"   kickoff texts Dana received in total: {len(g.db['outbox'])}")
run("A"); run("B")
