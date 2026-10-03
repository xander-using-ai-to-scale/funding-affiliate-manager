import tempfile
from common import *
with tempfile.TemporaryDirectory() as tmp:
    s, g = make(tmp)
    cid = partner(s, g, "Dana", "+15555550100")
    e = engine(s, g)
    g.record_inbound(cid, "sms", "I have a client who needs $200k for trucks, can you call me?")
    print("inbox before any outbound:", [r["last_message"] for r in e.reply_inbox()])
    g.send_message(cid, "sms", "Hey Dana, quick reminder about this month's partner webinar. Reply STOP to opt out.")  # e.g. a workflow/bulk text
    print("inbox after an outbound lands on top:", [r["last_message"] for r in e.reply_inbox()])
    print("conversation unreadCount still:", g.list_conversations(contact_id=cid)[0]["unreadCount"])
    # newest-first with a fixed limit: older unread replies starve while newer ones keep arriving
    ids = [partner(s, g, f"Q{i}", f"+155555502{i:02d}") for i in range(30)]
    for i, c in enumerate(ids):
        g.now_override = f"2026-10-05T15:{i:02d}:00+00:00"; g.record_inbound(c, "sms", f"reply {i}")
    got = [r["last_message"] for r in e.reply_inbox(limit=25)]
    print("triaged with limit 25:", got[:3], "...", got[-2:], "| oldest 5 never listed:", [f"reply {i}" for i in range(5)] )
