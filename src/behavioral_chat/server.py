"""Behavioral Chat MCP server.

Read-only by design: every tool only reads a chat export the user provides
and returns numbers. There is no messaging-account login, no sending,
editing or deleting of messages, no network access and no storage.

Run locally (Claude Desktop / Claude Code):   behavioral-chat-mcp
Run as a remote connector (streamable HTTP):   BC_TRANSPORT=http behavioral-chat-mcp
"""
from __future__ import annotations

import os

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from . import __version__, lexicons
from .analyze import analyze
from .parsers import ParseError, parse_path, parse_text

MAX_TEXT_BYTES = int(os.environ.get("BC_MAX_TEXT_BYTES", 4_000_000))
TRANSPORT = os.environ.get("BC_TRANSPORT", "stdio").lower()
# Reading files from disk is only offered when the server runs on the user's own machine.
ALLOW_FILES = os.environ.get("BC_ALLOW_FILES", "1" if TRANSPORT == "stdio" else "0") == "1"
ALLOWED_DIRS = [os.path.abspath(os.path.expanduser(d)) for d in os.environ.get("BC_ALLOWED_DIRS", "").split(os.pathsep) if d]

INSTRUCTIONS = """\
Behavioral Chat (for love, friends, family and colleagues) analyzes a two-person chat export (Telegram or WhatsApp) and returns symmetric behaviour
metrics: every category is measured for BOTH people the same way. All tools are read-only.

When you present results:
- Ask (or infer from the user) the relationship type: love, friends, family, colleagues or other.
- Treat both people the same. For every factor you mention for one person, give the same factor for the other.
- Offer hypotheses, never diagnoses. Do not label either person with a disorder or personality type.
- Give evidence for AND against each interpretation, using the counts, weekly trends and examples.
- Scenarios are levels of the alignment index under stated assumptions, not predictions.
- Keyword matching misses sarcasm and media; say the numbers are approximate.
- If the chat shows signs of coercion, threats, or abuse, say so plainly and point to local support services.
- Do not repeat phone numbers, addresses or explicit content from the examples unless the user asks.
"""

READ_ONLY = ToolAnnotations(
    title=None, read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
)

mcp = MCPServer(
    name="behavioral-chat",
    title="Behavioral Chat",
    description="Read-only, symmetric behaviour analysis of two-person Telegram and WhatsApp chat exports.",
    instructions=INSTRUCTIONS,
    version=__version__,
)

TYPES_DOC = ", ".join(lexicons.TYPES)


def _run(messages, relationship_type, participants, extra_keywords, include_daily):
    if not messages:
        raise ToolError("No messages found in this export.")
    try:
        return analyze(
            messages,
            relationship_type=relationship_type,
            participants=participants,
            extra_keywords=extra_keywords,
            include_daily=include_daily,
        )
    except ValueError as e:
        raise ToolError(str(e)) from e


@mcp.tool(
    title="Analyze chat export (text)",
    annotations=READ_ONLY.model_copy(update={"title": "Analyze chat export (text)"}),
)
def analyze_chat_text(
    content: str,
    relationship_type: str = "romantic",
    format: str = "auto",
    participants: list[str] | None = None,
    chat_name: str | None = None,
    extra_keywords: dict[str, list[str]] | None = None,
    include_daily: bool = False,
) -> dict:
    """Analyze the text of a chat export and return symmetric behaviour metrics for both people.

    content: the full export text — WhatsApp "_chat.txt", Telegram Desktop "result.json", or one Telegram
      "messages.html" page.
    relationship_type: love (romantic), friends (friendship), family, colleagues (work) or other. Decides which behaviour categories
      are counted (for example "sexual" and "requests to see" only for romantic).
    format: auto, whatsapp, telegram_json or telegram_html.
    participants: the two sender names to compare; defaults to the two most active senders.
    chat_name: for a full-account Telegram JSON export, the name of the chat to analyze.
    extra_keywords: optional {category: [keywords]} to add to or create categories, applied to both people.
    include_daily: also return day-by-day series (larger output).
    """
    if len(content.encode("utf-8")) > MAX_TEXT_BYTES:
        raise ToolError(f"Export is larger than {MAX_TEXT_BYTES // 1_000_000} MB; export without media or a shorter range.")
    try:
        msgs = parse_text(content, format, chat_name)
    except ParseError as e:
        raise ToolError(str(e)) from e
    return _run(msgs, relationship_type, participants, extra_keywords, include_daily)


if ALLOW_FILES:

    @mcp.tool(
        title="Analyze chat export (file on this computer)",
        annotations=READ_ONLY.model_copy(update={"title": "Analyze chat export (file on this computer)"}),
    )
    def analyze_chat_file(
        path: str,
        relationship_type: str = "romantic",
        participants: list[str] | None = None,
        chat_name: str | None = None,
        extra_keywords: dict[str, list[str]] | None = None,
        include_daily: bool = False,
    ) -> dict:
        """Read a chat export from this computer and return symmetric behaviour metrics for both people.

        path: a Telegram Desktop export folder (with messages.html or result.json), a result.json, a
          messages.html, a WhatsApp _chat.txt, or the WhatsApp export .zip. Only these export file types are read.
        relationship_type: love (romantic), friends (friendship), family, colleagues (work) or other.
        participants: the two sender names to compare; defaults to the two most active senders.
        chat_name: for a full-account Telegram JSON export, the chat to analyze.
        extra_keywords: optional {category: [keywords]} added for both people.
        include_daily: also return day-by-day series (larger output).
        """
        full = os.path.abspath(os.path.expanduser(path))
        if ALLOWED_DIRS and not any(full == d or full.startswith(d + os.sep) for d in ALLOWED_DIRS):
            raise ToolError("This path is outside the folders allowed in BC_ALLOWED_DIRS.")
        if not os.path.exists(full):
            raise ToolError(f"Not found: {path}")
        try:
            msgs = parse_path(full, chat_name)
        except ParseError as e:
            raise ToolError(str(e)) from e
        return _run(msgs, relationship_type, participants, extra_keywords, include_daily)


@mcp.tool(
    title="List relationship types and keywords",
    annotations=READ_ONLY.model_copy(update={"title": "List relationship types and keywords"}),
)
def list_relationship_types() -> dict:
    """List the relationship types, their behaviour categories, and every keyword used, so results are transparent."""
    return {"relationship_types": lexicons.describe(), "how_to_extend": "Pass extra_keywords={category: [words]}."}


def main() -> None:
    if TRANSPORT in ("http", "streamable-http"):
        mcp.run(
            "streamable-http",
            host=os.environ.get("BC_HOST", "127.0.0.1"),
            port=int(os.environ.get("BC_PORT", "8000")),
            stateless_http=True,
            json_response=True,
            max_request_body_size=MAX_TEXT_BYTES + 200_000,
        )
    else:
        mcp.run("stdio")


if __name__ == "__main__":
    main()
