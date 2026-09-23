# Call recap: 7FF partner program

**September 23, 2026** · Ty Talbot (7 Figures Funding), Francois Hewing, Justin Bellware

## What we covered

**The agent.** An AI affiliate manager that works inside GoHighLevel through a custom connector and is run from Slack. It reactivates a cold partner base, then keeps each relationship warm with personal touches: a check-in every two weeks and an offer once a month, written for each partner from what the CRM knows about them. It is built for GoHighLevel. Connectors for other systems can be added, and where an API falls short the agent can work in the web app from its own cloud computer.

**7FF's partner base.** More than 13,000 partners, most in Zoho. A few thousand have payroll integrations that can't move for security reasons, and newer work is in GoHighLevel. About 50 partners are active and engaged, which leaves roughly 12,950 to bring back.

**The simulation.** A 30-day run of the agent on 253 synthetic affiliates. The figures quoted on the call are corrected here: 115 personal check-ins, 59 replies, 12 deals submitted, and 13 affiliates producing on day 30 against 1 with no outreach. The 22% reply rate is an input assumption for personal messages (7% for bulk), not a result.

**How it's paid for.** Ty prefers usage plus performance to a monthly fee, since members balk at up-front monthly pricing. 7FF covers the AI and usage costs. Our share of deals from re-engaged partners is set by the partner's tier:

| Partner tier | Share |
|---|---|
| CEO | 5% |
| Executive | 10% |
| Apprentice | 10% |
| Free | 15% |

Re-engaged partners may also buy the Funding Machine, which is upside on top of their deals.

**AI costs.** Ty asked for a projection so the program can't run up an unexpected AI bill. The agent runs on low-cost models (GPT-6 Luna Pro through OpenRouter, GLM 5.3 Flash as backup) with Jev classifying. The projection is in the demo pack: about $10 of AI for the whole reactivation, about $36 a month after, and a hard cap of $250 a month. Texting through HighLevel is the larger cost.

**Data.** 7FF will send its NDA. Partner data must never be pushed out or resold.

**The agent's name.** Ty suggested using Morgan, the name of 7FF's existing AI, so partners aren't confused. To confirm.

**Case study and launch.** 7FF goes first as the case study, then one or two more betas, then a full launch at Funding Machine Live. Ty invited Justin to present there, possibly co-demoing with Francois.

**Development AI spend.** Justin offered to review 7FF's AI spend on development tools with Brock, for example routing work that doesn't need a reasoning model to cheaper models such as Jev.

## Agreed

- Usage plus performance, with no monthly fee.
- Shares by partner tier: CEO 5%, Executive 10%, Apprentice 10%, Free 15%.
- 7FF's NDA is signed before any partner data moves.
- 7FF is the first case study.

## Open questions

- What the tier percentages are calculated on, and how long after a partner's first reply their deals count.
- Whether a re-engaged partner's Funding Machine purchase counts toward the share.
- Which partners can move to GoHighLevel, and which stay in Zoho.
- Whether SMS consent is on file for the partner list, and on which number.
- Server and cloud-computer costs, and whether a dedicated relationship manager is included.
- The agent's name.

## Next steps

1. Ty sends 7FF's NDA, and it is signed before any partner data moves.
2. Justin sends the letter of intent, the proposal and the cost projection.
3. Technical session with Brock: read access to the Zoho partner data, which partners can move, the GoHighLevel sub-account, the texting number and SMS consent.
4. Ty confirms the agent's name: Morgan, or a new one.
5. Justin builds the Zoho import, the Jev layer and the message worker, and re-runs the simulation on the production models.
6. Pilot wave of 250 partners, reviewed together against the agreed gates before the next wave opens.
7. Justin and Brock review 7FF's development AI spend.
8. Once the pilot has results, plan the case study and the Funding Machine Live co-demo with Francois.
