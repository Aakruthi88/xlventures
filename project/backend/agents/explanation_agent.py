"""
Explanation Agent
=================
Provides explainable reasoning for each recommendation,
linking evidence back to specific data sources.

Phase 3: Returns hardcoded mock data.
Phase 12: Will parse LLM response from recommendation_agent
          and validate evidence against source data.
"""


def explain(recommendations: dict) -> dict:
    """
    Generate explanations with evidence for each recommendation.

    Args:
        recommendations: RecommendationAgent dict from recommendation_agent

    Returns:
        dict matching ExplanationAgent schema
    """
    # Phase 3: Mock response
    return {
        "explanations": [
            {
                "recommendation_id": "REC001",
                "reason": "Improve product adoption before renewal to demonstrate ROI",
                "evidence": [
                    "Health score is 42 (below 50 threshold)",
                    "Dashboard usage at 32% (below 40% training trigger per renewal playbook)",
                    "Renewal in 20 days - urgent timeline",
                    "Transcript: team exports to Excel instead of using dashboards"
                ],
                "confidence": 0.91
            },
            {
                "recommendation_id": "REC002",
                "reason": "Resolve critical integration blocker affecting daily operations",
                "evidence": [
                    "SAP sync takes 20 minutes daily per transcript",
                    "Open ticket: SAP integration sync failing intermittently",
                    "Integration guide: schedule sync outside peak hours, break into 200-record batches",
                    "API rate limit errors reported during payroll processing"
                ],
                "confidence": 0.88
            },
            {
                "recommendation_id": "REC003",
                "reason": "High-risk account requires executive engagement per escalation matrix",
                "evidence": [
                    "Health score 42 + renewal in 20 days triggers Tier 3 escalation per SOP",
                    "Customer champion (Priya Sharma) departed in April",
                    "Customer VP evaluating competitors (BambooHR, Workday)",
                    "QBR postponed twice - disengagement signal"
                ],
                "confidence": 0.85
            },
            {
                "recommendation_id": "REC004",
                "reason": "Counter competitive threat with targeted comparison",
                "evidence": [
                    "Transcript: management considering BambooHR and Workday",
                    "Customer success SOP: prepare tailored competitive comparison",
                    "Focus on platform strengths in manufacturing compliance reporting"
                ],
                "confidence": 0.79
            }
        ]
    }
