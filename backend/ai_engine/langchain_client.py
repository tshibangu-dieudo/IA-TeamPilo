"""
LangChain client for IBM Granite via watsonx.ai.
Framework-agnostic — no Django imports here.
See .ai/architecture.md: ai_engine never imports Django models.
"""
import os


class AIConnectionError(Exception):
    """Raised when the AI engine is not configured or cannot connect."""
    pass


class LangChainWatsonxClient:
    """
    Wrapper client around LangChain's WatsonxLLM / WatsonxAI interface.
    Gracefully handles missing credentials or missing package installations.
    """
    def __init__(self):
        # Read from environment variables ONLY per critical constraint
        self.api_key = os.environ.get("WATSONX_API_KEY")
        self.project_id = os.environ.get("WATSONX_PROJECT_ID")
        # Support both WATSONX_URL and WATSONX_API_URL env vars
        self.url = os.environ.get("WATSONX_URL") or os.environ.get("WATSONX_API_URL")
        self.model_id = os.environ.get("GRANITE_MODEL_ID", "ibm/granite-13b-chat-v2")

        if not self.api_key or not self.project_id or not self.url:
            raise AIConnectionError(
                "IBM watsonx.ai credentials are not fully configured in the environment. "
                "Please set WATSONX_API_KEY, WATSONX_PROJECT_ID, and WATSONX_URL."
            )

        try:
            # Prefer the newer langchain-ibm integration package
            from langchain_ibm import WatsonxLLM
            self.llm = WatsonxLLM(
                model_id=self.model_id,
                url=self.url,
                apikey=self.api_key,
                project_id=self.project_id,
                params={
                    "decoding_method": "sample",
                    "max_new_tokens": 200,
                    "temperature": 0.3,
                }
            )
        except ImportError:
            try:
                # Fall back to langchain-community integration
                from langchain_community.llms import WatsonxAI
                self.llm = WatsonxAI(
                    model_id=self.model_id,
                    url=self.url,
                    apikey=self.api_key,
                    project_id=self.project_id,
                    params={
                        "decoding_method": "sample",
                        "max_new_tokens": 200,
                        "temperature": 0.3,
                    }
                )
            except ImportError as err:
                raise AIConnectionError(
                    "No LangChain integration package (langchain_ibm or langchain_community) "
                    "could be loaded. Make sure the dependencies are installed."
                ) from err
