from core.llm_client import OllamaClient
from core.config import Config
from prompts.structure_prompts import JSON_CORRECTION_SYSTEM, JSON_CORRECTION_PROMPT

class JsonCorrector:
    def __init__(self, config: Config):
        self.client = OllamaClient(host=config.OLLAMA_HOST, model=config.OLLAMA_MODEL)
        
    def fix(self, bad_json: str, error_message: str, requirements: str) -> str:
        """
        Asks the LLM to fix an invalid JSON structure based on requirements.
        """
        prompt = JSON_CORRECTION_PROMPT.format(
            requirements=requirements,
            bad_json=bad_json, 
            error=error_message
        )
        response = self.client.generate(prompt=prompt, system=JSON_CORRECTION_SYSTEM, format="json")
        return response.strip()
