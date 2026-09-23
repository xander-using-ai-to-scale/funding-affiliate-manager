# 01 — Company and Offer

## Three related brands (do not merge them)

Public research shows one founder (Leo Kanell) behind at least three distinct
public-facing brands. The Funding Affiliate Manager agent should keep them
separate in its own reasoning, because they have different products and
(likely) different affiliate/partner programs.

| Brand | What it is | Public site |
|---|---|---|
| **7 Figures Funding ("7FF")** | The business-funding marketplace/consultancy that referred clients actually apply through. Owns the partner/affiliate program this agent most likely manages. | https://7figuresfunding.com |
| **My Funding Machine ("MFM")** | A SaaS "Funding Broker OS" for people who want to run their own funding brokerage (underwriting automation, CRM, contracts). Also runs a masterclass and FM Live events. | https://myfundingmachine.com |
| **My Figures** | A cash-flow/financial-management app given to 7FF's *funded clients* for account tracking. Has its own **separate** affiliate program at partners.myfigures.com — do not confuse with the 7FF partner program. | https://myfigures.com |

**UNVERIFIED — confirm with 7FF:** which of these brands the 10,000+
affiliates this agent serves actually belong to. This knowledge base assumes
the primary relationship is with the **7 Figures Funding** partner program
(portal.7figurespartners.com), since that is the only public page that
describes an affiliate/referral program for people who send business-funding
deals. If the operator actually means the MFM Skool/masterclass audience, or
a blend of both, re-scope this file.

**UNVERIFIED — confirm with 7FF:** the "10,000+ affiliates" figure came from
the operator's brief, not from any source reviewed here. Treat it as
directional, not a reporting baseline.

## Legal entity

The public Terms of Service on the partner signup page state: *"This website
... including LeoKanell.com, 7Figures.com, 7FiguresPartners.com,
7FiguresConsultant.com, 7figuresfunding.com, 7figureslending.com and
7FiguresU.com, is owned and operated by **7Figures Consultant LLC**."*
`myfundingmachine.com` is **not** in that list, which supports treating MFM as
a separate entity/brand. Use `{{LEGAL_ENTITY}}` in any outward-facing document
(disclosures, CAN-SPAM footer) until 7FF confirms the exact legal name and
registered address to use for this program.

## What 7 Figures Funding sells

- A business-funding **marketplace/consulting service**: 7FF is "not a
  lender." It reviews a prospect's profile, builds a funding strategy across
  multiple lenders/products, and prepares/submits applications.
- Pre-qualification uses a **soft credit pull** ("no hard inquiry to get
  pre-qualified"); a hard pull may occur only if the client moves forward
  with a specific offer.
- 7FF charges its own client a **consulting fee** for this work (not a
  percentage of the funding). Clients get a written service agreement and a
  3-business-day cancellation right. This fee is separate from any affiliate
  commission economics (see `03-affiliate-economics.md`).
- Funded clients get **1 year of access to My Figures** (the cash-flow app)
  as part of their engagement.
- Public stats claimed on the homepage (as of retrieval): "5k+ clients
  served," "30k+ estimated jobs created." Treat as marketing claims with a
  retrieval date, not audited figures.

## Who the customer is

Small business owners and startups seeking capital (working capital, credit
lines, cards, term loans, SBA, HELOC — see `02-funding-products.md`). 7FF
explicitly is not a lender and does not guarantee approval, amount, or terms.

## How a deal flows: affiliate → 7FF → funding

1. Affiliate signs up for a free partner account at
   `portal.7figurespartners.com/affiliates/signup.php` and creates a personal
   **Referral ID**, producing a link of the form
   `7figuresCredit.com/{{REFERRAL_ID}}` (also referenced as
   `{{AFFILIATE_LINK}}` elsewhere in this knowledge base). **Never invent or
   construct a link yourself — only use the affiliate's own recorded link.**
2. The affiliate sends that link to a business owner who needs funding.
3. The prospect completes a short application (7FF states "less than two
   minutes"; homepage says "most people"). This step is a **soft** pull.
4. A 7FF Funding Advisor calls the prospect to review qualifying options
   across the marketplace.
5. If the prospect proceeds with an offer, a hard credit pull may occur at
   that stage, per lender/issuer.
6. Some products can fund quickly ("as little as 48 hours" is 7FF's own
   marketing claim for at least one product — do not repeat this as a
   guarantee; see `06-compliance-guardrails.md`).
7. Affiliates track their own submissions in a **Partner CRM** and get
   deal/decision updates via a **Slack integration** (both stated on the
   partner landing page). This agent does not have access to 7FF's internal
   CRM/Slack data unless a specific integration is confirmed —
   **UNVERIFIED — confirm with 7FF** what data feed (if any) this agent can
   read for deal status.
8. This agent's own charter (see `07-faq-for-affiliates.md` and the
   compliance file) never underwrites, quotes terms, or touches the deal
   itself — it only manages the affiliate relationship around that flow.

## The partner/affiliate program (as publicly described)

From `https://7figuresfunding.com/launch-your-funding-empire` (retrieved
2026-09-23):

- "Become a 7Figures partner and start providing capital to your clients
  within minutes."
- **No fee for the affiliate** to join or use the program ("in no world
  would we charge you to send us leads").
- Affiliates get access to 7FF's financial-management platform (My Figures)
  for their referred clients, a **Partner CRM**, a **Slack integration** for
  real-time decision updates, and the "entire funding marketplace" (multiple
  lenders/products, not just one).
- 7FF "educates and empowers" the affiliate's clients directly — 7FF staff,
  not the affiliate, explain credit/funding mechanics to the end client.
- Partner portal: `portal.7figurespartners.com/affiliates/` (signup + login).
- Contact for the partner program: `partners@7figures.com` /
  `info@7figures.com`, `(833) 801-5653`.
- Per the portal's Terms of Service, anyone may join the referral program
  free of charge by signing up online or emailing `info@7figures.com` — the
  ToS is explicit that this is "an affiliate/partner program," not a
  business opportunity, franchise, or MLM (see `06-compliance-guardrails.md`
  for why that framing matters for what this agent may say).

## The Skool community

`https://www.skool.com/my-funding-machine` (retrieved 2026-09-23):

- Free, ~688-member community run by Leo Kanell (19 admins listed).
- Stated purpose: help members build "a 7 figure funding empire that
  provides funding & value for the small business owners they serve,"
  through a classroom (training), a calendar of live weekly workshops, and
  community discussion spaces.
- This is the **My Funding Machine** brand's Skool, not confirmed to be the
  same community as 7FF's affiliate base. **UNVERIFIED — confirm with 7FF**
  whether this Skool is the actual affiliate community this agent serves, a
  feeder audience into it, or a separate program.

## Sources

- https://7figuresfunding.com/ (retrieved 2026-09-23, via firecrawl)
- https://7figuresfunding.com/launch-your-funding-empire (retrieved 2026-09-23, via firecrawl)
- https://7figuresfunding.com/about-us (retrieved 2026-09-23, via firecrawl)
- https://portal.7figurespartners.com/affiliates/signup.php (retrieved 2026-09-23, via firecrawl — Terms of Service text)
- https://myfundingmachine.com (retrieved 2026-09-23, via WebFetch)
- https://myfundingmachine.com/about (retrieved 2026-09-23, via WebFetch)
- https://myfundingmachine.com/masterclass (retrieved 2026-09-23, via WebFetch)
- https://myfigures.com/ (retrieved 2026-09-23, via firecrawl)
- https://www.skool.com/my-funding-machine/about (retrieved 2026-09-23, via WebFetch)
- WebSearch: `"Seven Figures Funding" OR "myfundingmachine" affiliate program Skool community` (retrieved 2026-09-23)
- /private/tmp/claude-501/-Users-home-Funding-Affiliate-Manager/51b442fe-9411-4270-aeda-6e934de05076/scratchpad/repos/funding-director-orgo/files/agent-knowledge/07.Funding Department Charter.md (front-end/back-end split)
- /private/tmp/claude-501/-Users-home-Funding-Affiliate-Manager/51b442fe-9411-4270-aeda-6e934de05076/scratchpad/repos/funding-director-agent/grok-bot/PROFILE.md (confirms this agent's counterpart does not do affiliate/relationship work, and vice versa)
