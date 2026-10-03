# 05 — Conversation Playbook

**STATUS: every message below is a DRAFT.** The myconnectedmed prior
deployment's rule applies here by analogy: no external message goes out
until a human approves the exact template and the send path. Treat
everything in this file as draft copy for human review, not as pre-approved
send-ready content. See `06-compliance-guardrails.md` before any send.

## Voice

Warm, peer-to-peer, short. Write like a person who works there, texting a
partner they respect — not like an ad. Zero hype words ("amazing,"
"guaranteed," "don't miss out"). Never promise or imply an approval, a rate,
or an income outcome (see `06-compliance-guardrails.md`). One question or
one clear next step per message, not both.

## Personalization slots

`{{first_name}}` · `{{source}}` (see source tags in `04-affiliate-segments-and-sources.md`)
· `{{last_deal_date}}` · `{{niche}}` · `{{new_program}}` · `{{event_name}}`
· `{{event_date}}` · `{{AFFILIATE_LINK}}` · `{{sender_name}}` ·
`{{program_type}}` (7FF affiliate vs. MFM SaaS/Skool member — **never
cross-pitch**: don't sell the SaaS to a referral affiliate or vice versa
unless a human has confirmed the person is both).

## Required fields for every template (once approved)

Per template: Template ID + name · program type it applies to · approved
channel(s) + send hours (SMS/email only 8am–9pm **recipient's** local time,
per `06-compliance-guardrails.md`) · which personalization fields are
allowed · what may never be changed (offer, price, claims, timing,
commission, legal language) · stop conditions (opt-out, negative sentiment,
compliance concern, wrong person, human takeover requested).

---

### T1 — Bi-weekly touch (no ask, relationship maintenance)

**SMS (draft, count below):**
> Hey {{first_name}} — quick check-in from the 7FF team. Anything on an
> active deal I can help move, or questions on a client? Just reply here.

**Email:**
- Subject: "checking in"
- Body: "Hey {{first_name}}, — just doing a quick round of check-ins with our partners. Nothing urgent, just wanted to see how things are going and whether there's anything on your end — an active deal, a client question, anything — I can help with. Reply anytime. — {{sender_name}}"

---

### T2 — Monthly offer / program awareness

**SMS:**
> Hey {{first_name}}, heads up — {{new_program}} is live and could fit your
> {{niche}} clients. Want the quick rundown? Reply YES and I'll send it over.

**Email:**
- Subject: "new for your {{niche}} clients"
- Body: "Hey {{first_name}}, wanted to flag {{new_program}} in case it's useful for the clients you're already working with. No pressure — just reply and I'll send the details, or a link if you'd rather look it over yourself."

---

### T3 — 60–90 day personal check-in

**SMS:**
> Hey {{first_name}}, it's been a bit — how's it going on your end? Anything
> I can do to help — resources, new offers, programs? Just say the word.

**Email:**
- Subject: "how's it going?"
- Body: "Hey {{first_name}}, it's been a little while since we've talked, so I wanted to check in directly. How's it going on your side? Anything you need from us right now — resources, new offers, programs, or just a question you've been sitting on — let me know and I'll get you sorted."

---

### T4 — Dormant reactivation (has prior submission history, went quiet)

**SMS:**
> Hey {{first_name}}, haven't seen a submission since {{last_deal_date}} — no
> worries at all, just checking in. Anything change on your end, or can I
> help you get back going?

**Email:**
- Subject: "still here when you need us"
- Body: "Hey {{first_name}}, noticed it's been a while since your last submission ({{last_deal_date}}) — totally fine, just wanted to check in rather than assume anything. If something changed on your end, or if there's a blocker I can help clear, I'm here. And if now's just not the season for it, that's fine too — let me know either way."

---

### T5 — Dead-lead reactivation (signed up, never sent a deal, long-lapsed)

**For the 7FF reactivation, use the kickoff in `08-kickoff-framework.md` instead:** one text from the
partner's named manager with one hook from their record, then the reply sequence. The copy below is for
partners outside the kickoff (for example, someone who joined after it ran).

**SMS:**
> Hey {{first_name}}, {{sender_name}} here from 7 Figures Funding. You signed
> up a while back — still open to sending an occasional funding referral if
> a client needs it? Happy to help however works.

**Email:**
- Subject: "still open to this?"
- Body: "Hey {{first_name}}, this is {{sender_name}} from 7 Figures Funding. You joined our partner program a while back and I don't think we've connected since. No hard pitch here — just wanted to check whether it's still something you'd be open to if a client ever needs capital, and if so, I'm happy to get you set back up."

---

### T6 — New-offer announcement (formal launch, broader than T2)

**SMS:**
> Hey {{first_name}} — new offer just launched: {{new_program}}. Thought of
> your {{niche}} clients specifically. Want the details? Reply YES.

**Email:**
- Subject: "{{new_program}} is live"
- Body: "Hey {{first_name}}, wanted you to be one of the first to know — {{new_program}} just went live. Given the {{niche}} clients you work with, thought this could be a fit. Reply and I'll send the full rundown, or the link if you'd rather dig in yourself."

---

### T7 — Event invite

**SMS:**
> Hey {{first_name}}, we've got {{event_name}} on {{event_date}} — thought of
> you given your {{niche}} clients. Want the link to grab a spot?

**Email:**
- Subject: "{{event_name}} — {{event_date}}"
- Body: "Hey {{first_name}}, we've got {{event_name}} coming up on {{event_date}} and thought it'd be worth flagging for you given the clients you work with. Want the link to save a spot? No pressure either way."

---

### T8 — Growth-service offer (funnel page / lead reactivation / email / social / CRM help)

**SMS:**
> Hey {{first_name}}, quick one — want help setting up a funnel page,
> reactivating your own old leads, or getting email/social/CRM going for
> your funding referrals? Reply YES and I'll send details.

**Email:**
- Subject: "want a hand with any of this?"
- Body: "Hey {{first_name}}, a few partners have asked us for help lately with things like: a funnel/landing page for their funding referrals, reactivating their own old leads, running an email campaign, putting together social content, or getting a simple CRM in place. If any of that sounds useful to you, just say which one and I'll get you pointed in the right direction."

---

## Responses to common replies

### "I have a deal" / qualified referral
> Great — send them through {{AFFILIATE_LINK}}, or reply here with the
> business name and best contact and I'll make sure it's in the queue.
> Anything else you need from me on it?

Then hand off per the onboarding/activation skill: source, attribution key
(which `{{AFFILIATE_LINK}}` / affiliate), consent status, contact, known
need, owner, and next action — intact, to the Funding Operations side. This
agent does not underwrite or touch the deal itself.

### "Not right now" / "check back later"
> Totally understand — I'll check back down the road. If anything comes up
> sooner on your end, you know where to find me.

Log the stated reason if given; do not push further in the same
conversation.

### "What's the commission?" / "How much do I make?"
> Good question — I don't want to guess and give you the wrong number. Let
> me confirm the current terms and get back to you. (Route to a human;
> never state a percentage or dollar figure. See `03-affiliate-economics.md`.)

### "How do I submit a deal?"
> Easy — send your client through {{AFFILIATE_LINK}}. They do a quick
> soft-pull application, then a Funding Advisor calls them to walk through
> options. You can track status in your Partner CRM / Slack.

### Complaint
> I hear you, and I'm sorry that happened. Let me get this to the right
> person on our team right away so we can sort it out. Can you tell me a
> bit more about what happened?

Escalate to a human immediately; make no promise about outcome, refund, or
fix. Treat as a stop condition on any further scripted outreach until
resolved.

### Unsubscribe / STOP
Honor immediately and stop all further messaging on that channel — see
`06-compliance-guardrails.md`. Do not attempt to talk them out of it or ask
why (a single neutral acknowledgment is fine, e.g. "You're all set — no more
texts from us. Reach out anytime if that changes.").

## Sources

- /private/tmp/claude-501/-Users-home-Funding-Affiliate-Manager/51b442fe-9411-4270-aeda-6e934de05076/scratchpad/harvest/myconnectedmed/affiliate-manager/templates/approved-messages.md (required-fields structure; "empty by design" approval rule)
- /private/tmp/claude-501/-Users-home-Funding-Affiliate-Manager/51b442fe-9411-4270-aeda-6e934de05076/scratchpad/harvest/myconnectedmed/affiliate-manager/runbooks/partner-recovery.md (reactivation approach: identify the real blocker, don't assume)
- /private/tmp/claude-501/-Users-home-Funding-Affiliate-Manager/51b442fe-9411-4270-aeda-6e934de05076/scratchpad/repos/affiliate-manager-agent/grok-bot/skills/onboarding-activation-and-support.md (qualified-referral handoff fields)
- /private/tmp/claude-501/-Users-home-Funding-Affiliate-Manager/51b442fe-9411-4270-aeda-6e934de05076/scratchpad/harvest/scripts/mca_email_generator.py (tone/structure inspiration only — relevance line, one pain point, one question CTA; its guarantee-style "risk reversal" lines were deliberately NOT reused, since this agent may never imply a guarantee)
- The user's task brief (bi-weekly/monthly/60-90-day cadence, personalization slot names, and the exact 60–90-day check-in language, which is quoted directly from the brief)
