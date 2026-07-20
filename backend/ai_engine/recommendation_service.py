"""
Framework-agnostic service for AI-generated recommendation justifications.
Integrates LangChain Watsonx.ai client, chain, validation, and fallback template.
"""
from .langchain_client import LangChainWatsonxClient, AIConnectionError
from .chains import get_recommendation_justification_chain
from .validators import validate_recommendation_output, AIValidationError


def generate_recommendation_justification(input_context: dict) -> tuple[str, str]:
    """
    Generate recommendation justification using Watsonx Granite LLM.
    Falls back to a deterministic template if call fails, credentials are missing,
    or output validation fails.
    
    Args:
        input_context (dict): Structured input context matching Chain 1 contract.
        
    Returns:
        tuple: (justification_text, generated_by)
               where generated_by is 'granite' or 'fallback_template'.
    """
    # 1. Set up the deterministic fallback string per docs/13_AI_Architecture.md §6
    overloaded_user = input_context.get('overloaded_user', {})
    candidate = input_context.get('candidate', {})
    task = input_context.get('task', {})
    rule_context = input_context.get('rule_context', {})
    
    overloaded_name = overloaded_user.get('name', 'User')
    overloaded_workload = overloaded_user.get('workload_pct', 0)
    candidate_name = candidate.get('name', 'Teammate')
    candidate_workload = candidate.get('workload_pct', 0)
    task_title = task.get('title', 'Task')
    
    fallback_text = (
        f"{candidate_name} has matching skills and lower current workload "
        f"({candidate_workload}%) than {overloaded_name} ({overloaded_workload}%)."
    )
    
    # 2. Try watsonx/Granite LLM path
    try:
        # Instantiate client (raises AIConnectionError if config is missing)
        client = LangChainWatsonxClient()
        
        # Get compiled chain
        chain = get_recommendation_justification_chain(client.llm)
        
        # Map input contract to prompt template variables
        prompt_inputs = {
            "overloaded_user_name": overloaded_name,
            "overloaded_user_workload": overloaded_workload,
            "candidate_name": candidate_name,
            "candidate_workload": candidate_workload,
            "candidate_skills": ", ".join(candidate.get('matching_skills', [])),
            "task_title": task_title,
            "task_hours": task.get('estimated_hours', 0),
            "task_deadline": str(task.get('deadline', '')),
            "candidate_rank_reason": rule_context.get('candidate_rank_reason', ''),
        }
        
        # Invoke chain to generate response
        response_text = chain.invoke(prompt_inputs)
        
        # Validate output
        validated = validate_recommendation_output(response_text, input_context)
        return validated['justification'], 'granite'
        
    except (AIConnectionError, AIValidationError, Exception):
        # Graceful degradation: catch all client/validation/network exceptions
        # and return the template justification flagged as 'fallback_template'
        return fallback_text, 'fallback_template'
