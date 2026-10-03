# GHL API calls per kickoff message at execute time, and the wall-clock that implies for live waves.
import tempfile, collections
from common import *
from fam import kickoff, drafting
import fam.ghl as ghl
class Count(ghl.MockGHL):
    c = collections.Counter()
    def __getattribute__(self, name):
        attr = super().__getattribute__(name)
        if callable(attr) and not name.startswith("_") and name not in ("flush", "record_inbound"):
            Count.c[name] += 1
        return attr
with tempfile.TemporaryDirectory() as tmp:
    s, _ = make(tmp); g = Count(s.state_dir/"mock-ghl.json")
    ids = [partner(s, g, f"P{i}", f"+155555501{i:02d}") for i in range(20)]
    e = engine(s, g)
    w = kickoff.draft_wave(e, 250, drafter=drafting.TemplateDrafter()); a = w["action"]
    e.approve(a["action_id"], a["action_digest"], "Justin")
    Count.c.clear()
    e.execute(a["action_id"])
    n = sum(Count.c.values()) / 20
    print("GHL calls per kickoff at execute:", dict(Count.c), "=> per message:", n)
    for size, lat in ((250, 0.25), (500, 0.25), (2500, 0.25)):
        secs = size * (1.0 + n * max(0.12, lat))
        print(f"  wave {size}: ~{secs/60:.0f} min at 1.0s pause + {lat}s/call (fam-core MCP timeout is 15 min)")
