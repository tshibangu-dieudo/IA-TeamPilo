"""
Output validation layer for AI responses.
Protects against hallucinations and contract breaches.
See docs/13_AI_Architecture.md §5.
"""
import re


class AIValidationError(Exception):
    """Raised when the AI generated content fails safety or contract validation."""
    pass


def validate_recommendation_output(response: str, input_context: dict) -> dict:
    """
    Validates recommendation output:
    1. Check required text is present and within length bounds.
    2. Check that no unexpected numbers/metrics appear that aren't in input_context.
    
    Args:
        response: String response from LLM chain.
        input_context: Original dictionary context passed to recommendation.
        
    Returns:
        dict: Validated parsed data.
        
    Raises:
        AIValidationError: If validation checks fail.
    """
    text = response.strip()
    if not text or len(text) < 10:
        raise AIValidationError("AI output is empty or too short.")
    if len(text) > 500:
        raise AIValidationError("AI output exceeds maximum length of 500 characters.")
    
    # 2. Extract digit sequences from response and ensure they match numbers in the context
    digits = re.findall(r'\b\d+\b', text)
    
    # Collect all strings and values from the input context to verify against
    allowed_values = []
    def collect_values(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                collect_values(v)
        elif isinstance(obj, list):
            for item in obj:
                collect_values(item)
        else:
            allowed_values.append(str(obj).lower())
            
    collect_values(input_context)
    
    for digit in digits:
        # Check if the digit is a substring of any allowed context value
        found = False
        for allowed in allowed_values:
            if digit in allowed:
                found = True
                break
        
        # Allow standard small counts (1st, 2 tasks, etc.) and current year 2026
        if not found and digit not in ['1', '2', '3', '2026']:
            raise AIValidationError(
                f"AI response failed validation: contains unexpected number '{digit}' "
                "not present in the input context."
            )
            
    return {"justification": text}
