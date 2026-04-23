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
        Gerçek Post-Processing: Şema ve modellerdeki inatçı LLM halüsinasyonlarını 
        (örn: router = APIRouter() veya app = FastAPI()) regex ile bulup kökünden siler.
        """
        import re
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                if not file.endswith(".py"):
                    continue
                
                # Bu temizlik sadece config, models ve schemas klasörlerinde yapılır
                # (main.py veya routes/ dosyalarına dokunmayız çünkü onlarda bu kodlar gerçektir)
                if "models" not in root and "schemas" not in root and "config" not in root:
                    continue
                    
                filepath = Path(root) / file
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                original_content = content
                
                # Yanlışlıkla üretilmiş app/router tanımlarını ve importlarını sil
                content = re.sub(r'^.*?app\s*=\s*FastAPI\(\).*?$\n?', '', content, flags=re.MULTILINE)
                content = re.sub(r'^.*?router\s*=\s*APIRouter\(\).*?$\n?', '', content, flags=re.MULTILINE)
                content = re.sub(r'^from fastapi import .*?(FastAPI|APIRouter).*?$\n?', '', content, flags=re.MULTILINE)
                
                # Eğer değişiklik yapıldıysa dosyayı kaydet
                if content != original_content:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content.strip() + '\n')
                    print(f"  [POST-PROCESS] Halüsinasyon kökünden temizlendi: {filepath}")
        
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

