import tempfile
from common import *
from fam import cadence, drafting
for t in ("HELP", "Wrong number", "Take me off your list", "not interested", "who is this?", "lose my number",
          "I closed my business last year", "Stop.", "Please don't contact me again", "📷", ""):
    print(f"{t!r:35} -> {cadence.classify_reply(t)['intent']}")
with tempfile.TemporaryDirectory() as tmp:
    s, g = make(tmp)
    cid = partner(s, g, "Dana", "+15555550100")
    e = engine(s, g)
    r = e.record_reply(cid, "Wrong number")
    a = e.affiliate(cid)
    print("record_reply('Wrong number'):", r["intent"], r["actions_taken"], "| draft_reply:", r["draft_reply"], "| lifecycle now:", a.lifecycle, "| last_reply_date:", a.fields.get("last_reply_date"))
# body containing 'stop' as part of another word suppresses the opt-out line
with tempfile.TemporaryDirectory() as tmp:
    s, g = make(tmp)
    cid = partner(s, g, "Dana", "+15555550100")
    e = engine(s, g)
    a = e.prepare_messages([{"contact_id": cid, "channel": "sms", "kind": "personal_checkin",
                             "body": "Hey Dana, it's Justin. Your team has been nonstop lately! Got 10 min this week?"}])
    print("frozen SMS body:", a["preview"][0]["body"])
# empty model reply passes check()
print("check('') for a reply:", drafting.check("", {"first_name": "Dana"}, "Justin"))
