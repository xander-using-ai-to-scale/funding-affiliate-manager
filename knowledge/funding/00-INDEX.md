# 00 — Index

Knowledge base for the Funding Affiliate Manager agent (myfundingmachine.com
/ Seven Figures Funding "7FF"). This agent manages affiliate
**relationships** — check-ins, newsletters, offers, reactivation, events,
growth services. It never underwrites, quotes, or submits deals.

| File | What it's for |
|---|---|
| `01-company-and-offer.md` | Who 7FF/MFM/My Figures are, how they relate, what 7FF sells, the customer, the Skool community, and how a deal flows affiliate → 7FF → funding. |
| `02-funding-products.md` | Plain-English product cards for each funding type, flagged [7FF-LISTED] vs [INDUSTRY-STANDARD/unverified], with fit signals, red flags, and a one-line explanation for affiliates — no rates/underwriting. |
| `03-affiliate-economics.md` | How funding affiliates/ISOs generally get paid (flagged as general industry knowledge) plus 7FF's actual verified payout mechanics, placeholders for unverified commission terms, and the program KPIs to track. |
| `04-affiliate-segments-and-sources.md` | Affiliate archetypes (coaches, credit-repair pros, CPAs, agencies, real-estate investors, existing ISOs, Skool members, etc.), what motivates each, and the `src:*` source tags. |
| `05-conversation-playbook.md` | Voice rules and draft SMS/email message frameworks for every touch type (bi-weekly, monthly offer, 60–90-day check-in, reactivation, new offer, event invite, growth-service offer) plus responses to common replies. All drafts pending human approval. |
| `06-compliance-guardrails.md` | What the agent must never say, TCPA/quiet-hours, CAN-SPAM, A2P 10DLC, STOP/DNC, FTC affiliate disclosure, and data-handling rules. Operational guidance, not legal advice. |
| `07-faq-for-affiliates.md` | 20 likely affiliate questions with answer frameworks, placeholders where 7FF-specific facts are unconfirmed. |

## Open items — confirm with 7FF before this agent operates externally

**Scope/identity**
- Which brand's affiliates this agent actually serves (7FF marketplace
  partners vs. MFM Skool/masterclass audience vs. both) — `01`.
- The "10,000+ affiliates" figure (operator-stated, not source-verified) — `01`.
- Exact legal entity name (`{{LEGAL_ENTITY}}`) and mailing address to use in
  disclosures/CAN-SPAM footers (`{{PHYSICAL_ADDRESS}}`; public site lists
  915 S 500 E, Suite 100, American Fork, UT 84003, but confirm it's correct
  for this program) — `01`, `06`.
- Whether Skool community members are automatically 7FF partner-program
  affiliates or a separate/feeder audience — `01`, `04`.

**Economics**
- Standard commission rate/range (`{{COMMISSION_RATE}}`), whether it varies
  by product (`{{COMMISSION_RATE_BY_PRODUCT}}`) or by affiliate tier
  (`{{COMMISSION_TIER_RULES}}`), minimum payout threshold
  (`{{MIN_PAYOUT_THRESHOLD}}`), any performance clawback beyond the Everee
  6-month forfeiture (`{{CLAWBACK_TERMS}}`), and the attribution/cookie
  window (`{{ATTRIBUTION_WINDOW}}`) — `03`.
- System of record this agent can actually read for submissions/funded
  volume (Partner CRM export, Slack feed, other) — `03`, `07`.

**Products**
- Whether 7FF currently offers equipment financing, invoice factoring,
  business-purpose real estate/DSCR, or micro-business funding — these are
  industry-standard but not seen on 7FF's own public marketplace pages,
  which list only: 0% intro cards, business line of credit, business-purpose
  personal term loan, business term loan, SBA, short-term loan/MCA, and
  business-use HELOC — `02`.
- 7FF's own public pages disagree on the post-intro APR for 0% cards
  (17.99–29.99% vs. 15.99–24.99%) — worth flagging back to 7FF as a
  possible stale-page issue; this agent should never quote either number — `02`.
- Whether a partner needs a formal business entity to join
  (`{{PARTNER_ENTITY_REQUIREMENT}}`), and 7FF's exact answer on personal
  (non-business) funding (`{{PERSONAL_FUNDING_ANSWER}}`) — `07`.

**Compliance**
- Whether the SMS sending number/campaign is currently A2P 10DLC-registered — `06`.

## Rules for using this knowledge base

- Never invent a rate, approval odds, commission percentage, or dollar
  figure. Use the `{{PLACEHOLDER}}` tokens above until a human fills them
  from a current 7FF source.
- Every claim in every file is sourced at the bottom of that file. If a
  claim isn't sourced, don't repeat it externally.
- All message drafts in `05` require human approval before any send — this
  mirrors the prior deployment's "empty by design" approved-message rule.

## Sources

This index summarizes `01` through `07`, each of which lists its own
sources in full.
