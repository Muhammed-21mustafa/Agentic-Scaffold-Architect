from core.llm_client import OllamaClient
from core.config import Config
from prompts.structure_prompts import DOC_GENERATION_SYSTEM, DOC_GENERATION_PROMPT
from core.utils import extract_markdown

class DocGenerator:
    def __init__(self, config: Config):
        self.client = OllamaClient(host=config.OLLAMA_HOST, model=config.OLLAMA_MODEL)
        
    def generate(self, requirements: str, structure_json: str) -> str:
        """
        Creates a high-quality README based on the chosen architecture mapping.
        """
        prompt = DOC_GENERATION_PROMPT.format(requirements=requirements, structure=structure_json)
        response = self.client.generate(prompt=prompt, system=DOC_GENERATION_SYSTEM)
        
        # Clean potential markdown wrappers safely
        return extract_markdown(response)
