---
name: affiliate-reactivation
description: "Bring quiet, dormant, and dead affiliates back: personal check-ins for past producers, the Dormant Reactivation sequence at 90 days, the quarterly Dead-Lead campaign at 180+, and source-specific reactivation pushes (e.g., 'reactivate dead Skool leads'). Use when asked to reactivate, win back, or 'wake up' affiliates."
---

# Reactivation

| Cohort | Who | Play |
|---|---|---|
| Quiet (45–59d) | no reply/deal 45+ days | normal cadence, sharper hooks (new program, event) |
| Check-in (60–89d) | 60+ days | **personal** message drafted by you, approved in the daily batch |
| Dormant (90–179d) | 90+ days | past producers → personal; others → WF-4 Dormant Reactivation |
| Dead (180d+) | 180+ days | WF-5 Dead-Lead campaign once per 90 days; a reply moves them to `aff:reactivated` |

## "Launch reactivation for dead Skool leads"
1. `fam_affiliate_search(tag="src:skool")` + `fam_sweep` → count those with lifecycle `aff:dead` (report the number and 3 sample names).
2. Offer something of value first: a free growth-service (reactivating *their* old leads, a funnel page), the next training, what's new.
3. `fam_enrollment_prepare("dead_reactivation", contact_ids_json=[...], purpose="dead Skool leads reactivation")` → card → approval → execute.
4. Replies flow through reply triage; every reply is `aff:reactivated` automatically.

Never reactivate `aff:dnc`. Never pretend a previous conversation happened.
