"""Cost projection for reactivating 7 Figures Funding's partner base with the Funding Affiliate Manager.

    python3 scripts/cost_model.py     # writes docs/cost-projection.json and docs/ai-cost-projection.md

The job being priced: one custom SMS to each inactive partner to restart the relationship, then handling
every reply as a back-and-forth conversation. Jev classifies and ingests; GPT-6 Luna Pro drafts, with
GLM 5.3 Flash as the fallback; the Hermes agent runs the loop. Every number on the cost pages comes from
this file, so change an assumption here and rebuild (scripts/build_demo_pack.py) rather than editing pages.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRICED_ON = "2026-09-23"

# $ per million tokens. Sources: OpenRouter /api/v1/models; docs.typesafe.ai/models; HighLevel help center.
MODELS = {
    "luna": {"label": "GPT-6 Luna Pro", "maker": "OpenAI", "route": "openrouter: openai/gpt-6-luna-pro",
             "in": 0.10, "out": 0.50, "cache_read": 0.01, "batch_in": 0.05, "batch_out": 0.25,
             "long_prompt_over": 272_000, "long_in": 0.20, "long_out": 0.75,
             "note": "Reasoning ('pro' mode) is billed as output tokens."},
    "glm": {"label": "GLM 5.3 Flash", "maker": "Z.ai (open weights)", "route": "openrouter: z-ai/glm-5.3-flash",
            "in": 0.15, "out": 0.50, "cache_read": 0.05, "note": "Fallback when Luna Pro errors or is slow."},
    "jev": {"label": "Jev 1.13", "maker": "TypeSafe", "route": "api.typesafe.ai/v1/systemone (jev-1.13.0)",
            "in": 0.042, "out": 0.0, "note": "Input tokens only; output is free. 1,200 requests/min."},
}
SMS = {"base_per_segment": 0.00747, "carrier_out": {"low": 0.003, "base": 0.0045, "high": 0.005},
       "carrier_in": {"low": 0.0, "base": 0.003, "high": 0.003},
       "a2p_one_time": 71.90625, "a2p_monthly": 10.00,
       "sources": ["https://help.gohighlevel.com/support/solutions/articles/48001223556-phone-system-pricing-billing-guide",
                   "https://help.gohighlevel.com/support/solutions/articles/155000005200-a2p-10dlc-messaging-fees-registration-monthly-and-carrier-costs"]}
MEASURED = {"hermes_daily_loop_session": {"tokens_processed": 539_187, "output_tokens": 5_530, "tool_calls": 18,
                                          "where": "the agent's server, `hermes insights`, 2026-09-23"},
            "hermes_fixed_prompt_bytes": 20_412 + 42_800,
            "jev_classification_call": {"input_tokens": 548, "cost_usd": 0.000023,
                                        "where": "jev-agent-kit evidence/jev-pilot-validation.json"}}

# What runs the reactivation, and what exists today. "Built" is running on the agent's server now;
# "Set up" is configuration with no new code; "To build" is new work before the pilot.
SPEC = [
    {"part": "Hermes agent (the affiliate manager)", "status": "Built",
     "does": "Runs the daily loop, triages replies, talks with the manager in Slack, and puts every send on an approval card."},
    {"part": "Affiliate engine and GoHighLevel connector", "status": "Built",
     "does": "Cadence rules, lifecycle tags, notes, tasks, approvals, opt-out handling, and a guard that keeps every text to one segment."},
    {"part": "Simulation and reporting", "status": "Built",
     "does": "Runs the same code against a synthetic CRM, as in this pack's simulation tab."},
    {"part": "GoHighLevel sub-account and texting number", "status": "Set up",
     "does": "Holds the reactivation contacts, tags and conversations. The number is registered for A2P 10DLC before any text goes out."},
    {"part": "Models through OpenRouter", "status": "Set up",
     "does": "The agent and the message worker run on GPT-6 Luna Pro, with GLM 5.3 Flash as the fallback. Luna Pro was tested driving the agent's own tools on September 23, 2026. Usage is reported to 7FF every month."},
    {"part": "Zoho to GoHighLevel partner import (read-only)", "status": "Built",
     "does": "Copies partner name, tier, contact details and deal history into GoHighLevel and builds each partner's profile. Nothing is written back to Zoho, and partners with payroll integrations stay where they are. Tested on synthetic records; runs on 7FF's once read-only access is granted."},
    {"part": "Relationship graph", "status": "Built",
     "does": "A profile for every partner: an Obsidian note linked to their tier, niche, manager and the products their clients need, plus a searchable index. Every reply and recorded call adds to it, and every message is drafted from it."},
    {"part": "Call transcripts (phone and video)", "status": "Built",
     "does": "Reads GoHighLevel's call transcripts and any recorder's export (Read.ai, Fathom or others) dropped in the call inbox. Each call adds facts to the profile and turns promises into tasks. Needs call transcription switched on in GoHighLevel."},
    {"part": "Jev ingestion, checking and classifying", "status": "To build",
     "does": "Cleans each partner record on the way in, checks every draft against the compliance rules, and labels every reply."},
    {"part": "Message worker", "status": "To build",
     "does": "Drafts each kickoff and reply on GPT-6 Luna Pro, falling back to GLM 5.3 Flash. Runs outside the agent so each text pays only for its own short prompt; the kickoff runs in batch mode."},
    {"part": "Consent gate", "status": "To build",
     "does": "Texts only partners with a mobile number and SMS consent on file. Everyone else gets email and the newsletter."},
    {"part": "Deal attribution by tier", "status": "To build",
     "does": "Tags each re-engaged partner with their tier so every deal from the reactivation is counted against the right share. Needs 7FF's deal data."},
]
FLOW = [
    ("Import", "Partner records come over from Zoho, Jev cleans them, and each lands in GoHighLevel tagged with tier and status."),
    ("Gate", "Only partners with a mobile number and SMS consent get a text. STOP is final."),
    ("Draft", "The message worker writes one kickoff per partner from their record: name, tier, last deal, niche. Jev checks each draft."),
    ("Approve", "In the pilot a person approves each text in Slack. Later waves go out as sampled batches under a standing approval with a daily send limit."),
    ("Send", "GoHighLevel sends from the registered number, in daytime hours, within the daily send limit."),
    ("Converse", "Jev labels each reply and the worker drafts the answer under the same approval rules. Deals, commission questions and anything sensitive go to a person as a task."),
    ("Report", "A daily summary in Slack and a weekly scorecard: replies, opt-outs, deals by tier, and AI spend against the budget."),
]

PARTNERS_TOTAL = 13_000
PARTNERS_ACTIVE = 50
REACTIVATION_AUDIENCE = PARTNERS_TOTAL - PARTNERS_ACTIVE

# Tokens per call and volumes. low / base / high. Output tokens for Luna Pro include its hidden reasoning,
# the largest single uncertainty, so it gets the widest range.
SCENARIOS: dict[str, dict[str, Any]] = {
    "low": dict(ingest_in=600, draft_in=900, draft_out=200, qa_in=500, classify_in=700, reply_in=1_600,
                reply_out=250, session_in=300_000, session_out=4_000, sessions_per_day=6,
                reply_rate=0.05, inbound_per_responder=2, ongoing_reply_rate=0.03, ongoing_inbound=2,
                seg_out=1, seg_in=1, kick_seg=2, tier="low"),
    "base": dict(ingest_in=900, draft_in=1_300, draft_out=600, qa_in=700, classify_in=1_000, reply_in=2_400,
                 reply_out=700, session_in=540_000, session_out=6_000, sessions_per_day=12,
                 reply_rate=0.12, inbound_per_responder=4, ongoing_reply_rate=0.06, ongoing_inbound=3,
                 seg_out=1, seg_in=1, kick_seg=2, tier="base"),
    "high": dict(ingest_in=1_500, draft_in=2_000, draft_out=1_500, qa_in=1_000, classify_in=1_600,
                 reply_in=4_000, reply_out=1_800, session_in=1_200_000, session_out=12_000, sessions_per_day=30,
                 reply_rate=0.25, inbound_per_responder=8, ongoing_reply_rate=0.12, ongoing_inbound=5,
                 seg_out=2, seg_in=1, kick_seg=2, tier="high"),
}
# The relationship graph, priced on top of the scenarios above (it is not in the agreement's figures, which
# is why build() asserts base + graph stays inside the agreement's 2x numbers). One extraction pass for each
# partner whose record has real history, a fact extraction for each inbound reply, the profile added to each
# drafting prompt, and one extraction plus a revenue plan for each recorded call. Pre-call briefs and the
# partner notes are built from the profile with no model call.
GRAPH: dict[str, dict[str, float]] = {
    "low": dict(history_share=0.20, profile_in=800, profile_out=150, extract_in=400, extract_out=100, context_in=200,
                call_rate=0.10, call_in=5_000, call_out=600, plan_in=1_200, plan_out=400, monthly_calls=20),
    "base": dict(history_share=0.35, profile_in=1_500, profile_out=300, extract_in=600, extract_out=150,
                 context_in=400, call_rate=0.20, call_in=8_000, call_out=1_000, plan_in=2_000, plan_out=600,
                 monthly_calls=60),
    "high": dict(history_share=0.60, profile_in=4_000, profile_out=800, extract_in=1_200, extract_out=400,
                 context_in=1_000, call_rate=0.35, call_in=15_000, call_out=2_500, plan_in=3_500, plan_out=1_200,
                 monthly_calls=200),
}
GRAPH_TOKEN_KEYS = ("profile_in", "profile_out", "extract_in", "extract_out", "context_in", "call_in", "call_out",
                    "plan_in", "plan_out")
SHARED = dict(reply_share=0.85, touches_per_month=2, fallback_share=0.05, days_per_month=30)
BUDGET_MULTIPLIER = 2  # plan AI spend at twice the base projection: a comfortable starting budget, not a limit
PLANNING_MULTIPLES = (2, 5)  # the agreement quotes AI and texting at these multiples of the base projection
TOKEN_KEYS = ("ingest_in", "draft_in", "draft_out", "qa_in", "classify_in", "reply_in", "reply_out",
              "session_in", "session_out")


def _llm(calls: float, tin: float, tout: float, fallback: float) -> float:
    """Cost of `calls` drafting calls on Luna Pro, with `fallback` share served by GLM 5.3 Flash."""
    luna, glm = MODELS["luna"], MODELS["glm"]
    per = ((1 - fallback) * (tin * luna["in"] + tout * luna["out"])
           + fallback * (tin * glm["in"] + tout * glm["out"])) / 1e6
    return calls * per


def _jev(calls: float, tin: float) -> float:
    return calls * tin * MODELS["jev"]["in"] / 1e6


def project(p: dict[str, Any], fallback: float, g: dict[str, float] | None = None) -> dict[str, Any]:
    s = {**SHARED, **p}
    g = g or GRAPH["base"]
    out_rate = SMS["base_per_segment"] + SMS["carrier_out"][s["tier"]]
    in_rate = SMS["base_per_segment"] + SMS["carrier_in"][s["tier"]]

    # One-time reactivation of the inactive base
    kickoffs = REACTIVATION_AUDIENCE
    responders = kickoffs * s["reply_rate"]
    inbound = responders * s["inbound_per_responder"]
    replies = inbound * s["reply_share"]
    react_lines = [
        ("Jev: ingest and normalize every partner record", _jev(PARTNERS_TOTAL, s["ingest_in"]), PARTNERS_TOTAL),
        ("Luna Pro: draft one personal kickoff text each", _llm(kickoffs, s["draft_in"], s["draft_out"], fallback), kickoffs),
        ("Jev: compliance check on every draft", _jev(kickoffs + replies, s["qa_in"]), kickoffs + replies),
        ("Jev: classify every inbound reply", _jev(inbound, s["classify_in"]), inbound),
        ("Luna Pro: draft each conversation reply", _llm(replies, s["reply_in"], s["reply_out"], fallback), replies),
    ]
    react_ai = sum(c for _, c, _ in react_lines)
    react_sms_lines = [
        (f"Kickoff texts (up to {s['kick_seg']} segments each)", kickoffs * s["kick_seg"] * out_rate, kickoffs),
        ("Conversation replies", replies * s["seg_out"] * out_rate, replies),
        ("Inbound texts", inbound * s["seg_in"] * in_rate, inbound),
        ("A2P 10DLC brand + campaign registration (one time)", SMS["a2p_one_time"], 1),
    ]
    react_sms = sum(c for _, c, _ in react_sms_lines)

    # Monthly, steady state: every partner on the two-week cadence, AI-personalized
    touches = PARTNERS_TOTAL * s["touches_per_month"]
    m_inbound = touches * s["ongoing_reply_rate"] * s["ongoing_inbound"]
    m_replies = m_inbound * s["reply_share"]
    sessions = s["sessions_per_day"] * s["days_per_month"]
    month_lines = [
        ("Luna Pro: personalized cadence touches (2 per partner)", _llm(touches, s["draft_in"], s["draft_out"], fallback), touches),
        ("Jev: compliance check on every draft", _jev(touches + m_replies, s["qa_in"]), touches + m_replies),
        ("Jev: classify every inbound reply", _jev(m_inbound, s["classify_in"]), m_inbound),
        ("Luna Pro: draft each conversation reply", _llm(m_replies, s["reply_in"], s["reply_out"], fallback), m_replies),
        ("Hermes agent: daily loop, reply triage, manager chat (uncached)",
         _llm(sessions, s["session_in"], s["session_out"], fallback), sessions),
    ]
    month_ai = sum(c for _, c, _ in month_lines)
    month_sms_lines = [
        ("Outbound texts (touches + replies)", (touches + m_replies) * s["seg_out"] * out_rate, touches + m_replies),
        ("Inbound texts", m_inbound * s["seg_in"] * in_rate, m_inbound),
        ("A2P 10DLC campaign fee", SMS["a2p_monthly"], 1),
    ]
    month_sms = sum(c for _, c, _ in month_sms_lines)

    # The relationship graph (priced separately; see GRAPH)
    calls = responders * g["call_rate"]
    graph_react_lines = [
        ("Luna Pro: build a profile from each record with real history",
         _llm(kickoffs * g["history_share"], g["profile_in"], g["profile_out"], fallback), kickoffs * g["history_share"]),
        ("Luna Pro: the partner's profile in every kickoff and reply prompt",
         _llm(kickoffs + replies, g["context_in"], 0, fallback), kickoffs + replies),
        ("Luna Pro: pull facts from every inbound reply", _llm(inbound, g["extract_in"], g["extract_out"], fallback),
         inbound),
        ("Luna Pro: read each recorded call (facts, commitments)", _llm(calls, g["call_in"], g["call_out"], fallback),
         calls),
        ("Luna Pro: draft a revenue plan after each call", _llm(calls, g["plan_in"], g["plan_out"], fallback), calls),
    ]
    graph_month_lines = [
        ("Luna Pro: the partner's profile in every touch and reply prompt",
         _llm(touches + m_replies, g["context_in"], 0, fallback), touches + m_replies),
        ("Luna Pro: pull facts from every inbound reply", _llm(m_inbound, g["extract_in"], g["extract_out"], fallback),
         m_inbound),
        ("Luna Pro: read each recorded call", _llm(g["monthly_calls"], g["call_in"], g["call_out"], fallback),
         g["monthly_calls"]),
        ("Luna Pro: revenue plans", _llm(g["monthly_calls"], g["plan_in"], g["plan_out"], fallback), g["monthly_calls"]),
    ]
    graph_react = sum(c for _, c, _ in graph_react_lines)
    graph_month = sum(c for _, c, _ in graph_month_lines)

    def rows(lines):
        return [{"item": i, "usd": round(c, 4), "volume": round(v)} for i, c, v in lines]

    return {
        "assumptions": {k: s[k] for k in s if k != "tier"} | {"fallback_share": fallback,
                                                               "sms_out_per_segment": round(out_rate, 5),
                                                               "sms_in_per_segment": round(in_rate, 5)},
        "reactivation": {"kickoffs": kickoffs, "responders": round(responders), "inbound": round(inbound),
                         "replies": round(replies), "ai_lines": rows(react_lines), "ai_usd": round(react_ai, 2),
                         "sms_lines": rows(react_sms_lines), "sms_usd": round(react_sms, 2),
                         "total_usd": round(react_ai + react_sms, 2),
                         "ai_per_1000_kickoffs_usd": round(_llm(1000, s["draft_in"], s["draft_out"], fallback)
                                                           + _jev(1000, s["qa_in"]), 3),
                         "ai_per_conversation_usd": round((react_ai - _jev(PARTNERS_TOTAL, s["ingest_in"])
                                                           - _llm(kickoffs, s["draft_in"], s["draft_out"], fallback)
                                                           - _jev(kickoffs, s["qa_in"])) / max(responders, 1), 5),
                         "ai_per_reengaged_partner_usd": round(react_ai / max(responders, 1), 4)},
        "monthly": {"touches": touches, "inbound": round(m_inbound), "replies": round(m_replies),
                    "agent_sessions": sessions, "ai_lines": rows(month_lines), "ai_usd": round(month_ai, 2),
                    "sms_lines": rows(month_sms_lines), "sms_usd": round(month_sms, 2),
                    "total_usd": round(month_ai + month_sms, 2)},
        "graph": {"assumptions": dict(g), "calls": round(calls),
                  "reactivation": {"ai_lines": rows(graph_react_lines), "ai_usd": round(graph_react, 2),
                                   "with_base_ai_usd": round(react_ai + graph_react, 2)},
                  "monthly": {"ai_lines": rows(graph_month_lines), "ai_usd": round(graph_month, 2),
                              "with_base_ai_usd": round(month_ai + graph_month, 2)}},
    }


def build() -> dict[str, Any]:
    scen = {name: project(p, SHARED["fallback_share"], GRAPH[name]) for name, p in SCENARIOS.items()}
    stress = {**SCENARIOS["base"], **{k: SCENARIOS["base"][k] * 10 for k in TOKEN_KEYS}}
    stress_graph = {**GRAPH["base"], **{k: GRAPH["base"][k] * 10 for k in GRAPH_TOKEN_KEYS}}
    scen["stress_10x_tokens"] = project(stress, SHARED["fallback_share"], stress_graph)
    scen["all_on_glm_fallback"] = project(SCENARIOS["base"], 1.0, GRAPH["base"])
    batch = dict(SCENARIOS["base"])
    base = scen["base"]
    luna = MODELS["luna"]
    batch_saving = _llm(REACTIVATION_AUDIENCE, batch["draft_in"], batch["draft_out"], SHARED["fallback_share"]) * (
        1 - luna["batch_in"] / luna["in"])  # batch halves both prices, so the saving is half the kickoff line
    # Rollout in waves, each opened only when the one before it clears its gates (no dates)
    r = base["reactivation"]
    ai_per_partner = (r["ai_usd"] - _jev(PARTNERS_TOTAL, SCENARIOS["base"]["ingest_in"])) / REACTIVATION_AUDIENCE
    sms_per_partner = (r["sms_usd"] - SMS["a2p_one_time"]) / REACTIVATION_AUDIENCE
    sizes = [("Pilot", 250), ("Wave 2", 2_500), ("Full base", REACTIVATION_AUDIENCE - 2_750)]
    two_x = {k: round(base[part]["ai_usd"] * 2, 2) for k, part in (("reactivation", "reactivation"),
                                                                    ("monthly", "monthly"))}
    for part in ("reactivation", "monthly"):  # the graph must fit inside the agreement's 2x AI figure
        with_graph = base["graph"][part]["with_base_ai_usd"]
        assert with_graph <= two_x[part], f"{part}: base + relationship graph {with_graph} exceeds 2x {two_x[part]}"
    waves = [{"wave": name, "partners": n, "ai_usd": round(n * ai_per_partner, 2),
              "sms_usd": round(n * sms_per_partner, 2),
              "expected_replies": round(n * SCENARIOS["base"]["reply_rate"])} for name, n in sizes]
    return {
        "priced_on": PRICED_ON,
        "waves": waves,
        "wave_gates": ["Opt-outs stay under a ceiling agreed before the pilot (we suggest 3% of texts sent)",
                       "No carrier filtering or spam flags on the number",
                       "7FF has read a sample of the conversations and is happy with the tone",
                       "Deals from replies are reaching the funding team and being counted by tier",
                       "AI spend is tracking the projection, inside the starting budget"],
        "wave_notes": [f"Jev reads all {PARTNERS_TOTAL:,} records once at import (about "
                       f"{_usd(_jev(PARTNERS_TOTAL, SCENARIOS['base']['ingest_in']))}).",
                       f"The texting number is registered for A2P 10DLC ({_usd(SMS['a2p_one_time'])} one time).",
                       "How many texts a day the carriers allow depends on the trust score they give 7FF's registration. "
                       "A low score caps daily volume and makes each wave take longer; it doesn't change the cost."],
        "spec": SPEC, "flow": [{"step": a, "what": b} for a, b in FLOW],
        "models": MODELS, "sms": SMS, "measured": MEASURED,
        "population": {"partners_total": PARTNERS_TOTAL, "partners_active": PARTNERS_ACTIVE,
                       "reactivation_audience": REACTIVATION_AUDIENCE},
        "shared": SHARED,
        "scenarios": scen,
        "headline": {
            "reactivation_ai_usd": base["reactivation"]["ai_usd"],
            "reactivation_ai_range_usd": [scen["low"]["reactivation"]["ai_usd"], scen["high"]["reactivation"]["ai_usd"]],
            "monthly_ai_usd": base["monthly"]["ai_usd"],
            "monthly_ai_range_usd": [scen["low"]["monthly"]["ai_usd"], scen["high"]["monthly"]["ai_usd"]],
            "stress_monthly_ai_usd": scen["stress_10x_tokens"]["monthly"]["ai_usd"],
            "stress_reactivation_ai_usd": scen["stress_10x_tokens"]["reactivation"]["ai_usd"],
            "reactivation_sms_usd": base["reactivation"]["sms_usd"],
            "monthly_sms_usd": base["monthly"]["sms_usd"],
            "kickoff_batch_saving_usd": round(batch_saving, 2),
            "graph_reactivation_ai_usd": base["graph"]["reactivation"]["ai_usd"],
            "graph_monthly_ai_usd": base["graph"]["monthly"]["ai_usd"],
            "with_graph_reactivation_ai_usd": base["graph"]["reactivation"]["with_base_ai_usd"],
            "with_graph_monthly_ai_usd": base["graph"]["monthly"]["with_base_ai_usd"],
            "graph_range_reactivation_ai_usd": [scen["low"]["graph"]["reactivation"]["ai_usd"],
                                                scen["high"]["graph"]["reactivation"]["ai_usd"]],
            "graph_range_monthly_ai_usd": [scen["low"]["graph"]["monthly"]["ai_usd"],
                                           scen["high"]["graph"]["monthly"]["ai_usd"]],
            "multiples": {str(m): {k: round(base[part][f] * m, 2) for k, part, f in (
                ("reactivation_ai_usd", "reactivation", "ai_usd"), ("monthly_ai_usd", "monthly", "ai_usd"),
                ("reactivation_sms_usd", "reactivation", "sms_usd"), ("monthly_sms_usd", "monthly", "sms_usd"))}
                for m in PLANNING_MULTIPLES},
            "budget_multiplier": BUDGET_MULTIPLIER,
            "reactivation_ai_budget_usd": round(base["reactivation"]["ai_usd"] * BUDGET_MULTIPLIER, 2),
            "monthly_ai_budget_usd": round(base["monthly"]["ai_usd"] * BUDGET_MULTIPLIER, 2),
        },
    }


def _usd(v: float) -> str:
    return f"${v:,.2f}" if v >= 0.01 or v == 0 else f"${v:.4f}"


def assumption_notes(d: dict[str, Any]) -> list[str]:
    a, h = d["scenarios"]["base"]["assumptions"], d["headline"]
    return [
        f"Kickoff draft: {a['draft_in']:,} tokens in, {a['draft_out']:,} out (including Luna Pro's reasoning).",
        f"Conversation reply: {a['reply_in']:,} in, {a['reply_out']:,} out. The agent answers {a['reply_share']:.0%} "
        "of inbound messages; the rest are STOPs and 'thanks'.",
        f"Each partner who replies sends {a['inbound_per_responder']} messages on average.",
        f"Jev: {a['ingest_in']:,} tokens to ingest a record, {a['qa_in']:,} to check a draft, "
        f"{a['classify_in']:,} to classify a reply.",
        f"Hermes agent: {a['sessions_per_day']} sessions a day at {a['session_in']:,} tokens each, priced uncached "
        f"(a measured daily-loop session processed {d['measured']['hermes_daily_loop_session']['tokens_processed']:,}).",
        f"{a['fallback_share']:.0%} of drafting falls back to GLM 5.3 Flash; the 'All on GLM' column prices 100%.",
        f"The Hermes line ({_usd(d['scenarios']['base']['monthly']['ai_lines'][-1]['usd'])} of the "
        f"{_usd(d['scenarios']['base']['monthly']['ai_usd'])} a month) prices the agent's own loop on Luna Pro, uncached.",
        f"The starting budget is {h['budget_multiplier']}x the base projection for AI: room for longer conversations and "
        "more replies than expected. Texting is shown at its projection.",
        f"Kickoff texts run up to {a['kick_seg']} GSM-7 segments, leaving room for one line from the partner's own "
        f"record; every other text is kept to {a['seg_out']}. One em dash or curly quote would switch a text to UCS-2 "
        "and bill more segments; the agent strips them before sending, and refuses a kickoff over 2 segments.",
        f"The relationship graph adds about {_usd(h['graph_reactivation_ai_usd'])} to the reactivation and "
        f"{_usd(h['graph_monthly_ai_usd'])} a month (profiles, reply facts, call reading, revenue plans). With it, AI "
        f"comes to {_usd(h['with_graph_reactivation_ai_usd'])} and {_usd(h['with_graph_monthly_ai_usd'])} a month, "
        "inside the starting budget.",
        f"Texting: ${a['sms_out_per_segment']} per outbound segment and ${a['sms_in_per_segment']} per inbound, "
        "HighLevel base rate plus carrier fees.",
        "Every partner is assumed textable. Numbers without a working mobile or SMS consent only lower these costs.",
        "The monthly line keeps all partners on the two-week text cadence. Moving partners who never re-engage to "
        "email and the newsletter cuts the texting line sharply.",
        f"Sending the kickoff through OpenRouter's batch mode would save about {_usd(h['kickoff_batch_saving_usd'])} more.",
    ]


def markdown(d: dict[str, Any]) -> str:
    h, sc = d["headline"], d["scenarios"]
    names = [("low", "Low"), ("base", "Base"), ("high", "High"), ("stress_10x_tokens", "10x tokens"),
             ("all_on_glm_fallback", "All on GLM")]
    L = [f"# AI cost projection: reactivating 7FF's {d['population']['partners_total']:,} partners",
         "",
         f"Priced {d['priced_on']} from OpenRouter, TypeSafe (Jev) and HighLevel published rates. Generated by "
         "`scripts/cost_model.py`; do not edit by hand.",
         "",
         "## The answer",
         "",
         f"- **Reactivation, one time:** about **{_usd(h['reactivation_ai_usd'])} in AI** to send "
         f"{d['population']['reactivation_audience']:,} personal kickoff texts and run every conversation that "
         f"follows (range {_usd(h['reactivation_ai_range_usd'][0])} to {_usd(h['reactivation_ai_range_usd'][1])}).",
         f"- **Ongoing, per month:** about **{_usd(h['monthly_ai_usd'])} in AI** with all "
         f"{d['population']['partners_total']:,} partners on the two-week cadence (range "
         f"{_usd(h['monthly_ai_range_usd'][0])} to {_usd(h['monthly_ai_range_usd'][1])}).",
         f"- **Starting budget for AI: {h['budget_multiplier']}x the projection,** "
         f"{_usd(h['reactivation_ai_budget_usd'])} for the reactivation and {_usd(h['monthly_ai_budget_usd'])} a month.",
         f"- **If every token estimate is 10x too low:** {_usd(h['stress_monthly_ai_usd'])} a month.",
         f"- **Texting is the bigger line, and it isn't AI:** about {_usd(h['reactivation_sms_usd'])} for the "
         f"reactivation and {_usd(h['monthly_sms_usd'])} a month ongoing, billed by HighLevel's phone system.",
         "",
         "## Planning figures",
         "",
         "The agreement quotes each line at " + " and ".join(f"{m}x" for m in h["multiples"]) + " the base projection:",
         "",
         "| | " + " | ".join(f"{m}x" for m in h["multiples"]) + " |", "|---|" + "---:|" * len(h["multiples"]),
         *[f"| {label} | " + " | ".join(_usd(v[key]) for v in h["multiples"].values()) + " |" for key, label in (
             ("reactivation_ai_usd", "AI, reactivation (one time)"), ("monthly_ai_usd", "AI, every month"),
             ("reactivation_sms_usd", "Texting, reactivation (one time)"), ("monthly_sms_usd", "Texting, every month"))],
         "",
         "## What runs it",
         "",
         "| Part | Status | What it does |", "|---|---|---|",
         *[f"| {x['part']} | {x['status']} | {x['does']} |" for x in d["spec"]],
         "",
         "## The reactivation, step by step",
         "",
         *[f"{i}. **{x['step']}.** {x['what']}" for i, x in enumerate(d["flow"], 1)],
         "",
         "## Rollout in waves",
         "",
         "Each wave opens only when the one before it clears every gate. Costs are the base case.",
         "",
         "| Wave | Partners | Expected replies | AI | Texting |", "|---|---:|---:|---:|---:|",
         *[f"| {w['wave']} | {w['partners']:,} | {w['expected_replies']:,} | {_usd(w['ai_usd'])} | {_usd(w['sms_usd'])} |"
           for w in d["waves"]],
         "",
         "Gates:",
         "",
         *[f"- {g}" for g in d["wave_gates"]],
         "",
         "Before the pilot: " + " ".join(d["wave_notes"]),
         "",
         "## Scenarios",
         "",
         "| | " + " | ".join(n for _, n in names) + " |",
         "|---|" + "---:|" * len(names),
         "| Reply rate to the kickoff | " + " | ".join(f"{sc[k]['assumptions']['reply_rate']:.0%}" for k, _ in names) + " |",
         "| Partners who reply | " + " | ".join(f"{sc[k]['reactivation']['responders']:,}" for k, _ in names) + " |",
         "| **Reactivation AI (one time)** | " + " | ".join(f"**{_usd(sc[k]['reactivation']['ai_usd'])}**" for k, _ in names) + " |",
         "| Reactivation texting (one time) | " + " | ".join(_usd(sc[k]['reactivation']['sms_usd']) for k, _ in names) + " |",
         "| **Monthly AI** | " + " | ".join(f"**{_usd(sc[k]['monthly']['ai_usd'])}**" for k, _ in names) + " |",
         "| Monthly texting | " + " | ".join(_usd(sc[k]['monthly']['sms_usd']) for k, _ in names) + " |",
         "| AI per re-engaged partner | " + " | ".join(_usd(sc[k]['reactivation']['ai_per_reengaged_partner_usd']) for k, _ in names) + " |",
         "",
         "## The relationship graph",
         "",
         "Every partner gets a profile (an Obsidian note linked to their tier, niche, manager and the products their "
         "clients need), built from their record, then from every reply and recorded call. It is priced here on top "
         "of the figures above, and stays inside the starting budget.",
         "",
         "| | Low | Base | High |", "|---|---:|---:|---:|",
         "| Reactivation (one time) | " + " | ".join(_usd(sc[k]["graph"]["reactivation"]["ai_usd"]) for k in ("low", "base", "high")) + " |",
         "| Every month | " + " | ".join(_usd(sc[k]["graph"]["monthly"]["ai_usd"]) for k in ("low", "base", "high")) + " |",
         "",
         "| Base case | Volume | Cost |", "|---|---:|---:|",
         *[f"| {r['item']} | {r['volume']:,} | {_usd(r['usd'])} |" for r in sc["base"]["graph"]["reactivation"]["ai_lines"]],
         f"| **Reactivation total, AI with the graph** | | **{_usd(h['with_graph_reactivation_ai_usd'])}** (budget {_usd(h['reactivation_ai_budget_usd'])}) |",
         *[f"| {r['item']} (monthly) | {r['volume']:,} | {_usd(r['usd'])} |" for r in sc["base"]["graph"]["monthly"]["ai_lines"]],
         f"| **Monthly total, AI with the graph** | | **{_usd(h['with_graph_monthly_ai_usd'])}** (budget {_usd(h['monthly_ai_budget_usd'])}) |",
         "",
         "## Base case, line by line",
         "",
         "| Reactivation (one time) | Volume | Cost |", "|---|---:|---:|"]
    b = sc["base"]
    L += [f"| {r['item']} | {r['volume']:,} | {_usd(r['usd'])} |" for r in b["reactivation"]["ai_lines"]]
    L += [f"| **AI total** | | **{_usd(b['reactivation']['ai_usd'])}** |"]
    L += [f"| {r['item']} | {r['volume']:,} | {_usd(r['usd'])} |" for r in b["reactivation"]["sms_lines"]]
    L += ["", "| Monthly (steady state) | Volume | Cost |", "|---|---:|---:|"]
    L += [f"| {r['item']} | {r['volume']:,} | {_usd(r['usd'])} |" for r in b["monthly"]["ai_lines"]]
    L += [f"| **AI total** | | **{_usd(b['monthly']['ai_usd'])}** |"]
    L += [f"| {r['item']} | {r['volume']:,} | {_usd(r['usd'])} |" for r in b["monthly"]["sms_lines"]]
    L += ["", "## Assumptions (base)", "", *[f"- {n}" for n in d["assumption_notes"]],
          "", "## Prices used", "",
          "| Model | Role | Input $/M | Output $/M |", "|---|---|---:|---:|"]
    for key, role in (("luna", "Primary: drafts texts and replies"), ("glm", "Fallback"), ("jev", "Classify, ingest, check")):
        m = d["models"][key]
        L.append(f"| {m['label']} ({m['maker']}) | {role} | ${m['in']} | ${m['out']} |")
    L += ["", f"Luna Pro costs more for prompts over {d['models']['luna']['long_prompt_over']:,} tokens "
          f"(${d['models']['luna']['long_in']} in / ${d['models']['luna']['long_out']} out); none of these calls come close.",
          "", "Sources: " + ", ".join(d["sms"]["sources"]) + ", https://openrouter.ai/api/v1/models, https://docs.typesafe.ai/models", ""]
    return "\n".join(L)


def main() -> None:
    d = build()
    d["assumption_notes"] = assumption_notes(d)
    (ROOT / "docs" / "cost-projection.json").write_text(json.dumps(d, indent=2) + "\n")
    (ROOT / "docs" / "ai-cost-projection.md").write_text(markdown(d))
    h = d["headline"]
    print(json.dumps(h, indent=2))
    for k in ("low", "base", "high", "stress_10x_tokens", "all_on_glm_fallback"):
        s = d["scenarios"][k]
        print(f"{k:22} react AI ${s['reactivation']['ai_usd']:>8,.2f}  SMS ${s['reactivation']['sms_usd']:>9,.2f}"
              f"  | monthly AI ${s['monthly']['ai_usd']:>8,.2f}  SMS ${s['monthly']['sms_usd']:>9,.2f}"
              f"  | responders {s['reactivation']['responders']:,}")


if __name__ == "__main__":
    main()
