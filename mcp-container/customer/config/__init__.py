from customer.mcp_server import MCPConfig
from pydantic import Field, BaseModel
from pydantic import HttpUrl
from pathlib import Path
from typing import Any, Self
from pydantic import ConfigDict, Field, BaseModel, SecretStr, field_validator, HttpUrl
from typing import Type, Tuple

from pydantic_settings import (
    BaseSettings,
    YamlConfigSettingsSource,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
    NestedSecretsSettingsSource,
)


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

    mcp: MCPConfig = Field(description="MCP configuration")

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        secrets_nested_subdir=True, # Prevents additional fields not defined in the model
        env_nested_delimiter="__"
    )

    @classmethod
    def from_yaml_and_secrets_dir(cls, yaml_file: Path, secrets_path: Path) -> Self:

        cls.model_config["yaml_file"] = yaml_file
        cls.model_config["secrets_dir"] = secrets_path

        return cls()


    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:

        # Explicitly create NestedSecretsSettingsSource with NO prefix
        # so it maps filenames like 'api_key' and 'db/password' directly.
        nested_secrets = NestedSecretsSettingsSource(
            file_secret_settings,
            env_prefix=""
        )

        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls),
            nested_secrets,
        )
