import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
from fam.drafting import segments
run = Path(sys.argv[1]); out = Path(sys.argv[2])
r = json.loads((run / "report.json").read_text()); d = json.loads((run / "state/mock-ghl.json").read_text())
names = {c["id"]: c.get("firstName", "") for c in (d["contacts"] if isinstance(d["contacts"], list) else d["contacts"].values())}
threads = defaultdict(list)
for m in sorted((m for m in d["messages"] if m.get("messageType", "SMS") == "SMS"), key=lambda m: m["dateAdded"]):
    threads[m["contactId"]].append(m)
def norm(body, cid):
    n = names.get(cid, "")
    b = body.replace(n, "{first}") if n else body
    return re.sub(r"\b\d+ deals?\b", "{n} deals", b)
kinds = Counter(); distinct = defaultdict(Counter)
for cid, ms in threads.items():
    outs = [m for m in ms if m["direction"] == "outbound"]
    for i, m in enumerate(outs):
        k = "kickoff" if i == 0 else ("nudge" if " again from " in m["body"] else ("manager (scripted in the sim, sent outside approvals)" if "read every one of these myself" in m["body"] else "reply"))
        kinds[k] += 1; distinct[k][norm(m["body"], cid)] += 1
L = ["# Message digest: relationship simulation, framework templates (TemplateDrafter), seed 21", "",
     f"Every outbound text the simulation sent, from the mock CRM. Totals: {dict(kinds)}. Inbound partner texts are synthetic personas (relsim.py), not real people.", ""]
L += ["## Kickoff samples by opener and hook (as sent)", ""]
for k, v in sorted(r["samples"]["kickoffs"].items()):
    L += [f"- **{k}** (variant {v['variant']}, hook {v['hook']}, {segments(v['body'])} segments): {v['body']}"]
L += ["", f"## Nudge ({segments(r['samples']['nudge'])} segments)", "", r["samples"]["nudge"], ""]
for k in ("kickoff", "nudge", "reply", "manager (scripted in the sim, sent outside approvals)"):
    L += [f"## Distinct {k} bodies (first names replaced by {{first}}), with how many times each was sent", ""]
    for body, n in distinct[k].most_common(60):
        L += [f"- ×{n} ({segments(body)} seg): {body}"]
    L += [""]
picks = [cid for cid, ms in threads.items() if sum(m["direction"] == "inbound" for m in ms) >= 3][:10]
picks += [cid for cid, ms in threads.items() if sum(m["direction"] == "inbound" for m in ms) == 1][:4]
L += ["## Full threads (14 partners)", ""]
for cid in picks:
    L += [f"### {names.get(cid, cid)} ({cid})", ""]
    for m in threads[cid]:
        who = "US" if m["direction"] == "outbound" else "PARTNER"
        L += [f"- {m['dateAdded'][:10]} **{who}:** {m['body']}"]
    L += [""]
s = r["samples"]
L += ["## STOP messages received", ""] + [f"- {x}" for x in s["stop"]] + [""]
L += ["## Identity question sample", "", "```", json.dumps(s["identity"], indent=1), "```", ""]
for k in ("approval_card", "brief", "call_note", "plan"):
    L += [f"## Sample {k.replace('_', ' ')}", "", "```", s[k].strip(), "```", ""]
L += ["## Review file (first 120 lines)", "", "```", "\n".join(s["review_file"].splitlines()[:120]), "```", ""]
L += ["## Manager tasks created (sample of 10)", ""]
tasks = [t for v in (d["tasks"].values() if isinstance(d["tasks"], dict) else [d["tasks"]]) for t in v]
L += [f"- {t['body'][:240]!r}" for t in tasks[:10]]
out.write_text("\n".join(L)); print(out, len(L), dict(kinds))
