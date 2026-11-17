"""Entry point used by the plugin's .mcp.json: runs the read-only Behavioral Chat MCP server over stdio."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from behavioral_chat.server import main  # noqa: E402

if __name__ == "__main__":
    main()
