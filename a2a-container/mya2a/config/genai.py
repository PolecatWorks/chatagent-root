

from pydantic import BaseModel, Field, SecretStr




class GoogleGenai(BaseModel):
    """Configuration for LangChain loading of Google
    """
    model: str = Field(
        description="The model to use (e.g., 'gemini-1.5-flash-latest' or GitHub model name)"
    )
    api_key: SecretStr = Field(
        description="Optional API key for authenticated access to Genai model",
    )


class AzureOpenai(BaseModel):
    """Configuration for LangChain loading of Azure Openai
    """
    model: str = Field(
        description="The model to use (e.g., 'gemini-1.5-flash-latest' or GitHub model name)"
    )
    api_key: SecretStr = Field(
        description="Optional API key for authenticated access to Genai model",
    )
    api_version: str = Field(
        description="API version for Azure OpenAI, default is None"
    )
    http_client_verify: bool = Field(
        description="Whether to verify SSL certificates for HTTP requests, can be a boolean or a path to a CA bundle"
    )
    azure_endpoint: str = Field(
        description="Azure OpenAI endpoint for LangChain"
    )


GenaiConfig = GoogleGenai | AzureOpenai
