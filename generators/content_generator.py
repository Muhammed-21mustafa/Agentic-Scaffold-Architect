import re
import json
from typing import Dict, Any, List
from core.llm_client import OllamaClient
from core.config import Config
from prompts.structure_prompts import CONTENT_INJECTION_SYSTEM, CONTENT_INJECTION_PROMPT

# File extensions that are worth injecting code into.
# Everything else (e.g., images, binaries) is skipped.
INJECTABLE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs',
    '.html', '.css', '.scss',
    '.json', '.yaml', '.yml', '.toml',
    '.xml', '.gradle',
    '.md', '.txt',
    '.env', '.env.example',
    '.sh', '.bat',
    '.cfg', '.ini', '.conf',
}

# Files that are always worth injecting, regardless of extension
INJECTABLE_FILENAMES = {
    'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
    'Makefile', 'Procfile',
    'requirements.txt', 'package.json', 'pom.xml', 'build.gradle',
    '.gitignore', '.dockerignore', '.editorconfig',
}


class ContentGenerator:
    def __init__(self, config: Config):
        self.client = OllamaClient(
            host=config.OLLAMA_HOST,
            model=config.OLLAMA_MODEL,
            timeout=config.TIMEOUT_SECONDS
        )
    
    def inject_all(self, requirements: str, structure_json: str) -> str:
        """
        Walks the validated structure tree and injects boilerplate content
        into each important file via individual, focused LLM calls.
        Returns the updated structure JSON string with content fields filled.
        """
        data = json.loads(structure_json)
        items = data.get("items", [])
        
        total_files = self._count_injectable_files(items)
        injected = [0]  # mutable counter for nested function
        
        self._inject_recursive(items, requirements, structure_json, "", total_files, injected)
        
        data["items"] = items
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _inject_recursive(
        self,
        items: List[Dict[str, Any]],
        requirements: str,
        structure_json: str,
        parent_path: str,
        total: int,
        injected: list
    ):
        """Recursively walks the tree and injects content into file nodes."""
        for item in items:
            name = item.get("name", "")
            item_type = item.get("type", "file")
            
            if item_type == "folder":
                children = item.get("children", [])
                child_path = f"{parent_path}/{name}" if parent_path else name
                self._inject_recursive(children, requirements, structure_json, child_path, total, injected)
            elif item_type == "file" and self._should_inject(name):
                file_path = f"{parent_path}/{name}" if parent_path else name
                injected[0] += 1
                print(f"    [{injected[0]}/{total}] Kod enjekte ediliyor -> {file_path}")
                
                content = self._generate_content(requirements, structure_json, file_path)
                item["content"] = content
    
    def _generate_content(self, requirements: str, structure_json: str, file_path: str) -> str:
        """Makes a single, focused LLM call to generate content for one file."""
        prompt = CONTENT_INJECTION_PROMPT.format(
            requirements=requirements,
            structure=structure_json,
            file_path=file_path
        )
        response = self.client.generate(prompt=prompt, system=CONTENT_INJECTION_SYSTEM)
        return self._clean_llm_output(response)
    
    @staticmethod
    def _clean_llm_output(raw: str) -> str:
        """
        Aggressively cleans LLM output to extract only the source code.
        Handles: markdown wrappers, trailing ```, 'Note:' blocks, and conversational text.
        """
        text = raw.strip()
        if not text:
            return ""
        
        # 1. Extract content from ```lang ... ``` wrapper if present
        md_match = re.search(r'^```[^\n]*\n(.*?)```', text, re.DOTALL)
        if md_match:
            text = md_match.group(1).strip()
        
        # 2. Remove any remaining standalone ``` lines
        lines = text.split('\n')
        lines = [line for line in lines if line.strip() != '```']
        
        # 3. Remove trailing conversational text (Note:, Explanation:, etc.)
        clean_lines = []
        for line in lines:
            # If we hit a line that starts with known LLM commentary patterns, stop
            stripped = line.strip().lower()
            if stripped.startswith(('note:', 'explanation:', 'this is ', 'the above ', 'here is ')):
                break
            clean_lines.append(line)
        
        # 4. Remove trailing blank lines
        while clean_lines and not clean_lines[-1].strip():
            clean_lines.pop()
        
        return '\n'.join(clean_lines)
    
    def _should_inject(self, filename: str) -> bool:
        """Determines if a file is worth injecting code into."""
        if filename.lower() == "readme.md":
            return False  # README is handled by the Doc Agent
        
        if filename in INJECTABLE_FILENAMES:
            return True
        
        dot_idx = filename.rfind('.')
        if dot_idx != -1:
            ext = filename[dot_idx:].lower()
            return ext in INJECTABLE_EXTENSIONS
        
        return False
    
    def _count_injectable_files(self, items: List[Dict[str, Any]]) -> int:
        """Counts how many files will receive content injection."""
        count = 0
        for item in items:
            if item.get("type") == "folder":
                count += self._count_injectable_files(item.get("children", []))
            elif item.get("type") == "file" and self._should_inject(item.get("name", "")):
                count += 1
        return count
