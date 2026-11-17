<p align="center"><img src="assets/logo.png" alt="Behavioral Chat logo: two people talking" width="128"></p>

# Behavioral Chat

**For love, friends, family and colleagues: read-only, symmetric behaviour analysis of two-person
Telegram and WhatsApp chats.**

This is the Claude directory plugin. It contains one skill, `behavioral-chat`, made of instructions
and data only: a written method (`skills/behavioral-chat/references/method.md`) and keyword lists in
Persian, Finglish and English (`skills/behavioral-chat/references/lexicons.json`).

## What it does

You export a chat you took part in (Telegram Desktop or WhatsApp "Export chat") and upload it to
Claude. Claude follows the method to measure how both people behave over time: affection, care,
appreciation, requests, boundaries, labeling of the other, apologies, plans, endings, and
categories specific to the relationship type. Every factor is measured for both people the same
way. You get per-person totals, weekly series, reply times, an alignment index (warm vs tension),
a balance index, a volume trend with scenarios, correlations, emerging words and a written
interpretation with evidence on both sides.

Relationship types: romantic, friendship, family, work, other.

## What runs, and what it connects to

- The plugin ships no code, no MCP server and no hooks.
- Claude reads only the export you upload and does the counting with its own code tool, inside
  your conversation. Nothing is sent to the author or to any other service.
- No messaging-account login, and no message is ever sent, edited or deleted.

## Limits and responsible use

- Keyword matching is approximate. It misses sarcasm, tone and what is inside photos, videos and
  voice notes. Results are evidence for hypotheses, never a diagnosis of anyone.
- Only analyze chats you took part in. Do not use this to monitor someone else's conversations.
- The other person is not present: be fair to them.

## Privacy Policy

Behavioral Chat processes only the chat export the user supplies, inside the user's own Claude
conversation, to compute the analysis shown there. The plugin has no server, stores nothing,
collects nothing and shares nothing; there are no accounts, cookies, analytics or third parties.
Chat exports contain personal data of a second person, and users are responsible for having a
lawful reason to process it. Contact: sabaazad93@gmail.com

## Source, contact and contributing

The open-source engine, a local MCP server and a command-line tool live in the same repository:
https://github.com/sabaazdn73/behavioral-chat

Questions, feedback, new languages or keyword lists, and collaboration on further development:
**Saba Azadegan — sabaazad93@gmail.com**.

## License

MIT
