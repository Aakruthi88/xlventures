"""
Sentiment Agent
===============
Analyzes the sentiment of customer meeting transcripts using LLM.

Phase 8: Uses local LLM via llm.py for real sentiment analysis.
"""

from agents.llm import query_llm_json

# Fallback mock response in case of LLM query or parsing failure
DEFAULT_FALLBACK = {
    "sentiment": "Negative",
    "confidence": 0.89,
    "key_phrases": [
        "low analytics adoption",
        "slow SAP integration",
        "competitors considered"
    ]
}


def analyze(transcript_text: str) -> dict:
    """
    Analyze sentiment of a customer meeting transcript.

    Args:
        transcript_text: The customer meeting transcript text

    Returns:
        dict matching SentimentAgent schema
    """
    system_prompt = (
        "You are an AI sentiment analysis agent for a Customer Success platform.\n"
        "Your task is to analyze the customer meeting transcript and classify the overall sentiment into exactly one of these categories:\n"
        "- Positive\n"
        "- Neutral\n"
        "- Negative\n"
        "- Urgent\n\n"
        "Also extract up to three key phrases from the text that support your classification.\n"
        "Respond with a valid JSON object matching the format below:\n"
        "{\n"
        "    \"sentiment\": \"Positive | Neutral | Negative | Urgent\",\n"
        "    \"confidence\": 0.95,\n"
        "    \"key_phrases\": [\n"
        "        \"phrase 1\",\n"
        "        \"phrase 2\",\n"
        "        \"phrase 3\"\n"
        "    ]\n"
        "}\n"
        "Return ONLY the raw JSON object. No explanations, no markdown formatting."
    )

    user_prompt = f"Analyze the sentiment of this customer transcript:\n\"{transcript_text}\""

    try:
        result = query_llm_json(user_prompt, system_prompt)
        
        # Verify keys and validate sentiment type
        sentiment = result.get("sentiment")
        valid_sentiments = {"Positive", "Neutral", "Negative", "Urgent"}
        
        if not sentiment or sentiment not in valid_sentiments:
            # Try parsing case-insensitively or title casing it
            if sentiment and sentiment.title() in valid_sentiments:
                result["sentiment"] = sentiment.title()
            else:
                raise ValueError("Invalid or missing sentiment class in LLM response.")

        # Ensure confidence is a float and key_phrases is a list of strings
        if "confidence" not in result:
            result["confidence"] = 0.95
        else:
            try:
                result["confidence"] = float(result["confidence"])
            except ValueError:
                result["confidence"] = 0.95

        if "key_phrases" not in result or not isinstance(result["key_phrases"], list):
            result["key_phrases"] = []
        else:
            # Keep up to 3 phrases, convert to strings
            result["key_phrases"] = [str(p) for p in result["key_phrases"][:3]]

        return result

    except Exception as e:
        print(f"[Sentiment Agent] LLM analysis failed or returned malformed data: {e}")
        print("[Sentiment Agent] Returning fallback mock response.")
        return DEFAULT_FALLBACK

