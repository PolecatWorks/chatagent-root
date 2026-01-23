# This file enables support for adev during development. It is not required for the production application
from chatbot.config import ServiceConfig
from chatbot import app_init
from aiohttp import web
import logging
import logging.config


def create_app():
    print("Starting service")
    # logging.basicConfig(level=logging.DEBUG)

    app = web.Application()

    config_filename = "tests/test_data/config.yaml"
    secrets_dir = "tests/test_data/secrets"

    # with open("tests/test_data/config.yaml", "rb") as config_file:
    configObj: ServiceConfig = ServiceConfig.from_yaml_and_secrets_dir(config_filename, secrets_dir)

    logging.basicConfig(level=logging.DEBUG)
    app = app_init(app, configObj)

    return app
