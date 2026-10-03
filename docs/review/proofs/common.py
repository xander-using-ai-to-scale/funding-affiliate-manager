import os, sys, tempfile
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
ROOT = Path("/Users/home/Funding Affiliate Manager")
sys.path.insert(0, str(ROOT / "files/local-packages/fam/src"))
os.environ.setdefault("FAM_CONFIG_DIR", str(ROOT / "config"))
os.environ.setdefault("FAM_POLICY_PATH", str(ROOT / "policies/permissions.json"))
from fam.config import Settings
from fam.engine import FamEngine
from fam.ghl import MockGHL
TODAY = date(2026, 10, 5)
def ago(d): return (TODAY - timedelta(days=d)).isoformat()
def make(tmp, demo=False):
    base = Settings.load()
    s = replace(base, state_dir=Path(tmp)/"state", vault_dir=Path(tmp)/"vault", ghl_mode="mock", demo_mode=demo,
                kickoff={**base.kickoff, "send_pause_seconds": 0})
    s.state_dir.mkdir(parents=True, exist_ok=True)
    g = MockGHL(s.state_dir/"mock-ghl.json")
    return s, g
def engine(s, g, day=TODAY):
    g.now_override = f"{day.isoformat()}T15:00:00+00:00"
    return FamEngine(settings=s, backend=g, today=day)
def partner(s, g, first, phone, last="Smith", **extra):
    ids = s.field_ids()
    fields = {"join_date": "2023-04-11", "last_reply_date": ago(200), "tier": "Executive", "deals_submitted": 3, **extra}
    return g.create_contact({"firstName": first, "lastName": last, "email": f"{first.lower()}@ex.com" if first else "",
        "phone": phone, "tags": ["aff:dormant", "fam:kickoff-pending"],
        "customFields": [{"id": ids[k], "field_value": v} for k, v in fields.items() if k in ids]})["id"]
