"""
Framework-agnostic service for AI-powered chat responses (Chain 3).
Integrates LangChain Watsonx client, chain, and deterministic fallback.
See docs/13_AI_Architecture.md §3.3 and §6.

Rules:
- No Django imports. Receives and returns plain Python dicts/strings.
- If Watsonx is unavailable or output validation fails, falls back to a
  deterministic template that surfaces the raw data snapshot.
- Never raises exceptions to the caller — always returns (answer, source).
"""
import json

from .langchain_client import LangChainWatsonxClient, AIConnectionError
from .chains import get_chat_assistant_chain


def _build_fallback_answer(question: str, data_snapshot: dict) -> str:
    """
    Deterministic fallback per docs/13_AI_Architecture.md §6.
    Returns the raw data snapshot as a readable string.
    """
    try:
        snapshot_text = json.dumps(data_snapshot, indent=2, default=str)
    except Exception:
        snapshot_text = str(data_snapshot)
    return (
        f"AI assistant temporarily unavailable. "
        f"Here is the raw data for your question \"{question}\":\n{snapshot_text}"
    )


def generate_chat_response(
    question: str,
    data_snapshot: dict,
    scope: str = "",
    conversation_history: list | None = None,
) -> tuple[str, str]:
    """
    Generate a chat response grounded in the provided data snapshot.

    Args:
        question: The user's natural-language question.
        data_snapshot: Dict of scoped project/team data assembled by chat/services.py.
        scope: Human-readable scope string (e.g. "project_id=uuid-1234").
        conversation_history: List of prior {"role": ..., "content": ...} dicts,
                              most recent last. None or [] means no history.

    Returns:
        (answer: str, generated_by: str)
        generated_by is 'granite' or 'fallback_template'.
    """
    fallback = _build_fallback_answer(question, data_snapshot)

    # Format conversation history as a readable string for the prompt
    history_lines = []
    for msg in (conversation_history or []):
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")
        history_lines.append(f"{role}: {content}")
    history_text = "\n".join(history_lines) if history_lines else "(none)"

    # Serialise snapshot for the prompt
    try:
        snapshot_text = json.dumps(data_snapshot, indent=2, default=str)
    except Exception:
        snapshot_text = str(data_snapshot)

    try:
        client = LangChainWatsonxClient()
        chain = get_chat_assistant_chain(client.llm)

        prompt_inputs = {
            "scope": scope or "all accessible data",
            "data_snapshot": snapshot_text,
            "conversation_history": history_text,
            "question": question,
        }

        answer = chain.invoke(prompt_inputs)
        answer = answer.strip()

        if not answer or len(answer) < 5:
            return fallback, "fallback_template"

        # Hard length cap — reject runaway responses
        if len(answer) > 800:
            answer = answer[:800].rsplit(" ", 1)[0] + "…"

        return answer, "granite"

    except (AIConnectionError, Exception):
        return fallback, "fallback_template"
