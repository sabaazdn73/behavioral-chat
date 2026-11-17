# Behavioral Chat — method

This is the exact method behind every number. Compute it with your own code tool on the export the
user uploaded, then report it. Use the keyword lists in `lexicons.json` (same folder). If you cannot
run code, say so and give only a qualitative reading, clearly labelled as such.

## 1. Read the export into messages

Each message becomes: sender, timestamp (local time as written in the export), text, media kind
(photo, video, voice, sticker, gif, audio, file, media or none) and a "timed" flag (self-destructing
or view-once media).

**Telegram, JSON (`result.json`)**

- A single-chat export has a top-level `messages` list. A full-account export has
  `chats.list`: ask which personal chat to use (match its `name`).
- Keep entries whose `type` is `"message"`. Sender is `from` (or `actor`), timestamp is `date`
  (ISO format).
- `text` is either a string or a list mixing strings and objects with a `text` field: join them.
- Media: `photo` present → photo. `media_type`: `voice_message` → voice, `video_message` and
  `video_file` → video, `animation` → gif, `sticker` → sticker, `audio_file` → audio, anything else
  → media. Otherwise a `file` field → file.
- Timed: the entry has `self_destruct_period_seconds`.

**Telegram, HTML (`messages.html`, `messages2.html`, …)**

- Read every page in natural order (messages, messages2, …, messages10).
- Each `div.message` that is not a `service` message is one message. The timestamp is the
  `title` of `div.date`, written `dd.mm.yyyy HH:MM:SS`.
- The sender is the text of `div.from_name`. Consecutive messages from the same person ("joined"
  messages) have no `from_name`: reuse the last sender. Ignore a `from_name` inside a
  `div.forwarded` block.
- Text is `div.text`. Media comes from `div.media_wrap`: its label or link mentions photo, video,
  voice, sticker or animation/gif; otherwise media. Timed when the label says "self-destructing".

**WhatsApp (`_chat.txt`, or the `.zip` WhatsApp makes)**

- A new message starts with a date and time:
  - iPhone: `[d/m/yy, h:mm:ss AM] Name: text`
  - Android: `d/m/yy, h:mm - Name: text`
  Separators may be `/`, `.` or `-`; seconds and AM/PM are optional; a left-to-right mark may come
  first. Any other line continues the previous message.
- Work out the date order from the whole file: if any first number is above 31 the order is
  year-month-day; else if any first number is above 12 it is day-month-year; else if any second
  number is above 12 it is month-day-year; otherwise assume day-month-year. Two-digit years are
  20xx. Convert AM/PM to 24-hour time.
- A line with a date but no `Name: ` part is a system notice (encryption notice, someone joined):
  skip it.
- Media placeholders ("<Media omitted>", "image omitted", "video omitted", "audio omitted",
  "sticker omitted", "GIF omitted", and attached file names ending in .jpg, .mp4, .opus, .webp) set
  the media kind and are removed from the text. "view once" in the text marks it as timed.

## 2. Choose the two people

Use the two senders the user names. Otherwise use the two most active senders and say who they are.
Ignore everyone else and report how many messages were ignored. Sort all messages by time.

## 3. Normalize text before matching

Apply in this order, to a copy of the text (keep the original for quotes and question marks):

1. Unicode NFC.
2. Arabic letter variants to Persian: ي and ى → ی, ك → ک, ة and ۀ → ه, أ, إ and آ → ا.
3. Remove Arabic diacritics (U+064B–U+0652), superscript alef (U+0670) and tatweel (U+0640).
4. Remove zero-width non-joiner and joiner and left-to-right / right-to-left marks.
5. Collapse any character repeated three or more times to one (`soooo` → `so`, `جووووون` → `جون`).
6. Collapse doubled Persian vowels ا, و, ی, ه to one.
7. Lowercase.

Normalize each keyword the same way before matching.

## 4. Count behaviour categories

- Take the categories listed for the relationship type in `lexicons.json`
  (`relationship_types`; `type_aliases` maps love → romantic, friends → friendship,
  colleagues → work). Unknown types use `other`.
- A message belongs to a category when any of its keywords (Persian or Latin list) occurs in the
  normalized text, or any of its emoji occurs in the original text.
- Word boundaries: a Persian keyword must not be preceded by a Persian letter, and must not be
  followed by one unless it ends in `*`. A Latin keyword behaves the same with the letters a–z.
  A space inside a keyword matches one or more whitespace characters.
- One message counts at most once per category, but can count in several categories.
- Special rule: a message in `refusals` is not also counted as `sexual` or `see_request`.
- The user may add keywords to any category (or a new category, group "neutral"). Apply them to
  both people.

## 5. Per-person totals

For each of the two people:

- messages, characters, questions (count of `?` and `؟`), media by kind, media total, timed media
- off-hours share: messages sent on Saturday or Sunday, or before 08:00, or from 20:00, as a % of
  that person's messages
- restarts after silence: messages that come 3 hours or more after the previous message from
  anyone
- replies: when a message follows one from the other person within 24 hours, the gap in minutes is
  a reply time for the sender. Report the median, and the share of replies slower than 60 minutes
- one count per category
- first date each category was used, and up to two short example messages per category (first 90
  characters), to check by eye

## 6. Weekly series and joint indices

- Week 1 starts on the date of the first message; week index = days since that date ÷ 7, rounded
  down. The last week may be shorter: messages per day = messages that week ÷ days in that week.
- For every week and person: messages per day, questions, media, each category, median reply time
  and slow-reply share.
- **Alignment** (0–100) per week: warm ÷ (warm + tension) × 100, where warm is the sum over both
  people of all categories in group "warm" and tension the same for group "tension". Empty when
  both are zero.
- **Balance** (0–100) per week: the mean of min ÷ max between the two people for messages,
  questions and warm-category messages (skip a measure where both are zero), × 100. 100 is perfectly
  even.

## 7. Trend and scenarios

- **Trend** per person: fit a straight line to the natural log of messages per day against the week
  number, using weeks with at least one message (needs three such weeks). The weekly factor is
  e^slope: below 1 means the conversation is shrinking. Extend the line four weeks for a projection.
- **Scenarios** for alignment, never predictions:
  - same pattern: mean alignment of the last three weeks
  - early pattern returns: mean alignment of the first three weeks
  - tension drops 80%: warm ÷ (warm + 0.2 × tension) × 100 over the last three weeks

## 8. Correlations

Build daily series (one value per calendar day from first to last message, zeros included) of
messages and every category for each person.

- Between people: Pearson r between each of person A's series and each of person B's. Keep
  |r| ≥ 0.4, top ten by |r|.
- Within a person: between two different series of the same person. Keep |r| ≥ 0.5, top ten.
- Skip a pair when there are fewer than five days or either series is constant. Describe them as
  things that move together, never as causes.

## 9. Emerging words

- Tokenize the normalized text into runs of Persian letters (U+0600–U+06FF) or a–z. Drop tokens of
  one letter and tokens in `emerging_word_stopwords`.
- For each person, a word is emerging when nobody (neither person) used it in week 1, this person
  first used it in week 2 or later, used it at least 3 times in total, and it has at least 3
  letters.
- Report up to 15 per person, by total use, with the date first seen and the weekly counts.

## 10. Limits to state once

Keyword matching misses sarcasm, tone, context and anything inside photos, videos or voice notes,
and it can match a word that is being quoted or objected to. Read the example messages and discard
matches that are clearly wrong. Treat every result as evidence for a hypothesis, never as a
diagnosis of either person.
