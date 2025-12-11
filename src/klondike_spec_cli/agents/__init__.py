"""Agent adapter system for multi-agent support.

This package provides a pluggable system for supporting different AI coding agents
(GitHub Copilot, Claude Code, etc.) with klondike workflows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import AgentAdapter

# Registry of available agents
_AGENT_REGISTRY: dict[str, type[AgentAdapter]] = {}


def register_agent(adapter_class: type[AgentAdapter]) -> type[AgentAdapter]:
    """Register an agent adapter class.

    Can be used as a decorator or called directly.

    Args:
        adapter_class: The adapter class to register

    Returns:
        The adapter class (for decorator usage)
    """
    # Instantiate to get the name
    instance = adapter_class()
    _AGENT_REGISTRY[instance.name] = adapter_class
    return adapter_class


def get_agent(agent_name: str) -> AgentAdapter:
    """Get an agent adapter instance by name.

    Args:
        agent_name: The agent name (e.g., 'copilot', 'claude')

    Returns:
        An instance of the agent adapter

    Raises:
        ValueError: If the agent name is not registered
    """
    if agent_name not in _AGENT_REGISTRY:
        valid_agents = ", ".join(sorted(_AGENT_REGISTRY.keys()))
        raise ValueError(f"Unknown agent: '{agent_name}'. Available agents: {valid_agents}")
    return _AGENT_REGISTRY[agent_name]()


def list_agents() -> list[str]:
    """List all registered agent names.

    Returns:
        Sorted list of agent names
    """
    return sorted(_AGENT_REGISTRY.keys())


def get_default_agent() -> str:
    """Get the default agent name.

    Returns:
        The default agent name ('copilot')
    """
    return "copilot"


# Import and register built-in agents
# These imports must come after the registry functions are defined
from .claude import ClaudeAdapter  # noqa: E402
from .copilot import CopilotAdapter  # noqa: E402

register_agent(CopilotAdapter)
register_agent(ClaudeAdapter)

# Public API
__all__ = [
    "AgentAdapter",
    "get_agent",
    "get_default_agent",
    "list_agents",
    "register_agent",
]
