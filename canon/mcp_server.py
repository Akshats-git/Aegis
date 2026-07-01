"""MCP server exposing Canon to coding agents (Claude Code / Codex / Cursor).

Run:  python -m canon.mcp_server
Then register it in your agent's MCP config. The two tools below are the agent-facing
surface: one read (recall current truth) and one write (report an outcome -> improve()).

This file degrades gracefully: if the `mcp` package isn't installed yet it prints the
tool contract so you can see the shape without the dependency.
"""

from __future__ import annotations

from .memory import get_memory
from .ingest import ingest_all
from .schema import Status

_mem = get_memory()
ingest_all(_mem)


def recall_canon(topic: str) -> dict:
    """Return the CURRENT canonical decision/API for a topic, plus retired alternatives.

    A coding agent calls this before acting, so it never resurfaces a reversed decision
    or a removed API.
    """
    current = _mem.recall(topic)
    return {
        "topic": topic,
        "current": [n.model_dump() for n in current],
        "note": "Only ACTIVE canon is returned; superseded/removed items were forget()-en.",
    }


def report_outcome(node_id: str, success: bool) -> dict:
    """Feedback hook: tests passed / decision upheld in review -> improve() the edge."""
    _mem.improve(node_id, success)
    return {"node_id": node_id, "success": success, "status": "weight updated"}


def main() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print("mcp not installed. Tool contract:")
        print("  recall_canon(topic: str) -> current canonical truth")
        print("  report_outcome(node_id: str, success: bool) -> improve() the graph")
        return

    server = FastMCP("canon")
    server.tool()(recall_canon)
    server.tool()(report_outcome)
    server.run()


if __name__ == "__main__":
    main()
