# 08 — The kickoff framework

The first text a quiet partner gets from their new partner manager. One text, written for that partner
from their own record, signed by a named person, reviewed by that person before it goes. Its only job
is to start a conversation. `fam kickoff draft` builds every kickoff from this framework
(`files/local-packages/fam/src/fam/drafting.py` holds the same rules as code).

## The four parts

Every kickoff has exactly these four parts, in this order, in two SMS segments or fewer
(the engine refuses a third).

1. **Greeting with their first name.** "Hey Dana," / "Hi Dana," / "Hey Dana!"
2. **Who is writing, and why now.** The manager's name, the company, and the change: "it's Justin with
   7 Figures Funding … I'm now your partner manager."
3. **One hook from their record.** The most reliable one available, in this order:

   | Hook | Used when | Example |
   |---|---|---|
   | Deals | they have sent deals | "You've sent us 7 deals since 2023" |
   | Tier | CEO, Executive or Apprentice | "You're one of our Executive partners" |
   | Tenure | we know the join year | "You've been a partner with us since 2023" |
   | Niche | we know what they do | "You've been with us as a business consultant" |
   | Source | we know where they came from | "You joined us through our Skool community" |
   | Fallback | the record is thin | "You joined our partner program a while back" |

4. **One question: the call ask.** "Open to a quick call this week?"

## The three openers

Three wordings rotate, assigned by contact id so a partner always gets the same one. The graph tracks
reply rate and calls per variant (`fam kickoff status`); keep the winners, retire the losers.

- **A** — Hey {first}, it's {sender} with 7 Figures Funding. {hook}, and I'm now your partner manager. I'd love
  to learn what you're working toward and how we can help you close more deals. Open to a quick call this week?
- **B** — Hi {first}, {sender} here from 7 Figures Funding. {hook}, and I just became your partner manager. I'm
  reaching out personally to learn your goals and see where we can help. Got time for a quick call this week?
- **C** — Hey {first}! It's {sender} at 7 Figures Funding. {hook}, and I'm your new partner manager. I want to
  get to know your business and how we can help you close more deals. Would a quick call this week work?

The model may reword a kickoff to fit the person. Its draft is checked against everything below and
replaced by the template when it fails.

## Never

- A funded amount, a rate, an approval, or any dollar figure.
- Guilt about being quiet ("haven't heard from you", "it's been a while", "went quiet").
- A past conversation that didn't happen.
- AI, an assistant, drafting, automation, or anything about who is typing.
- More than one question.

## After the kickoff

- **No answer in 5 days:** one nudge, then the partner moves to the normal cadence.
  "Hey {first}, {sender} again from 7 Figures Funding. No rush at all, I just didn't want my last text to
  get buried. Is there a better time to connect?"
- **They answer:** reply triage takes over (`skills/funding-affiliates/affiliate-reply-triage`). Each reply
  asks one thing: the next discovery question from their profile (what they're working toward, who their
  clients are, what would help), then the call ask after two replies, then the booking link when they say
  yes. A declined call is not asked again right away.
- **A call is booked:** post the pre-call brief (`fam_pre_call_brief`). After the call, its transcript fills
  the profile, the promises become tasks, and the revenue plan is written.
- **"Is this a bot?" / "Is this really Justin?":** no draft. The manager gets a task and replies personally.

## Waves

Kickoffs go out in waves (`config/kickoff.json`: wave size, batch cap, nudge delay), highest-value partners
first: past producers, then higher tiers, then the most recent engagement, then tenure. Each wave is a
review file listing every message in full; the manager approves the wave or holds some back
(`approve <id> except 4, 17`). Live texts are paced under the A2P throughput limit, inside the SMS window.

## Sources

Approved by Justin (Using AI to Scale), 2026-10-02: named sender, two-segment limit, the variant A wording.
Compliance rules: `06-compliance-guardrails.md`.
