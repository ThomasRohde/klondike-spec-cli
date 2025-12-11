"""Tests for klondike MCP server functionality."""

import json
import os
import tempfile
from pathlib import Path

import pytest
from pith.testing import CliRunner

from klondike_spec_cli.cli import app


class TestMcpCommand:
    """Test the mcp command."""

    def test_mcp_config_outputs_json(self):
        """Test that mcp config outputs valid JSON."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Initialize a klondike project first
                runner.invoke(app, ["init"])

                # Generate config to stdout
                result = runner.invoke(app, ["mcp", "config"])

                assert result.exit_code == 0
                # Parse the output as JSON
                output_lines = result.output.strip().split("\n")
                # Find the JSON portion (skip any echo messages)
                json_start = None
                for i, line in enumerate(output_lines):
                    if line.strip().startswith("{"):
                        json_start = i
                        break

                if json_start is not None:
                    json_text = "\n".join(output_lines[json_start:])
                    config = json.loads(json_text)
                    assert "mcpServers" in config
                    assert "klondike" in config["mcpServers"]
                    assert "command" in config["mcpServers"]["klondike"]
                    assert "args" in config["mcpServers"]["klondike"]
            finally:
                os.chdir(original_cwd)

    def test_mcp_config_writes_to_file(self):
        """Test that mcp config can write to a file."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                output_path = Path(tmpdir) / "mcp-config.json"
                result = runner.invoke(app, ["mcp", "config", "--output", str(output_path)])

                assert result.exit_code == 0
                assert output_path.exists()

                # Verify content
                config = json.loads(output_path.read_text())
                assert "mcpServers" in config
                assert "klondike" in config["mcpServers"]
            finally:
                os.chdir(original_cwd)

    def test_mcp_install_generates_config(self):
        """Test that mcp install generates configuration."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                output_path = Path(tmpdir) / "mcp-install-config.json"
                result = runner.invoke(app, ["mcp", "install", "--output", str(output_path)])

                assert result.exit_code == 0
                assert "MCP configuration installed" in result.output
                assert output_path.exists()
            finally:
                os.chdir(original_cwd)

    def test_mcp_unknown_action(self):
        """Test that unknown action is rejected."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                result = runner.invoke(app, ["mcp", "unknown"])

                assert result.exit_code != 0
                assert "Unknown action" in result.output
            finally:
                os.chdir(original_cwd)


class TestMcpServerModule:
    """Test the mcp_server module directly."""

    def test_generate_mcp_config_structure(self):
        """Test that generate_mcp_config returns correct structure."""
        from klondike_spec_cli.mcp_server import generate_mcp_config

        config = generate_mcp_config()

        assert "mcpServers" in config
        assert "klondike" in config["mcpServers"]
        server_config = config["mcpServers"]["klondike"]
        assert "command" in server_config
        assert "args" in server_config
        assert "-m" in server_config["args"]
        assert "klondike_spec_cli.mcp_server" in server_config["args"]

    def test_generate_mcp_config_writes_file(self):
        """Test that generate_mcp_config can write to file."""
        from klondike_spec_cli.mcp_server import generate_mcp_config

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "config.json"
            config = generate_mcp_config(output_path)

            assert output_path.exists()
            file_content = json.loads(output_path.read_text())
            assert file_content == config

    def test_mcp_available_flag(self):
        """Test that MCP_AVAILABLE flag is set correctly."""
        from klondike_spec_cli.mcp_server import MCP_AVAILABLE

        # MCP_AVAILABLE should be a boolean
        assert isinstance(MCP_AVAILABLE, bool)

    def test_create_mcp_server_without_sdk(self):
        """Test create_mcp_server when MCP SDK is not available."""
        from klondike_spec_cli import mcp_server

        # Temporarily mock MCP_AVAILABLE to False
        original_value = mcp_server.MCP_AVAILABLE
        mcp_server.MCP_AVAILABLE = False

        try:
            result = mcp_server.create_mcp_server()
            assert result is None
        finally:
            mcp_server.MCP_AVAILABLE = original_value


class TestMcpServerTools:
    """Test MCP server tool functions with a real klondike project."""

    def setup_method(self):
        """Set up a temporary klondike project for each test."""
        self.tmpdir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.tmpdir)

        # Initialize a klondike project
        runner = CliRunner()
        runner.invoke(app, ["init"])

        # Add some test features
        runner.invoke(app, ["feature", "add", "--description", "Test Feature 1"])
        runner.invoke(app, ["feature", "add", "--description", "Test Feature 2"])

    def teardown_method(self):
        """Clean up after each test."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_load_features_helper(self):
        """Test the _load_features helper function."""
        from klondike_spec_cli.mcp_server import _load_features

        registry = _load_features()
        assert registry is not None
        assert len(registry.features) >= 2

    def test_load_progress_helper(self):
        """Test the _load_progress helper function."""
        from klondike_spec_cli.mcp_server import _load_progress

        progress = _load_progress()
        assert progress is not None

    def test_get_klondike_root_finds_project(self):
        """Test that _get_klondike_root finds the project."""
        from klondike_spec_cli.mcp_server import _get_klondike_root

        root = _get_klondike_root()
        assert root == Path(self.tmpdir)
        assert (root / ".klondike").exists()


class TestMcpServerToolsWithSdk:
    """Test MCP server tools that require the SDK."""

    def setup_method(self):
        """Set up a temporary klondike project."""
        self.tmpdir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.tmpdir)

        runner = CliRunner()
        runner.invoke(app, ["init"])
        runner.invoke(app, ["feature", "add", "--description", "Feature One"])
        runner.invoke(app, ["feature", "add", "--description", "Feature Two"])

    def teardown_method(self):
        """Clean up."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_mcp_server_creation_with_sdk(self):
        """Test MCP server creation when SDK is available."""
        from klondike_spec_cli.mcp_server import MCP_AVAILABLE, create_mcp_server

        if not MCP_AVAILABLE:
            pytest.skip("MCP SDK not installed")

        mcp = create_mcp_server()
        assert mcp is not None
        assert mcp.name == "klondike"


class TestMcpServeFallback:
    """Test MCP serve command fallback behavior."""

    def test_mcp_serve_without_sdk_shows_error(self):
        """Test that mcp serve shows helpful error when SDK not installed."""
        from klondike_spec_cli import mcp_server

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            original_mcp_available = mcp_server.MCP_AVAILABLE

            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                # Mock MCP as unavailable
                mcp_server.MCP_AVAILABLE = False

                result = runner.invoke(app, ["mcp", "serve"])

                assert result.exit_code != 0
                # Error message is in the exception, not stdout (since stderr is used for MCP stdio)
                assert result.exception is not None
                assert "MCP SDK not available" in str(result.exception)
            finally:
                os.chdir(original_cwd)
                mcp_server.MCP_AVAILABLE = original_mcp_available

    def test_mcp_serve_invalid_transport(self):
        """Test that invalid transport is rejected."""
        from klondike_spec_cli import mcp_server

        # Skip if MCP not available (we can't test transport validation)
        if not mcp_server.MCP_AVAILABLE:
            pytest.skip("MCP SDK not installed")

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                runner.invoke(app, ["init"])

                result = runner.invoke(app, ["mcp", "serve", "--transport", "invalid"])

                assert result.exit_code != 0
                assert "Invalid transport" in result.output
            finally:
                os.chdir(original_cwd)
