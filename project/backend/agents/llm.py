"""
LLM Wrapper
============
Provides a unified LLM interface using local Ollama (Llama 3.1).
Falls back gracefully when Ollama is not available.

Phase 5: Local-only, free, no API keys required.
"""

import json

# Track Ollama availability globally to avoid repeated connection attempts
_ollama_available = None


def check_ollama_available() -> bool:
    """Check if Ollama is running locally on port 11434."""
    global _ollama_available
    if _ollama_available is not None:
        return _ollama_available

    try:
        import ollama
        # Simple connectivity test - list models
        ollama.list()
        _ollama_available = True
        print("[LLM] Ollama is available at localhost:11434")
    except Exception as e:
        _ollama_available = False
        print(f"[LLM] Ollama not available, using rule-based fallback. ({e})")

    return _ollama_available


def get_available_chat_model() -> str:
    """
    Get the name of an installed chat model from Ollama.
    Prefers qwen2.5:0.5b, falls back to any other installed chat model.
    """
    if not check_ollama_available():
        return "qwen2.5:0.5b"
    
    try:
        import ollama
        models = ollama.list().get("models", [])
        names = [m.get("model", "") or m.get("name", "") for m in models]
        
        # Look for our preferred light models
        for preferred in ["qwen2.5:0.5b", "qwen2.5:1.5b", "llama3.2:latest", "llama3.2", "llama3.1"]:
            # Check for substring match in case tag differs
            for name in names:
                if preferred in name:
                    return name
                    
        # Fallback to any non-embedding model
        for name in names:
            if "embed" not in name.lower():
                return name
    except Exception:
        pass
        
    return "qwen2.5:0.5b"


def query_llm(prompt: str, system_prompt: str = "", model: str = None) -> str:
    """
    Send a prompt to the local Ollama LLM and return the response text.

    Args:
        prompt: The user prompt to send
        system_prompt: Optional system instructions
        model: The Ollama model name (defaults to auto-detected)

    Returns:
        The LLM response text, or empty string on failure
    """
    if not check_ollama_available():
        return ""

    if model is None:
        model = get_available_chat_model()

    try:
        import ollama
        
        print(f"[LLM] Querying model: {model}")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = ollama.chat(model=model, messages=messages, options={"temperature": 0.0})
        return response["message"]["content"]
    except Exception as e:
        print(f"[LLM] Ollama query failed for model {model}: {e}")
        return ""


def query_llm_json(prompt: str, system_prompt: str = "", model: str = None) -> dict:
    """
    Send a prompt to Ollama and parse the response as JSON.

    Args:
        prompt: The user prompt
        system_prompt: Optional system instructions
        model: The Ollama model name

    Returns:
        Parsed JSON dict, or empty dict on failure
    """
    if model is None:
        model = get_available_chat_model()
        
    raw = query_llm(prompt, system_prompt, model)
    if not raw:
        return {}

    try:
        # Try to extract JSON from the response (LLMs sometimes wrap in markdown)
        # Look for JSON between ```json ... ``` or { ... }
        cleaned = raw.strip()

        # Strip markdown code fences if present
        if "```json" in cleaned:
            start = cleaned.index("```json") + 7
            end = cleaned.index("```", start)
            cleaned = cleaned[start:end].strip()
        elif "```" in cleaned:
            start = cleaned.index("```") + 3
            end = cleaned.index("```", start)
            cleaned = cleaned[start:end].strip()

        # Find the outermost JSON object
        brace_start = cleaned.find("{")
        brace_end = cleaned.rfind("}") + 1
        if brace_start >= 0 and brace_end > brace_start:
            cleaned = cleaned[brace_start:brace_end]

        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[LLM] Failed to parse JSON from LLM response: {e}")
        print(f"[LLM] Raw response was: {raw[:200]}")
        return {}


def get_llm():
    """
    Return a LangChain Ollama LLM instance using the local model.
    
    Returns:
        Ollama LLM instance from langchain_community
    """
    model_name = get_available_chat_model()
    try:
        from langchain_community.llms import Ollama
        return Ollama(
            base_url="http://localhost:11434",
            model=model_name
        )
    except Exception as e:
        print(f"[LLM] Failed to import/instantiate LangChain Ollama LLM: {e}")
        return None

