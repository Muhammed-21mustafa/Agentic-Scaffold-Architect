from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class Node(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    name: str = Field(description="Name of the file or directory")
    type: str = Field(description="Must be exactly 'file' or 'folder'")
    content: Optional[str] = Field(default=None, description="Boilerplate source code for this file")
    children: Optional[List['Node']] = Field(default=None, description="List of sub-nodes if type is 'folder'")

class FolderStructure(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    root_name: str = Field(description="Name of the root project directory")
    items: List[Node] = Field(description="Contents of the root directory")

# Rebuild model to support recursive type hints
Node.model_rebuild()
