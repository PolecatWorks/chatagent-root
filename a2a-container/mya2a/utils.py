



import httpx
from langchain_core.language_models import BaseChatModel
from mya2a.config.genai import AzureOpenai, GenaiConfig, GoogleGenai


def create_chat_model(config: GenaiConfig) -> BaseChatModel:

    match config:
        case GoogleGenai():
            from langchain_google_genai import ChatGoogleGenerativeAI

            model = ChatGoogleGenerativeAI(
                model=config.model,
                google_api_key=config.api_key.get_secret_value(),
                # http_client=httpx_client,
            )
        case AzureOpenai():
            from langchain_openai import AzureChatOpenAI

            httpx_client = httpx.Client(verify=config.httpx_verify_ssl)

            # https://python.langchain.com/api_reference/openai/llms/langchain_openai.llms.azure.AzureOpenAI.html#langchain_openai.llms.azure.AzureOpenAI.http_client
            model = AzureChatOpenAI(
                model=config.model,
                azure_endpoint=str(config.azure_endpoint),
                api_version=config.azure_api_version,
                api_key=config.azure_api_key.get_secret_value(),
                http_client=httpx_client,
            )
        case _:
            raise ValueError(
                f"Unsupported model provider: {config.model_provider}"
            )


    return model
