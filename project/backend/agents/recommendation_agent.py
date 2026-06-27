"""
Recommendation Agent (Decision Agent)
=====================================
Generates next-best-action recommendations by synthesizing
insights from all other agents using LLM reasoning.

Phase 3: Returns hardcoded mock data.
Phase 11: Will use Groq LLM for real recommendation generation.
"""


def generate(customer_summary: dict, risks: dict, opportunities: dict,
             sentiment: dict, knowledge_docs: dict,
             past_approvals: list = None) -> dict:
    """
    Generate next-best-action recommendations for a customer.

    Args:
        customer_summary: CustomerSummary dict from customer_agent
        risks: RiskAgent dict from risk_agent
        opportunities: OpportunityAgent dict from opportunity_agent
        sentiment: SentimentAgent dict from sentiment_agent
        knowledge_docs: KnowledgeAgent dict from knowledge_agent
        past_approvals: List of previously approved recommendations (optional)

    Returns:
        dict matching RecommendationAgent schema
    """
    # Phase 3: Mock response
    return {
        "recommendations": [
            {
                "id": "REC001",
                "action": "Schedule analytics training session for ABC Manufacturing team",
                "priority": "High",
                "confidence": 0.91
            },
            {
                "id": "REC002",
                "action": "Escalate SAP integration issues to engineering team with priority fix",
                "priority": "High",
                "confidence": 0.88
            },
            {
                "id": "REC003",
                "action": "Initiate executive sponsor outreach before renewal deadline",
                "priority": "High",
                "confidence": 0.85
            },
            {
                "id": "REC004",
                "action": "Prepare competitive comparison document addressing BambooHR and Workday",
                "priority": "Medium",
                "confidence": 0.79
            }
        ]
    }
