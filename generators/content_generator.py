import re
import json
from typing import Dict, Any, List, Tuple
from core.llm_client import OllamaClient
from core.config import Config
from prompts.structure_prompts import CONTENT_INJECTION_SYSTEM, CONTENT_INJECTION_PROMPT

# File extensions that are worth injecting code into.
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

# Dependency-based generation order.
# Lower number = generated first. Files generated earlier become context for later files.
FILE_PRIORITY = {
    'config/': 10,
    '.env': 10,
    'settings': 10,
    'models/__init__': 20,
    'db': 20,
    'database': 20,
    'models/': 30,
    'schemas/': 40,
    'services/': 50,
    'routes/': 60,
    'api/': 60,
    'main.py': 70,
    'app.py': 70,
    'asgi.py': 70,
    'wsgi.py': 70,
    'tests/': 80,
    'Dockerfile': 90,
    'docker-compose': 90,
    'requirements.txt': 90,
    '.gitignore': 90,
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
        
        Key design decisions:
        1. Files are generated in dependency order (config → models → schemas → routes → main)
        2. Each file receives the code of previously generated files as context
        3. This prevents duplicate classes, phantom imports, and inconsistent APIs
        """
        data = json.loads(structure_json)
        items = data.get("items", [])
        
        # Step 1: Collect all injectable files with their paths
        file_refs = []
        self._collect_files(items, "", file_refs)
        
        # Step 2: Sort by dependency order
        file_refs.sort(key=lambda x: self._get_priority(x[0]))
        
        total = len(file_refs)
        generated_context: Dict[str, str] = {}  # file_path -> generated code
        
        # Step 3: Generate content in order, building context as we go
        for idx, (file_path, item_ref) in enumerate(file_refs, 1):
            print(f"    [{idx}/{total}] Kod enjekte ediliyor -> {file_path}")
            
            # Build context from previously generated files
            context_str = self._build_context(generated_context)
            
            content = self._generate_content(
                requirements, structure_json, file_path, context_str
            )
            item_ref["content"] = content
            generated_context[file_path] = content
        
        data["items"] = items
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _collect_files(
        self,
        items: List[Dict[str, Any]],
        parent_path: str,
        result: List[Tuple[str, Dict[str, Any]]]
    ):
        """Recursively collects all injectable file nodes with their full paths."""
        for item in items:
            name = item.get("name", "")
            item_type = item.get("type", "file")
            
            if item_type == "folder":
                child_path = f"{parent_path}/{name}" if parent_path else name
                self._collect_files(item.get("children", []), child_path, result)
            elif item_type == "file" and self._should_inject(name):
                file_path = f"{parent_path}/{name}" if parent_path else name
                result.append((file_path, item))
    
    def _get_priority(self, file_path: str) -> int:
        """Returns generation priority for a file. Lower = generated first."""
        path_lower = file_path.lower()
        for pattern, priority in FILE_PRIORITY.items():
            if pattern.lower() in path_lower:
                return priority
        return 50  # Default: middle priority
    
    def _build_context(self, generated: Dict[str, str]) -> str:
        """
        Builds a context string from previously generated files.
        To avoid token overflow, includes only the first 20 lines of each file
        (imports + class/function definitions — the most useful part for context).
        """
        if not generated:
            return "(No files generated yet — this is the first file.)"
        
        parts = []
        for path, code in generated.items():
            # Take first 20 lines to keep context manageable
            lines = code.split('\n')[:20]
            summary = '\n'.join(lines)
            if len(code.split('\n')) > 20:
                summary += '\n# ... (truncated)'
            parts.append(f"--- {path} ---\n{summary}")
        
        return '\n\n'.join(parts)
    
    def _generate_content(
        self, requirements: str, structure_json: str,
        file_path: str, previously_generated: str
    ) -> str:
        """Makes a single, focused LLM call to generate content for one file."""
        prompt = CONTENT_INJECTION_PROMPT.format(
            requirements=requirements,
            structure=structure_json,
            file_path=file_path,
            previously_generated=previously_generated
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
        
        # 0. Strip file path prefix if model echoed the target filename
        #    e.g., "config/__init__.py:\nfrom pydantic..." → "from pydantic..."
        text = re.sub(r'^[\w/\\_\-\.]+\.(py|txt|yml|yaml|json|toml|cfg|ini|sh|bat):\s*\n', '', text)
        
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
