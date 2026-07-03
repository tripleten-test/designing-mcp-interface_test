"""
server.py — Entry point for the git-activity-analyzer MCP server.

Importing `app` registers the three resources and the prompt template.
Importing `tools` (which itself does `from app import server`) registers
the two tools.  Both imports are intentional side-effect imports.

Run with:
    python server.py          # stdio transport (default, for local MCP clients)
    python server.py --sse    # SSE transport (for remote / browser clients)
"""

import app   # noqa: F401 — registers resources and prompt
import tools  # noqa: F401 — registers tools

from app import server

if __name__ == "__main__":
    server.run()
