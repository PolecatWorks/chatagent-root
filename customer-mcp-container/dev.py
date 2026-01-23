from customer.config import ServiceConfig
from customer import app_init

import logging

config_filename = "tests/test_data/config.yaml"
secrets_filename = "tests/test_data/secrets"

configObj: ServiceConfig = ServiceConfig.from_yaml_and_secrets_dir(
    config_filename, secrets_filename
)

logging.config.dictConfig(configObj.logging)

app = app_init(configObj)
