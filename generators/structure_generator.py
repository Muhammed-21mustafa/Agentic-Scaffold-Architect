from core.llm_client import OllamaClient
from core.config import Config
from prompts.structure_prompts import STRUCTURE_GENERATION_SYSTEM, STRUCTURE_GENERATION_PROMPT

class StructureGenerator:
    def __init__(self, config: Config):
        self.client = OllamaClient(host=config.OLLAMA_HOST, model=config.OLLAMA_MODEL)
        
    def generate(self, requirements: str) -> str:
        """
        Transforms user requirements into a target JSON folder structure.
        """
        prompt = STRUCTURE_GENERATION_PROMPT.format(requirements=requirements)
        
        # Explicit format restriction for local Ollama if supported
        response = self.client.generate(prompt=prompt, system=STRUCTURE_GENERATION_SYSTEM, format="json")
        return response.strip()
