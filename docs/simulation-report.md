# Funding Affiliate Manager — 30-day simulation

Synthetic program of **253 affiliates** run day-by-day through the real engine (sweep → approvals → execution → reply triage → deals) against a mock CRM. No one was contacted.

## What the agent did

| Metric | Simulation | Projected at 10,000 affiliates |
|---|---:|---:|
| Personal check-ins / follow-ups sent | 115 | 4,545 |
| Cadence workflow enrollments (bi-weekly touch, monthly offer, reactivation) | 449 | 17,747 |
| Newsletter deliveries (every 2 weeks) | 759 | 30,000 |
| Event / training invites | 390 | 15,415 |
| “Check back with me” tasks worked on their due day | 24 | 949 |
| Replies triaged | 59 | 2,332 |
| Deals submitted after outreach | 12 | 474 |

## Reply triage

| Intent | Count |
|---|---:|
| check_back_later | 16 |
| has_deal | 16 |
| wants_service | 13 |
| event_interest | 5 |
| general_reply | 5 |
| question | 2 |
| commission_question | 1 |
| unsubscribe | 1 |

## Lifecycle: with the agent vs. without

Time passes either way. *Without the agent* is the same program aged 30 days with no outreach, replies, or deals.

| Lifecycle | Day 0 | End — without agent | End — with agent |
|---|---:|---:|---:|
| aff:active | 93 | 47 | 70 |
| aff:applied | 12 | 12 | 0 |
| aff:dead | 27 | 30 | 29 |
| aff:dormant | 20 | 39 | 26 |
| aff:producing | 45 | 1 | 13 |
| aff:quiet | 56 | 124 | 104 |
| aff:reactivated | 0 | 0 | 11 |

Assumptions: reply rate personal = 0.22; reply rate bulk = 0.07; deal follow through = every 'has a deal' reply is submitted 1–3 days later; manager = approves each daily batch (simulated as sim-manager)

## Sample approval card

```
*Approval needed* — 22 daily personal touches (3 real, 19 simulated)
action `act_9f4c6b9bf753` · digest `a016ac6194410043` · demo mode: True
1. Priya Brooks (email, simulated) — _Circling back, Priya_: Hi Priya, You asked me to circle back after tax season, so here I am. How are things looking now? If any of your credit repair pro clients need working capital, I can walk you thro
2. Priya Russell (email, simulated) — _Priya, quick check-in_: Hi Priya, It's been a little while since we connected and I wanted to check in personally. How's business going on your side? Is there anything I can help with — resources for your
3. Ethan Bell (sms, simulated): Hey Ethan, it's been a minute! How's business going? Anything I can help with — resources, new programs, or help working your leads? Reply STOP to opt out.
4. Derek Powell (email, simulated) — _Derek, quick check-in_: Hi Derek, It's been a little while since we connected and I wanted to check in personally. How's business going on your side? Is there anything I can help with — resources for your
5. Heather Powell (sms, simulated): Hey Heather, it's been a minute! How's business going? Anything I can help with — resources, new programs, or help working your leads? Reply STOP to opt out.
6. Victor Diaz (sms, simulated): Hey Victor, it's been a minute! How's business going? Anything I can help with — resources, new programs, or help working your leads? Reply STOP to opt out.
7. Marcus Sanders (email, simulated) — _Marcus, quick check-in_: Hi Marcus, It's been a little while since we connected and I wanted to check in personally. How's business going on your side? Is there anything I can help with — resources for you
8. Andre Reyes (email, simulated) — _Andre, quick check-in_: Hi Andre, It's been a little while since we connected and I wanted to check in personally. How's business going on your side? Is there anything I can help with — resources for your
Reply *approve act_9f4c6b9bf753* to send, or tell me what to change.
```

## Sample drafts

- **scheduled_followup · email** — Hi Priya,

You asked me to circle back after tax season, so here I am. How are things looking now?

If any of your credit repair pro clients need working capital, I can walk you through the fastest way to send the file over. And if it's still not the right time, just tell me when and I'll put it on 
- **personal_checkin · email** — Hi Priya,

It's been a little while since we connected and I wanted to check in personally. How's business going on your side?

Is there anything I can help with — resources for your CPA clients, our newest funding programs, or even help reactivating your own leads?

Just hit reply — I read every on
- **personal_checkin · sms** — Hey Ethan, it's been a minute! How's business going? Anything I can help with — resources, new programs, or help working your leads?
- **personal_checkin · email** — Hi Derek,

It's been a little while since we connected and I wanted to check in personally. How's business going on your side?

Is there anything I can help with — resources for your bookkeeper clients, our newest funding programs, or even help reactivating your own leads?

Just hit reply — I read e
- **personal_checkin · sms** — Hey Heather, it's been a minute! How's business going? Anything I can help with — resources, new programs, or help working your leads?
- **personal_checkin · sms** — Hey Victor, it's been a minute! How's business going? Anything I can help with — resources, new programs, or help working your leads?

## Sample reply triage

- “I have about 2,000 old leads on my list I never worked. Can you help reactivate them?” → **wants_service** → last_reply_date=today; lifecycle → aff:reactivated; growth service queued: reactivation · alert: Marcus Sanders wants help with lead reactivation.
- “Slammed with tax season right now, check back with me in a few weeks.” → **check_back_later** → last_reply_date=today; lifecycle → aff:reactivated; follow-up task 2026-09-15
- “Yes — send me the training invite.” → **event_interest** → last_reply_date=today; lifecycle → aff:reactivated; want:event
- “Thanks, appreciate you checking in!” → **general_reply** → last_reply_date=today; lifecycle → aff:reactivated
- “I actually have a client who needs about $150k for equipment — can I send you the file?” → **has_deal** → last_reply_date=today; lifecycle → aff:reactivated; deal:incoming + same-day call task · alert: 🔥 Andre Myers has a deal. Same-day call task created.
- “I actually have a client who needs about $150k for equipment — can I send you the file?” → **has_deal** → last_reply_date=today; lifecycle → aff:reactivated; deal:incoming + same-day call task · alert: 🔥 Ethan Perry has a deal. Same-day call task created.
- “I actually have a client who needs about $150k for equipment — can I send you the file?” → **has_deal** → last_reply_date=today; deal:incoming + same-day call task · alert: 🔥 Tiffany Jenkins has a deal. Same-day call task created.
- “Got a merchant for you, restaurant owner doing around 80k a month. How do I submit?” → **has_deal** → last_reply_date=today; deal:incoming + same-day call task · alert: 🔥 Camila Brooks has a deal. Same-day call task created.

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
    "aff:active": 70,
    "aff:dead": 29,
    "aff:dormant": 26,
    "aff:producing": 13,
    "aff:quiet": 104,
    "aff:reactivated": 11
  },
  "submitted_deal_last_30d": 13,
  "replied_last_30d": 53,
  "touched_last_30d": 253,
  "reply_rate_30d": 0.209,
  "active_rate": 0.372,
  "silent_90_plus": 55,
  "dnc": 1,
  "open_growth_services": 17
}
```
