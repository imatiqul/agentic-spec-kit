"""agentic-spec-kit MCP server (Phase 12): read-only answers about a project, over the Model Context Protocol.

Importing this package registers nothing with the core: no check, no command, no hook (MCP-1). The plugin loader
finds it like any other extension, and that is all it does with it. The server is a program of its own,
`scripts/agentic_mcp.py`; only that program imports `protocol` and `tools` (docs/design/mcp-server.md).
"""
__version__ = "0.1.0"
