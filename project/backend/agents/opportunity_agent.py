"""
Opportunity Agent
=================
Identifies upsell, cross-sell, and engagement opportunities
based on customer data and knowledge base context.

Phase 3: Returns hardcoded mock data.
Phase 10: Will implement real rule-based opportunity detection.
"""


def find(customer_summary: dict, knowledge_docs: dict) -> dict:
    """
    Find business opportunities for a customer.

    Args:
        customer_summary: CustomerSummary dict from customer_agent
        knowledge_docs: KnowledgeAgent dict from knowledge_agent

    Returns:
        dict matching OpportunityAgent schema
    """
    # Phase 3: Mock response
    return {
        "opportunities": [
            {
                "type": "Training",
                "item": "Analytics Adoption Workshop",
                "rationale": "Dashboard usage at 32% - personalized training can improve adoption before renewal"
            },
            {
                "type": "Cross Sell",
                "item": "Premium Support Package",
                "rationale": "7 open tickets indicate need for faster resolution SLA"
            },
            {
                "type": "Service",
                "item": "SAP Integration Health Check",
                "rationale": "Ongoing SAP sync issues affecting daily operations"
            }
        ]
    }
