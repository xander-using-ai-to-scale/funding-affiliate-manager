# Funding Affiliate Manager — 30-day simulation

Synthetic program of **253 affiliates** run day-by-day through the real engine (sweep → approvals → execution → reply triage → deals) against a mock CRM. No one was contacted.

## What the agent did

| Metric | Simulation | Projected at 10,000 affiliates |
|---|---:|---:|
| Personal check-ins / follow-ups sent | 152 | 6,008 |
| Cadence workflow enrollments (bi-weekly touch, monthly offer, reactivation) | 437 | 17,273 |
| Newsletter deliveries (every 2 weeks) | 759 | 30,000 |
| Event / training invites | 391 | 15,455 |
| “Check back with me” tasks worked on their due day | 57 | 2,253 |
| Replies triaged | 67 | 2,648 |
| Deals submitted after outreach | 17 | 672 |

## Reply triage

| Intent | Count |
|---|---:|
| has_deal | 24 |
| wants_service | 15 |
| check_back_later | 13 |
| event_interest | 9 |
| general_reply | 5 |
| unsubscribe | 1 |

## Lifecycle: with the agent vs. without

Time passes either way. *Without the agent* is the same program aged 30 days with no outreach, replies, or deals.

| Lifecycle | Day 0 | End — without agent | End — with agent |
|---|---:|---:|---:|
| aff:active | 93 | 47 | 72 |
| aff:applied | 12 | 12 | 0 |
| aff:dead | 27 | 30 | 29 |
| aff:dormant | 20 | 39 | 25 |
| aff:producing | 45 | 1 | 16 |
| aff:quiet | 56 | 124 | 98 |
| aff:reactivated | 0 | 0 | 13 |

Assumptions: reply rate personal = 0.22; reply rate bulk = 0.07; deal follow through = every 'has a deal' reply is submitted 1–3 days later; manager = approves each daily batch (simulated as sim-manager)

## Sample approval card

```
*Approval needed* — 22 daily personal touches (3 real, 19 simulated)
action `act_3e08b9735d1c` · digest `bac718fb40bac4f3` · demo mode: True
1. Priya Brooks (email, simulated) — _Circling back, Priya_: Hi Priya, You asked me to circle back after tax season, so here I am. How are things looking now? If any of your credit repair pro clients need working capital, I can walk you thro
2. Derek Powell (email, simulated) — _Derek, quick check-in_: Hi Derek, It's been a little while since we connected and I wanted to check in personally. How's business going on your side? Is there anything I can help with — resources for your
3. Priya Russell (email, simulated) — _Priya, quick check-in_: Hi Priya, It's been a little while since we connected and I wanted to check in personally. How's business going on your side? Is there anything I can help with — resources for your
4. Ethan Bell (sms, simulated): Hey Ethan, it's been a minute! How's business going? Anything I can help with — resources, new programs, or help working your leads? Reply STOP to opt out.
5. Heather Powell (sms, simulated): Hey Heather, it's been a minute! How's business going? Anything I can help with — resources, new programs, or help working your leads? Reply STOP to opt out.
6. Victor Diaz (sms, simulated): Hey Victor, it's been a minute! How's business going? Anything I can help with — resources, new programs, or help working your leads? Reply STOP to opt out.
7. Marcus Sanders (email, simulated) — _Marcus, quick check-in_: Hi Marcus, It's been a little while since we connected and I wanted to check in personally. How's business going on your side? Is there anything I can help with — resources for you
8. Andre Reyes (email, simulated) — _Andre, quick check-in_: Hi Andre, It's been a little while since we connected and I wanted to check in personally. How's business going on your side? Is there anything I can help with — resources for your
Reply *approve act_3e08b9735d1c* to send, or tell me what to change.
```

## Sample drafts

- **scheduled_followup · email** — Hi Priya,

You asked me to circle back after tax season, so here I am. How are things looking now?

If any of your credit repair pro clients need working capital, I can walk you through the fastest way to send the file over. And if it's still not the right time, just tell me when and I'll put it on 
- **personal_checkin · email** — Hi Derek,

It's been a little while since we connected and I wanted to check in personally. How's business going on your side?

Is there anything I can help with — resources for your bookkeeper clients, our newest funding programs, or even help reactivating your own leads?

Just hit reply — I read e
- **personal_checkin · email** — Hi Priya,

It's been a little while since we connected and I wanted to check in personally. How's business going on your side?

Is there anything I can help with — resources for your CPA clients, our newest funding programs, or even help reactivating your own leads?

Just hit reply — I read every on
- **personal_checkin · sms** — Hey Ethan, it's been a minute! How's business going? Anything I can help with — resources, new programs, or help working your leads?
- **personal_checkin · sms** — Hey Heather, it's been a minute! How's business going? Anything I can help with — resources, new programs, or help working your leads?
- **personal_checkin · sms** — Hey Victor, it's been a minute! How's business going? Anything I can help with — resources, new programs, or help working your leads?

## Sample reply triage

- “I have about 2,000 old leads on my list I never worked. Can you help reactivate them?” → **wants_service** → last_reply_date=today; lifecycle → aff:reactivated; growth service queued: reactivation · alert: Marcus Sanders wants help with reactivation.
- “Slammed with tax season right now, check back with me in a few weeks.” → **check_back_later** → last_reply_date=today; lifecycle → aff:reactivated; follow-up task 2026-09-15
- “Yes — send me the training invite.” → **event_interest** → last_reply_date=today; lifecycle → aff:reactivated; want:event
- “Thanks, appreciate you checking in!” → **general_reply** → last_reply_date=today; lifecycle → aff:reactivated
- “I actually have a client who needs about $150k for equipment — can I send you the file?” → **has_deal** → last_reply_date=today; lifecycle → aff:reactivated; deal:incoming + same-day call task · alert: 🔥 Ethan Foster has a deal. Same-day call task created.
- “I actually have a client who needs about $150k for equipment — can I send you the file?” → **has_deal** → last_reply_date=today; lifecycle → aff:reactivated; deal:incoming + same-day call task · alert: 🔥 Camila Powell has a deal. Same-day call task created.
- “I actually have a client who needs about $150k for equipment — can I send you the file?” → **has_deal** → last_reply_date=today; deal:incoming + same-day call task · alert: 🔥 Carlos Perry has a deal. Same-day call task created.
- “Got a merchant for you, restaurant owner doing around 80k a month. How do I submit?” → **has_deal** → last_reply_date=today; lifecycle → aff:reactivated; deal:incoming + same-day call task · alert: 🔥 Lena Diaz has a deal. Same-day call task created.

## End-of-run scorecard

```json
{
  "date": "2026-10-01",
  "affiliates": 253,
  "by_source": {
    "skool": 85,
    "referral": 39,
    "linkedin": 31,
    "webinar": 29,
    "website": 27,
    "facebook": 20,
    "legacy-import": 11,
    "event": 11
  },
  "cohorts": {
    "aff:active": 72,
    "aff:dead": 29,
    "aff:dormant": 25,
    "aff:producing": 16,
    "aff:quiet": 98,
    "aff:reactivated": 13
  },
  "submitted_deal_last_30d": 16,
  "replied_last_30d": 57,
  "touched_last_30d": 253,
  "reply_rate_30d": 0.225,
  "active_rate": 0.399,
  "silent_90_plus": 54,
  "dnc": 1,
  "open_growth_services": 21
}
```
