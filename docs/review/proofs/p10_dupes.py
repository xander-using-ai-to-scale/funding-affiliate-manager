import tempfile
from common import *
from fam import kickoff, drafting
with tempfile.TemporaryDirectory() as tmp:
    s, g = make(tmp)
    a = partner(s, g, "Dana", "+15555550100"); b = partner(s, g, "Dana", "(555) 555-0100", last="Reyes")
    c = partner(s, g, "Tom", "555-0100 x12")   # an office line with an extension
    e = engine(s, g)
    w = kickoff.draft_wave(e, 250, drafter=drafting.TemplateDrafter())
    print("wave recipients:", [(d["name"], g.get_contact(d["contact_id"])["phone"]) for d in w["drafts"]])
