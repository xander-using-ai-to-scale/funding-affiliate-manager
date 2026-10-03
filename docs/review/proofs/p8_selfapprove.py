# The approval gate is a row in fam.sqlite3. Any process running as the agent's Unix user can write it:
# here a plain shell command (what Hermes' `terminal` toolset can run) approves an action with no human.
import tempfile, subprocess, os, json
from common import *
with tempfile.TemporaryDirectory() as tmp:
    s, g = make(tmp)
    cid = partner(s, g, "Dana", "+15555550100")
    e = engine(s, g)
    a = e.prepare_messages([{"contact_id": cid, "channel": "sms", "kind": "personal_checkin", "body": "Hey Dana, it's Justin. Got 10 min this week?"}])
    e.request_approval(a["action_id"])
    env = {**os.environ, "PYTHONPATH": str(ROOT/"files/local-packages/fam/src"), "FAM_STATE_DIR": str(s.state_dir),
           "FAM_VAULT_DIR": str(s.vault_dir), "FAM_GHL_MODE": "mock", "FAM_CONFIG_DIR": str(ROOT/"config")}
    out = subprocess.run(["python3", "-m", "fam.cli", "approve", a["action_id"], a["action_digest"], "--approver", "Justin"],
                         env=env, capture_output=True, text=True)
    print("shell `fam approve` exit", out.returncode, out.stdout.strip().replace("\n", " ")[:160])
    print("action state:", e.store.get_action(a["action_id"])["state"], "| execute:", e.execute(a["action_id"])["state"])
