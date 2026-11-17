<p align="center"><img src="assets/logo-512.png" alt="Behavioral Chat logo: two people talking" width="128"></p>

# Behavioral Chat

**For love, friends, family and colleagues: read-only, symmetric behaviour analysis of two-person chats.**

Behavioral Chat reads a chat export you made yourself (Telegram or WhatsApp) and measures how
both people behave over time: affection, care, requests, boundaries, labeling of the other,
apologies, plans, endings, and categories specific to the relationship type. Every factor is
measured for **both** people the same way, so the picture is fair to each side.

It ships in three forms that share one engine:

| Form | Where it runs | Use it when |
|---|---|---|
| **Claude plugin** (this repository) | Claude Code, Claude Desktop, Cowork | One install: the skill plus the local MCP server |
| **MCP server** (`behavioral-chat-mcp`) | Claude Desktop, Claude Code, any MCP client | You want Claude to analyze an export on your computer |
| **Remote connector** (same server over HTTPS) | claude.ai, Claude mobile, Claude Desktop | You host it and list it in the Connectors Directory |
| **Skill** (`skills/behavioral-chat`) | claude.ai, Claude Desktop, Claude Code | No server: Claude runs the bundled script on an uploaded export |

## Read-only by design

- No messaging-account login. No Telegram API, no WhatsApp API.
- No tool can send, edit, forward or delete a message, or change anything anywhere.
- No network calls, no database, no logs of chat content.
- Every tool is annotated `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`.
- The file tool only exists when the server runs on the user's own computer (stdio), only reads
  chat-export file types (`.json .html .htm .txt .zip`), and can be limited to chosen folders with
  `BC_ALLOWED_DIRS`.

## Tools

| Tool | What it does |
|---|---|
| `analyze_chat_text` | Analyze export text (WhatsApp `_chat.txt`, Telegram `result.json`, or a Telegram `messages.html` page) |
| `analyze_chat_file` | Local only. Analyze an export folder or file on this computer |
| `list_relationship_types` | Show every relationship type, category and keyword used |

Arguments: `relationship_type` (`love`/`romantic`, `friends`/`friendship`, `family`, `colleagues`/`work`, `other`),
`participants` (two sender names, defaults to the two most active), `chat_name` (for full-account
Telegram exports), `extra_keywords` (`{category: [words]}`, applied to both people),
`include_daily`.

### What comes back

- `totals` per person: messages, characters, questions, media (and timed media), restarts after a
  silence, median reply time, share of replies slower than an hour, share of messages sent off-hours,
  and a count for every behaviour category.
- `weekly`: the same per week, plus messages per day, **alignment** (warm ÷ warm + tension, both
  people) and **balance** (how even the two people were).
- `trend`: exponential fit of weekly volume per person, with a four-week extension.
- `scenarios`: alignment levels if the recent pattern continues, if the early pattern returns, or if
  tension drops 80%. Scenarios, not predictions.
- `correlations_between_people` and `correlations_within_person` (daily, |r| ≥ 0.4 / 0.5).
- `emerging_words`: words nobody used in week 1 that one person started using later.
- `category_first_use`, `examples` (two short messages per category per person) and `method`.

### Categories by relationship type

| Type | Categories |
|---|---|
| romantic | warmth, care, appreciation, commitment, plans, requests, requests to see/hear, sexual or body-focused, refusals & boundaries, labeling the other, jealousy & checking up, apology, endings |
| friendship | warmth, care, support, humor, appreciation, plans, requests, refusals, labeling, apology, endings |
| family | warmth, care, support, appreciation, plans, requests, obligation & guilt, refusals, labeling, apology, endings |
| work | appreciation, care, tasks & deadlines, requests, refusals, blame & criticism, labeling, apology, plans |

Keywords cover Persian (colloquial), Finglish and English. Persian/Arabic letter variants,
diacritics, zero-width joiners and stretched letters (جووووون) are normalized first. A message that
sets a boundary *about* sexual content or photos counts as a boundary, not as sexual content.

## What runs, and what it connects to

- The plugin starts the local MCP server with `uv run --frozen` from `server.py` in this folder.
  On first start, `uv` installs the Python dependencies pinned in `uv.lock` (`mcp`,
  `beautifulsoup4` and their dependencies) from PyPI. That is the only network access, and it
  happens before any chat is read.
- After that, the server reads only the export file you point it to and returns numbers. It makes
  no network requests and writes nothing to disk.
- The skill's `scripts/run_analysis.py` runs the same engine on an uploaded file, also without
  network access. It writes a JSON or HTML file only where you ask it to.

## Install

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/) for the plugin.

```bash
pip install git+https://github.com/sabaazdn73/behavioral-chat@v0.1.0
# or run without installing:
uvx --from git+https://github.com/sabaazdn73/behavioral-chat@v0.1.0 behavioral-chat-mcp
```

**Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "behavioral-chat": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/sabaazdn73/behavioral-chat@v0.1.0", "behavioral-chat-mcp"],
      "env": { "BC_ALLOWED_DIRS": "~/Downloads" }
    }
  }
}
```

**As a Claude plugin (skill + local server)**: once it is listed in the directory, add it from
Customize in Claude. Until then, use the server or the skill as described below.

**Claude Code (server only)**:

```bash
claude mcp add behavioral-chat -- uvx --from git+https://github.com/sabaazdn73/behavioral-chat@v0.1.0 behavioral-chat-mcp
```

**Remote connector** (streamable HTTP, stateless; put it behind HTTPS):

```bash
BC_TRANSPORT=http BC_HOST=0.0.0.0 BC_PORT=8000 behavioral-chat-mcp   # endpoint: /mcp
```

In remote mode only `analyze_chat_text` and `list_relationship_types` exist. Exports up to 4 MB
(`BC_MAX_TEXT_BYTES`).

**Skill only** — zip the `skills/behavioral-chat` folder and upload it in Claude under
Customize → Skills. Run `python build_skill.py` first so the engine is copied into the skill's
`scripts/` folder.

**Command line**:

```bash
behavioral-chat analyze ~/Downloads/ChatExport --type romantic --html report.html
```

## How to export a chat

- **Telegram**: Telegram Desktop (from desktop.telegram.org) → open the chat → ⋮ → Export chat
  history → untick media → format "Machine-readable JSON". The mobile apps and the App Store macOS
  app can't export.
- **WhatsApp**: open the chat → ⋮ (Android) or the contact name (iPhone) → Export chat → Without
  media. WhatsApp caps exports at roughly 40,000 messages.

## Limits and responsible use

- Keyword matching is approximate. It misses sarcasm, tone and what is inside photos, videos and
  voice notes. Treat results as evidence for hypotheses, not as facts about anyone.
- Only analyze chats you took part in. Do not use this to monitor someone else's conversations.
- The other person is not present. Results should be shared and discussed with that in mind.
- No diagnoses: the tool measures behaviour, it does not label people.

## Privacy Policy

Behavioral Chat processes only the chat export the user supplies, only to compute the analysis that
is returned in the same request.

- **Local server and Skill**: data stays on the user's device or in their Claude session. Nothing is
  sent anywhere by Behavioral Chat.
- **Remote connector**: the export text is received over HTTPS, analyzed in memory, and discarded
  when the response is sent. It is not written to disk, logged, used for training, or shared. Server
  access logs contain no message content.
- No accounts, cookies, analytics or third-party processors.
- Chat exports contain personal data of a second person. Users are responsible for having a lawful
  reason to process it; operators of a hosted instance in the EU act as data processors under GDPR
  and should publish their own contact details here.
- Contact: sabaazad93@gmail.com

## Contact and contributing

Questions, feedback, new languages or keyword lists, and collaboration on further development:
**Saba Azadegan — sabaazad93@gmail.com**. Issues and pull requests are welcome.

## License

MIT
