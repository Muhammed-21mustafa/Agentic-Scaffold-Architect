from pydantic import BaseModel, Field

class Config(BaseModel):
    OLLAMA_HOST: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="llama3")
    MAX_RETRIES: int = Field(default=3)
    TIMEOUT_SECONDS: int = Field(default=120)
