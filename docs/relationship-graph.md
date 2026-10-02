# The relationship graph

How the Funding Affiliate Manager gets to know each of 7FF's partners, and uses what it knows to restart and
keep the relationship. Prepared for 7 Figures Funding by Justin Bellware, October 2026.

The interactive version, with a worked example and the simulation, is `docs/relationship-example.html` (also the
"Relationship graph" tab of the demo pack).

## The idea

Before anyone texts a partner, their record becomes a profile: who they are, who their clients are, what their
clients need, what they want, what was promised. Every message is written from that profile, and every reply and
every recorded call adds to it. A person approves every message. Over time each partner's profile turns into a
plan for getting them sending deals, and the program as a whole becomes something 7FF can see and search.

## What the agent knows about a partner

| | What | Where it comes from |
|---|---|---|
| Who they are | tier, plan, when they joined, deals sent and the last one, where they came from, their manager | the partner record (Zoho), at import |
| What they do | their line of work, who their clients are, what those clients need, typical deal size, where they work | record notes, replies, calls |
| What they want | goals in their own words, what would help, what has gotten in the way | replies, calls |
| How to reach them | text, call or email, and the best time | replies, calls |
| Open loops | every promise either side made, with a due date | replies, calls |
| Revenue plan | who they serve, which 7FF programs fit, the next 30 days | written after the first call |

Every fact keeps its source and date. The profile is "complete" when the ten things a manager most needs are known
(tier, line of work, goals, clients, what would help, what their clients need, channel, deal size, region, best
time). When something is missing, the next message asks for it, one question at a time.

## Where it lives

1. **An Obsidian vault.** One note per partner, linked to hub notes for their tier, line of work, manager, source
   and the products their clients need. Obsidian's graph view shows the program clustered by those links. Call
   notes, review files for every batch of messages, and a daily log sit alongside. A `Manager notes` section in each
   partner note belongs to the manager; the agent reads it and never edits it.
2. **An index** in the agent's database: facts, interactions and links, for questions like "Executive partners
   whose clients need equipment financing" and for ordering the kickoff waves. It can be rebuilt from the notes.
3. **GoHighLevel fields** on every contact: tier, a short profile summary, completeness, the next step, and a link
   to the note, so the team works from the same picture.

The vault is 7FF's data. It is kept separate from any other client's, synced to a private repository, and deleted
when the agreement ends, as the agreement sets out. No graph database or outside service holds partner data.

## How it grows

1. **Import.** Partner records come over from Zoho (read-only). Plain fields go straight into the profile; records
   with real notes get one reading pass. Quiet partners are queued for the kickoff.
2. **The kickoff.** One text to each quiet partner from their named partner manager: a greeting, who is writing
   and why now, one line from their own record (deals sent, tier, how long they've been a partner), and one question,
   a quick call. Two SMS segments at most. Three openers rotate, and the graph tracks which one gets replies. Waves go
   out highest-value partners first, each as a review file listing every text in full; the manager approves the wave
   or holds some back. One gentle nudge after five days, then the normal cadence.
3. **The conversation.** Every new text is read (several in a row count as one), its facts go into the profile, and
   the reply asks the next thing the profile is missing. After a couple of replies it asks for a call; when they say
   yes, it sends the manager's booking link and posts a pre-call brief.
4. **The call.** The recording's transcript comes in, its facts go into the profile, and the promises become open
   loops and tasks for the manager.
5. **The revenue plan.** Who they serve, what their clients need, which 7FF programs fit, the next 30 days. The
   manager walks through it with them.

## Calls, from any recorder

Phone calls through GoHighLevel are read from GoHighLevel's call transcripts (call transcription has to be switched
on for 7FF's sub-account). Video calls are read from whatever 7FF records with: Read.ai, Fathom or another tool's
transcript export (JSON, VTT or plain text) dropped into the agent's call inbox. A dedicated connector for 7FF's
recorder can be added once we know which one it is. A call is matched to its partner by email, then phone, then
name; a call that matches nobody waits for the manager to say who it was. Every recorded call opens with a
recording notice, since Florida and several other states require everyone's consent.

## Who is texting

Messages go out in the partner manager's name and voice, and the manager reads and approves every one, so they are
the manager's messages. They never mention AI, drafting or an assistant. If a partner asks "is this a bot?" or "is
this really Justin?", the agent doesn't answer: the manager gets a task, replies personally, and nothing else is
drafted to that partner until they have.

## What it never stores

Health details, religion, politics, bank or card account numbers, Social Security, EIN or other ID numbers, and
passwords never enter a profile. Personal details are kept only when the partner volunteered them, and are used
only to be warm.

## Tested

- **One partner, start to plan.** A fictional partner, Dana Reyes, run through the real code: a Zoho-style record,
  the kickoff, three replies, a booked call, a recorded call, a revenue plan. Her profile goes from 40% to 100%
  complete, and her note shows where every fact came from.
- **250 quiet partners, 30 days.** The same code on 250 quiet partners with synthetic records: 250 kickoff texts in
  reviewed waves, nudges, replies, calls and plans, with a simulated manager approving every batch. 48 partners
  wrote back and their profiles average 44.2% complete; 8 calls were held and read into the graph (half by phone, half
  by video recorder), and 8 revenue plans were written. 10 opt-outs were honored, and 5 asked "is this a bot?"; each
  went to the manager. Full report: `docs/relationship-simulation.md`.
- Automated tests cover the note, the kickoff limits, every form of STOP, the identity rule, the inbox, the review
  file and holding messages back, and call matching.

The simulation's reply rates come from assumptions, not results; real replies will set them. In it, the reply
doesn't depend on which opener was used, so it shows the tracking works, not which opener wins.

## Cost

The graph's AI use (reading records with history, pulling facts from replies, reading calls, writing revenue plans,
and the profile in every drafting prompt) is priced in `docs/ai-cost-projection.md`, under "The relationship
graph". With it, AI stays inside the starting budget.

## What we need from 7FF

- Read-only Zoho access, after the NDA: partner records, notes, deals and calls.
- The GoHighLevel sub-account and texting number (A2P 10DLC registration), with call recording, the recording
  announcement and call transcription switched on.
- The name of the tool 7FF records video calls with, and if possible one transcript export from it with names
  removed, so the call inbox reads its format exactly.
- Who signs the kickoff: each partner's assigned manager, or one named person for the reactivation.
