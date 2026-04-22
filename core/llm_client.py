import json
import urllib.request
import urllib.error
from typing import Optional

class OllamaClient:
    def __init__(self, host: str, model: str, timeout: int = 120):
        self.host = host.rstrip('/')
        self.model = model
        self.timeout = timeout
        
    def generate(self, prompt: str, system: Optional[str] = None, format: Optional[str] = None) -> str:
        """
        Sends a generation request to the local Ollama instance.
        """
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if system:
            payload["system"] = system
        if format:
            payload["format"] = format
            
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama generation failed: {e}. Is Ollama running at {self.host}?")
        except Exception as e:
            raise RuntimeError(f"Unexpected error communicating with LLM: {e}")
