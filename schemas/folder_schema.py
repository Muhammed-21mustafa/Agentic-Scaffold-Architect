from typing import List, Optional
from pydantic import BaseModel, Field

class Node(BaseModel):
    name: str = Field(description="Name of the file or directory")
    type: str = Field(description="Must be exactly 'file' or 'folder'")
    children: Optional[List['Node']] = Field(default=None, description="List of sub-nodes if type is 'folder'")

class FolderStructure(BaseModel):
    root_name: str = Field(description="Name of the root project directory")
    items: List[Node] = Field(description="Contents of the root directory")

# Rebuild model to support recursive type hints
Node.model_rebuild()
