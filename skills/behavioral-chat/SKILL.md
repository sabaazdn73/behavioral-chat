---
name: behavioral-chat
description: Analyze a two-person Telegram or WhatsApp chat export for behaviour patterns, measuring every factor for both people the same way. Use when someone shares a chat export and wants to understand the dynamics of a relationship with a partner, friend, family member or colleague.
---

# Behavioral Chat

Read-only, symmetric analysis of a chat between two people. The goal is clarity, not a verdict:
every factor is measured for both people the same way, interpretations are hypotheses with
evidence on both sides, and nobody gets a diagnosis.

## 1. Get the data

The user must supply an export of a chat they took part in. Never try to log in to a messaging
account or read someone else's chats.

- Telegram: Telegram Desktop → open the chat → ⋮ → Export chat history → "Machine-readable JSON"
  (HTML also works). Mobile apps can't export.
- WhatsApp: open the chat → ⋮ / contact name → Export chat → "Without media" → a `_chat.txt` or `.zip`.

Then run the analysis in whichever way is available:

1. **Behavioral Chat connector or local MCP server is connected** → call `analyze_chat_file` (local
   path) or `analyze_chat_text` (export text).
2. **No connector, but you can run code and the file is uploaded** → run the bundled script:
   ```bash
   python scripts/run_analysis.py <uploaded file or folder> --type love --json /tmp/bc.json
   ```
   Add `--html report.html` for a page with English charts. If `bs4` is missing for a Telegram HTML
   export, `pip install beautifulsoup4` or ask for the JSON export instead.

## 2. Settle three things before interpreting

- **Relationship type**: love, friends, family, colleagues or other. It decides which categories
  are counted (for example "sexual or body-focused" and "requests to see" only exist for romantic).
  Ask if it is not obvious.
- **Who is the user**: which of the two senders they are, so you can speak to them directly.
- **Their question**: what they want to understand (where it is going, what the other person wants,
  why they feel a certain way). Shape the answer around it.

The user can add their own keywords per category: `extra_keywords={"warmth": ["..."]}` in the MCP
call, or `--keywords keywords.json` with the script. Both people get the same keywords. Mention this
if the default categories miss something that matters to them.

## 3. Read the numbers

Start from `totals`, then `weekly`, then the rest:

- **Totals per person**: messages, characters, questions, media (and timed media), restarts after a
  silence, reply median and share of slow replies, and one count per behaviour category.
- **Weekly series**: how each category moved over time. Look for a week where something starts,
  peaks or disappears.
- **Alignment** (0–100): warm messages ÷ (warm + tension), both people combined.
  **Balance** (0–100): how even the two people's messages, questions and warm messages were.
- **Trend**: `weekly_factor` < 1 means the conversation is shrinking; compare the two people.
- **Correlations**: e.g. "on days A asked to see more, B sent more media" (daily, r ≥ 0.4). These
  are co-movements, not causes.
- **Emerging words**: words nobody used in week 1 that one person started using later, with the
  date. Often the clearest sign of where the conversation went.
- **Examples**: up to two short messages per category per person. Use them as evidence, read them
  in context, and drop any that the keyword matched by mistake.

Keyword matching is approximate: it misses sarcasm, tone and anything inside photos or voice notes,
and it can match a word that is being objected to. Say so once, plainly.

## 4. Write the interpretation

Answer in the user's language. Keep it warm and direct. Structure:

1. **What the numbers show**: three to five observations, each with the figure for BOTH people.
2. **Side by side**: a short table of factors with one column per person. Every factor you mention
   for one person gets the same factor for the other — goal as it appears, how "no" is handled,
   affection, requests, labeling of the other, self-disclosure, consistency of words and actions,
   investment over time.
3. **What each person seems to be after**: the most likely goal for each, with evidence for and
   evidence against, and how confident you are.
4. **Where it may be heading**: the trend and the three scenario levels for alignment (same pattern,
   early pattern returns, tension drops 80%). Call them scenarios, never predictions.
5. **One or two concrete suggestions** the user can act on, if they asked for advice.

## 5. Rules that always apply

- **Symmetry**: if a measure is shown for one person, show it for the other, even when it is zero.
- **Hypotheses, not diagnoses**: no personality types, disorders or labels like "narcissist" or
  "toxic". Describe behaviour and what it may mean.
- **Respect both people**: the other person isn't present. Be fair to them, and leave out their
  phone number, address, surname and any explicit content unless the user needs it.
- **Safety**: if the chat shows threats, coercion, blackmail, pressure to send intimate images,
  or controlling behaviour, say so clearly and point to local support services. If the user
  seems at risk, that comes before the analysis.
- **Consent and scope**: only analyze chats the user was part of. Decline to help someone monitor a
  partner's or anyone else's private conversations.
- **No pressure tactics**: don't help the user, or anyone, use the results to manipulate the other
  person.

## 6. Optional: a report page

If the user wants something to keep, generate the HTML report (charts in English) with
`scripts/run_analysis.py ... --html report.html`, or build a page from the JSON yourself with one
colour per person, the totals as side-by-side bars, weekly lines, alignment and balance with the
scenario levels, slow replies, and the emerging-words tables.
