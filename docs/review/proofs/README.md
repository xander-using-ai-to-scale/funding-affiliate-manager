# Proof scripts from the 2026-10-03 gap review

Each script shows one bug from [../2026-10-03-gap-review.md](../2026-10-03-gap-review.md) against the mock CRM in a
temp directory. None of them touch GoHighLevel, Zoho, OpenRouter or the droplet. p2 uses a local socket.
The first fix batch turned the bugs in items 1–8 into tests in `tests/test_pilot_fixes.py` (the Test column). The
scripts stay as the record of what was wrong; run against the fixed code they show the fixed behavior, except p1,
which now stops early because the second wave comes back empty.

    python3 docs/review/proofs/p1_overlap.py

| Script | Shows | Test |
|---|---|---|
| p1_overlap | Two waves drafted before either is approved text the same partners twice | `Waves`: second wave can't take held partners; expiry |
| p2_timeout | A GHL timeout mid-wave leaves the action stuck in "executing" and partners still pending | `Idempotent` |
| p3_names | Accented names and emoji push kickoffs over 2 segments; skipped partners stay in the queue | open (next batch) |
| p4_intents | HELP, "take me off your list", "nonstop" (opt-out line skipped), picture messages | `Triage`, `OptOut` |
| p5_zoho | The Zoho import doesn't refresh its token and silently drops history on a 401 | open (next batch) |
| p6_inbox | A reply that arrives after our last outbound text disappears from the inbox | `Inbox` |
| p7_postsend | A 429 after GHL accepted a text leads to a second kickoff | `Bookkeeping` |
| p8_selfapprove | `fam approve` from a shell approves and executes an action | `SelfApproval` |
| p9_calls | GHL calls per kickoff at execute (runtime estimate) | estimate only |
| p10_dupes | The same phone number in two formats is texted twice | open (next batch) |
| p11_active | A 48-deal CEO partner is ranked first for "I'm your new partner manager" | open (needs 7FF's active list) |
| p12_killswitch | Setting the stop flag mid-wave doesn't stop the wave | `StopAndWindow` |
| p13_stopcounts | STOP counts as a reply in variant stats and the scorecard | `Triage.test_stop_help_and_wrong_numbers_are_not_replies` |
| p14_after | Kickoff non-repliers fall into bulk reactivation; first-sweep call volume | open (next batch) |
| digest.py | Builds the message digest from a relationship-simulation run | tool |
| runsims.py | Runs the relationship simulation on two seeds | tool |

The vault-sync conflict proof was run by hand with three local git repositories; the script `deploy/droplet/vault-sync.sh` line 12 (`|| true`) is the cause.
