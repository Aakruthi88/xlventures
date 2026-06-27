"""
Explanation Agent
=================
Provides explainable reasoning for each recommendation,
linking evidence back to specific data sources.

Phase 3: Returns hardcoded mock data.
Phase 12: Parses response from recommendation_agent, validates
          evidence, and enforces output format compliance.
"""


def explain(llm_response: dict = None, customer_summary: dict = None,
            risks: dict = None, knowledge_docs: dict = None,
            recommendations: dict = None) -> dict:
    """
    Validate, clean, and format explanations from the recommendation agent.
    This agent only validates and formats existing explanations; it does not
    generate new recommendations or make another LLM call.

    Args:
        llm_response: The recommendation agent response dict (containing recommendations & explanations).
        customer_summary: Optional customer summary dictionary for tracing facts.
        risks: Optional risk details dictionary for tracing facts.
        knowledge_docs: Optional retrieved knowledge documents for tracing facts.
        recommendations: Alias for llm_response to preserve backwards compatibility.

    Returns:
        dict: A dictionary matching the ExplanationAgent schema:
              {
                  "explanations": [
                      {
                          "recommendation_id": str,
                          "reason": str,
                          "evidence": list,
                          "confidence": float
                      }
                  ]
              }
    """
    # Preserve backwards compatibility if recommendations parameter is used.
    if llm_response is None:
        llm_response = recommendations

    # 1. Schema fallback: if the upstream response is missing or malformed,
    #    return the empty schema expected by the rest of the planner.
    if not isinstance(llm_response, dict) or "explanations" not in llm_response:
        print("[Explanation Agent] Warning: Input response is missing or not a dict. Returning empty explanations.")
        return {"explanations": []}

    explanations_list = llm_response.get("explanations")
    if not isinstance(explanations_list, list):
        print("[Explanation Agent] Warning: 'explanations' is not a list. Returning empty explanations.")
        return {"explanations": []}

    validated_explanations = []
    has_source_data = any(value is not None for value in [customer_summary, risks, knowledge_docs])

    # 2. Lightweight fact tracing helper.
    #    This only checks whether an evidence string can be matched against
    #    already-available source data. It never invents or rewrites evidence.
    def normalize_text(value) -> str:
        if value is None:
            return ""
        if isinstance(value, (str, int, float, bool)):
            return str(value).strip()
        if isinstance(value, (list, tuple, set)):
            pieces = [normalize_text(item) for item in value if normalize_text(item)]
            return " ".join(pieces)
        if isinstance(value, dict):
            pieces = [normalize_text(item) for item in value.values() if normalize_text(item)]
            return " ".join(pieces)
        return str(value).strip()

    def collect_fact_strings(value) -> list:
        facts = []
        if value is None:
            return facts
        if isinstance(value, (str, int, float, bool)):
            text = normalize_text(value)
            if text:
                facts.append(text)
            return facts
        if isinstance(value, dict):
            for item in value.values():
                facts.extend(collect_fact_strings(item))
            return facts
        if isinstance(value, (list, tuple, set)):
            for item in value:
                facts.extend(collect_fact_strings(item))
            return facts
        return facts

    fact_sources = []
    for source in [customer_summary, risks, knowledge_docs]:
        fact_sources.extend(collect_fact_strings(source))

    def is_grounded_fact(evidence_str: str) -> bool:
        if not evidence_str:
            return False
        if not has_source_data:
            # The current planner architecture does not always pass source data
            # into this agent, so we preserve compatibility and keep the evidence.
            return True

        evidence_lower = normalize_text(evidence_str).lower()
        if not evidence_lower:
            return False

        for fact in fact_sources:
            fact_lower = normalize_text(fact).lower()
            if not fact_lower:
                continue
            if evidence_lower in fact_lower or fact_lower in evidence_lower:
                return True
        return False

    # 3. Validate and normalize each explanation entry individually.
    for idx, exp in enumerate(explanations_list):
        if not isinstance(exp, dict):
            continue

        # 3.1 recommendation_id: use the matching recommendation id when present,
        #     otherwise fall back to a stable generated id.
        rec_id = exp.get("recommendation_id")
        if not isinstance(rec_id, str) or not rec_id.strip():
            recs_list = llm_response.get("recommendations", [])
            if isinstance(recs_list, list) and idx < len(recs_list):
                rec_item = recs_list[idx]
                if isinstance(rec_item, dict):
                    rec_id = rec_item.get("id")
            if not isinstance(rec_id, str) or not rec_id.strip():
                rec_id = f"REC{idx + 1:03d}"

        # 3.2 reason: keep the existing string or supply a default.
        reason = exp.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            reason = "No explanation reason provided."

        # 3.3 confidence: coerce to float, otherwise use a safe default.
        confidence = exp.get("confidence")
        if confidence is None:
            confidence = 0.95
        else:
            try:
                confidence = float(confidence)
            except (ValueError, TypeError):
                confidence = 0.95

        # 3.4 evidence: normalize to a list of strings and verify each entry.
        evidence = exp.get("evidence")
        if isinstance(evidence, (list, tuple, set)):
            evidence_items = evidence
        elif isinstance(evidence, str) and evidence.strip():
            evidence_items = [evidence]
        else:
            evidence_items = []

        cleaned_evidence = []
        for item in evidence_items:
            item_str = normalize_text(item)
            if not item_str:
                continue
            if has_source_data:
                if is_grounded_fact(item_str):
                    cleaned_evidence.append(item_str)
            else:
                # When source data is unavailable, preserve the original evidence
                # string rather than inventing or altering it.
                cleaned_evidence.append(item_str)

        # Keep the evidence list empty if nothing could be validated.
        validated_explanations.append({
            "recommendation_id": rec_id,
            "reason": reason,
            "evidence": cleaned_evidence,
            "confidence": confidence
        })

    return {"explanations": validated_explanations}

