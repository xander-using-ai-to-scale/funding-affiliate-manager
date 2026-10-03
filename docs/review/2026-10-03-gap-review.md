# Gap review before the pilot

Three reviewers, 2026-10-03: technical, sales and direct response, and partner-program operations.
They worked read-only on the repo and on a fresh 30-day simulation. Each reviewer had to back every finding with a
file and line, a quoted message, or a script that shows the bug.

Every finding marked **blocks the pilot** was then re-checked before it went into this document:
- **Against the code:** items 1, 2, 4–8, 10–15, 17 and 18.
- **By re-running the proof scripts (p1, p2, p8, p12, p13):** items 1–4 and 14.
- **Not checked line by line:** item 9 (7FF's other systems) and the sales and program judgment calls.

The proof scripts are in [proofs/](proofs/).

- **The simulation.** `relsim`, run on the framework templates with 250 quiet partners over 30 days.
  - Seed 21 reproduced the published report exactly: 250 kickoffs, 205 nudges, 108 texts in, 85 replies, 48 partners
    talking, 8 calls, 8 plans, 8 deals, 10 opt-outs, 5 identity escalations.
  - A second seed (7) gave 59 talking, 7 calls, 8 deals, 8 opt-outs and 3 escalations.
  - The reply rates are assumptions built into the simulation, not evidence.
- **The messages.** Every text the simulation sent, with send counts and segment counts, is in
  [2026-10-03-message-digest.md](2026-10-03-message-digest.md).
- **The proof scripts.** The technical reviewer's scripts (p1–p14) are in [proofs/](proofs/). Each one is a test we
  don't have yet.

Severity: **blocks the pilot**, **before wave 2**, **later**. Owner: **us**, **7FF**, **Justin**, **joint**.

## Fix status (first batch, 2026-10-03, uncommitted)

Items 1–8 below, plus showing the partner's text to the approver. 76 tests pass; the new ones are in
`tests/test_pilot_fixes.py`, one per proof script. Nothing is deployed to the droplet yet.

| Item | Status | What changed | Still open |
|---|---|---|---|
| 1. Self-approval | Partial | `agent.disabled_toolsets` removes terminal, code execution, file, browser and computer use from every bundle, cron job and delegated child (verified in the droplet's Hermes source). `fam approve`/`fam resume` removed from the CLI. `fam_read` (knowledge/ and the vault only) and `fam_daily_note` replace file access. | Signed approvals, a separate OS user for approvals, recording the Slack user id |
| 2. Double texts, lost kickoffs | Fixed | Outbox row per message before sending. A timeout or 5xx becomes "unknown", held for a person (`fam_outbox_settle`, human-only), never resent. One kickoff per partner, enforced by a unique index. Bookkeeping retries on its own. | Live GoHighLevel not exercised |
| 3. Overlapping waves | Fixed | Open batches reserve their partners. Unapproved batches expire after 48 h. At send time a message is skipped if the partner replied, opted out, or wrote again after the draft. | |
| 4. Stop and quiet hours | Fixed | Both checked before every message. Window is 9:00–20:00 in the recipient's time zone from the area code, and a number whose zone is unclear needs the window open everywhere it could be. Batches pause and finish later on a no-model cron job, for up to 36 h after approval. Override works only against the mock CRM. | Policy change: was 11:00–20:00 Eastern |
| 5. Approver blind | Fixed | Review file and card show what they wrote, our last message, how it was read, the planned move, and flags. Slack mentions are neutralized. Big waves stay in the vault; only flagged messages go to Slack. | |
| 6. Triage misfires | Fixed | Whole-word matching. HELP, wrong number, not interested, book a call, and plans to send deals are new intents. A named time gets a confirmation. Questions just asked aren't repeated, openers vary, texters aren't asked for calls. No "send the file" by text. | |
| 7. Inbox drops replies | Fixed | Every untriaged inbound, read or unread, oldest first, paged; per-conversation watermark. Triage every 20 min, 7 days, waking the model only when a text arrives. | Live paging (`startAfterDate`) not exercised |
| 8. Opt-out, HELP, consent | Mostly fixed | Exact opt-out sentence check; more opt-out phrasings; quoted email text stripped; HELP to a person; email footer with postal address (live email refused until `mailing_address` is set); Zoho `Email_Opt_Out` blocks email only. | Consent fields wait on 7FF's records. 7FF to confirm the mailing address |

The simulation moved. Seed 21 now gives 57 partners talking, 5 calls, 5 plans and 5 deals; the published report
says 48, 8, 8 and 8. Part of that is intended: texters aren't pushed to calls. Part is the simulation: its partners
have no scripted response to the two new moves ("ask for the first deal", "polite close"). The published pages
were not regenerated.

---

## 1. What blocks the pilot

### Approvals and sending

1. **The agent can approve its own sends.** Owner: us.
   - **What's wrong:** the agent's Slack and cron toolsets include `terminal`, `code_execution` and `file`
     (hermes/config.template.yaml:142). The droplet CLI has `fam approve`, and the approval digest is printed on the
     card the agent posts itself. The reviewer proved `fam approve` → approved → executed from a shell.
   - **Why it's worse:** inbound texts are stored raw and fed into every later draft, so any partner can put
     instructions into the context of an agent that has that shell.
   - **Fix:**
     - Take `terminal`, `code_execution` and `file` out of the Slack and cron toolsets.
     - Remove `approve` and `resume` from the droplet CLI.
     - Sign each approval with a key that only the approvals process can read, run as a separate user.
     - Record the approver's Slack user id, not a name the model passes in.
2. **One slow or rate-limited GHL response causes double texts or lost kickoffs.** Owner: us.
   - **What's wrong:** the send loop only catches `FamError` (engine.py:868). A bare `TimeoutError` or a 429 after
     GHL has accepted the text aborts the wave mid-way with the action stuck in "executing". The partner who got
     the text stays "kickoff-pending" and is texted again in the next wave. The GHL message id is thrown away.
   - **Fix:**
     - Keep an outbox row per message: written before the send, updated with the GHL message id after it.
     - Refuse a second kickoff to any contact that already has one.
     - Catch every exception per message. Mark an unknown outcome "unknown" for a person to settle; never resend
       it automatically.
     - Make the bookkeeping a separate step that can be retried.
3. **Overlapping waves text the same partners twice.** Owner: us.
   - **What's wrong:** a drafted wave that isn't approved never expires. A wave drafted the next day picks the same
     still-pending partners, and approving both texts everyone twice (proof p1).
   - **Fix:**
     - Reserve a wave's contacts when it is prepared.
     - Expire unapproved waves.
     - At send time, skip a kickoff whose contact is no longer pending, and skip a reply if a newer inbound text
       arrived after it was prepared.
4. **The kill switch and quiet hours are checked once per wave, and only in Eastern time.** Owner: us.
   - **What's wrong:** the stop flag and the send window are checked before the loop starts (engine.py:789,
     806–808). A stop set mid-wave didn't stop the wave: 4 of 6 texts went out after it (proof p12). A wave started at 19:50 ET
     sends after 20:00. 11:00 ET is 05:00 in Hawaii. `FAM_IGNORE_SMS_WINDOW` overrides the window from a shell.
   - **Fix:**
     - Check both for every message.
     - Use the recipient's time zone, taken from the area code with a conservative fallback.
     - Pause the wave in a way it can resume from.
     - Allow the override only in mock mode.
5. **The person approving can't see what the partner said.** Owner: us.
   - **What's wrong:** the review file shows only our draft (vault.py:183–193). The Slack card cuts previews to
     180 characters. Every reply bug in item 6 would pass approval.
   - **Fix:**
     - For each reply, show the partner's last text, our last message, the intent and the planned move above the
       draft.
     - Flag pairs that don't fit, such as a weekday in their text and "question" as the intent.
     - Post the review file into the Slack thread.

### Replies

6. **Reply triage fumbles the replies that matter most.** Owner: us.
   - **What happened in the simulation** (digest, full threads):
     - "Sounds good, Wednesday afternoon?" was answered "Good question… let me get you the exact answer today."
       The "?" rule fires before the yes→book check (cadence.py:424; drafting.py:142–146).
     - "Deals are typically $150k" was read as interest in an event, because "typically" contains "call"
       (cadence.py:426). We answered "I'll send the link over so you can grab a spot."
     - "Not a good time right now, maybe next quarter" isn't caught as check-back-later.
     - A partner who named a time was sent the booking link to pick a time again.
     - "Great to hear from you" opened three replies in a row in one thread.
     - Questions they had just answered were asked again.
     - Partners who said "texting is easier" were asked for a call anyway.
     - Victor said he wants to send "a deal a month" and was never asked for one.
   - **Fix:**
     - Detect yes, a day or a time before treating "?" as a question.
     - Match whole words.
     - Add check-back phrasings ("not a good time", "next quarter", "slammed", "after the holidays").
     - When they name a time, confirm it.
     - Don't ask about a slot they answered in their last two texts.
     - Respect a stated preference for text.
     - When they say they intend to send deals, ask for one.
     - Turn these exact digest lines into regression tests.
     - The model drafter uses the same move logic, so a better model would only reword the wrong move.
7. **The inbox drops replies.** Owner: us.
   - **What's wrong:**
     - A conversation whose last message is ours is skipped (engine.py:235–236), so a partner's text that arrives
       after one of our sends disappears (proof p6).
     - It lists the newest 25 conversations, so older unread ones are never seen.
     - Triage runs only on weekdays, on a cron with no time zone set.
     - Picture messages arrive empty and are classed as a general reply.
   - **Fix:**
     - Keep a per-conversation watermark of the inbound message ids already handled.
     - Drain the inbox oldest-first.
     - Run every 15–30 minutes, seven days a week, in an explicit time zone.
     - Show picture-message links to the manager.

### Opt-outs and consent

8. **Opt-out, HELP and consent have gaps.** Owner: us, and 7FF for consent and the A2P HELP/STOP replies.
   - **What's wrong:**
     - Any body containing "stop" inside another word ("nonstop") skips the opt-out line (engine.py:663).
     - HELP gets a friendly drafted reply, and the partner is marked reactivated.
     - "Take me off your list", "don't contact me again" and "lose my number" aren't caught.
     - A quoted email footer containing "unsubscribe" opts out a partner who wrote "call me Tuesday".
     - Kickoff emails (for partners with no phone) have no unsubscribe link and no physical address.
     - There are no consent fields.
     - Zoho's `Email_Opt_Out` blocks SMS too.
     - The window is ET only (item 4).
   - **Fix:**
     - Append the opt-out line unless that exact sentence is already in the body.
     - Add HELP and the missing phrasings.
     - Strip quoted text before matching.
     - Put a compliant footer on email.
     - Add consent-basis and consent-date fields, filled from 7FF's records at import.
9. **Opt-outs stop at the GHL boundary.** Owner: joint.
   - **What's wrong:** a partner who texts STOP to us keeps hearing from Morgan, Zoho campaigns or 7FF staff.
     Zoho is read-only for the length of the agreement.
   - **Fix:**
     - A two-way suppression feed before every wave. We send 7FF our STOPs, do-not-contacts and wrong numbers;
       7FF sends us their opt-outs, disputes, banned partners and ex-staff.
     - A written rule on who contacts in-scope partners about the program.

### Who gets a kickoff, and what they get

10. **Active producers get "I'm your new partner manager", and the targeting data is wrong.** Owner: 7FF (data)
    and us.
    - **What's wrong:**
      - There is no exclusion list.
      - Ranking puts lifetime deals first, so a 48-deal CEO partner is first in wave 1 (proof p11).
      - The Zoho map leaves tier, deals and last-deal date blank.
      - It stores `Last_Activity_Time`, which is staff activity, as the partner's last reply, and uses
        `Created_Time` as the join year quoted in the text.
      - Import runs once, so tier and deal changes in Zoho never arrive. Partners who stay in Zoho drift into
        "quiet".
    - **Fix:**
      - 7FF supplies the active-producer list, the tier field, and a deals feed keyed by partner ID.
      - Import a hard exclusion tag that enroll, draft and prepare all honor.
      - Map the fields correctly.
      - Re-sync on a schedule.
      - The top lapsed producers get a personal call or a hand-written text from Justin, not the batch.
11. **A partner with a deal has no tracked way to send it.** Owner: joint.
    - **What's wrong:**
      - No partner Referral ID or personal link is imported, only one shared submit link.
      - Our has-deal reply says "send the file here", which invites bank statements over SMS against our own
        guardrails.
      - The simulated call's blocker was "I lost the submission link", and we promised to send it "by Friday".
    - **Fix:**
      - Import each partner's Referral ID and link, and put it in every engaged thread.
      - A 7FF deal-registration form for warm handoffs.
      - Never take files by text.
      - A named intake owner at 7FF, with a standard time to contact the merchant.
12. **The first texts will surface old grievances, and no one at 7FF owns the answers.** Owner: 7FF, and us.
    - **What's wrong:**
      - Commission terms are still placeholders.
      - Unpaid commissions are forfeited if Everee isn't set up within 6 months.
      - "You've sent us 11 deals" invites "and you never paid me", which is classed as a commission question and
        answered "Good question".
      - There is no complaint intent.
    - **Fix:**
      - 7FF flags each partner's payout status, open complaints, and funded vs declined counts before wave 1.
        Flagged partners get a text Justin writes himself.
      - Add a complaint intent that stops drafting and alerts the manager.
      - Get an approved commission card per tier.
      - Put a number in the hook only if it's verified.
      - Name a 7FF owner for commissions and one for deal status, each with a response standard.
13. **The kickoff asks a stranger for a meeting and gives nothing.** Owner: us; Justin approves the copy.
    - **What's wrong:**
      - All 250 kickoffs end in a call ask, and the only "why now" is us ("I'm now your partner manager").
      - Partners don't "close more deals"; 7FF's advisors do.
      - The niche hook never fires: tenure always wins first, and 0 of 250 used niche.
      - "You're one of our Apprentice partners" went out 52 times as a label with no benefit.
      - A call as the first ask doesn't scale to wave 3, where one manager would have to take every call.
    - **Fix:** the first ask is a one-word-reply question or a give, such as their link and a one-page list of what
      7FF funds. Calls are reserved for partners with a deal, partners who ask, and scoping a service. Revised
      copy is in section 4.

### Attribution and the agreement

14. **Nobody can prove who is a "Re-engaged Partner".** Owner: joint.
    - **What's wrong:**
      - The agreement says "inactive on the Effective Date and replies" (proposal-and-agreement-7ff.md:114).
        "Inactive" is undefined and there is no baseline snapshot.
      - Every inbound text, STOP and "wrong number" included, sets the last-reply date and logs a reply
        (engine.py:456), so the scorecard reply rate counts opt-outs (proof p13).
      - Outbound message ids are discarded.
      - `affiliate_id` isn't mapped from Zoho, so 7FF's deal list can't be matched to our partners.
      - `record_deal` stores no deal ID, amount or tier.
      - The SQLite database (approvals, interactions, audit log) isn't backed up.
    - **Fix:**
      - Freeze an Inactive Partner Register before the first send, from 7FF's deal data: partner ID, last
        submission, tier, and a look-back rule. Put its hash in the audit log.
      - Count only qualifying engagement: a two-way reply after a Program message that isn't an opt-out, a wrong
        number, a HELP or a not-interested.
      - Keep an append-only Re-engaged Register and send it to 7FF weekly.
      - Map the Zoho ID.
      - Back up SQLite nightly, encrypted and off the droplet.
15. **The agreement leaves the money undefined.** Owner: Justin.
    - The basis key term is blank.
    - §5 pays on deals "submitted" and §6 reports "submitted and funded".
    - The tier is taken at submission, so when 7FF upgrades a Free partner to CEO our share drops from 15% to 5%.
    - There is no attribution window, and none survives termination.
    - §8's 30-day deletion would destroy the records we need to invoice.
    - Funding Machine purchases are still open.
    - There is no indemnity for TCPA claims on 7FF's consent data.
    - **Fix:**
      - The share is calculated on net revenue collected on funded deals, with a true-up.
      - The tier is locked on the re-engagement date.
      - A per-partner window that survives termination, with reporting and audit duties surviving with it.
      - A carve-out from §8 for the register.
      - Mutual indemnity: 7FF for consent and list data, us for sending outside the agreed rules.
16. **The pilot can't prove lift, and three openers can't pick a winner.** Owner: joint.
    - **What's wrong:**
      - The waves go past producers first, so the pilot tests the wrong population.
      - There is no holdout group.
      - A, B and C differ only in greeting and filler. At about 83 per arm, the minimum detectable difference is
        about 17 points.
    - **Fix:**
      - Draw the pilot as a stratified random sample (producers and never-produced).
      - Keep a randomized holdout from each wave that isn't contacted until after the 90-day review.
      - Run two arms on one big lever (call ask vs one-word or give ask), decided on positive reply rate, with
        opt-outs per 100 as the guardrail.
      - Write the 90-day decision rule now.

### Live systems

17. **The live GHL client has never run against the real API.** Owner: us; 7FF provides the sub-account and a
    test number.
    - **What's wrong:**
      - Only constructor tests exist.
      - `mark_read`, call listing, transcription, unread search and tag-search paging are unexercised.
      - Calls are scanned in the 50 newest conversations only.
      - Retries happen only on 429, with no `Retry-After`.
      - Pacing is per process, and sends carry no `fromNumber`.
      - Separately, the Zoho import never refreshes its token and silently drops history on a 401 (proof p5).
    - **Fix:**
      - A contract script against the real sub-account: upsert, tag search across all pages, SMS to a test phone,
        read it back, `mark_read`, transcription. Record fixtures from it.
      - Fix Zoho token refresh and resume, or have 7FF send a CSV export.
18. **The droplet isn't running the program yet.** Owner: Justin.
    - The gateway isn't started (no Slack tokens), so approval cards go nowhere.
    - GHL is the mock.
    - The drafting model is unset.
    - Profiles aren't built.
    - Vault sync wedges on its first merge conflict and then commits conflict markers (proof in `vs/`). The
      approval card points the manager at that vault.

---

## 2. Before wave 2

- **Approval doesn't hold at our own volumes.** About 13,000 kickoffs, 10,000 nudges and 5,300 replies in the
  reactivation, then about 26,000 touches a month. Fixes:
  - Define approval by message class in the agreement:
    - each one-to-one reply;
    - the full review file for kickoffs;
    - template, audience and a sample-read rate for bulk.
  - Size waves to what the approver and the caller can actually handle.
  - Name a backup approver.
  - Set a response standard for replies in the SMS window.
  - Group review files by template and show only the parts that change.
  - Add `edit N: <text>`.
- **A flood after the kickoff.** Partners who ignore the kickoff and the nudge fall into bulk reactivation, up to
  2,000 a day under standing approvals (proof p14). With the newsletter, events and reminders on top, a non-replier
  can get about 10 messages a month. Fixes:
  - Tag them `kickoff-noreply`.
  - Move them to email and the newsletter only.
  - Cap each partner at one message a day, across every workflow and channel.
- **Long waves run inside one MCP call.** 250 texts ≈ 10 minutes and 2,500 ≈ 104 minutes, against a 900-second
  timeout. The first full sweep is about 26,000 GHL calls. Fixes:
  - A resumable background worker for sends.
  - A chunked, incremental sweep.
  - A daily SMS cap set to the A2P tier.
- **Names and numbers.**
  - Accented names and emoji push kickoffs over 2 segments ("María" → 4). Those partners get skipped and stay
    stuck in the queue.
  - A contact with no name gets "Hey jsmith@gmail.com".
  - Phones aren't normalized to E.164 or deduped, and nobody reads delivery status.
- **Production-based lifecycle and scorecard.**
  - "Producing" needs a deal in the last 30 days, but 7FF reports deals only after month end.
  - The playbook's "haven't seen a submission since…" will be wrong.
  - Fixes:
    - Get a weekly submissions and status feed.
    - Lifecycle stages: registered, first submission, first funded, repeat, lapsed, offboarded.
    - A scorecard by wave, tier, source, niche and opener covering activation, time to first submission,
      submission-to-funded rate, revenue per partner, and lift against the holdout.
- **Count the partners we can actually reach.**
  - Dedupe across Zoho, GHL, the portal and Everee.
  - Flag landlines and terminated partners.
  - Use pilot delivery failures and wrong-number replies.
  - Report a reachable, consented count and use it as the denominator.
  - Warm up a dedicated email subdomain.
- **Partner tools.**
  - A "what we fund / don't fund" sheet from 7FF underwriting.
  - Decline reasons passed back to partners.
  - Deal-status updates to partners (received, advisor reached out, funded).
  - A co-branded one-pager.
  - A short certification as the first training.
- **Incentives and recognition.**
  - 7FF funds a reactivation bonus on the first funded deal back. The agreement says whether it reduces the basis.
  - Partner spotlights, with permission.
  - A council of top producers.
  - Decide where the partner community lives.
  - The Growth Kit stays out of messages until it's scoped: what's free, what's paid, who delivers it.
- **Deal integrity.** 7FF writes a registration policy: first complete registration wins, plus a protection
  period, a house-account rule and who decides disputes. Flag self-referrals, duplicates and volume spikes from
  dormant accounts. Never change a partner's payout details from a text.
- **Partners' own marketing.**
  - A refreshed partner agreement at re-onboarding: approved claims, FTC disclosure, no texting without consent,
    state-law responsibility.
  - No Growth Kit list reactivation without proof of consent.
- **Who the manager is.** Choose the signer for each wave, who also approves and takes the calls. An authority
  matrix: the manager may route, explain and schedule, but may not commit to commissions, discounts, approvals or
  payout dates. A RACI at 7FF with a name and a backup for each area.
- **The call.**
  - Confirm the time they named.
  - An agenda and a morning-of reminder.
  - The brief gains the referral link, deal outcomes, payout status and open complaints. Its "What they want: ask"
    field is broken.
  - The revenue plan becomes a one-screen "Your referral plan" emailed to the partner, with the link sent during
    the call.
- **Observability and data.**
  - Meter every model call into SQLite (AI is invoiced at cost) and roll it into the scorecard.
  - Log why the model fell back to a template.
  - An external heartbeat for the gateway, cron and vault sync.
  - Either list Super Browser, Orgo and the vault's git host as service providers in the agreement, or remove them
    from 7FF's agent.
  - Write a purge runbook.
- **"Is this a bot?"** The simulation's stand-in manager answer ("I read every one of these myself…") is a dodge.
  Justin should agree his own direct, truthful wording before the pilot.

## 3. Later

- **Second manager:** a per-manager GHL user and `fromNumber`. Call matching treats a partner who shares a
  manager's first name as us.
- **Concurrency:** lock each note file while writing, switch SQLite to WAL, keep one engine per process.
- **Full timestamps.** Interactions store dates only, so "replied after the kickoff" can't be proven on the same day.
- **Template versions.** Record the template version and a hash of each sent body.
- **Scope beyond reactivation.** New partners and the ~50 active partners earn us nothing under the current
  agreement. Decide whether they're in scope. Define offboarding. Learn what the tiers actually are.

---

## 4. Framework templates, revised (sales reviewer)

These aren't approved copy; they're a starting point for Justin.
- **Counts:** measured with the repo's own counter. "+STOP" means " Reply STOP to opt out." is included.
- **Links:** `{link}` is always the partner's own imported link, never one we build.
- **Dollar figures and AI:** none of these texts mentions either.
- **Bonus wording:** anything that mentions a bonus needs terms approved by 7FF.

**Kickoffs by segment** (all +STOP, all 2 segments)

| Segment | Chars | Text |
|---|---|---|
| Past producer: still-X check | 287 | Hi {first}, it's Justin at 7 Figures Funding. I just took over as your partner manager, and first, thank you for the {n} deals you've sent us since {year}. Quick one so I point you to the right programs: are you still working mostly with {client_phrase}? |
| Past producer: deal ask | 258 | Hi {first}, it's Justin at 7 Figures Funding, your new partner manager. Thanks for the {n} deals you've sent us since {year}. Simple question: is there a client on your list right now who could use working capital or a line of credit? |
| Past producer: reason now (needs approved terms) | 251 | Hi {first}, it's Justin at 7 Figures Funding, your new partner manager. Thanks for the {n} deals since {year}. For partners coming back, we're adding a bonus on top of your commission on your next funded deal. Want the details? |
| Never produced | 234 | Hi {first}, it's Justin at 7 Figures Funding. You joined our partner program in {year} and I'm your new partner manager. Before I send you anything: do your clients ever ask you where to find business funding? |
| Thin record | 228 | Hi {first}, it's Justin at 7 Figures Funding. You're on our partner list and I'm your new partner manager. Quick one so I don't waste your time: do you work with business owners who might need funding? |
| Any segment: give | 268 | Hi {first}, it's Justin at 7 Figures Funding, your new partner manager. You've been a partner since {year}, so I put your referral link and a one-page list of what we fund in one place. You send a name, we do the rest. Want me to text it over? |

**Sequence.** It stops the moment the partner replies, opts out, complains, or asks who's texting.

1. The kickoff, Tue–Thu, late morning in the recipient's time zone.
2. An email companion a day later, where we have an address: their link, a one-page program list, and one
   question. It needs the CAN-SPAM address and legal entity first.
3. A give nudge 3 business days later (159 chars +STOP, 1 segment): "{first}, Justin again at 7 Figures Funding.
   Want your referral link and a one-page list of what we fund? Reply YES and I'll text it."
4. A second email: one approved partner story and the programs that fit their niche.
5. Top producers only: a live call from Justin, with a short human voicemail if no answer. Prerecorded or
   ringless voicemail only if 7FF's consent covers it.
6. A niche trigger (145 chars, 1 segment): "{first}, Justin again. When one of your {client_phrase} needs cash for a
   slow month or a new truck, want me to have your link ready?"
7. A breakup (177 chars +STOP): "{first}, I'll keep this short. If referrals aren't a fit right now, reply PASS
   and I'll stop texting you. If they are, reply LINK and I'll send yours." PASS turns SMS off. An exit-survey
   version asks why they stopped: lost the link, a client experience, commission, or no clients right now.

**Reply situations** (no STOP line)

| Situation | Chars | Text |
|---|---|---|
| Shares their clients | 101 | Construction contractors, got it. Do any of yours need working capital or a line of credit right now? |
| Prefers text / says YES | 193 | Text works great. Here's your link: {link}. When a client needs capital, send them there, or text me their name and number (with their OK) and I'll take it from there. |
| Names a time | 96 | Thursday works. I'll call you at 10am ET at this number. If another time is better, just say so. |
| Yes, no time | 51 | Great. Does Thursday at 10am or 2pm ET work better? |
| Not now | 141 | Totally fair, {first}. I'll check back in {month}. If a client needs capital before then, text me their name and I'll take it from there. |
| Has a deal | 192 | Love it. Easiest is to send them to {link}. Or text me their name and best number (with their OK) and I'll get an advisor on it. Please no statements or SSNs by text. |
| "Send me info" | 160 | Here you go: {link}. One page on what we fund is in your email. Who are your clients mostly, so I send you the programs that fit them? |
| States a goal | 157 | A deal a month is a good target. Easiest way: when a client mentions cash flow, equipment or a second location, send them your link. Anyone come to mind now? |
| "When do I get paid?" | 184 | We pay on Fridays for everything earned through the Tuesday before. Your first commission comes with an invite to Everee, our payroll system; set it up and payment lands within 7 days. |
| "You never paid me" (then stop drafting, alert) | 124 | I'm sorry, {first}. I want to get this right. Which client was it? I'm looking into it myself and I'll come back to you. |
| "What happened to my last deal?" | 87 | Fair question. Which client was it? I'll pull the file status and text you what I find. |
| Moved on | 165 | Totally get it, {first}. Thanks for telling me. If a client ever needs capital, your link still works: {link}. Want me to stop texting? |
| Rates too high | 176 | Fair. Rates depend on the client and the product, and some cost more than others. If you tell me which client it was, I'll have an advisor walk through other options with them. |
| "Who are you?" | 173 | Fair question. I'm Justin, the new partner manager for 7 Figures Funding's referral partners. You're on our list as a partner since {year}. Want me to send your referral link? |

**Booking and after the call** (no STOP line)

| Message | Chars | Text |
|---|---|---|
| Confirm | 139 | You're set: Thursday 10am ET, I'll call this number. 15 minutes: your clients, the 2 programs that fit them, and getting your link working. |
| Reminder | 67 | Morning {first}, still good for 10am ET? I'll call this number. |
| Same-day recap | 232 | Great talking, {first}. Your link: {link}. For your {client_phrase}, lead with working capital and the line of credit. When one comes up, send the link or text me a name. Plan is in your email. |
| First deal back | 125 | Got your client's file, {first}. Thank you. An advisor is reaching out to them, and I'll text you when there's an update. |

---

## 5. What we're not thinking of

1. **Most quiet partners went quiet for a reason:** money, a deal outcome, or a lost client. The kickoff is the
   first time anyone has asked, so the reactivation is a complaint-intake event before it is a sales event.
2. **Partners judge the program by what happens after they submit.** Deal-status visibility is the product. A
   partner who sends a client and hears nothing never sends again.
3. **We control none of the levers that make partners produce.** Underwriting, approval rates, advisor speed and
   commission payment are all 7FF's, and the agreement holds 7FF to no standard on any of them.
4. **The list is a compliance liability before it's an asset.** Consent provenance, reassigned numbers, 7FF's own
   parallel messaging, and partners' outreach to their own leads all sit on it.
5. **Reactivation is the one chance to re-paper every partner who answers.** Fresh consent, current terms, the
   W-9 and Everee, corrected contact details, and a working link.
6. **The case study is the real prize.** It needs a holdout and a clean ledger from wave 1, and neither can be
   rebuilt afterward.
7. **Engagement isn't production.** A complete profile and a revenue plan aren't a deal, and the current
   lifecycle rewards conversation.
8. **Our incentives drift from 7FF's at specific points.**
   - Tier upgrades cut our share.
   - Recruits and active partners earn us nothing.
   - Free partners pay us the most.
9. **Merchant data will flow through us.** "Send the file" and calls make us a service provider under 7FF's
   data-security duties, and the agreement has no security or breach-notice terms.
10. **Audience beats count.** A coach with a 3,000-person list is worth more than ten one-off referrers. Ask about
    audience size, and offer "we'll write the email to your client list".
11. **Ask the 50 active partners first.** Interview a handful before the pilot: why they send, what almost made
    them stop, and the words they use.
12. **Borrow trust for top producers.** A short intro from Ty before Justin's first text. Brief 7FF's front desk,
    because partners will call the main line asking who Justin is.
13. **Sender reputation.** It is shared with 7FF if the program uses 7FF's A2P brand or number. Thousands of
    near-identical texts from one 10DLC number get carrier-filtered, so vary content by segment and pace the
    sends.
14. **Approvals cover message text, not targeting.** Every card should show who was excluded and why.
15. **One manager is a single point of failure.** Every "call today" depends on one person, while the
    performance pay arrives only after funding, month end and the 15-day payment term.

---

## 6. Questions for 7FF

**Ty (commercial)**
- What is our share calculated on: fee collected, net of the partner's commission, net of refunds? Is it paid on
  submission or on collected funding? How are clawbacks handled?
- Which tier applies after a partner changes tier? Do Funding Machine purchases count?
- What attribution window applies per partner, and does it survive termination?
- What result at the 90-day review means continue?
- Will 7FF fund a reactivation bonus, and does it reduce the basis?
- Are new partners and the ~50 active partners in scope?
- Who is the partner lead, and what turnaround will they commit to on approvals?
- Will Morgan stay off in-scope partners during the program?

**Partner program and support**
- Who talks to partners today, and will they pause program outreach to in-scope partners?
- Do partners have assigned managers in Zoho? Who signs the kickoff?
- Is there a list of known grievances, open commission disputes, banned partners or partners in litigation?
- Is there a partner agreement beyond the signup terms? Is there a deal-registration rule?
- What are the tiers (paid memberships? commission levels?) and what does each get?
- Is the My Funding Machine Skool group the partner community? Who runs trainings today?

**Commissions and Everee**
- What is the commission schedule by tier and product, and when is a commission earned?
- How many partners have forfeited or unclaimed commissions under the 6-month rule?
- Can the manager see a partner's commission ledger and payout status?
- Are there clawbacks? When is the W-9 collected, and who issues 1099s?

**Funding operations and underwriting**
- Where does a warm handoff go, and how is the partner's referral ID stamped on it?
- What is the standard time for contacting the merchant? Do the Partner CRM and the Slack deal updates work today?
- What are the partner-facing criteria and restricted industries? Can decline reasons be shared with the partner?
- What are submission-to-funded conversion and typical funding time by product?

**Brock (tech and data)**
- Which Zoho fields hold tier, plan, deals, assigned manager, SMS consent (source, date, wording) and referral ID?
  Which system is the source of truth for referral IDs and commissions?
- Can you send a regular export of submissions and statuses by partner ID?
- Can Zoho, Morgan and 7FF's campaigns take in our do-not-contact list?
- Which records are duplicates, which partners are terminated, and which must stay in Zoho?
- Which legal entity is the A2P registration under? Can call recording and transcription be turned on? Which video
  recorder do you use?
- In what format do you want the data export when the agreement ends?

**Compliance and counsel**
- What consent wording, sender and numbers does the partner list's consent cover, and does it cover marketing
  texts from a new number?
- Do you scrub against the FCC Reassigned Numbers Database?
- Which state texting laws and frequency limits does 7FF apply?
- Are referral partners brokers or finders under the state commercial-financing laws? Who handles registration and
  disclosures?
- What claims and FTC disclosure language may partners use? Are there extra rules for credit-repair partners?
- What are 7FF's positions on indemnity and insurance, vendor security requirements, and breach notice?
