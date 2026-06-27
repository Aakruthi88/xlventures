"""
Risk Agent
==========
Identifies and assesses risks based on customer data, sentiment,
and knowledge base context using rule-based logic.

Phase 3: Returns hardcoded mock data.
Phase 9: Will implement real rule-based risk assessment.
"""


def assess(customer_summary: dict, sentiment: dict, knowledge_docs: dict) -> dict:
    """
    Assess risks for a customer based on their summary, sentiment, and KB context.

    Args:
        customer_summary: CustomerSummary dict from customer_agent
        sentiment: SentimentAgent dict from sentiment_agent
        knowledge_docs: KnowledgeAgent dict from knowledge_agent

    Returns:
        dict matching RiskAgent schema
    """
    # Phase 3: Mock response
    return {
        "risks": [
            {
                "type": "Renewal Risk",
                "severity": "High",
                "evidence": "Renewal is in 20 days and health score is 42"
            },
            {
                "type": "Low Adoption",
                "severity": "Medium",
                "evidence": "Dashboard usage is 32%, well below the 40% threshold"
            },
            {
                "type": "Support Risk",
                "severity": "High",
                "evidence": "7 open support tickets including critical SAP integration issues"
            },
            {
                "type": "Churn Risk",
                "severity": "High",
                "evidence": "Negative sentiment detected; customer considering competitors"
            }
        ],
        "overall_risk": "High"
    }
