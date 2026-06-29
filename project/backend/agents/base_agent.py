"""
Base Agent
==========
Abstract base class for all specialized agents in the platform.

Every agent inherits from BaseAgent and implements execute().
This ensures a consistent interface for the dynamic AgentExecutor
to discover, invoke, and trace agents at runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseAgent(ABC):
    """
    Abstract base class for all platform agents.

    Attributes:
        name: Unique identifier used by the planner to select this agent.
        description: Human-readable summary of the agent's purpose.
        tools: List of tool references this agent can use (for future extensibility).
    """

    def __init__(self, name: str, description: str, tools: List[Any] = None):
        self.name = name
        self.description = description
        self.tools = tools or []

    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's logic on the shared workflow state.

        Args:
            state: The current workflow state dict containing session context
                   and outputs from previously executed agents.

        Returns:
            A dict of state updates to merge into the workflow state.
            Only keys that this agent is responsible for should be returned.
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
