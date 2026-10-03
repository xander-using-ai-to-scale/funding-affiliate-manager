"""Build docs/demo-pack.html from a simulation run.

    PYTHONPATH=files/local-packages/fam/src FAM_GHL_MODE=mock python3 -m fam.cli sim seed --count 250 --start 2026-09-01 --out sim-output
    PYTHONPATH=files/local-packages/fam/src FAM_GHL_MODE=mock python3 -m fam.cli sim run --days 30 --start 2026-09-01 --out sim-output
    python3 scripts/build_demo_pack.py --sim sim-output

The page embeds the run's report, the mock CRM as it stands on the last day (synthetic affiliates only;
emails and phone numbers are left out), one Obsidian daily note, the cost projection (run
scripts/cost_model.py first), the partnership proposal, the proposal-and-agreement document (needs pandoc;
render its PDF and .docx with scripts/build_documents.py), and the next steps from the call recap.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = {"onboarding": "Onboarding drip", "biweekly_touch": "Bi-weekly touch", "monthly_offer": "Monthly offer",
             "dormant_reactivation": "Dormant reactivation", "dead_reactivation": "Dead-lead campaign",
             "newsletter": "Newsletter", "event_invite": "Training invite", "new_offer": "New offer",
             "reply_router": "Reply router"}
PACK_URL = "https://claude.ai/artifact/CN1vFC59fCQTNd8Txvb89w"
DEMO_HEADER = re.compile(r"^\[SIMULATED (SMS|EMAIL) — demo mode, not delivered\]\n?")


def _fields(contact: dict[str, Any]) -> dict[str, Any]:
    return {f["id"]: f.get("field_value", f.get("value")) for f in contact.get("customFields", [])}


def _events(cid: str, db: dict[str, Any]) -> list[list[Any]]:
    events: list[list[Any]] = []
    for note in db["notes"].get(cid, []):
        day, body = note["dateAdded"][:10], note["body"]
        if body.startswith("[SIMULATED ENROLLMENT"):
            key = body.rsplit("workflow:", 1)[-1].strip()
            events.append([day, "wf", WORKFLOWS.get(key, key), 0])
        elif body.startswith("[SIMULATED SMS"):
            events.append([day, "sms", DEMO_HEADER.sub("", body).strip(), 0])
        elif body.startswith("[SIMULATED EMAIL"):
            subject, _, text = DEMO_HEADER.sub("", body).partition("\n")
            events.append([day, "email", text.strip(), 0, subject.strip()])
        elif body.startswith("Reply ("):
            intent, _, text = body[len("Reply ("):].partition("): ")
            events.append([day, "reply", text, intent])
        elif body.startswith("Deal submitted"):
            events.append([day, "deal", "Deal submitted to the funding team", 0])
        elif body.startswith("Opted out"):
            events.append([day, "optout", "Replied STOP. Marked do-not-contact.", 0])
        elif body.startswith(("Follow-up scheduled for", "Task for the manager")):
            continue  # the task itself is shown
        else:
            events.append([day, "note", body, 0])
    for m in db["messages"]:
        if m["contactId"] == cid and m["direction"] == "outbound":
            kind = "sms" if m.get("messageType", "").upper() == "SMS" else "email"
            events.append([m["dateAdded"][:10], kind, m["body"], 1, m.get("subject", "")])
    for e in db["enrollments"]:
        if e["contactId"] == cid:
            key = str(e.get("workflowId", "")).removeprefix("wf-")
            events.append([e["at"][:10], "wf", WORKFLOWS.get(key, key), 1])
    for t in db["tasks"].get(cid, []):
        events.append([t["dueDate"][:10], "task", t["title"], 1 if t.get("completed") else 0])
    order = {"wf": 0, "sms": 1, "email": 1, "reply": 2, "task": 3, "deal": 4, "optout": 4, "note": 5}
    events.sort(key=lambda e: (e[0], order.get(e[1], 9)))
    return events


def crm(db: dict[str, Any]) -> list[dict[str, Any]]:
    stages = {}
    for key, opp in db["opportunities"].items():
        stages.setdefault(opp["contactId"], {})[key.split(":")[0]] = opp["pipelineStageId"].split("-")[-1]
    rows = []
    for cid, c in db["contacts"].items():
        f = _fields(c)
        tags = c.get("tags", [])
        rows.append({
            "id": cid,
            "n": f"{c.get('firstName', '')} {c.get('lastName', '')}".strip(),
            "src": f.get("source") or next((t[4:] for t in tags if t.startswith("src:")), ""),
            "lc": next((t[4:] for t in tags if t.startswith("aff:") and t != "aff:dnc"), "active"),
            "niche": f.get("niche") or "",
            "aud": f.get("audience_size") or "",
            "deals": int(float(f.get("deals_submitted") or 0)),
            "join": f.get("join_date") or "",
            "ld": f.get("last_deal_date") or "",
            "lr": f.get("last_reply_date") or "",
            "lt": f.get("last_touch_date") or "",
            "ltc": f.get("last_touch_channel") or "",
            "nt": f.get("next_touch_date") or "",
            "wants": [t[5:] for t in tags if t.startswith("want:")],
            "dnc": "aff:dnc" in tags,
            "test": "fam:test-contact" in tags,
            "hot": "deal:incoming" in tags,
            "stage": stages.get(cid, {}).get("pl-lifecycle", ""),
            "svc": stages.get(cid, {}).get("pl-services", ""),
            "ev": _events(cid, db),
        })
    rows.sort(key=lambda r: r["n"])
    return rows


def featured(rows: list[dict[str, Any]]) -> str:
    def score(r: dict[str, Any]) -> tuple[int, int]:
        kinds = Counter(e[1] for e in r["ev"])
        told_deal = any(e[1] == "reply" and e[3] == "has_deal" for e in r["ev"])
        return (2 * told_deal + kinds["deal"] + (not r["test"]), len(r["ev"]))
    return max(rows, key=score)["id"] if rows else ""


def proposal_body(path: Path) -> str:
    html = path.read_text()
    start = html.index('<div class="wrap">') + len('<div class="wrap">')
    body = html[start:html.rindex("</div>")].strip()
    # links from the proposal to a tab of this pack switch tabs instead of reloading the page
    return re.sub(rf'href="{re.escape(PACK_URL)}#(\w+)"', r'href="#\1" data-go="\1"', body)


def next_steps(recap: Path) -> list[str]:
    text = recap.read_text()
    section = text.split("## Next steps", 1)[1].split("\n## ", 1)[0]
    return [re.sub(r"^\d+\.\s+", "", line).strip() for line in section.splitlines() if re.match(r"^\d+\.\s", line)]


def agreement_html(md: Path) -> str:
    """The proposal-and-agreement document as an HTML fragment for its tab."""
    meta = dict(re.findall(r"^(title|subtitle):\s*(.+)$", md.read_text().split("---", 2)[1], re.M))
    if shutil.which("pandoc"):
        body = subprocess.run(["pandoc", str(md), "-f", "markdown", "-t", "html5", "--shift-heading-level-by=1"],
                              check=True, capture_output=True, text=True).stdout
        body = re.sub(r"\[([^\[\]<>]{1,80})\]", r'<span class="fill">[\1]</span>', body)  # blanks to fill
    else:
        body = f"<pre class=\"card\">{md.read_text()}</pre>"
    return f'<h1>{meta.get("title", "")}</h1><p class="muted" style="margin-top:0">{meta.get("subtitle", "")}</p>{body}'


def check_figures(cost: dict[str, Any], proposal: Path, agreement: Path) -> None:
    """Fail the build if a cost figure quoted in the proposal or agreement no longer matches the model."""
    h = cost["headline"]
    usd = lambda v: f"${v:,.2f}"
    want = {proposal: [usd(h[k]) for k in ("reactivation_ai_usd", "monthly_ai_usd", "reactivation_ai_budget_usd",
                                           "monthly_ai_budget_usd", "reactivation_sms_usd", "monthly_sms_usd")],
            agreement: [usd(m[k]) for m in h["multiples"].values() for k in ("reactivation_ai_usd", "monthly_ai_usd")]}
    missing = [f"{path.name}: {v}" for path, vals in want.items() for v in vals if v not in path.read_text()]
    if missing:
        raise SystemExit("Cost figures out of date (rerun scripts/cost_model.py, then fix): " + ", ".join(missing))


def build(sim_dir: Path, out: Path, template: Path, proposal: Path) -> dict[str, Any]:
    report = json.loads((sim_dir / "report.json").read_text())
    db = json.loads((sim_dir / "state" / "mock-ghl.json").read_text())
    rows = crm(db)
    daily = sorted((sim_dir / "vault" / "Daily").glob("*.md"))
    sample_day = daily[1] if len(daily) > 1 else (daily[0] if daily else None)
    vault_note = sample_day.read_text() if sample_day else ""
    vault_note = re.sub(r"\[\[(?:Affiliates|Partners)/[^|\]]+\|([^\]]+)\]\]", r"\1", vault_note)
    docs = ROOT / "docs"
    cost = json.loads((docs / "cost-projection.json").read_text())
    agreement = docs / "proposal-and-agreement-7ff.md"
    check_figures(cost, proposal, agreement)
    data = {"report": report, "crm": rows, "featured": featured(rows), "vault_day": sample_day.stem if sample_day else "",
            "vault_note": vault_note[:3500], "custom_values": db.get("custom_values", {}), "cost": cost,
            "next_steps": next_steps(docs / "call-recap-2026-09-23.md")}
    page = template.read_text()
    page = page.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
    page = page.replace("<!--__PROPOSAL__-->", proposal_body(proposal))
    page = page.replace("<!--__AGREEMENT__-->", agreement_html(agreement))
    from build_relationship_example import part as relationship_part  # the "Relationship graph" tab
    page = page.replace("<!--__RELATIONSHIP__-->", relationship_part())
    out.write_text(page)
    return {"out": str(out), "bytes": out.stat().st_size, "affiliates": len(rows),
            "events": sum(len(r["ev"]) for r in rows), "featured": data["featured"]}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sim", default="sim-output", help="a `fam sim run` output directory")
    p.add_argument("--out", default=str(ROOT / "docs" / "demo-pack.html"))
    p.add_argument("--template", default=str(ROOT / "docs" / "demo-pack.template.html"))
    p.add_argument("--proposal", default=str(ROOT / "docs" / "proposal-7ff.html"))
    a = p.parse_args()
    print(json.dumps(build(Path(a.sim), Path(a.out), Path(a.template), Path(a.proposal)), indent=2))


if __name__ == "__main__":
    main()
