from typing import Dict, Any

from core.config import Config
from generators.sql_generator import SqlGenerator
from generators.structure_generator import StructureGenerator
from validators.sql_validator import SqlValidator
from validators.json_validator import JsonValidator
from correctors.sql_corrector import SqlCorrector
from correctors.json_corrector import JsonCorrector

class SystemPipeline:
    def __init__(self, config: Config):
        self.config = config
        self.max_retries = config.MAX_RETRIES
        
        self.sql_gen = SqlGenerator(config)
        self.struct_gen = StructureGenerator(config)
        
        self.sql_val = SqlValidator()
        self.json_val = JsonValidator()
        
        self.sql_corr = SqlCorrector(config)
        self.json_corr = JsonCorrector(config)

    def run(self, idea_string: str) -> Dict[str, Any]:
        """Orchestrates the deterministic LLM code generation pipeline."""
        print(f"[*] Step 1: Generating initial SQL for idea: '{idea_string}'")
        sql = self.sql_gen.generate(idea_string)
        
        print("[*] Step 2 & 3: Validating and correcting SQL")
        sql = self._ensure_valid_sql(sql)
        
        print("[*] Step 4: Generating folder structure based on validated SQL")
        folder_json = self.struct_gen.generate(sql)
        
        print("[*] Step 5 & 6: Validating and correcting JSON structure")
        folder_json = self._ensure_valid_json(folder_json, sql)
        
        return {"sql": sql, "structure": folder_json}

    def _ensure_valid_sql(self, sql: str) -> str:
        current_sql = sql
        for attempt in range(self.max_retries):
            is_valid, error_msg = self.sql_val.validate(current_sql)
            if is_valid:
                return current_sql
            
            print(f" [!] SQL validation failed (Attempt {attempt + 1}/{self.max_retries}): {error_msg}")
            if attempt < self.max_retries - 1:
                current_sql = self.sql_corr.fix(current_sql, error_msg)
            
        raise RuntimeError("SQL Pipeline failed to converge after max retries.")

    def _ensure_valid_json(self, json_str: str, sql_context: str) -> str:
        current_json = json_str
        for attempt in range(self.max_retries):
            is_valid, error_msg = self.json_val.validate(current_json)
            if is_valid:
                return current_json
                
            print(f" [!] JSON validation failed (Attempt {attempt + 1}/{self.max_retries}): {error_msg}")
            if attempt < self.max_retries - 1:
                current_json = self.json_corr.fix(current_json, error_msg, sql_context)
            
        raise RuntimeError("JSON Pipeline failed to converge after max retries.")
