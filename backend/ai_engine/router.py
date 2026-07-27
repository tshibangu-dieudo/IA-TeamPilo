"""
Intent router for chat requests.
Orchestrates routing between TeamPilot data mode and general knowledge mode.
Framework-agnostic — no Django imports.
"""
from typing import Tuple, Optional

from .intent_classifier import classify_intent
from .chat_service import generate_chat_response, generate_general_knowledge_response


def route_chat_request(
    question: str,
    intent: str,
    data_snapshot: Optional[dict] = None,
    scope: str = "",
    conversation_history: Optional[list] = None,
) -> Tuple[str, str, str]:
    """
    Route chat request based on pre-classified intent.
    
    Using approach (a): intent is classified once by the caller (services.py),
    then passed here to avoid duplicate classification.
    
    Args:
        question: The user's natural-language question.
        intent: Pre-classified intent ("TEAMPILOT_DATA" or "GENERAL_KNOWLEDGE").
        data_snapshot: Dict of scoped project/team data (only for TEAMPILOT_DATA mode).
        scope: Human-readable scope string (e.g. "project_id=uuid-1234").
        conversation_history: List of prior {"role": ..., "content": ...} dicts.
    
    Returns:
        (answer: str, generated_by: str, intent: str)
        generated_by: 'granite' or 'fallback_template'
        intent: "TEAMPILOT_DATA" or "GENERAL_KNOWLEDGE"
    """
    if intent == "TEAMPILOT_DATA":
        # Use data snapshot mode
        answer, generated_by = generate_chat_response(
            question=question,
            data_snapshot=data_snapshot or {},
            scope=scope,
            conversation_history=conversation_history,
        )
    elif intent == "GENERAL_KNOWLEDGE":
        # Use general knowledge mode (no snapshot)
        answer, generated_by = generate_general_knowledge_response(
            question=question,
        )
    else:
        # Unknown intent - default to TeamPilot data mode for safety
        answer, generated_by = generate_chat_response(
            question=question,
            data_snapshot=data_snapshot or {},
            scope=scope,
            conversation_history=conversation_history,
        )
        intent = "TEAMPILOT_DATA"
    
    return answer, generated_by, intent
