# Two waves drafted on different days before either is approved contain the same partners; approving both double-texts.
import tempfile, json
from common import *
from fam import kickoff, drafting
with tempfile.TemporaryDirectory() as tmp:
    s, g = make(tmp)
    for i in range(3): partner(s, g, f"P{i}", f"+1555555010{i}")
    e1 = engine(s, g, TODAY)
    w1 = kickoff.draft_wave(e1, 250, drafter=drafting.TemplateDrafter())
    e2 = engine(s, g, TODAY + timedelta(days=1))
    w2 = kickoff.draft_wave(e2, 250, drafter=drafting.TemplateDrafter())
    print("wave1", w1["wave"], [d["contact_id"] for d in w1["drafts"]])
    print("wave2", w2["wave"], [d["contact_id"] for d in w2["drafts"]])
    for e, w in ((e2, w1), (e2, w2)):
        a = w["action"]; e.approve(a["action_id"], a["action_digest"], "Justin"); r = e.execute(a["action_id"])
        print("executed", a["action_id"], {k: r[k] for k in ("mock","failed")})
    from collections import Counter
    print("kickoffs per contact:", Counter(m["contactId"] for m in g.db["outbox"]))
