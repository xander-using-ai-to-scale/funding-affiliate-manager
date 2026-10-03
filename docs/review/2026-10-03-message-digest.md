# Message digest: relationship simulation, framework templates (TemplateDrafter), seed 21

Every outbound text the simulation sent, from the mock CRM. Totals: {'kickoff': 250, 'nudge': 205, 'reply': 85, 'manager (scripted in the sim, sent outside approvals)': 5}. Inbound partner texts are synthetic personas (relsim.py), not real people.

## Kickoff samples by opener and hook (as sent)

- **A/deals** (variant A, hook deals, 2 segments): Hey Tanya, it's Justin with 7 Figures Funding. You've sent us 11 deals since 2024, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week?
- **A/tenure** (variant A, hook tenure, 2 segments): Hey Victor, it's Justin with 7 Figures Funding. You've been a partner with us since 2025, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week?
- **A/tier** (variant A, hook tier, 2 segments): Hey Jamal, it's Justin with 7 Figures Funding. You're one of our CEO partners, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week?
- **B/deals** (variant B, hook deals, 2 segments): Hi Tiffany, Justin here from 7 Figures Funding. You've sent us 11 deals since 2022, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week?
- **B/tenure** (variant B, hook tenure, 2 segments): Hi Jenna, Justin here from 7 Figures Funding. You've been a partner with us since 2025, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week?
- **B/tier** (variant B, hook tier, 2 segments): Hi Nadia, Justin here from 7 Figures Funding. You're one of our Executive partners, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week?
- **C/deals** (variant C, hook deals, 2 segments): Hey Keisha! It's Justin at 7 Figures Funding. You've sent us 11 deals since 2023, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work?
- **C/tenure** (variant C, hook tenure, 2 segments): Hey Andre! It's Justin at 7 Figures Funding. You've been a partner with us since 2025, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work?
- **C/tier** (variant C, hook tier, 2 segments): Hey Priya! It's Justin at 7 Figures Funding. You're one of our Executive partners, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work?

## Nudge (2 segments)

Hey Tiffany, Justin again from 7 Figures Funding. No rush at all, I just didn't want my last text to get buried. Is there a better time to connect?

## Distinct kickoff bodies (first names replaced by {first}), with how many times each was sent

- ×19 (2 seg): Hey {first}, it's Justin with 7 Figures Funding. You're one of our Apprentice partners, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- ×17 (2 seg): Hey {first}! It's Justin at 7 Figures Funding. You're one of our Apprentice partners, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.
- ×16 (2 seg): Hi {first}, Justin here from 7 Figures Funding. You're one of our Apprentice partners, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.
- ×13 (2 seg): Hey {first}! It's Justin at 7 Figures Funding. You've sent us {n} deals since 2024, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.
- ×11 (2 seg): Hi {first}, Justin here from 7 Figures Funding. You've sent us {n} deals since 2022, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.
- ×11 (2 seg): Hi {first}, Justin here from 7 Figures Funding. You've been a partner with us since 2025, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.
- ×11 (2 seg): Hey {first}! It's Justin at 7 Figures Funding. You've been a partner with us since 2024, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.
- ×10 (2 seg): Hey {first}, it's Justin with 7 Figures Funding. You've sent us {n} deals since 2022, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- ×10 (2 seg): Hey {first}, it's Justin with 7 Figures Funding. You've been a partner with us since 2023, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- ×9 (2 seg): Hey {first}, it's Justin with 7 Figures Funding. You've sent us {n} deals since 2023, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- ×9 (2 seg): Hey {first}! It's Justin at 7 Figures Funding. You've sent us {n} deals since 2023, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.
- ×8 (2 seg): Hey {first}, it's Justin with 7 Figures Funding. You've been a partner with us since 2024, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- ×7 (2 seg): Hi {first}, Justin here from 7 Figures Funding. You've sent us {n} deals since 2025, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.
- ×7 (2 seg): Hi {first}, Justin here from 7 Figures Funding. You've sent us {n} deals since 2024, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.
- ×7 (2 seg): Hey {first}, it's Justin with 7 Figures Funding. You're one of our Executive partners, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- ×7 (2 seg): Hi {first}, Justin here from 7 Figures Funding. You've been a partner with us since 2022, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.
- ×7 (2 seg): Hi {first}, Justin here from 7 Figures Funding. You've been a partner with us since 2024, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.
- ×7 (2 seg): Hi {first}, Justin here from 7 Figures Funding. You've been a partner with us since 2023, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.
- ×6 (2 seg): Hi {first}, Justin here from 7 Figures Funding. You've sent us {n} deals since 2023, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.
- ×6 (2 seg): Hey {first}! It's Justin at 7 Figures Funding. You're one of our Executive partners, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.
- ×6 (2 seg): Hey {first}! It's Justin at 7 Figures Funding. You've been a partner with us since 2025, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.
- ×6 (2 seg): Hey {first}, it's Justin with 7 Figures Funding. You've been a partner with us since 2025, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- ×6 (2 seg): Hey {first}! It's Justin at 7 Figures Funding. You've been a partner with us since 2023, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.
- ×6 (2 seg): Hey {first}, it's Justin with 7 Figures Funding. You've been a partner with us since 2022, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- ×5 (2 seg): Hey {first}, it's Justin with 7 Figures Funding. You've sent us {n} deals since 2024, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- ×5 (2 seg): Hi {first}, Justin here from 7 Figures Funding. You're one of our Executive partners, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.
- ×4 (2 seg): Hey {first}! It's Justin at 7 Figures Funding. You've sent us {n} deals since 2025, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.
- ×4 (2 seg): Hey {first}! It's Justin at 7 Figures Funding. You've been a partner with us since 2022, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.
- ×3 (2 seg): Hey {first}, it's Justin with 7 Figures Funding. You're one of our CEO partners, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- ×2 (2 seg): Hey {first}, it's Justin with 7 Figures Funding. You've sent us {n} deals since 2025, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- ×2 (2 seg): Hey {first}! It's Justin at 7 Figures Funding. You've sent us {n} deals since 2022, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.
- ×1 (2 seg): Hey {first}! It's Justin at 7 Figures Funding. You've sent us {n} deals since 2021, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.
- ×1 (2 seg): Hi {first}, Justin here from 7 Figures Funding. You've sent us {n} deals since 2021, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.
- ×1 (2 seg): Hey {first}, it's Justin with 7 Figures Funding. You've been a partner with us since 2021, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.

## Distinct nudge bodies (first names replaced by {first}), with how many times each was sent

- ×205 (2 seg): Hey {first}, Justin again from 7 Figures Funding. No rush at all, I just didn't want my last text to get buried. Is there a better time to connect? Reply STOP to opt out.

## Distinct reply bodies (first names replaced by {first}), with how many times each was sent

- ×36 (1 seg): Great to hear from you, {first}! What are you working toward this year?
- ×18 (1 seg): Really appreciate you sharing that, {first}. Would a quick 15-minute call this week be easier to talk it through?
- ×8 (1 seg): Perfect. Grab any time that works for you here: https://example.com/book/justin
- ×5 (1 seg): Totally understand, {first}. I'll reach back out then. Good luck in the meantime!
- ×4 (1 seg): Great to hear from you, {first}! What kind of clients are you working with most these days?
- ×4 (1 seg): Will do, {first}! I'll send the link over so you can grab a spot.
- ×4 (1 seg): That's great, {first}. I'll give you a call today to get the details, or send the file here whenever you're ready.
- ×2 (1 seg): Good question, {first}. Let me get you the exact answer today.
- ×2 (1 seg): Great to hear from you, {first}! What would make this partnership worth your time?
- ×2 (1 seg): Happy to help with that, {first}. Would a quick 15-minute call this week be easier to talk it through?

## Distinct manager (scripted in the sim, sent outside approvals) bodies (first names replaced by {first}), with how many times each was sent

- ×5 (1 seg): Hey {first}, Justin here, I read every one of these myself. Happy to jump on a quick call anytime if that's easier.

## Full threads (14 partners)

### Grant (c_6550547f6965)

- 2026-10-05 **US:** Hey Grant! It's Justin at 7 Figures Funding. You've sent us 11 deals since 2024, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.
- 2026-10-10 **US:** Hey Grant, Justin again from 7 Figures Funding. No rush at all, I just didn't want my last text to get buried. Is there a better time to connect? Reply STOP to opt out.
- 2026-10-11 **PARTNER:** Sorry, crazy week! Mainly software startups.
- 2026-10-11 **US:** Great to hear from you, Grant! What are you working toward this year?
- 2026-10-12 **PARTNER:** My goal this year is to close two deals a month by the end of the year.
- 2026-10-12 **US:** Really appreciate you sharing that, Grant. Would a quick 15-minute call this week be easier to talk it through?
- 2026-10-13 **PARTNER:** Texting is easier for me right now, let's keep it here for now.
- 2026-10-13 **US:** Great to hear from you, Grant! What kind of clients are you working with most these days?

### Priya (c_cb700c871373)

- 2026-10-05 **US:** Hi Priya, Justin here from 7 Figures Funding. You've sent us 4 deals since 2022, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.
- 2026-10-08 **PARTNER:** Hey, nice to meet you Justin. These days it's a lot of farm operations.
- 2026-10-08 **US:** Great to hear from you, Priya! What are you working toward this year?
- 2026-10-09 **PARTNER:** I want to close two deals a month by the end of the year. Anywhere from $12k to $50k, usually about $25k.
- 2026-10-09 **US:** Really appreciate you sharing that, Priya. Would a quick 15-minute call this week be easier to talk it through?
- 2026-10-10 **PARTNER:** Texting is easier for me right now, let's keep it here for now.
- 2026-10-10 **US:** Great to hear from you, Priya! What kind of clients are you working with most these days?

### Victor (c_eb43581b9e7e)

- 2026-10-06 **US:** Hey Victor, it's Justin with 7 Figures Funding. You've sent us 1 deal since 2023, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- 2026-10-06 **PARTNER:** Hi Justin, thanks for reaching out. Mainly manufacturers. Usually it's new equipment.
- 2026-10-06 **US:** Great to hear from you, Victor! What are you working toward this year?
- 2026-10-07 **PARTNER:** Trying to get back to sending a deal a month, that's the plan.
- 2026-10-07 **PARTNER:** Deals are typically $150k or so.
- 2026-10-07 **US:** Will do, Victor! I'll send the link over so you can grab a spot.

### Trevor (c_730ae20448e8)

- 2026-10-07 **US:** Hey Trevor! It's Justin at 7 Figures Funding. You're one of our Executive partners, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.
- 2026-10-12 **US:** Hey Trevor, Justin again from 7 Figures Funding. No rush at all, I just didn't want my last text to get buried. Is there a better time to connect? Reply STOP to opt out.
- 2026-10-12 **PARTNER:** Not a good time right now, maybe next quarter.
- 2026-10-12 **US:** Great to hear from you, Trevor! What are you working toward this year?
- 2026-10-13 **PARTNER:** I want to close two deals a month by the end of the year.
- 2026-10-13 **US:** Really appreciate you sharing that, Trevor. Would a quick 15-minute call this week be easier to talk it through?
- 2026-10-14 **PARTNER:** Sounds good, Wednesday afternoon?
- 2026-10-14 **US:** Good question, Trevor. Let me get you the exact answer today.

### Monique (c_20ac2f22f9ee)

- 2026-10-07 **US:** Hey Monique, it's Justin with 7 Figures Funding. You're one of our Executive partners, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- 2026-10-08 **PARTNER:** Hey Justin! Good to hear from you. Text is best for me. Usually it's money to open a second location.
- 2026-10-08 **US:** Great to hear from you, Monique! What are you working toward this year?
- 2026-10-09 **PARTNER:** I want to build a second income stream from referrals.
- 2026-10-09 **US:** Really appreciate you sharing that, Monique. Would a quick 15-minute call this week be easier to talk it through?
- 2026-10-10 **PARTNER:** Sounds good, Wednesday afternoon?
- 2026-10-10 **US:** Good question, Monique. Let me get you the exact answer today.

### Grant (c_763adfab6f57)

- 2026-10-07 **US:** Hey Grant, it's Justin with 7 Figures Funding. You're one of our Apprentice partners, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- 2026-10-07 **PARTNER:** Hi Justin, thanks for reaching out. I mostly work with auto repair shops these days. Mostly working capital to cover payroll, sometimes money to open a second location.
- 2026-10-07 **US:** Great to hear from you, Grant! What are you working toward this year?
- 2026-10-08 **PARTNER:** Honestly I'd love to build a second income stream from referrals.
- 2026-10-08 **US:** Really appreciate you sharing that, Grant. Would a quick 15-minute call this week be easier to talk it through?
- 2026-10-09 **PARTNER:** Sure, Thursday morning works.
- 2026-10-09 **US:** Perfect. Grab any time that works for you here: https://example.com/book/justin

### Brandon (c_5422856327ed)

- 2026-10-08 **US:** Hi Brandon, Justin here from 7 Figures Funding. You're one of our Apprentice partners, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.
- 2026-10-09 **PARTNER:** Hey Justin! Good to hear from you. Most of them are in North Carolina and Ohio. They always seem to need cash flow in the slow season.
- 2026-10-09 **US:** Great to hear from you, Brandon! What are you working toward this year?
- 2026-10-10 **PARTNER:** Honestly I'd love to grow my referral income this year.
- 2026-10-10 **US:** Really appreciate you sharing that, Brandon. Would a quick 15-minute call this week be easier to talk it through?
- 2026-10-11 **PARTNER:** Sure, Wednesday morning works.
- 2026-10-11 **US:** Perfect. Grab any time that works for you here: https://example.com/book/justin

### Monique (c_23b8bbb24bcb)

- 2026-10-09 **US:** Hey Monique! It's Justin at 7 Figures Funding. You've been a partner with us since 2025, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.
- 2026-10-09 **PARTNER:** Hi Justin, thanks for reaching out. All over the country really. Text is best for me.
- 2026-10-09 **US:** Great to hear from you, Monique! What are you working toward this year?
- 2026-10-10 **PARTNER:** Trying to build a second income stream from referrals, that's the plan.
- 2026-10-10 **PARTNER:** Anywhere from $37k to $150k, usually about $75k.
- 2026-10-10 **US:** Really appreciate you sharing that, Monique. Would a quick 15-minute call this week be easier to talk it through?
- 2026-10-11 **PARTNER:** Sure, Thursday morning works.
- 2026-10-11 **US:** Perfect. Grab any time that works for you here: https://example.com/book/justin

### Tanya (c_671a9aa2cf1d)

- 2026-10-09 **US:** Hi Tanya, Justin here from 7 Figures Funding. You've been a partner with us since 2024, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.
- 2026-10-14 **US:** Hey Tanya, Justin again from 7 Figures Funding. No rush at all, I just didn't want my last text to get buried. Is there a better time to connect? Reply STOP to opt out.
- 2026-10-16 **PARTNER:** Sorry, crazy week! Mainly self-employed contractors.
- 2026-10-16 **US:** Great to hear from you, Tanya! What are you working toward this year?
- 2026-10-17 **PARTNER:** My goal this year is to add funding as a service for my clients.
- 2026-10-17 **US:** Really appreciate you sharing that, Tanya. Would a quick 15-minute call this week be easier to talk it through?
- 2026-10-18 **PARTNER:** Texting is easier for me right now, let's keep it here for now.
- 2026-10-18 **US:** Great to hear from you, Tanya! What kind of clients are you working with most these days?
- 2026-10-19 **PARTNER:** Most of my clients are self-employed contractors.
- 2026-10-19 **US:** Great to hear from you, Tanya! What would make this partnership worth your time?
- 2026-10-20 **PARTNER:** What would help is posts I can share with my audience.
- 2026-10-20 **US:** Happy to help with that, Tanya. Would a quick 15-minute call this week be easier to talk it through?
- 2026-10-21 **PARTNER:** Sure, Wednesday morning works.
- 2026-10-21 **US:** Perfect. Grab any time that works for you here: https://example.com/book/justin

### Raj (c_30da28eaa092)

- 2026-10-09 **US:** Hey Raj! It's Justin at 7 Figures Funding. You've been a partner with us since 2024, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.
- 2026-10-10 **PARTNER:** Hey, nice to meet you Justin. Mainly restaurants.
- 2026-10-10 **US:** Great to hear from you, Raj! What are you working toward this year?
- 2026-10-11 **PARTNER:** I want to add funding as a service for my clients.
- 2026-10-11 **US:** Really appreciate you sharing that, Raj. Would a quick 15-minute call this week be easier to talk it through?
- 2026-10-12 **PARTNER:** Sure, Wednesday morning works.
- 2026-10-12 **US:** Perfect. Grab any time that works for you here: https://example.com/book/justin

### Tanya (c_87addf5e8339)

- 2026-10-05 **US:** Hey Tanya, it's Justin with 7 Figures Funding. You've sent us 11 deals since 2024, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- 2026-10-05 **PARTNER:** Remove me

### Jamal (c_e8930d0a8c22)

- 2026-10-05 **US:** Hey Jamal, it's Justin with 7 Figures Funding. You've sent us 11 deals since 2022, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- 2026-10-05 **PARTNER:** please stop texting me

### Lena (c_8a03528a1c66)

- 2026-10-05 **US:** Hey Lena, it's Justin with 7 Figures Funding. You've sent us 7 deals since 2024, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.
- 2026-10-06 **PARTNER:** Hey Justin! Good to hear from you. Slammed right now, can you check back with me in a few weeks?
- 2026-10-06 **US:** Totally understand, Lena. I'll reach back out then. Good luck in the meantime!

### Kevin (c_8904a5601b0e)

- 2026-10-05 **US:** Hi Kevin, Justin here from 7 Figures Funding. You've sent us 7 deals since 2023, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.
- 2026-10-10 **US:** Hey Kevin, Justin again from 7 Figures Funding. No rush at all, I just didn't want my last text to get buried. Is there a better time to connect? Reply STOP to opt out.
- 2026-10-12 **PARTNER:** Not a good time right now, maybe next quarter.
- 2026-10-12 **US:** Great to hear from you, Kevin! What are you working toward this year?

## STOP messages received

- UNSUBSCRIBE
- please stop texting me
- Remove me
- Remove me
- UNSUBSCRIBE
- STOP
- STOP
- STOP
- Remove me
- STOP

## Identity question sample

```
{
 "text": "Am I talking to a bot?",
 "alert": "Yolanda Vance asked if they're texting with a real person. Please reply to them yourself; I won't draft anything to them until your task is done.",
 "actions": [
  "last_reply_date=today",
  "lifecycle \u2192 aff:reactivated",
  "kickoff conversation started",
  "personal reply task for the manager"
 ],
 "draft": "none (manager replies)",
 "manager_replied": "2026-10-06"
}
```

## Sample approval card

```
*Approval needed* — 40 kickoff wave 1 (40 real, 0 simulated) · 80 SMS segments
action `act_71f669224634` · digest `7e8de4f74b548683` · demo mode: False
Every message in full: `Reviews/2026-10-05 kickoff wave 1 (act_71f669224634).md` (40 messages; read them there)
1. Tanya Nguyen (sms, mock): Hey Tanya, it's Justin with 7 Figures Funding. You've sent us 11 deals since 2024, and I'm now your partner manager. I'd love to learn what you're working toward and how we can hel
2. Omar Foster (sms, mock): Hey Omar, it's Justin with 7 Figures Funding. You've sent us 11 deals since 2022, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help
3. Tiffany Perry (sms, mock): Hey Tiffany, it's Justin with 7 Figures Funding. You've sent us 11 deals since 2023, and I'm now your partner manager. I'd love to learn what you're working toward and how we can h
4. Keisha Coleman (sms, mock): Hey Keisha! It's Justin at 7 Figures Funding. You've sent us 11 deals since 2023, and I'm your new partner manager. I want to get to know your business and how we can help you clos
5. Keisha Foster (sms, mock): Hey Keisha! It's Justin at 7 Figures Funding. You've sent us 11 deals since 2023, and I'm your new partner manager. I want to get to know your business and how we can help you clos
6. Tiffany Myers (sms, mock): Hi Tiffany, Justin here from 7 Figures Funding. You've sent us 11 deals since 2022, and I just became your partner manager. I'm reaching out personally to learn your goals and see 
7. Brittany Foster (sms, mock): Hi Brittany, Justin here from 7 Figures Funding. You've sent us 11 deals since 2022, and I just became your partner manager. I'm reaching out personally to learn your goals and see
8. Grant Perry (sms, mock): Hey Grant! It's Justin at 7 Figures Funding. You've sent us 11 deals since 2024, and I'm your new partner manager. I want to get to know your business and how we can help you close
Reply *approve act_71f669224634* to send, *approve act_71f669224634 except 4, 17* to hold some back, or tell me what to change.
```

## Sample brief

```
- **Partner:** Sofia Long, business coach. Came from referral. Joined 2023-10-03. Tier: Free
- **Lifecycle:** reactivated. Last reply 2026-10-07, last deal 2024-03-01, deals sent 4
- **Who they are:** A business coach on the Free tier, partner since October 2023. Has sent 4 deals, the last in March 2024. Works mostly with agency owners; their clients usually need equipment financing. Best reached by email.
- **What they told us last:** Hi Justin, thanks for reaching out. They always seem to need new equipment. Email me, I'm in meetings all day.
- **What they want:** ask
- **Open loops / tasks:** none
- **Why this call:** first call since the kickoff
- **Recommended outcome:** a first deal or a date for one, and the next check-in on the calendar
- **Programs that fit their clients:** Business Term Loan, Short-Term Business Loan
- **Ask if it doesn't come up:** What are you working toward this year?
- **Do NOT promise:** approvals, rates, timelines, commission changes, or payout dates
- **Recording:** say at the start that the call is recorded so you remember what you talked about
```

## Sample call note

```
---
type: call
date: 2026-10-09
partner: "[[Partners/Sofia Long (902323)|Sofia Long]]"
ghl_contact_id: c_05c428902323
source: ghl_phone
external_id: m_91b7ac5bd431
duration_min: 19.0
recording: "mock:recording/m_91b7ac5bd431"
participants: "Justin, Sofia Long"
---

# Call with Sofia Long (2026-10-09)

## Summary
19-minute call with Sofia. Learned: best time, blockers, deal size, deal types, goals, regions. 1 follow-up agreed.

## What we learned
- **What their clients need:** equipment financing
- **Typical deal size:** around $50k
- **Goals:** close two deals a month by the end of the year
- **What's gotten in the way:** I lost the submission link
- **Best time to reach them:** evenings
- **Where they work:** California
- **Where they work:** Florida

## Commitments
- [ ] We: send Sofia the submission link and a one-page program summary by Friday (by 2026-10-16)

## Transcript
**Justin:** Hey Sofia, thanks for making time. Quick heads up, I record my calls so I don't lose track of what we talk about. That okay?
**Sofia Long:** Totally fine.
**Justin:** Tell me about your clients and what they usually need.
**Sofia Long:** These days it's a lot of agency owners. They always seem to need new equipment. Anywhere from $25k to $100k, usually about $50k.
**Justin:** Where are most of them?
**Sofia Long:** Most of them are in Florida and California.
**Justin:** What's gotten in the way of sending deals?
**Sofia Long:** Honestly I haven't sent anything because I lost the submission link. Honestly I'd love to close two deals a month by the end of the year.
**Justin:** What would make this worth your time?
**Sofia Long:** Honestly a simple page I can send my clients to would make a big difference.
**Justin:** Done. I'll send you the submission link and a one-page program summary by Friday, and I'll check in next week.
**Sofia Long:** Evenings are best to reach me.
```

## Sample plan

```
**Who they serve:** agency owners (California, Florida)
**What their clients need:** equipment financing, around $50k
**7FF programs to lead with:** Business Term Loan, Short-Term Business Loan
**Their goal:** close two deals a month by the end of the year
**Next 30 days:**
1. We: send Sofia the submission link and a one-page program summary by Friday (by 2026-10-16)
2. Next check-in, ask: "What would make this partnership worth your time?"
**How we'll know it's working:** deals submitted by Sofia, counted by month.
```

## Review file (first 120 lines)

```
---
type: review
date: 2026-10-05
action_id: act_71f669224634
messages: 40
---

# Review: kickoff wave 1

40 kickoff wave 1 (40 real, 0 simulated) · 80 SMS segments

Approve all with `approve act_71f669224634`, or hold some back with `approve act_71f669224634 except 4, 17` (the numbers below).

### 1. [[Partners/Tanya Nguyen (5e8339)|Tanya Nguyen]]
_sms · kickoff · mock · 2 segments · variant A_

> Hey Tanya, it's Justin with 7 Figures Funding. You've sent us 11 deals since 2024, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.

### 2. [[Partners/Omar Foster (858e21)|Omar Foster]]
_sms · kickoff · mock · 2 segments · variant A_

> Hey Omar, it's Justin with 7 Figures Funding. You've sent us 11 deals since 2022, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.

### 3. [[Partners/Tiffany Perry (0ca7f4)|Tiffany Perry]]
_sms · kickoff · mock · 2 segments · variant A_

> Hey Tiffany, it's Justin with 7 Figures Funding. You've sent us 11 deals since 2023, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.

### 4. [[Partners/Keisha Coleman (5f2d02)|Keisha Coleman]]
_sms · kickoff · mock · 2 segments · variant C_

> Hey Keisha! It's Justin at 7 Figures Funding. You've sent us 11 deals since 2023, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.

### 5. [[Partners/Keisha Foster (9d17a3)|Keisha Foster]]
_sms · kickoff · mock · 2 segments · variant C_

> Hey Keisha! It's Justin at 7 Figures Funding. You've sent us 11 deals since 2023, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.

### 6. [[Partners/Tiffany Myers (069f34)|Tiffany Myers]]
_sms · kickoff · mock · 2 segments · variant B_

> Hi Tiffany, Justin here from 7 Figures Funding. You've sent us 11 deals since 2022, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.

### 7. [[Partners/Brittany Foster (1903a6)|Brittany Foster]]
_sms · kickoff · mock · 2 segments · variant B_

> Hi Brittany, Justin here from 7 Figures Funding. You've sent us 11 deals since 2022, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.

### 8. [[Partners/Grant Perry (7f6965)|Grant Perry]]
_sms · kickoff · mock · 2 segments · variant C_

> Hey Grant! It's Justin at 7 Figures Funding. You've sent us 11 deals since 2024, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.

### 9. [[Partners/Jamal Russell (0a8c22)|Jamal Russell]]
_sms · kickoff · mock · 2 segments · variant A_

> Hey Jamal, it's Justin with 7 Figures Funding. You've sent us 11 deals since 2022, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.

### 10. [[Partners/Brandon Hughes (2c2e0e)|Brandon Hughes]]
_sms · kickoff · mock · 2 segments · variant B_

> Hi Brandon, Justin here from 7 Figures Funding. You've sent us 11 deals since 2023, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.

### 11. [[Partners/Luis Ward (b701be)|Luis Ward]]
_sms · kickoff · mock · 2 segments · variant B_

> Hi Luis, Justin here from 7 Figures Funding. You've sent us 7 deals since 2025, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.

### 12. [[Partners/Brittany Foster (30eb64)|Brittany Foster]]
_sms · kickoff · mock · 2 segments · variant C_

> Hey Brittany! It's Justin at 7 Figures Funding. You've sent us 7 deals since 2025, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.

### 13. [[Partners/Lena Ross (8a1c66)|Lena Ross]]
_sms · kickoff · mock · 2 segments · variant A_

> Hey Lena, it's Justin with 7 Figures Funding. You've sent us 7 deals since 2024, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.

### 14. [[Partners/Camila Myers (84aa14)|Camila Myers]]
_sms · kickoff · mock · 2 segments · variant A_

> Hey Camila, it's Justin with 7 Figures Funding. You've sent us 7 deals since 2024, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.

### 15. [[Partners/Priya Jenkins (f5459c)|Priya Jenkins]]
_sms · kickoff · mock · 2 segments · variant A_

> Hey Priya, it's Justin with 7 Figures Funding. You've sent us 7 deals since 2022, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.

### 16. [[Partners/Kevin Long (601b0e)|Kevin Long]]
_sms · kickoff · mock · 2 segments · variant B_

> Hi Kevin, Justin here from 7 Figures Funding. You've sent us 7 deals since 2023, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.

### 17. [[Partners/Priya Vance (bdb1cb)|Priya Vance]]
_sms · kickoff · mock · 2 segments · variant C_

> Hey Priya! It's Justin at 7 Figures Funding. You've sent us 7 deals since 2024, and I'm your new partner manager. I want to get to know your business and how we can help you close more deals. Would a quick call this week work? Reply STOP to opt out.

### 18. [[Partners/Luis Nguyen (6875f2)|Luis Nguyen]]
_sms · kickoff · mock · 2 segments · variant A_

> Hey Luis, it's Justin with 7 Figures Funding. You've sent us 7 deals since 2022, and I'm now your partner manager. I'd love to learn what you're working toward and how we can help you close more deals. Open to a quick call this week? Reply STOP to opt out.

### 19. [[Partners/Jamal Ward (7fba50)|Jamal Ward]]
_sms · kickoff · mock · 2 segments · variant B_

> Hi Jamal, Justin here from 7 Figures Funding. You've sent us 7 deals since 2024, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.

### 20. [[Partners/Grant Brooks (d3c23c)|Grant Brooks]]
_sms · kickoff · mock · 2 segments · variant B_

> Hi Grant, Justin here from 7 Figures Funding. You've sent us 7 deals since 2022, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.

### 21. [[Partners/Gina Ward (2ad0b2)|Gina Ward]]
_sms · kickoff · mock · 2 segments · variant B_

> Hi Gina, Justin here from 7 Figures Funding. You've sent us 7 deals since 2024, and I just became your partner manager. I'm reaching out personally to learn your goals and see where we can help. Got time for a quick call this week? Reply STOP to opt out.

### 22. [[Partners/Omar Diaz (74750b)|Omar Diaz]]
_sms · kickoff · mock · 2 segments · variant B_
```

## Manager tasks created (sample of 10)

- '[For the manager] Has a deal to send — call today. They said: Perfect timing.\nI actually have a client who needs about $250k for working capital to cover payroll. Can I send you the file?'
- '[For the manager] Has a deal to send — call today. They said: Perfect timing. I actually have a client who needs about $50k for a line of credit. Can I send you the file?'
- '[For the manager] From the call on 2026-10-09: send Sofia the submission link and a one-page program summary by Friday'
- '[For the manager] Heather asked who they\'re texting with: "Am I talking to a bot?". Reply to them yourself. The agent won\'t draft anything to them until this task is done.'
- '[For the manager] Answer: Sounds good, Wednesday afternoon?'
- '[For the manager] From the call on 2026-10-13: send Monique the submission link and a one-page program summary by Friday'
- '[For the manager] Brandon asked who they\'re texting with: "Am I talking to a bot?". Reply to them yourself. The agent won\'t draft anything to them until this task is done.'
- '[For the manager] From the call on 2026-10-15: send Raj the submission link and a one-page program summary by Friday'
- 'They asked: Hey Justin! Good to hear from you. Slammed right now, can you check back with me in a few weeks?'
- '[For the manager] Scope lead reactivation for Heather Myers. I could really use help working my old leads. All over the country really.'