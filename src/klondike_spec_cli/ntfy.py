"""ntfy.sh push notification integration for klondike events.

This module provides a simple API for sending push notifications to ntfy.sh
when important events occur (session start/end, feature verified/blocked, errors).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class NtfyEventConfig:
    """Configuration for which event types should trigger notifications."""

    session_start: bool = True
    session_end: bool = True
    feature_verified: bool = True
    feature_blocked: bool = True
    errors: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> NtfyEventConfig:
        """Create from dictionary, with sensible defaults."""
        if data is None:
            return cls()
        return cls(
            session_start=data.get("session_start", True),
            session_end=data.get("session_end", True),
            feature_verified=data.get("feature_verified", True),
            feature_blocked=data.get("feature_blocked", True),
            errors=data.get("errors", True),
        )

    def to_dict(self) -> dict[str, bool]:
        """Convert to dictionary for serialization."""
        return {
            "session_start": self.session_start,
            "session_end": self.session_end,
            "feature_verified": self.feature_verified,
            "feature_blocked": self.feature_blocked,
            "errors": self.errors,
        }


@dataclass
class NtfyConfig:
    """Configuration for ntfy.sh notifications.

    Attributes:
        channel: The ntfy topic/channel to publish to (required)
        server: The ntfy server URL (defaults to https://ntfy.sh)
        token: Optional access token for authentication
        events: Configuration for which event types trigger notifications
        enabled: Whether notifications are enabled (auto-detected from channel presence)
    """

    channel: str | None = None
    server: str = "https://ntfy.sh"
    token: str | None = None
    events: NtfyEventConfig = field(default_factory=NtfyEventConfig)

    @property
    def enabled(self) -> bool:
        """Check if notifications are enabled (channel must be configured)."""
        return self.channel is not None and len(self.channel.strip()) > 0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> NtfyConfig:
        """Create from dictionary."""
        if data is None:
            return cls()
        return cls(
            channel=data.get("channel"),
            server=data.get("server", "https://ntfy.sh"),
            token=data.get("token"),
            events=NtfyEventConfig.from_dict(data.get("events")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {
            "server": self.server,
            "events": self.events.to_dict(),
        }
        if self.channel:
            result["channel"] = self.channel
        if self.token:
            result["token"] = self.token
        return result


class NtfyClient:
    """Client for sending notifications to ntfy.sh.

    This client handles all the details of formatting and sending notifications,
    including error handling, rate limiting, and authentication.
    """

    def __init__(self, config: NtfyConfig):
        """Initialize the ntfy client with configuration.

        Args:
            config: NtfyConfig instance with server, channel, and auth settings
        """
        self.config = config
        self.timeout = 5  # seconds

    def _send(
        self,
        message: str,
        title: str | None = None,
        priority: int = 3,
        tags: list[str] | None = None,
    ) -> bool:
        """Send a notification to ntfy.sh.

        Args:
            message: The notification message body
            title: Optional notification title
            priority: Message priority (1=min, 3=default, 5=max)
            tags: Optional list of tags/emojis

        Returns:
            True if notification was sent successfully, False otherwise
        """
        if not REQUESTS_AVAILABLE:
            logger.debug("ntfy notifications unavailable (requests library not installed)")
            return False

        if not self.config.enabled:
            logger.debug("ntfy notifications disabled (no channel configured)")
            return False

        # Truncate message if too long (ntfy limit is 4096 bytes)
        if len(message) > 4000:
            message = message[:3997] + "..."

        url = f"{self.config.server}/{self.config.channel}"
        headers = {"Content-Type": "text/plain; charset=utf-8"}

        if title:
            # Encode title as UTF-8 for proper emoji/unicode support
            headers["X-Title"] = title.encode("utf-8").decode("latin1")

        if priority != 3:  # Only set if non-default
            headers["X-Priority"] = str(priority)

        if tags:
            headers["X-Tags"] = ",".join(tags)

        # Add authentication if token is configured
        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"

        try:
            response = requests.post(
                url,
                data=message.encode("utf-8"),
                headers=headers,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                logger.debug(f"ntfy notification sent: {title or message[:50]}")
                return True
            elif response.status_code == 429:
                logger.warning("ntfy rate limit exceeded - notification not sent")
                return False
            else:
                logger.warning(
                    f"ntfy notification failed: HTTP {response.status_code} - {response.text[:100]}"
                )
                return False

        except requests.exceptions.Timeout:
            logger.warning(f"ntfy notification timed out after {self.timeout}s")
            return False
        except requests.exceptions.RequestException as e:
            logger.warning(f"ntfy notification failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending ntfy notification: {e}")
            return False

    def session_started(self, session_number: int, focus: str) -> bool:
        """Notify that a new session has started.

        Args:
            session_number: The session number
            focus: The session focus description

        Returns:
            True if notification sent successfully
        """
        if not self.config.events.session_start:
            return False

        return self._send(
            message=f"Focus: {focus}",
            title=f"🚀 Session #{session_number} Started",
            priority=3,
            tags=["rocket"],
        )

    def session_ended(self, session_number: int, summary: str, features_completed: int = 0) -> bool:
        """Notify that a session has ended.

        Args:
            session_number: The session number
            summary: Summary of work completed
            features_completed: Number of features completed

        Returns:
            True if notification sent successfully
        """
        if not self.config.events.session_end:
            return False

        tags = ["checkered_flag"]
        if features_completed > 0:
            tags.append("tada")

        feat_msg = (
            f" ({features_completed} feature{'s' if features_completed != 1 else ''} completed)"
            if features_completed > 0
            else ""
        )

        return self._send(
            message=summary,
            title=f"✅ Session #{session_number} Complete{feat_msg}",
            priority=3,
            tags=tags,
        )

    def feature_verified(self, feature_id: str, description: str) -> bool:
        """Notify that a feature has been verified.

        Args:
            feature_id: The feature ID (e.g., "F001")
            description: Feature description

        Returns:
            True if notification sent successfully
        """
        if not self.config.events.feature_verified:
            return False

        return self._send(
            message=description,
            title=f"✅ {feature_id} Verified",
            priority=3,
            tags=["white_check_mark", "tada"],
        )

    def feature_blocked(self, feature_id: str, description: str, reason: str) -> bool:
        """Notify that a feature has been blocked.

        Args:
            feature_id: The feature ID (e.g., "F001")
            description: Feature description
            reason: Why the feature is blocked

        Returns:
            True if notification sent successfully
        """
        if not self.config.events.feature_blocked:
            return False

        return self._send(
            message=f"{description}\n\nReason: {reason}",
            title=f"⛔ {feature_id} Blocked",
            priority=4,  # Higher priority for blocks
            tags=["no_entry", "warning"],
        )

    def error_occurred(self, error_title: str, error_details: str) -> bool:
        """Notify that an error has occurred.

        Args:
            error_title: Brief error title
            error_details: Detailed error information

        Returns:
            True if notification sent successfully
        """
        if not self.config.events.errors:
            return False

        return self._send(
            message=error_details,
            title=f"🚨 Error: {error_title}",
            priority=5,  # Max priority for errors
            tags=["rotating_light", "skull"],
        )


def get_ntfy_client(config: NtfyConfig | None) -> NtfyClient | None:
    """Get a configured ntfy client if notifications are enabled.

    Args:
        config: NtfyConfig instance or None

    Returns:
        NtfyClient if configured and enabled, None otherwise
    """
    if config is None or not config.enabled:
        return None
    return NtfyClient(config)
