"""
Intent classifier for chat routing.
Lightweight keyword/pattern-based classification to distinguish between:
- TEAMPILOT_DATA: Questions about project/team/task data
- GENERAL_KNOWLEDGE: General project management questions

Framework-agnostic — no Django imports.
"""
import re
from typing import Tuple


# Keyword lists for TeamPilot data questions
TEAMPILOT_DATA_KEYWORDS = [
    # Project-related
    'projet', 'project', 'projets', 'projects',
    # Task-related
    'tâche', 'task', 'tâches', 'tasks',
    # Team-related
    'équipe', 'team', 'équipes', 'teams',
    # Workload-related
    'charge', 'workload', 'surcharge', 'overloaded',
    # Risk-related
    'risque', 'risk', 'risques', 'risks',
    # Recommendation-related
    'recommandation', 'recommendation', 'recommandations',
    # Status-related
    'statut', 'status', 'état', 'state',
    # Progress-related
    'avancement', 'progress', 'progression',
    # Member-related
    'membre', 'member', 'membres',
    # Count-related
    'combien', 'nombre', 'count', 'how many',
    # Data-related
    'données', 'data', 'donnée',
    # Specific entities
    'actif', 'active', 'en retard', 'delayed', 'bloqué', 'blocked',
]

# Keyword lists for general knowledge questions
GENERAL_KNOWLEDGE_KEYWORDS = [
    # How-to questions
    'comment', 'how', 'how to',
    # Best practices
    'meilleure pratique', 'best practice', 'bonne pratique',
    # Improvement
    'améliorer', 'improve', 'amélioration',
    # Tips
    'conseil', 'tip', 'astuce',
    # Methodology
    'méthode', 'methodology', 'méthodologie',
    # Agile
    'agile', 'scrum', 'kanban',
    # General advice
    'conseil', 'advice', 'suggestion',
    # Learning
    'apprendre', 'learn', 'formation',
]


def classify_intent(question: str) -> Tuple[str, float]:
    """
    Classify user question intent using keyword matching.
    
    Args:
        question: The user's natural-language question.
    
    Returns:
        (intent: str, confidence: float)
        intent: "TEAMPILOT_DATA" or "GENERAL_KNOWLEDGE"
        confidence: Float between 0.0 and 1.0 (based on keyword match ratio)
    """
    question_lower = question.lower()
    
    # Count keyword matches for each category
    teampilot_matches = sum(
        1 for keyword in TEAMPILOT_DATA_KEYWORDS
        if keyword in question_lower
    )
    
    general_matches = sum(
        1 for keyword in GENERAL_KNOWLEDGE_KEYWORDS
        if keyword in question_lower
    )
    
    # Calculate confidence scores
    total_keywords = len(TEAMPILOT_DATA_KEYWORDS) + len(GENERAL_KNOWLEDGE_KEYWORDS)
    teampilot_score = teampilot_matches / len(TEAMPILOT_DATA_KEYWORDS) if TEAMPILOT_DATA_KEYWORDS else 0
    general_score = general_matches / len(GENERAL_KNOWLEDGE_KEYWORDS) if GENERAL_KNOWLEDGE_KEYWORDS else 0
    
    # Determine intent based on higher score
    if teampilot_score > general_score:
        confidence = min(teampilot_score * 2, 1.0)  # Boost confidence for clearer matches
        return "TEAMPILOT_DATA", confidence
    elif general_score > teampilot_score:
        confidence = min(general_score * 2, 1.0)
        return "GENERAL_KNOWLEDGE", confidence
    else:
        # Tie or no matches - default to TEAMPILOT_DATA (safer for a project management tool)
        return "TEAMPILOT_DATA", 0.5
