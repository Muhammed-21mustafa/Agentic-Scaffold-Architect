import os
import json
from typing import Dict, Any

class FileSystemBuilder:
    def __init__(self, base_path: str = "./scaffolds"):
        self.base_path = base_path
        
    def build(self, structure_json: str, documentation: str) -> str:
        """Parses the JSON structure and physically creates the project folders and files."""
        os.makedirs(self.base_path, exist_ok=True)
        
        data = json.loads(structure_json)
        root_name = data.get("root_name", "project")
        items = data.get("items", [])
        
        project_dir = os.path.join(self.base_path, root_name)
        os.makedirs(project_dir, exist_ok=True)
        
        # Ana dizine README'yi yaz
        with open(os.path.join(project_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write(documentation)
            
        for item in items:
            self._build_item(project_dir, item)
            
        return project_dir
        
    def _build_item(self, current_path: str, item: Dict[str, Any]):
        name = item.get("name")
        item_type = item.get("type", "file")
        
        target_path = os.path.join(current_path, name)
        
        if item_type == "folder":
            os.makedirs(target_path, exist_ok=True)
            children = item.get("children", [])
            for child in children:
                self._build_item(target_path, child)
        elif item_type == "file":
            if name.lower() == "readme.md":
                return # README.md zaten daha büyük bir mantıkla yazıldı, bunu ezme!
            # Dosyayı yarat (eğer uzantısı .py, .js vs varsa içi boş kalır)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(f"// AI Generated Scaffold: {name}\n")
