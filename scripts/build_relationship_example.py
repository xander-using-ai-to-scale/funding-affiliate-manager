"""Build the relationship-graph page from the frozen worked example and the relationship simulation.

    python3 scripts/build_relationship_example.py      # writes docs/relationship-example.html

Inputs (regenerate them, never edit them):
  examples/partner-journey/steps.json   fam example partner-journey --out examples/partner-journey [--model]
  docs/relationship-simulation.json     fam sim relationships --start 2026-10-05 (then copy report.json here)

The page is one component (docs/relationship-graph.part.html) that also becomes the demo pack's
"Relationship graph" tab (scripts/build_demo_pack.py calls part()). The build stops if a figure quoted in
docs/relationship-graph.md no longer matches the data, or if the page would carry an internal detail.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
STEPS = ROOT / "examples" / "partner-journey" / "steps.json"
SIM = DOCS / "relationship-simulation.json"
PART = DOCS / "relationship-graph.part.html"
SPEC = DOCS / "relationship-graph.md"
OUT = DOCS / "relationship-example.html"
MODEL_LABELS = {"openai/gpt-6-luna-pro": "GPT-6 Luna Pro", "z-ai/glm-5.3-flash": "GLM 5.3 Flash"}
sys.path.insert(0, str(ROOT / "scripts"))
from export_share_pack import BLOCK  # noqa: E402  (the share pack's scan, so the page passes it too)


def data() -> dict[str, Any]:
    ex = json.loads(STEPS.read_text())
    sim = json.loads(SIM.read_text())
    steps = [{"n": s["n"], "title": s["title"], "day": s["day"], "input": s.get("input", {}), "output": s["output"],
              "profile": {k: s["profile"].get(k) for k in ("completeness", "summary", "next_step")},
              "graph": s["graph"], "note": s["note"]} for s in ex["steps"]]
    keep = ("day", "avg_completeness", "avg_completeness_talking", "talking", "calls")
    return {
        "example": {"meta": {**ex["meta"], "model_label": MODEL_LABELS.get(ex["meta"].get("model", ""), "")},
                    "steps": steps},
        "sim": {"meta": sim["meta"], "totals": sim["totals"], "variants": sim["variants"], "accuracy": sim["accuracy"],
                "graph_end": sim["graph_end"], "timeline": [{k: d[k] for k in keep} for d in sim["timeline"]],
                "kickoffs": [sim["samples"]["kickoffs"][k] for k in sorted(sim["samples"]["kickoffs"])],
                "sample": {k: sim["sample_partner"][k] for k in ("name", "before", "after")},
                "assumptions": sim["assumptions"]},
    }


def figures(d: dict[str, Any]) -> dict[str, str]:
    """Every figure docs/relationship-graph.md quotes, as it must appear there."""
    pcts = [s["profile"]["completeness"] for s in d["example"]["steps"]]
    t, last = d["sim"]["totals"], d["sim"]["timeline"][-1]
    return {"example start": f"{pcts[0]}%", "example end": f"{pcts[-1]}%",
            "partners": f"{d['sim']['meta']['partners']} quiet partners", "kickoffs": f"{t['kickoffs_sent']} kickoff texts",
            "wrote back": f"{last['talking']} partners wrote back",
            "their completeness": f"{last['avg_completeness_talking']}%", "calls": f"{t['calls_held']} calls",
            "plans": f"{t['revenue_plans']} revenue plans", "opt-outs": f"{t['opt_outs']} opt-outs",
            "identity": f"{t['identity_escalations']} asked"}


def check(d: dict[str, Any]) -> None:
    text = re.sub(r"\s+", " ", SPEC.read_text())  # a figure may wrap across lines
    missing = [f"{k} ({v})" for k, v in figures(d).items() if v not in text]
    if missing:
        raise SystemExit(f"{SPEC.name} quotes figures that no longer match the data: " + ", ".join(missing))


def part(d: dict[str, Any] | None = None) -> str:
    d = d or data()
    payload = json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = PART.read_text().replace("/*__REL_DATA__*/null", payload)
    hits = [pat for pat in BLOCK if re.search(pat, html)]
    if hits:
        raise SystemExit(f"relationship page carries internal details: {hits}")
    return html


def tokens() -> str:
    """The demo pack's color and type tokens, so the page and the pack's tab look the same."""
    tpl = (DOCS / "demo-pack.template.html").read_text()
    return tpl[tpl.index(":root{"):tpl.index("*{box-sizing")]


SHELL = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Partner Relationship Graph</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
__TOKENS__
*{box-sizing:border-box}
body{background:var(--ground);color:var(--ink);font:15px/1.6 var(--body);padding-inline:16px;padding-block:0 72px;margin:0}
.wrap{max-width:1120px;margin:0 auto}
a{color:var(--accent)}
button{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.muted{color:var(--ink-3)}
header.top{padding-block:44px 30px;display:grid;gap:12px}
.eyebrow{font:500 12px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin:0}
h1{font:700 clamp(32px,5.4vw,54px)/1.03 var(--display);letter-spacing:-.02em;margin:0;text-wrap:balance;max-width:22ch}
.lede{font-size:17px;color:var(--ink-2);max-width:68ch;margin:0}
.facts{display:flex;flex-wrap:wrap;gap:6px 18px;font:13px/1.4 var(--mono);color:var(--ink-3);margin:0}
</style>
<div class="wrap">
<header class="top">
  <p class="eyebrow">7 Figures Funding · partner relationships</p>
  <h1>Know every partner before the first text</h1>
  <p class="lede">Each partner's record becomes a profile before anyone writes to them. Every reply and every recorded call
  adds to it, every message is written from it, and a person approves every one. Below: one partner's journey through
  the real code, then the same code run on __PARTNERS__ quiet partners.</p>
  <p class="facts"><span>Synthetic partners</span><span>Mock CRM</span><span>No one was contacted</span><span>Example started <b>__START__</b></span></p>
</header>
__PART__
</div>
"""


def main() -> None:
    d = data()
    check(d)
    page = (SHELL.replace("__TOKENS__", tokens()).replace("__PARTNERS__", f"{d['sim']['meta']['partners']:,}")
            .replace("__START__", d["example"]["meta"]["start"]).replace("__PART__", part(d)))
    OUT.write_text(page)
    print(json.dumps({"out": str(OUT.relative_to(ROOT)), "bytes": OUT.stat().st_size,
                      "completeness": [s["profile"]["completeness"] for s in d["example"]["steps"]],
                      "drafter": d["example"]["meta"]["drafter"], "figures": figures(d)}, indent=2))


if __name__ == "__main__":
    main()
