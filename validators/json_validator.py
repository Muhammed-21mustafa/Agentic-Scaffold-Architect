import json
from typing import Tuple, Optional
from schemas.folder_schema import FolderStructure
from pydantic import ValidationError

class JsonValidator:
    def validate(self, json_string: str) -> Tuple[bool, Optional[str]]:
        """
        Validates whether a raw LLM string can be parsed and maps to the Pydantic schema.
        Returns (is_valid, error_message).
        """
        if not json_string or not json_string.strip():
            return False, "JSON string is empty."
            
        try:
            # Standard Python JSON parse check
            parsed_json = json.loads(json_string)
            
            # Deep structure validation with Pydantic
            FolderStructure.model_validate(parsed_json)
            
            return True, None
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON Syntax: {str(e)}"
        except ValidationError as e:
            return False, f"JSON Schema Validation Error: {e.json()}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
