"""
Outline MCP Server

A Model Context Protocol server for Outline note app, focused on reading documents.
"""

__version__ = "0.1.0"
__author__ = "Outline MCP Server Contributors"
__email__ = "your.email@example.com"
__license__ = "MIT"

from .outline_mcp_server import mcp


def main():
    """Entry point for the MCP server."""
    mcp.run()


__all__ = ["mcp", "main"]
