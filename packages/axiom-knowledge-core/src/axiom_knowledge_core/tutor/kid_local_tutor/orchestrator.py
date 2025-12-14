"""
orchestrator.py
===============

This module defines a simple orchestrator for coordinating multiple AI agents.
In the MVP implementation only a single agent (the `TutorQnA` pipeline) is
used.  The orchestrator API is designed to allow future expansion to a
multi‑agent swarm: a controller can dispatch tasks to specialised agents
(e.g. planner, researcher, verifier) and integrate their outputs.

The orchestrator also provides hooks for semantic drift detection and trust
logging (not yet implemented).  Each agent’s output can be signed and stored
in memory for auditing.
"""

from __future__ import annotations

from typing import List, Dict, Any

from .rehydrate import TutorQnA


class Orchestrator:
    """Manage one or more agents to answer user queries.

    Parameters
    ----------
    agents: list
        A list of agents to coordinate.  Each agent must implement a method
        `answer(question: str)` that returns a tuple `(response: str, context: Any)`.
    """

    def __init__(self, agents: List[Any]) -> None:
        if not agents:
            raise ValueError("Orchestrator requires at least one agent")
        self.agents = agents

    def answer(self, question: str) -> Dict[str, Any]:
        """Dispatch a question to the first agent.

        In future versions this method could run multiple agents in parallel,
        combine their results, and verify consistency.  For now we simply
        delegate to the single agent.

        Returns
        -------
        dict
            A dictionary containing the answer and any context returned by the agent.
        """
        # Single‑agent path
        agent = self.agents[0]
        try:
            answer_text, context = agent.answer(question)
        except Exception as exc:
            return {
                "answer": f"Error: {exc}",
                "context": [],
                "error": True,
            }
        return {
            "answer": answer_text,
            "context": context,
            "error": False,
        }


__all__ = ["Orchestrator"]