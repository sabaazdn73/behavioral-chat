"""Command line: analyze an export on your own computer and write JSON and/or an HTML report.

    behavioral-chat analyze ~/Downloads/Telegram\\ Desktop/ChatExport --type romantic --html report.html
"""
from __future__ import annotations

import argparse
import json
import sys

from .analyze import analyze
from .parsers import ParseError, parse_path
from .report import render_html


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="behavioral-chat")
    sub = ap.add_subparsers(dest="cmd", required=True)
    an = sub.add_parser("analyze", help="Analyze a chat export")
    an.add_argument("path", help="Telegram export folder/result.json/messages.html, or WhatsApp _chat.txt/.zip")
    an.add_argument("--type", default="romantic", choices=["love", "romantic", "friends", "friendship", "family", "colleagues", "work", "other"])
    an.add_argument("--participants", nargs=2, metavar=("PERSON_A", "PERSON_B"))
    an.add_argument("--chat-name", help="Chat to pick from a full-account Telegram JSON export")
    an.add_argument("--keywords", help='JSON file {"category": ["word", ...]} added for both people')
    an.add_argument("--json", dest="json_out", help="Write the full result as JSON")
    an.add_argument("--html", dest="html_out", help="Write an HTML report with charts")
    args = ap.parse_args(argv)
    try:
        msgs = parse_path(args.path, args.chat_name)
        extra = None
        if args.keywords:
            with open(args.keywords, encoding="utf-8") as fh:
                extra = json.load(fh)
        res = analyze(msgs, args.type, args.participants, extra_keywords=extra, include_daily=True)
    except (ParseError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=1)
    if args.html_out:
        with open(args.html_out, "w", encoding="utf-8") as fh:
            fh.write(render_html(res))
    if not args.json_out and not args.html_out:
        json.dump(res, sys.stdout, ensure_ascii=False, indent=1)
    else:
        a, b = res["meta"]["participants"]
        print(f"{res['meta']['messages_analyzed']} messages between {a} and {b} analyzed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
