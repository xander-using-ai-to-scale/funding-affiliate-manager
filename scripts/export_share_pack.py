"""Export the client-facing pack for 7 Figures Funding into its own directory (a separate, private repo).

    python3 scripts/export_share_pack.py --out ../7ff-affiliate-manager

Copies only the documents meant for 7FF, plus the standalone cost model, and writes a README from the
cost projection. It refuses to write anything if a file contains an internal address, a local path, a
credential-looking string, a meeting passcode, or unverified research notes.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "docs/demo-pack.html", "docs/proposal-7ff.html", "docs/workflow-map.html",
    "docs/ai-cost-projection.md", "docs/cost-projection.json",
    "docs/proposal-and-agreement-7ff.pdf", "docs/proposal-and-agreement-7ff.docx",
    "docs/call-recap-2026-09-23.md",
    "docs/simulation-report.md", "docs/simulation-report.json",
    "docs/relationship-example.html", "docs/relationship-graph.md",
    "docs/relationship-simulation.md", "docs/relationship-simulation.json",
    "scripts/cost_model.py",
]
BLOCK = [r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", r"fam@", r"/Users/", r"/home/fam", r"droplet",
         r"UNVERIFIED", r"sk-or-", r"sk-[A-Za-z0-9]{20}", r"xox[abprs]-", r"xapp-", r"dop_v1_", r"ghp_",
         r"\bpit-[0-9a-f]{8}", r"600338", r"817236", r"passcode"]


def scan(path: Path) -> list[str]:
    if path.suffix in (".pdf", ".docx"):  # binary renders: scan the markdown they were built from
        path = path.with_suffix(".md")
    text = path.read_text(errors="ignore")
    return [f"{path.relative_to(ROOT)}: {pat}" for pat in BLOCK if re.search(pat, text)]


def readme(cost: dict) -> str:
    h, pop = cost["headline"], cost["population"]
    return f"""# 7FF Affiliate Manager: demo pack

Private. Prepared for 7 Figures Funding by Justin Bellware.

An AI Funding Affiliate Manager to bring 7FF's {pop['partners_total']:,} partners back into conversation and keep
them sending deals, working in GoHighLevel with a person approving every message.

## Start here

Download [`docs/demo-pack.html`](docs/demo-pack.html) and open it in a browser. It has everything in one page:
AI costs, the 30-day simulation, the relationship graph, the CRM it leaves behind, the partnership proposal, the
agreement, and how the agent is built. (GitHub shows HTML files as source code, so open the file rather than viewing it here.)

## What it costs

- **About ${h['reactivation_ai_usd']:,.2f} of AI** for the whole reactivation: {pop['reactivation_audience']:,} personal
  kickoff texts and every conversation after (range ${h['reactivation_ai_range_usd'][0]:,.2f} to
  ${h['reactivation_ai_range_usd'][1]:,.2f}).
- **About ${h['monthly_ai_usd']:,.2f} of AI a month** after that, with every partner on a two-week cadence.
- **Starting budget: twice the projection,** ${h['reactivation_ai_budget_usd']:,.2f} for the reactivation and
  ${h['monthly_ai_budget_usd']:,.2f} a month.
- **Texting is the bigger line:** about ${h['reactivation_sms_usd']:,.2f} for the reactivation and
  ${h['monthly_sms_usd']:,.2f} a month, billed by HighLevel.

The full projection, with scenarios, rollout waves and every assumption, is in
[`docs/ai-cost-projection.md`](docs/ai-cost-projection.md).

## Everything here

| File | What |
|---|---|
| `docs/demo-pack.html` | The whole pack in one page |
| `docs/ai-cost-projection.md` | AI and texting cost projection (`cost-projection.json` alongside) |
| `docs/proposal-7ff.html` | Partnership proposal, draft for discussion |
| `docs/proposal-and-agreement-7ff.pdf` | The proposal and agreement to sign (`.docx` alongside) |
| `docs/call-recap-2026-09-23.md` | Recap of our call: what we covered, what we agreed, next steps |
| `docs/simulation-report.md` | The 30-day simulation on 253 synthetic affiliates (`.json` alongside) |
| `docs/relationship-example.html` | The relationship graph: one partner from record to revenue plan, and 250 partners over 30 days |
| `docs/relationship-graph.md` | How the agent gets to know each partner: the profile, where it lives, calls, what it never stores |
| `docs/relationship-simulation.md` | The relationship simulation report (`.json` alongside) |
| `docs/workflow-map.html` | The affiliate operating system: lifecycle, cadence, daily loop, guardrails |
| `scripts/cost_model.py` | The cost model behind every cost figure |

## Rerun the costs

Change an assumption in `scripts/cost_model.py`, then run it (Python 3.10 or later, no dependencies):

```bash
python3 scripts/cost_model.py
```

It rewrites `docs/cost-projection.json` and `docs/ai-cost-projection.md`. Prices were taken from OpenRouter,
TypeSafe and HighLevel on {cost['priced_on']}.

The simulation uses synthetic affiliates only. Nobody was contacted.
"""


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", required=True, help="the share repo's working directory")
    out = Path(p.parse_args().out)
    problems = [hit for f in FILES for hit in scan(ROOT / f)]
    if problems:
        raise SystemExit("Not exported; internal details found:\n  " + "\n  ".join(problems))
    for f in FILES:
        (out / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / f, out / f)
    (out / "README.md").write_text(readme(json.loads((ROOT / "docs/cost-projection.json").read_text())))
    (out / ".gitignore").write_text(".DS_Store\n__pycache__/\n")
    print(f"exported {len(FILES)} files and README.md to {out}")


if __name__ == "__main__":
    main()
