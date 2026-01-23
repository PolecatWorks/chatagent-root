# from .tool import ToolBoxConfig, ToolConfig
from pydantic import Field, BaseModel
from mya2a.hams.config import HamsConfig
from pydantic import Field, BaseModel, SecretStr, field_validator
from pydantic import HttpUrl
from pydantic_settings import BaseSettings, YamlConfigSettingsSource, SettingsConfigDict
from pydantic_file_secrets import FileSecretsSettingsSource
from pathlib import Path
from typing import Any, Self, Literal # TODO: Review Self and Literal for Python version compatibility
from datetime import timedelta
from pydantic import ConfigDict, Field, BaseModel, SecretStr, field_validator, HttpUrl

from .currency import CurrencyAgentConfig

import os


# TODO: Look here in future: https://github.com/pydantic/pydantic/discussions/2928#discussioncomment-4744841
class WebServerConfig(BaseModel):
    """
    Configuration for the web server
    """

    url: HttpUrl = Field(description="Host to listen on")
    prefix: str = Field(description="Prefix for the name of the resources")




class ServiceConfig(BaseSettings):
    """
    Configuration for the service
    """

    logging: dict[str, Any] = Field(description="Logging configuration")


    webservice: WebServerConfig = Field(description="Web server configuration")
    hams: HamsConfig = Field(description="Health and monitoring configuration")
    currency: CurrencyAgentConfig = Field("Config for currency agent")

    model_config = {
        # secrets_dir='/run/secrets',
        "secrets_nested_subdir": True,
    }

    @classmethod
    def from_yaml(cls, config_path: Path, secrets_path: Path) -> Self:
        return cls(
            **YamlConfigSettingsSource(cls, config_path)(), _secrets_dir=secrets_path
        )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            FileSecretsSettingsSource(file_secret_settings),
        )
