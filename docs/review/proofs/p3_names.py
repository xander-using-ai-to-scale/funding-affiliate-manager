import tempfile
from common import *
from fam import kickoff, drafting, cadence
d = drafting.TemplateDrafter()
for first in ("María", "José", "Zoë", "Mike 💰", "Siobhán", "JOHN"):
    p = {"first_name": first, "deals": 3, "joined": "2023-04-11", "tier": "Executive"}
    out = d.kickoff(p, "Justin", "A")
    print(f"{first!r:12} segments={drafting.segments(out['body'])} enc={cadence.sms_segments(cadence.sms_normalize(out['body']))['encoding']} problems={drafting.check(out['body'], p, 'Justin', kickoff=True)}")
# a wave where the top-ranked partner has an accented name: skipped every wave, never sent, holds a slot
with tempfile.TemporaryDirectory() as tmp:
    s, g = make(tmp)
    top = partner(s, g, "María", "+15555550100", deals_submitted=40)
    for i in range(3): partner(s, g, f"P{i}", f"+1555555011{i}", deals_submitted=1)
    for day in range(3):
        e = engine(s, g, TODAY + timedelta(days=day))
        w = kickoff.draft_wave(e, 2, drafter=d)
        print("day", day, "drafted", len(w.get("drafts", [])), "skipped", [x["name"] for x in w.get("skipped", [])])
        if w.get("ok"):
            a = w["action"]; e.approve(a["action_id"], a["action_digest"], "Justin"); e.execute(a["action_id"])
# contact with no first/last name
from fam.cadence import affiliate_from_contact
a = affiliate_from_contact({"id": "c1", "email": "jsmith@gmail.com", "phone": "+15555550100"}, {})
print("first_name with no name on record:", repr(a.first_name), "->", d.kickoff({"first_name": a.first_name}, "Justin", "A")["body"][:45])
a = affiliate_from_contact({"id": "c2", "contactName": "ACME FUNDING LLC", "phone": "+15555550100"}, {})
print("first_name from company contactName:", repr(a.first_name))
