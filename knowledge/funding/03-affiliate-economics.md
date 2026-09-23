# 03 — Affiliate Economics

**Never state a commission percentage, dollar amount, or payout timeline as
fact to an affiliate unless it is pulled from an approved, current 7FF
source at the time of the conversation.** Everything below marked
`{{PLACEHOLDER}}` is unknown to this agent and must be filled from a verified
7FF source before it is ever repeated externally.

## How business-funding affiliates/ISOs typically get paid — general industry knowledge (flagged as such)

This section is generic broker/ISO-channel knowledge, not 7FF-specific. It
exists so the agent understands the *shape* of affiliate economics in this
industry when a partner asks a general question, while still deferring the
actual number to 7FF.

- **Referral fee vs. ISO split:** A pure "referral fee" model pays a flat or
  percentage bounty for a funded deal the affiliate introduced, with 7FF
  doing all the work. An "ISO split" model (more common among brokers who
  do more of the client-facing work) shares a percentage of the funder's
  origination fee/commission with the ISO. **UNVERIFIED — confirm with
  7FF** which model applies to this program; the public partner page
  describes a lightweight "send us leads, we do the rest" flow, which reads
  closer to a referral-fee model.
- **When paid:** Typically upon the deal funding (not upon submission or
  approval), sometimes net of a short holdback period in case of early
  default/payback issues.
- **Clawbacks:** Many ISO/referral agreements in this industry include a
  clawback if the funded client defaults very early, pays off unusually
  fast (reducing the funder's yield), or if fraud/misrepresentation is
  found. **UNVERIFIED — confirm with 7FF** whether 7FF's program has any
  clawback provision; nothing in the public sources reviewed states one.

## What is actually confirmed publicly about 7FF's commission mechanics

From the 7 Figures Partners portal Terms of Service (`portal.7figurespartners.com/affiliates/signup.php`,
retrieved 2026-09-23) — these are real, sourced mechanics, safe to repeat:

- Commissions are **paid on Fridays**, for all commissions earned through
  the **preceding Tuesday at 11:59 PM MST**.
- On an affiliate's **first** earned commission, they get an invitation to
  join 7FF's payroll system, **Everee**.
- Once the affiliate creates their Everee account, payment for
  already-earned commissions arrives within **7 days**.
- If the affiliate does **not** create an Everee account within **6
  months** of getting the invite, unpaid commissions are **forfeited** and
  the affiliate waives any claim to them. This is the closest thing to a
  "clawback" that is publicly documented, and it's really a
  use-it-or-lose-it deadline tied to payroll setup, not a performance
  clawback.
- Affiliates may ask 7FF to give their referred client a **discount**, up to
  the affiliate's own commission percentage on that sale — the discount
  amount comes directly out of the affiliate's commission (they forfeit
  that portion). The ToS illustrates this with a 10% example; **that 10% is
  an illustration of the mechanism, not 7FF's actual standard commission
  rate.** Discount requests must go to `info@7figures.com` for approval and,
  once granted, cannot be reversed.
- Governing law for commission payments is the State of Utah.
- Joining the partner/referral program itself is **free** — no signup fee,
  no franchise fee (the ToS explicitly disclaims being a franchise, MLM, or
  "business opportunity" under FTC rules — see `06-compliance-guardrails.md`
  for why the agent must preserve that framing).

## Placeholders for 7FF's actual commission terms

- Standard commission rate / range: `{{COMMISSION_RATE}}`
- Whether the rate varies by product type: `{{COMMISSION_RATE_BY_PRODUCT}}`
- Whether the rate varies by affiliate tier/volume: `{{COMMISSION_TIER_RULES}}`
- Minimum payout threshold, if any: `{{MIN_PAYOUT_THRESHOLD}}`
- Any performance clawback beyond the Everee 6-month forfeiture: `{{CLAWBACK_TERMS}}`
- Cookie/attribution window (how long a referral link stays credited to the affiliate): `{{ATTRIBUTION_WINDOW}}`

## Program-level KPIs this agent should track

Define every metric with an explicit **measurement window** and **source
system**; never blend numbers computed on different windows or definitions
(per the affiliate-manager skill's operating rule).

| KPI | Definition | Suggested window |
|---|---|---|
| Active affiliates | Affiliates with a live, non-suspended partner account | Point-in-time snapshot |
| Affiliates submitting ≥1 deal / 30 days | Distinct affiliates with at least one tracked submission in the trailing 30 days | Rolling 30-day |
| Deals submitted | Count of tracked submissions (via `{{AFFILIATE_LINK}}` / Partner CRM) | Per period, state the period |
| Funded volume | Dollar amount of referred deals that reached funded status | Per period, state the period; source = Partner CRM / 7FF funding system, not affiliate self-report |
| Time-to-first-deal | Days from affiliate signup to their first tracked submission | Per cohort (e.g., signup month) |
| Reactivation rate | Share of dormant affiliates (see `04-affiliate-segments-and-sources.md` / `05-conversation-playbook.md` dormancy definition) who submit a new deal within N days of a reactivation touch | Define N explicitly, e.g. 30 or 60 days post-touch |
| Reply rate | Share of outbound touches (SMS/email) that get any reply | Per campaign/touch type |

**UNVERIFIED — confirm with 7FF:** the actual system of record for
submissions/funded volume (Partner CRM export? Slack feed? something else?)
and whether this agent has read access to it, or must rely on affiliates
self-reporting. Until confirmed, treat any "funded volume" or "deals
submitted" number an affiliate reports in conversation as unverified and
label it as self-reported when passing it along to a human.

## Sources

- https://portal.7figurespartners.com/affiliates/signup.php (retrieved 2026-09-23, via firecrawl — Terms of Service, Commission Payments and Offering Client Discounts sections)
- https://7figuresfunding.com/launch-your-funding-empire (retrieved 2026-09-23, via firecrawl — "No Fee For You" section)
- /private/tmp/claude-501/-Users-home-Funding-Affiliate-Manager/51b442fe-9411-4270-aeda-6e934de05076/scratchpad/repos/affiliate-manager-agent/skills/roles/affiliate-manager/SKILL.md (Weekly scorecard section — KPI list and "never merge metrics from different definitions or time windows" rule)
- /private/tmp/claude-501/-Users-home-Funding-Affiliate-Manager/51b442fe-9411-4270-aeda-6e934de05076/scratchpad/harvest/affiliate-program-launch/01-governance-key.md (general industry governance framing: traceability, least-privilege, decision rights — used only for the generic-industry framing, not as 7FF fact)
- General industry knowledge (referral-fee vs. ISO-split, clawback norms) — flagged inline as generic, not sourced to 7FF
