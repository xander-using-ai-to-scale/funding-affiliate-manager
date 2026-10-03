import tempfile
from common import *
from fam import kickoff, drafting
with tempfile.TemporaryDirectory() as tmp:
    s, g = make(tmp)
    a = partner(s, g, "Ann", "+15555550101"); b = partner(s, g, "Bob", "+15555550102")
    e = engine(s, g)
    w = kickoff.draft_wave(e, 250, drafter=drafting.TemplateDrafter()); act = w["action"]
    e.approve(act["action_id"], act["action_digest"], "Justin"); e.execute(act["action_id"])
    e = engine(s, g, TODAY + timedelta(days=1))
    e.record_reply(a, "STOP"); e.record_reply(b, "wrong number")
    for cid in (a, b):
        aff = e.affiliate(cid)
        print(aff.first_name, "| dnc:", aff.is_dnc, "| last_reply_date:", aff.fields.get("last_reply_date"), "| lifecycle:", aff.lifecycle,
              "| 'reply' interactions:", len(e.graph.interactions(cid, ["reply"])))
    print("variant_stats:", e.graph.variant_stats())
    sc = e.scorecard(); print("scorecard replied_last_30d:", sc["replied_last_30d"], "reply_rate_30d:", sc["reply_rate_30d"])
