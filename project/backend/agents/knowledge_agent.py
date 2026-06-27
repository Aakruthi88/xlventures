"""
Knowledge Agent
===============
Retrieves relevant enterprise knowledge documents using RAG
(Retrieval-Augmented Generation) from the knowledge base.

Phase 3: Returns hardcoded mock data.
Phase 7: Will use ChromaDB + sentence-transformers for real retrieval.
"""


def retrieve(transcript_text: str) -> dict:
    """
    Retrieve relevant knowledge base documents for a given transcript.

    Args:
        transcript_text: The customer meeting transcript text

    Returns:
        dict matching KnowledgeAgent schema with retrieved_docs
    """
    # Phase 3: Mock response
    return {
        "retrieved_docs": [
            {
                "source": "renewal_playbook.md",
                "snippet": "Schedule customer training for low dashboard adoption. If dashboard usage is below 40%, schedule a personalized training session to demonstrate analytics capabilities.",
                "score": 0.92
            },
            {
                "source": "onboarding_guide.md",
                "snippet": "Critical checkpoint: verify that more than 50% of licensed seats have been activated. If activation is below 50%, escalate to CSM for adoption intervention.",
                "score": 0.87
            },
            {
                "source": "integration_guide.md",
                "snippet": "SAP integration sync failures during payroll batch processing. Schedule payroll sync outside peak hours. For 500+ employees, request rate limit increase.",
                "score": 0.84
            }
        ]
    }
