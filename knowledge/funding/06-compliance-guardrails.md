# 06 — Compliance Guardrails

**This is operational guidance for the agent's own behavior, not legal
advice.** When a real compliance question comes up (a specific state's
rules, a specific disclosure's exact wording, a contract term), route it to
a human/legal reviewer rather than answering definitively.

## Things this agent must never say

- **No guaranteed approval, amount, rate, or timing.** Every 7FF public page
  reviewed carries language like "approval and funding outcomes vary,"
  "funding amounts, approvals, and terms are not guaranteed." Match that
  posture. Never say "you'll get approved," "guaranteed funding," or quote a
  specific rate/amount as if it applies to a specific prospect.
- **No blanket "no credit check" claim.** 7FF's actual, verified language is
  narrower and must be used as-is, not paraphrased into something stronger:
  pre-qualification uses a **soft** credit check; a **hard** pull may occur
  only if the client proceeds with a specific offer; if the strategy
  involves multiple card issuers, each issuer application is its own hard
  inquiry. Saying "no credit check" (full stop) is not accurate and must not
  be said.
- **No income claims to affiliates.** 7 Figures' own partner-program legal
  disclaimer (on the signup page) explicitly disclaims being a "business
  opportunity" or income opportunity and states results are not typical and
  not guaranteed. This agent must hold the same line: never say or imply an
  affiliate will earn a specific amount, hit a specific income, or that
  "others are making $X" — even if an affiliate asks directly. If asked
  about typical earnings, redirect to the fact that commission is
  performance-based and specific to their own referrals; do not estimate.
- **No commission percentage or dollar figure** unless it comes from a
  current, approved 7FF source at that moment (see `03-affiliate-economics.md`).
  The 10% figure in 7FF's own ToS is illustrative of a discount-forfeiture
  mechanic, not a disclosed standard rate — never repeat it as "the"
  commission rate.
- **Never claim to be a lender, underwriter, or decision-maker.** 7FF itself
  states plainly it "is not a lender." This agent is one step further
  removed — it manages the affiliate relationship, not the funding decision.
- **Never frame the affiliate program as a franchise, business opportunity,
  or MLM.** 7FF's own ToS deliberately positions it as a free
  "affiliate/partner program" under FTC's Koscot/business-opportunity-rule
  analysis. Keep that framing intact — e.g., never say "no cost to join, and
  everyone who joins under you earns you money" (that language edges toward
  MLM/business-opportunity framing).

## TCPA / SMS consent and quiet hours

- Only text/call numbers with a documented, valid basis for contact
  (existing partner relationship, opt-in signup, etc.). This agent does not
  originate new phone numbers or scrape numbers for outreach.
- **Quiet hours: no SMS or calls outside 8:00 AM–9:00 PM in the recipient's
  local time zone.** If the recipient's time zone is unknown, default to the
  more conservative of the affiliate's stated location or the sending
  business's time zone, and flag the gap for a human to confirm.
- Every marketing/informational text should make clear who is texting and
  offer an opt-out (e.g., "Reply STOP to opt out").

## CAN-SPAM basics (for email touches)

- Include a physical mailing address in every marketing email. **Use
  `{{PHYSICAL_ADDRESS}}`** until confirmed — the only address seen in public
  sources is 7FF's listed office (915 S 500 E, Suite 100, American Fork, UT
  84003), but confirm with 7FF that this is the correct address to use for
  affiliate-program email, and under which legal entity name (`{{LEGAL_ENTITY}}`,
  see `01-company-and-offer.md`).
- Include a clear, working unsubscribe mechanism, and honor opt-outs
  promptly (industry practice: within 10 business days; sooner is better,
  and this agent should treat it as immediate).
- Don't use deceptive subject lines or a "From" name that misrepresents who
  is sending.

## A2P 10DLC note

- Business-to-consumer/partner SMS at any volume in the US generally needs
  the sending number and campaign registered under the A2P 10DLC framework
  (carrier-registered, proper use-case categorization) or messages risk
  being filtered/blocked. **UNVERIFIED — confirm with 7FF** whether the
  sending number/campaign this agent uses is already 10DLC-registered; if
  not, flag to a human before any SMS campaign goes live at volume.

## STOP / DNC handling

- Any reply containing STOP, UNSUBSCRIBE, CANCEL, QUIT, or clear "stop
  texting/emailing me" language must immediately halt further outreach on
  that channel to that person. Do not send a "just confirming" follow-up
  message beyond a single neutral acknowledgment (see T-response in
  `05-conversation-playbook.md`).
- Maintain the exclusion permanently unless the person explicitly opts back
  in (e.g., replies START).

## FTC affiliate disclosure basics

- If an affiliate is publicly promoting 7FF (social posts, a blog, a video)
  and stands to earn a commission, FTC guidance generally expects a clear,
  conspicuous disclosure of that financial relationship near the claim (not
  buried in a bio or hidden behind a "see more"). This agent can remind
  affiliates of this expectation in enablement content but should not draft
  specific disclosure language without a human/legal sign-off on the exact
  wording 7FF wants used.

## Data handling

- **Never** accept, store, or forward SSNs, full bank account/routing
  numbers, bank statements, or bureau/credit-report credentials in chat,
  notes, or this knowledge base. This mirrors the funding-director-orgo
  charter's hard rule ("no raw SSN, bank credential, bureau credential, or
  API secret in memory") and applies equally on the affiliate-relationship
  side — if an affiliate pastes a client's sensitive document/data into
  chat to "help," redirect them to the proper 7FF client intake channel
  instead of processing it here.
- Treat any client PII an affiliate shares (name, contact info, stated need)
  as sensitive; only pass it through the approved handoff path (see
  `05-conversation-playbook.md` — "I have a deal" flow), not into general
  notes or unrelated systems.

## Sources

- https://7figuresfunding.com/ (retrieved 2026-09-23, via firecrawl — "approval...not guaranteed" disclaimers, soft/hard-pull language)
- https://7figuresfunding.com/business-funding (retrieved 2026-09-23, via firecrawl)
- https://portal.7figurespartners.com/affiliates/signup.php (retrieved 2026-09-23, via firecrawl — earnings/business-opportunity/franchise/MLM disclaimer)
- /private/tmp/claude-501/-Users-home-Funding-Affiliate-Manager/51b442fe-9411-4270-aeda-6e934de05076/scratchpad/repos/funding-director-orgo/files/agent-knowledge/07.Funding Department Charter.md (hard rules on guessed data, guarantees, credentials)
- /private/tmp/claude-501/-Users-home-Funding-Affiliate-Manager/51b442fe-9411-4270-aeda-6e934de05076/scratchpad/repos/affiliate-manager-agent/skills/roles/affiliate-manager/SKILL.md ("never fabricate an approval," approval-boundary section)
- General regulatory background (TCPA quiet hours, CAN-SPAM, A2P 10DLC, FTC affiliate disclosure) — general industry/regulatory knowledge, not 7FF-specific; flagged as operational guidance, not legal advice
