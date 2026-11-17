"""Run Behavioral Chat on an uploaded chat export (no MCP server needed).

    python scripts/run_analysis.py <file-or-folder> --type love --json out.json --html report.html
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Uploaded skill zip: the engine is bundled next to this file (see build_skill.py).
# Plugin install from the repository: the engine lives in ../../../src.
for path in (HERE, os.path.normpath(os.path.join(HERE, "..", "..", "..", "src"))):
    if os.path.isdir(os.path.join(path, "behavioral_chat")):
        sys.path.insert(0, path)
        break

from behavioral_chat.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(["analyze", *sys.argv[1:]]))
