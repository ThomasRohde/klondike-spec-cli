"""Tests for ntfy.sh integration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from klondike_spec_cli.ntfy import (
    REQUESTS_AVAILABLE,
    NtfyClient,
    NtfyConfig,
    NtfyEventConfig,
    get_ntfy_client,
)


class TestNtfyEventConfig:
    """Tests for NtfyEventConfig."""

    def test_default_config(self):
        """Test default event configuration enables all events."""
        config = NtfyEventConfig()
        assert config.session_start is True
        assert config.session_end is True
        assert config.feature_verified is True
        assert config.feature_blocked is True
        assert config.errors is True

    def test_from_dict_none(self):
        """Test creating from None dict returns defaults."""
        config = NtfyEventConfig.from_dict(None)
        assert config.session_start is True

    def test_from_dict_partial(self):
        """Test creating from partial dict uses defaults."""
        config = NtfyEventConfig.from_dict({"session_start": False})
        assert config.session_start is False
        assert config.session_end is True  # Default

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = NtfyEventConfig(session_start=False, errors=False)
        result = config.to_dict()
        assert result["session_start"] is False
        assert result["errors"] is False
        assert result["session_end"] is True


class TestNtfyConfig:
    """Tests for NtfyConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = NtfyConfig()
        assert config.channel is None
        assert config.server == "https://ntfy.sh"
        assert config.token is None
        assert config.enabled is False  # No channel configured

    def test_enabled_with_channel(self):
        """Test configuration is enabled when channel is set."""
        config = NtfyConfig(channel="my-topic")
        assert config.enabled is True

    def test_enabled_with_empty_channel(self):
        """Test configuration is disabled with empty/whitespace channel."""
        config = NtfyConfig(channel="  ")
        assert config.enabled is False

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "channel": "test-topic",
            "server": "https://custom.ntfy.sh",
            "token": "tk_test123",
            "events": {"session_start": False},
        }
        config = NtfyConfig.from_dict(data)
        assert config.channel == "test-topic"
        assert config.server == "https://custom.ntfy.sh"
        assert config.token == "tk_test123"
        assert config.events.session_start is False

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = NtfyConfig(channel="test", token="secret")
        result = config.to_dict()
        assert result["channel"] == "test"
        assert result["token"] == "secret"
        assert "events" in result


class TestNtfyClient:
    """Tests for NtfyClient."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return NtfyConfig(channel="test-topic", server="https://ntfy.sh")

    @pytest.fixture
    def client(self, config):
        """Create a test client."""
        return NtfyClient(config)

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not available")
    @patch("klondike_spec_cli.ntfy.requests.post")
    def test_send_success(self, mock_post, client):
        """Test successful notification send."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = client._send("Test message", title="Test Title", priority=5, tags=["test"])

        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://ntfy.sh/test-topic"
        assert call_args[1]["headers"]["X-Title"] == "Test Title"
        assert call_args[1]["headers"]["X-Priority"] == "5"
        assert call_args[1]["headers"]["X-Tags"] == "test"

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not available")
    @patch("klondike_spec_cli.ntfy.requests.post")
    def test_send_with_token(self, mock_post, config):
        """Test notification send with authentication token."""
        config.token = "tk_test123"
        client = NtfyClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client._send("Test")

        call_args = mock_post.call_args
        assert call_args[1]["headers"]["Authorization"] == "Bearer tk_test123"

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not available")
    @patch("klondike_spec_cli.ntfy.requests.post")
    def test_send_rate_limited(self, mock_post, client):
        """Test handling of rate limit (429) response."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response

        result = client._send("Test")
        assert result is False

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not available")
    @patch("klondike_spec_cli.ntfy.requests.post")
    def test_send_disabled(self, mock_post):
        """Test send when notifications are disabled."""
        config = NtfyConfig()  # No channel
        client = NtfyClient(config)

        result = client._send("Test")
        assert result is False
        mock_post.assert_not_called()

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not available")
    @patch("klondike_spec_cli.ntfy.requests.post")
    def test_send_truncates_long_message(self, mock_post, client):
        """Test that very long messages are truncated."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        long_message = "x" * 5000
        client._send(long_message)

        call_args = mock_post.call_args
        sent_data = call_args[1]["data"]
        assert len(sent_data) <= 4000

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not available")
    @patch("klondike_spec_cli.ntfy.requests.post")
    def test_session_started(self, mock_post, client):
        """Test session started notification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = client.session_started(42, "Working on F058")
        assert result is True

        call_args = mock_post.call_args
        assert b"Focus: Working on F058" in call_args[1]["data"]
        assert "Session #42 Started" in call_args[1]["headers"]["X-Title"]

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not available")
    @patch("klondike_spec_cli.ntfy.requests.post")
    def test_session_ended(self, mock_post, client):
        """Test session ended notification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = client.session_ended(42, "Completed F058", features_completed=1)
        assert result is True

        call_args = mock_post.call_args
        assert b"Completed F058" in call_args[1]["data"]
        assert "(1 feature completed)" in call_args[1]["headers"]["X-Title"]

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not available")
    @patch("klondike_spec_cli.ntfy.requests.post")
    def test_feature_verified(self, mock_post, client):
        """Test feature verified notification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = client.feature_verified("F058", "ntfy integration")
        assert result is True

        call_args = mock_post.call_args
        assert "F058 Verified" in call_args[1]["headers"]["X-Title"]
        assert b"ntfy integration" in call_args[1]["data"]

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not available")
    @patch("klondike_spec_cli.ntfy.requests.post")
    def test_feature_blocked(self, mock_post, client):
        """Test feature blocked notification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = client.feature_blocked("F059", "Some feature", "Dependency not ready")
        assert result is True

        call_args = mock_post.call_args
        assert "F059 Blocked" in call_args[1]["headers"]["X-Title"]
        assert b"Reason: Dependency not ready" in call_args[1]["data"]

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not available")
    @patch("klondike_spec_cli.ntfy.requests.post")
    def test_error_occurred(self, mock_post, client):
        """Test error notification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = client.error_occurred("Build failed", "Exit code: 1")
        assert result is True

        call_args = mock_post.call_args
        assert "Error: Build failed" in call_args[1]["headers"]["X-Title"]
        assert call_args[1]["headers"]["X-Priority"] == "5"  # Max priority

    def test_event_filters(self, config):
        """Test that event filters prevent notifications."""
        config.events.session_start = False
        client = NtfyClient(config)

        with patch("klondike_spec_cli.ntfy.requests.post") as mock_post:
            result = client.session_started(1, "test")
            assert result is False
            mock_post.assert_not_called()


class TestGetNtfyClient:
    """Tests for get_ntfy_client helper function."""

    def test_returns_none_for_none_config(self):
        """Test returns None when config is None."""
        result = get_ntfy_client(None)
        assert result is None

    def test_returns_none_for_disabled_config(self):
        """Test returns None when notifications are disabled."""
        config = NtfyConfig()  # No channel
        result = get_ntfy_client(config)
        assert result is None

    def test_returns_client_for_enabled_config(self):
        """Test returns client when notifications are enabled."""
        config = NtfyConfig(channel="test")
        result = get_ntfy_client(config)
        assert result is not None
        assert isinstance(result, NtfyClient)
