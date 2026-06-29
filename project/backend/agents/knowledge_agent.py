"""
Knowledge Agent
===============
Retrieves relevant enterprise knowledge documents using RAG from the knowledge base.
Refactored: Uses the search_knowledge_base LangChain tool.
"""

from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from tools.knowledge_search_tool import search_knowledge_base


class KnowledgeAgent(BaseAgent):
    """
    Searches the enterprise knowledge base for playbooks, integration guides,
    and SOPs using the registered search_knowledge_base tool.
    """

    def __init__(self):
        super().__init__(
            name="knowledge_agent",
            description="Searches enterprise knowledge base (playbooks, integration guides, SOPs) using tools.",
            tools=[search_knowledge_base]
        )

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute knowledge base retrieval using the search_knowledge_base tool.

        Args:
            state: Must contain 'transcript_text'.

        Returns:
            Dict with 'knowledge' key containing retrieved docs.
        """
        transcript_text = state.get("transcript_text", "")
        try:
            docs = search_knowledge_base.invoke({"query": transcript_text})
            return {"knowledge": {"retrieved_docs": docs}}
        except Exception as e:
            print(f"[KnowledgeAgent] Failed: {e}")
            return {"knowledge": {"retrieved_docs": []}}


# ── Module-level backward-compatible function ─────────────────────────────────

def retrieve(transcript_text: str) -> dict:
    """Backward-compatible wrapper."""
    docs = search_knowledge_base.invoke({"query": transcript_text})
    return {"retrieved_docs": docs}
