import json, sys
from datetime import date
from pathlib import Path
from fam import relsim
from fam.config import Settings
sp = Path(sys.argv[1])
base = Settings.load() if hasattr(Settings, "load") else Settings()
out = {}
for seed in (21, 7):
    r = relsim.run(base, sp / f"relsim-seed{seed}", start=date(2026, 10, 5), days=30, count=250, seed=seed)
    out[seed] = {k: r["totals"].get(k) for k in ("kickoffs_sent", "nudges_sent", "texts_in", "replies_sent", "calls_held",
                                                  "revenue_plans", "deals", "opt_outs", "identity_escalations")}
    out[seed]["talking"] = r["timeline"][-1]["talking"]; out[seed]["accuracy"] = r["accuracy"].get("overall")
print(json.dumps(out, indent=1))
