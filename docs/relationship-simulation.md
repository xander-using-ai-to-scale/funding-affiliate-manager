# Relationship simulation: 250 quiet partners, 30 days

Synthetic partners imported from Zoho-style records, then run day by day through the real engine from 2026-10-05: kickoff waves of 40, one nudge after 5 days, replies, calls, revenue plans. Every message was approved by a (simulated) manager. No one was contacted.

## The graph

| | Day 0 (records only) | Day 30 |
|---|---:|---:|
| Average profile completeness, all partners | 25.0% | 28.7% |
| Average completeness, partners who wrote back | n/a | 44.2% |
| Facts in the graph | 624 | 761 |
| Links to hub notes (tier, niche, manager, source, product) | 1,040 | 1,060 |
| Calls on file | 0 | 8 |
| Revenue plans | 0 | 8 |

Facts by where they came from: call 56, text reply 81, Zoho 500, Zoho notes 124

## What happened

| | Count |
|---|---:|
| Kickoff texts sent | 250 |
| Kickoffs the reviewer held back | 1 |
| Nudges | 205 |
| Texts from partners | 108 |
| Conversations triaged (several texts in a row count once) | 100 |
| Our replies sent | 85 |
| Discovery questions asked | 42 |
| Call asks | 20 |
| Calls booked | 8 |
| Calls held and ingested | 8 |
|   by phone (GoHighLevel transcript) | 4 |
|   by video (recorder export in the call inbox) | 4 |
| Commitments pulled from calls | 12 |
| Revenue plans written | 8 |
| Deals submitted | 8 |
| Opt-outs honored | 10 |
| "Is this a bot?" handed to the manager | 5 |
| Drafts the engine refused | 0 |

## Kickoff variants

| Variant | Sent | Replied | Calls | Reply rate |
|---|---:|---:|---:|---:|
| A | 86 | 20 | 1 | 23% |
| B | 85 | 16 | 3 | 19% |
| C | 79 | 22 | 4 | 28% |

## How much of what partners said reached their profile

Keyword rules only (the live agent extracts with the model): **86%** of stated facts captured, **86%** captured correctly.

| Slot | Said | Captured | Correct |
|---|---:|---:|---:|
| best_time | 8 | 8 | 8 |
| blockers | 8 | 8 | 8 |
| channel | 3 | 3 | 3 |
| client_types | 24 | 16 | 16 |
| deal_size | 15 | 15 | 15 |
| deal_types | 13 | 13 | 13 |
| goals | 22 | 17 | 17 |
| needs | 8 | 6 | 6 |
| regions | 9 | 9 | 9 |

## Sample kickoffs

- **A/deals** (2 segments): Hey Tanya, it's Justin with 7 Figures Funding. You've sent us 11 deals since 2024, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week?
- **A/tenure** (2 segments): Hey Victor, it's Justin with 7 Figures Funding. You've been a partner with us since 2025, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week?
- **A/tier** (2 segments): Hey Jamal, it's Justin with 7 Figures Funding. You're one of our CEO partners, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week?
- **B/deals** (2 segments): Hi Tiffany, Justin here from 7 Figures Funding. You've sent us 11 deals since 2022, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week?
- **B/tenure** (2 segments): Hi Jenna, Justin here from 7 Figures Funding. You've been a partner with us since 2025, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week?
- **B/tier** (2 segments): Hi Nadia, Justin here from 7 Figures Funding. You're one of our Executive partners, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week?
- **C/deals** (2 segments): Hey Keisha! It's Justin at 7 Figures Funding. You've sent us 11 deals since 2023, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work?
- **C/tenure** (2 segments): Hey Andre! It's Justin at 7 Figures Funding. You've been a partner with us since 2025, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work?
- **C/tier** (2 segments): Hey Priya! It's Justin at 7 Figures Funding. You're one of our Executive partners, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work?

Nudge: Hey Tiffany, Justin again from 7 Figures Funding. No rush at all, I just didn't want my last text to get buried. Is there a better time to connect?

## Sample partner

Sofia Long (engaged). Notes before and after are in partners/before.md and partners/after.md.

- 2026-10-07 **them:** Hi Justin, thanks for reaching out. They always seem to need new equipment. Email me, I'm in meetings all day.
  - triage: general_reply; facts: channel
  - **us** (book): Perfect. Grab any time that works for you here: https://example.com/book/justin

## "Is this a bot?"

- They wrote: Am I talking to a bot?
- Agent: last_reply_date=today; lifecycle → aff:reactivated; kickoff conversation started; personal reply task for the manager. Draft: none (manager replies)
- Manager replied personally on 2026-10-06

## Assumptions

- personas (share of partners): engaged 6%, warm 8%, nudge 5%, later 4%, has_deal 2%, silent 70%, stop 3%, identity 2%
- replies: written from each partner's hidden truth; some phrasings are ones the keyword rules miss
- drafting: framework templates and keyword rules (no model); the live agent drafts with the model
- manager: approves every batch (simulated); holds one kickoff back in wave 1 to edit it
- calls: every booked call happens 1-3 days later; odd calls by phone, even calls by video recorder
- variants: a synthetic partner's reply does not depend on the kickoff wording, so the variant table shows the tracking works, not which copy wins; real replies decide that
