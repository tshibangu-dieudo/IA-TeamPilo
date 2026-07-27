"""
Validators for chat responses to ensure grounding and entity matching.
Framework-agnostic — no Django imports.
"""
from typing import Dict, List, Tuple


# Entity keywords for detection
ENTITY_KEYWORDS = {
    'member': ['membre', 'member', 'membres', 'members', 'utilisateur', 'user', 'utilisateurs', 'users'],
    'team': ['équipe', 'team', 'équipes', 'teams'],
    'project': ['projet', 'project', 'projets', 'projects'],
    'task': ['tâche', 'task', 'tâches', 'tasks'],
    'organization': ['organisation', 'organization', 'entreprise', 'company'],
    'skill': ['compétence', 'skill', 'compétences', 'skills'],
}


def detect_requested_entities(question: str) -> List[str]:
    """
    Detect which entities the user is asking about based on keywords.
    
    Args:
        question: The user's question.
    
    Returns:
        List of entity types detected (e.g., ['member', 'project']).
    """
    question_lower = question.lower()
    detected = []
    
    for entity, keywords in ENTITY_KEYWORDS.items():
        if any(keyword in question_lower for keyword in keywords):
            detected.append(entity)
    
    return detected


def check_entity_availability(snapshot: Dict, requested_entities: List[str]) -> Tuple[bool, str]:
    """
    Check if the requested entities are available in the snapshot.
    
    Args:
        snapshot: The data snapshot (new structured format).
        requested_entities: List of entity types requested.
    
    Returns:
        (available: bool, message: str)
        If not available, message explains what's missing.
    """
    if not requested_entities:
        return True, ""
    
    # Check snapshot structure for entity availability
    # Evolving snapshot structure: {projects: [], teams: [], members: [], tasks: [], skills: [], analytics: {}, metadata: {}}
    available_keys = set(snapshot.keys())
    
    # Map entity types to snapshot keys (evolving structure)
    entity_to_keys = {
        'member': ['members'],
        'team': ['teams'],
        'project': ['projects'],
        'task': ['tasks'],
        'organization': [],  # Not currently in snapshot (no organization model exists)
        'skill': ['skills'],  # Skills are now embedded in members, but we check for standalone skills key too
    }
    
    missing_entities = []
    for entity in requested_entities:
        required_keys = entity_to_keys.get(entity, [])
        if not any(key in available_keys for key in required_keys):
            missing_entities.append(entity)
    
    if missing_entities:
        entity_names = {
            'member': 'données de charge des membres',
            'team': 'données d\'équipe',
            'project': 'données de projet',
            'task': 'données de tâches',
            'organization': 'données d\'organisation',
            'skill': 'données de compétences',
        }
        missing_names = [entity_names.get(e, e) for e in missing_entities]
        return False, f"Je ne dispose pas des {', '.join(missing_names)}."
    
    return True, ""


def validate_response_grounding(answer: str, snapshot: Dict) -> Tuple[bool, str]:
    """
    Validate that the response doesn't hallucinate entities or numbers.
    This is a lightweight validation — full semantic validation would require more complex logic.
    
    Args:
        answer: The generated answer.
        snapshot: The data snapshot.
    
    Returns:
        (valid: bool, message: str)
        If invalid, message explains the issue.
    """
    # Extract numbers from answer
    import re
    answer_numbers = re.findall(r'\d+\.?\d*', answer)
    
    # Extract numbers from snapshot
    snapshot_str = str(snapshot)
    snapshot_numbers = re.findall(r'\d+\.?\d*', snapshot_str)
    
    # Check if answer contains numbers not in snapshot (with some tolerance for percentages, etc.)
    # This is a simple heuristic — not perfect but catches obvious hallucinations
    for num in answer_numbers:
        # Skip common small numbers that might be in explanations (1, 2, 3, etc.)
        if float(num) <= 10:
            continue
        # Check if this number appears in the snapshot
        if num not in snapshot_numbers:
            # This might be a hallucinated number
            # For now, we'll be conservative and only flag if it's a large number
            if float(num) > 100:
                return False, f"Réponse contient un nombre ({num}) non présent dans les données."
    
    return True, ""


def get_available_data_description(snapshot: Dict) -> str:
    """
    Generate a description of what data is available in the snapshot.
    Used when the user asks about something not available.
    
    Args:
        snapshot: The data snapshot (evolving structured format).
    
    Returns:
        String describing available data.
    """
    available = []
    
    # Evolving snapshot structure: {projects: [], teams: [], members: [], tasks: [], skills: [], analytics: {}, metadata: {}}
    if snapshot.get('projects'):
        available.append("données de projet")
    if snapshot.get('teams'):
        available.append("données d'équipe")
    if snapshot.get('members'):
        available.append("données des membres et de leur charge de travail")
    if snapshot.get('tasks'):
        available.append("données de tâches")
    if snapshot.get('skills'):
        available.append("données de compétences")
    if snapshot.get('analytics', {}).get('risk_score'):
        available.append("score de risque")
    if snapshot.get('analytics', {}).get('recommendations'):
        available.append("recommandations en attente")
    
    if available:
        return f"Les données disponibles concernent : {', '.join(available)}."
    else:
        return "Aucune donnée n'est actuellement disponible."
