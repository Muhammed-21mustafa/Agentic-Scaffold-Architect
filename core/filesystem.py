import os
import json
from pathlib import Path
from typing import Dict, Any

class FileSystemBuilder:
    def __init__(self, base_path: str = "./scaffolds"):
        self.base_path = Path(base_path)
        
    def build(self, structure_json: str, documentation: str) -> str:
        """Parses the JSON structure and physically creates the project folders and files."""
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        data = json.loads(structure_json)
        root_name = data.get("root_name", "project")
        items = data.get("items", [])
        
        project_dir = self.base_path / root_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Ana dizine README'yi yaz
        with open(project_dir / "README.md", "w", encoding="utf-8") as f:
            f.write(documentation)
            
        for item in items:
            self._build_item(project_dir, item)
            
        self._post_process(project_dir)
            
        return str(project_dir)
        
    def _post_process(self, project_dir: Path):
        """
        Safety net: Fixes common LLM hallucinations that slip through prompt engineering.
        For example: ensuring no duplicate `app = FastAPI()` instances exist outside main.py/app.py.
        """
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                if not file.endswith(".py"):
                    continue
                
                # These are allowed to have app = FastAPI()
                if file in ("main.py", "app.py", "asgi.py"):
                    continue
                
                filepath = Path(root) / file
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if "app = FastAPI()" in content:
                    content = content.replace("from fastapi import FastAPI", "from fastapi import APIRouter")
                    content = content.replace("app = FastAPI()", "router = APIRouter()")
                    content = content.replace("@app.", "@router.")
                    
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"  [POST-PROCESS] Fixed duplicate FastAPI instance in: {filepath}")
        
    def _build_item(self, current_path: Path, item: Dict[str, Any]):
        name = item.get("name")
        item_type = item.get("type", "file")
        content = item.get("content")
        
        target_path = current_path / name
        
        if item_type == "folder":
            target_path.mkdir(parents=True, exist_ok=True)
            children = item.get("children", [])
            for child in children:
                self._build_item(target_path, child)
        elif item_type == "file":
            if name.lower() == "readme.md":
                return # README.md zaten daha büyük bir mantıkla yazıldı, bunu ezme!
            
            # İçerik varsa yaz, yoksa standart scaffold notu bırak
            file_content = content if content else f"// AI Generated Scaffold: {name}\n"
            
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(file_content)

