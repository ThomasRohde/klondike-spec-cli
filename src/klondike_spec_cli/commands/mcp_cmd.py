"""MCP (Model Context Protocol) command handlers for Klondike Spec CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pith import PithException, echo

from ..mcp_server import MCP_AVAILABLE, generate_mcp_config, generate_vscode_mcp_config, run_server


def mcp_serve(transport: str) -> None:
    """Start the MCP server.

    Args:
        transport: Transport protocol to use (stdio or streamable-http)
    """
    if not MCP_AVAILABLE:
        # Write to stderr since stdout is reserved for MCP protocol in stdio mode
        sys.stderr.write("Error: MCP SDK not installed.\n")
        sys.stderr.write("Install with: pip install 'klondike-spec-cli[mcp]'\n")
        sys.stderr.write("Or: pip install mcp\n")
        raise PithException("MCP SDK not available")

    if transport not in ["stdio", "streamable-http"]:
        raise PithException(f"Invalid transport: {transport}. Use: stdio, streamable-http")

    # For stdio transport, don't write anything to stdout - it's reserved for MCP protocol
    # Write status messages to stderr instead
    if transport == "stdio":
        sys.stderr.write("Starting klondike MCP server (stdio)...\n")
    else:
        echo(f"🚀 Starting klondike MCP server (transport: {transport})...")
        echo("   Press Ctrl+C to stop")
        echo("")

    try:
        run_server(transport=transport)
    except KeyboardInterrupt:
        if transport != "stdio":
            echo("")
            echo("✅ MCP server stopped")


def mcp_install(output: str | None) -> None:
    """Install MCP server configuration for VS Code workspace.

    Args:
        output: Optional output path for config file
    """
    # Default to .vscode/mcp.json in current workspace
    if output:
        output_path = Path(output)
    else:
        output_path = Path.cwd() / ".vscode" / "mcp.json"

    config = generate_vscode_mcp_config(output_path)

    echo("✅ MCP configuration installed")
    echo(f"   📄 Config file: {output_path}")
    echo("")
    echo("📋 MCP Server Configuration:")
    echo(json.dumps(config, indent=2))
    echo("")
    echo("💡 To use with GitHub Copilot:")
    echo("   1. Reload VS Code window (Ctrl+Shift+P → 'Reload Window')")
    echo("   2. The klondike MCP server will be available in Copilot Chat")
    echo("")
    echo("   Tools available: get_features, start_feature, verify_feature, etc.")


def mcp_config(output: str | None) -> None:
    """Generate MCP configuration file.

    Args:
        output: Optional output path for config file
    """
    if output:
        output_path = Path(output)
        generate_mcp_config(output_path)
        echo(f"✅ MCP config written to: {output_path}")
    else:
        config = generate_mcp_config()
        echo(json.dumps(config, indent=2))
