"""
LangChain chains for the three AI workflows.
See .ai/architecture.md: The Three AI Chains (never more, never fewer).
1. Recommendation Justification
2. Risk Explanation
3. Chat Assistant
"""
import os

AI_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(AI_ENGINE_DIR, "prompts")


def get_recommendation_justification_chain(llm):
    """
    Compile and return the LCEL chain for task reassignment recommendation.
    Imports are inside the function to prevent import crashes during Django startup
    when AI libraries are not installed in the environment.
    """
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    prompt_path = os.path.join(PROMPTS_DIR, "recommendation_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        template_text = f.read()
    
    prompt = PromptTemplate.from_template(template_text)
    return prompt | llm | StrOutputParser()
