"""Parse chat exports into a common list of messages.

Supported inputs (all produced by the user, from their own account):
  * Telegram Desktop export, JSON  (result.json, single chat or full account export)
  * Telegram Desktop export, HTML  (messages.html, messages2.html, ... in one folder)
  * WhatsApp "Export chat"          (_chat.txt, or the .zip WhatsApp produces)

Nothing here touches the network or any messaging account.
"""
from __future__ import annotations

import io
import json
import os
import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable

ALLOWED_SUFFIXES = (".json", ".html", ".htm", ".txt", ".zip")


@dataclass
class Message:
    sender: str
    ts: datetime
    text: str = ""
    media: str | None = None  # "photo", "video", "voice", "sticker", "gif", "file", "media"
    timed: bool = False       # self-destructing / view-once media
    extra: dict = field(default_factory=dict)


class ParseError(ValueError):
    pass


# --------------------------------------------------------------------------- telegram json
def _tg_text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        out = []
        for part in value:
            if isinstance(part, str):
                out.append(part)
            elif isinstance(part, dict):
                out.append(part.get("text", ""))
        return "".join(out)
    return ""


def _tg_media(m: dict) -> str | None:
    if "photo" in m:
        return "photo"
    mt = m.get("media_type")
    if mt:
        return {
            "voice_message": "voice",
            "video_message": "video",
            "video_file": "video",
            "animation": "gif",
            "sticker": "sticker",
            "audio_file": "audio",
        }.get(mt, "media")
    if "file" in m:
        return "file"
    return None


def parse_telegram_json(raw: str, chat_name: str | None = None) -> list[Message]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ParseError(f"Not valid JSON: {e}") from e
    chats = []
    if "messages" in data:
        chats = [data]
    elif isinstance(data.get("chats"), dict):
        chats = data["chats"].get("list", [])
    if not chats:
        raise ParseError("No Telegram chat found in this JSON export.")
    if len(chats) > 1:
        if not chat_name:
            names = [c.get("name") for c in chats if c.get("type") == "personal_chat"][:30]
            raise ParseError(
                "This is a full-account export with several chats. Pass chat_name. "
                f"Personal chats found: {names}"
            )
        chats = [c for c in chats if (c.get("name") or "").strip().lower() == chat_name.strip().lower()]
        if not chats:
            raise ParseError(f"No chat named {chat_name!r} in this export.")
    out = []
    for m in chats[0].get("messages", []):
        if m.get("type") != "message":
            continue
        try:
            ts = datetime.fromisoformat(m["date"])
        except (KeyError, ValueError):
            continue
        out.append(
            Message(
                sender=(m.get("from") or m.get("actor") or "unknown").strip(),
                ts=ts,
                text=_tg_text(m.get("text", "")),
                media=_tg_media(m),
                timed="self_destruct_period_seconds" in m,
            )
        )
    return out


# --------------------------------------------------------------------------- telegram html
def parse_telegram_html(pages: Iterable[str]) -> list[Message]:
    try:
        from bs4 import BeautifulSoup
    except ImportError as e:  # pragma: no cover
        raise ParseError("Telegram HTML exports need the 'beautifulsoup4' package.") from e
    out: list[Message] = []
    last_sender = None
    for page in pages:
        soup = BeautifulSoup(page, "html.parser")
        for m in soup.select("div.message"):
            if "service" in (m.get("class") or []):
                continue
            body = m.select_one("div.body")
            if body is None:
                continue
            date_el = body.select_one("div.date")
            title = date_el.get("title", "") if date_el else ""
            mt = re.match(r"(\d{2})\.(\d{2})\.(\d{4}) (\d{2}):(\d{2}):(\d{2})", title)
            if not mt:
                continue
            d, mo, y, hh, mi, ss = map(int, mt.groups())
            ts = datetime(y, mo, d, hh, mi, ss)
            fn = body.select_one("div.from_name")
            if fn is not None:
                # forwarded blocks also carry a from_name; keep only the outer one
                if fn.find_parent("div", class_="forwarded") is None:
                    last_sender = fn.get_text(" ", strip=True)
            txt_el = body.select_one("div.text")
            text = txt_el.get_text("\n", strip=True) if txt_el else ""
            media, timed = None, False
            mw = body.select_one("div.media_wrap")
            if mw is not None:
                label = mw.get_text(" ", strip=True).lower()
                href = (mw.find("a") or {}).get("href", "") if mw.find("a") else ""
                timed = "self-destructing" in label
                if "photo" in label or "photo" in href:
                    media = "photo"
                elif "video" in label or "video" in href:
                    media = "video"
                elif "voice" in label:
                    media = "voice"
                elif "sticker" in href or "sticker" in label:
                    media = "sticker"
                elif "animation" in href or "gif" in href:
                    media = "gif"
                else:
                    media = "media"
            out.append(Message(sender=last_sender or "unknown", ts=ts, text=text, media=media, timed=timed))
    return out


# --------------------------------------------------------------------------- whatsapp txt
_WA_IOS = re.compile(
    r"^‎?\[(\d{1,4})[./-](\d{1,2})[./-](\d{1,4}),?\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([AaPp]\.?[Mm]\.?)?\]\s+(.*)$"
)
_WA_AND = re.compile(
    r"^‎?(\d{1,4})[./-](\d{1,2})[./-](\d{1,4}),?\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([AaPp]\.?[Mm]\.?)?\s+[-–]\s+(.*)$"
)
_WA_MEDIA = [
    (re.compile(r"<media omitted>|<multimedia omitido>|<mídia oculta>", re.I), "media"),
    (re.compile(r"image omitted|imagem omitida|<attached: .*?photo|\.jpe?g", re.I), "photo"),
    (re.compile(r"video omitted|vídeo omitido|\.mp4", re.I), "video"),
    (re.compile(r"audio omitted|áudio omitido|\.opus", re.I), "voice"),
    (re.compile(r"sticker omitted|figurinha omitida|\.webp", re.I), "sticker"),
    (re.compile(r"gif omitted", re.I), "gif"),
]


def _wa_date_order(rows: list[tuple[int, int, int]]) -> str:
    """Return 'dmy', 'mdy' or 'ymd' by looking at all dates in the file."""
    if any(a > 31 for a, _, _ in rows):
        return "ymd"
    if any(a > 12 for a, _, _ in rows):
        return "dmy"
    if any(b > 12 for _, b, _ in rows):
        return "mdy"
    return "dmy"


def parse_whatsapp_txt(raw: str) -> list[Message]:
    raw = raw.replace("\r\n", "\n").replace(" ", " ").replace(" ", " ")
    heads = []
    for line in raw.split("\n"):
        m = _WA_IOS.match(line) or _WA_AND.match(line)
        heads.append(m)
    rows = [(int(m.group(1)), int(m.group(2)), int(m.group(3))) for m in heads if m]
    if not rows:
        raise ParseError("No WhatsApp message lines found.")
    order = _wa_date_order(rows)
    out: list[Message] = []
    cur: Message | None = None
    for line, m in zip(raw.split("\n"), heads):
        if not m:
            if cur is not None:
                cur.text += "\n" + line
            continue
        a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if order == "ymd":
            y, mo, d = a, b, c
        elif order == "mdy":
            mo, d, y = a, b, c
        else:
            d, mo, y = a, b, c
        if y < 100:
            y += 2000
        hh, mi, ss = int(m.group(4)), int(m.group(5)), int(m.group(6) or 0)
        ampm = (m.group(7) or "").lower().replace(".", "")
        if ampm == "pm" and hh < 12:
            hh += 12
        if ampm == "am" and hh == 12:
            hh = 0
        rest = m.group(8)
        if ": " not in rest:  # system line (encryption notice, someone joined, ...)
            cur = None
            continue
        sender, text = rest.split(": ", 1)
        sender = sender.strip().lstrip("‎").strip()
        text = text.lstrip("‎")
        media = None
        for rx, kind in _WA_MEDIA:
            if rx.search(text):
                media = kind
                text = rx.sub("", text).strip()
                break
        timed = "view once" in text.lower()
        try:
            ts = datetime(y, mo, d, hh, mi, ss)
        except ValueError:
            continue
        cur = Message(sender=sender, ts=ts, text=text, media=media, timed=timed)
        out.append(cur)
    for m in out:
        m.text = m.text.strip()
    return out


# --------------------------------------------------------------------------- dispatch
def detect_format(raw: str) -> str:
    s = raw.lstrip()[:2000]
    if s.startswith("{"):
        return "telegram_json"
    if "<html" in s.lower() or 'class="message' in raw[:20000]:
        return "telegram_html"
    return "whatsapp"


def parse_text(content: str, fmt: str = "auto", chat_name: str | None = None) -> list[Message]:
    fmt = detect_format(content) if fmt == "auto" else fmt
    if fmt == "telegram_json":
        return parse_telegram_json(content, chat_name)
    if fmt == "telegram_html":
        return parse_telegram_html([content])
    if fmt == "whatsapp":
        return parse_whatsapp_txt(content)
    raise ParseError(f"Unknown format {fmt!r}")


def _natural_key(name: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name)]


def parse_path(path: str, chat_name: str | None = None) -> list[Message]:
    """Read an export from disk. Accepts a file or a Telegram export folder."""
    path = os.path.abspath(os.path.expanduser(path))
    if os.path.isdir(path):
        htmls = sorted(
            (f for f in os.listdir(path) if re.fullmatch(r"messages\d*\.html", f)), key=_natural_key
        )
        if htmls:
            return parse_telegram_html(open(os.path.join(path, f), encoding="utf-8").read() for f in htmls)
        for cand in ("result.json", "_chat.txt"):
            if os.path.exists(os.path.join(path, cand)):
                return parse_path(os.path.join(path, cand), chat_name)
        raise ParseError("Folder has no messages*.html, result.json or _chat.txt.")
    if not path.lower().endswith(ALLOWED_SUFFIXES):
        raise ParseError(f"Only chat exports are read ({', '.join(ALLOWED_SUFFIXES)}).")
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            txts = [n for n in z.namelist() if n.lower().endswith(".txt")]
            if not txts:
                raise ParseError("No .txt chat inside this zip.")
            with z.open(txts[0]) as fh:
                return parse_whatsapp_txt(io.TextIOWrapper(fh, encoding="utf-8").read())
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    if path.lower().endswith((".html", ".htm")):
        folder = os.path.dirname(path)
        siblings = sorted(
            (f for f in os.listdir(folder) if re.fullmatch(r"messages\d*\.html", f)), key=_natural_key
        )
        if os.path.basename(path) in siblings and len(siblings) > 1:
            return parse_telegram_html(open(os.path.join(folder, f), encoding="utf-8").read() for f in siblings)
    return parse_text(raw, "auto", chat_name)
