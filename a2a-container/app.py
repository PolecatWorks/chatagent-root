# This file enables support for adev during development. It is not required for the production application
from fastapi import FastAPI
from mya2a import a2a_init, app_init
from mya2a.config import ServiceConfig
# from mya2a import app_init
import logging
import logging.config
from pydantic_yaml import to_yaml_str


def create_app()-> FastAPI:
    """Create a FastAPI app for dev purposes
    include the config and secrets from the test data

    Returns:
        FastAPI: The test app
    """
    print("Starting service")
    logging.basicConfig(level=logging.DEBUG)


    config_filename = "tests/test_data/config.yaml"
    secrets_dir = "tests/test_data/secrets"

    # with open("tests/test_data/config.yaml", "rb") as config_file:
    configObj: ServiceConfig = ServiceConfig.from_yaml(config_filename, secrets_dir)


    logging.basicConfig(level=logging.DEBUG)
    # app = app_init(app, configObj)

    app = FastAPI(
        title="a2a Development API",
        debug=True,
    )


    app = app_init(app, configObj)
    app = a2a_init(app, configObj)


    print(f"CONFIG =\n{to_yaml_str(configObj, indent=2)}")

    return app
