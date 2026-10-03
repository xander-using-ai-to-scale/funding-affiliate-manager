# fam_emergency_stop during an in-flight wave does not stop it: execute() checks the flag once, before the loop.
import tempfile
from common import *
import fam.ghl as ghl
with tempfile.TemporaryDirectory() as tmp:
    s, _ = make(tmp)
    holder = {}
    class Stopper(ghl.MockGHL):
        n = 0
        def send_message(self, *a, **k):
            Stopper.n += 1
            if Stopper.n == 2:   # the manager hits the kill switch after the 2nd text (another process, same DB)
                FamEngine(settings=s, backend=self, today=TODAY).emergency_stop("wrong template!")
            return super().send_message(*a, **k)
    g = Stopper(s.state_dir/"mock-ghl.json")
    ids = [partner(s, g, f"P{i}", f"+155555501{i:02d}") for i in range(6)]
    e = engine(s, g)
    a = e.prepare_messages([{"contact_id": c, "channel": "sms", "kind": "kickoff", "body": "Hey there, it's Justin. Quick call this week?"} for c in ids], purpose="kickoff wave 1")
    e.request_approval(a["action_id"]); e.approve(a["action_id"], a["action_digest"], "Justin")
    r = e.execute(a["action_id"])
    print("stop flag:", e.store.get_flag("external_writes_enabled"), "| texts sent after the stop:", r["mock"] - 2, "of", len(ids))
