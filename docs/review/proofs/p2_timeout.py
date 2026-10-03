# (a) urllib raises bare TimeoutError (not URLError) when the server accepts the request but answers slowly.
# (b) LiveGHL._call only catches HTTPError/URLError, and _execute_messages only catches FamError,
#     so a slow send aborts execute() with the action stuck in 'executing' and the approval consumed.
import socket, threading, tempfile, json
from urllib import request, error
srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(5)
port = srv.getsockname()[1]
def hold():
    while True:
        c, _ = srv.accept(); c.recv(65536)  # read the request, never answer
threading.Thread(target=hold, daemon=True).start()
try:
    request.urlopen(request.Request(f"http://127.0.0.1:{port}/conversations/messages", data=b"{}", method="POST"), timeout=1)
except Exception as exc:
    print("(a) urlopen raised:", type(exc).__name__, "| is URLError:", isinstance(exc, error.URLError))

from common import *
import fam.ghl as ghl
# Real LiveGHL._call against the hanging server (timeout patched from 30s to 1s for the demo)
orig = request.urlopen
ghl.request.urlopen = lambda req, timeout=30: orig(req, timeout=1)
ghl.BASE_URL = f"http://127.0.0.1:{port}"
live = ghl.LiveGHL(token="pit-test", location_id="loc1")
try:
    live.send_message("c1", "sms", "hi")
except Exception as exc:
    print("(b) LiveGHL.send_message raised:", type(exc).__name__, "| is FamError:", type(exc).__name__ == "FamError")
ghl.request.urlopen = orig

class SlowSend(ghl.MockGHL):
    n = 0
    def send_message(self, *a, **k):
        SlowSend.n += 1
        if SlowSend.n == 2:
            super().send_message(*a, **k)   # GHL accepted it...
            raise TimeoutError("timed out")  # ...but the response never arrived
        return super().send_message(*a, **k)
with tempfile.TemporaryDirectory() as tmp:
    s, _ = make(tmp)
    g = SlowSend(s.state_dir/"mock-ghl.json")
    ids = [partner(s, g, f"P{i}", f"+1555555010{i}") for i in range(4)]
    e = engine(s, g)
    a = e.prepare_messages([{"contact_id": c, "channel": "sms", "kind": "kickoff", "body": "Hey there, it's Justin. Quick call this week?"} for c in ids], purpose="kickoff wave 1")
    e.request_approval(a["action_id"]); e.approve(a["action_id"], a["action_digest"], "Justin")
    try:
        e.execute(a["action_id"])
    except Exception as exc:
        print("(c) execute raised", type(exc).__name__)
    row = e.store.get_action(a["action_id"]); apr = e.store.get_approval(row["approval_id"])
    print("(c) action state:", row["state"], "| result_json:", repr(row["result_json"]), "| approval used_at set:", bool(apr["used_at"]))
    print("(c) texts actually delivered:", len(g.db["outbox"]), "of", len(ids))
    tags = {c: [t for t in g.get_contact(c)["tags"] if t.startswith("fam:kickoff")] for c in ids}
    print("(c) kickoff tags after crash:", tags)
    try:
        e.execute(a["action_id"])
    except Exception as exc:
        print("(c) retry:", type(exc).__name__, exc)
