"""
Sentiment Agent
===============
Analyzes the sentiment of customer meeting transcripts using LLM.

Phase 3: Returns hardcoded mock data.
Phase 8: Will use Groq LLM for real sentiment analysis.
"""


def analyze(transcript_text: str) -> dict:
    """
    Analyze sentiment of a customer meeting transcript.

    Args:
        transcript_text: The customer meeting transcript text

    Returns:
        dict matching SentimentAgent schema
    """
    # Phase 3: Mock response
    return {
        "sentiment": "Negative",
        "confidence": 0.89,
        "key_phrases": [
            "low analytics adoption",
            "slow SAP integration",
            "competitors considered"
        ]
    }
