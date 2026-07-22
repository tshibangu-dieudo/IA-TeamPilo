"""
LangChain chains for the three AI workflows.
See .ai/architecture.md: The Three AI Chains (never more, never fewer).
1. Recommendation Justification
2. Risk Explanation
3. Chat Assistant

All chains use lazy imports so that missing AI dependencies do not
crash Django startup. The ai_engine layer is framework-agnostic:
no Django models, no direct DB access.
"""
import os

AI_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(AI_ENGINE_DIR, "prompts")


def _load_prompt(filename: str) -> str:
    """Load a prompt template from the prompts directory."""
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_recommendation_justification_chain(llm):
    """
    Chain 1 — Recommendation Justification.
    Explains a task reassignment decision made by business rules.
    See docs/13_AI_Architecture.md §3.1.
    """
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    prompt = PromptTemplate.from_template(_load_prompt("recommendation_prompt.txt"))
    return prompt | llm | StrOutputParser()


def get_risk_explanation_chain(llm):
    """
    Chain 2 — Risk Explanation.
    Explains why a project risk score was computed at a given level.
    See docs/13_AI_Architecture.md §3.2.
    """
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    prompt = PromptTemplate.from_template(_load_prompt("risk_explanation_prompt.txt"))
    return prompt | llm | StrOutputParser()


def get_chat_assistant_chain(llm):
    """
    Chain 3 — Chat Assistant.
    Answers natural-language questions grounded in a scoped data snapshot.
    See docs/13_AI_Architecture.md §3.3.

    Input variables expected by the prompt template:
        scope               — string describing the scope (e.g. "project_id=uuid")
        data_snapshot       — JSON string of the scoped data
        conversation_history — string of prior turns (empty string if none)
        question            — the user's current question
    """
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    prompt = PromptTemplate.from_template(_load_prompt("chat_prompt.txt"))
    return prompt | llm | StrOutputParser()
