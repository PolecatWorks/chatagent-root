from pydantic import Field, BaseModel
from .genai import GenaiConfig


class CurrencyAgentConfig(BaseModel):
    genai: GenaiConfig = Field(description="Genai configuration")
