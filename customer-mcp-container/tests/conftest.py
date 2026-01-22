import pytest
from customer.config import ServiceConfig
from customer import app_init
from customer.mcp_server import mcp_init
from fastmcp.utilities.tests import run_server_async



def pytest_addoption(parser):
    parser.addoption(
        "--enable-livellm", action="store_true", help="Enable live LLM tests"
    )



@pytest.fixture
def mcp_app():
    config_filename = "tests/test_data/config.yaml"
    secrets_dir =  "tests/test_data/secrets"

    config: ServiceConfig = ServiceConfig.from_yaml_and_secrets_dir(config_filename, secrets_dir)

    mcp_app = mcp_init(config.mcp)

    return mcp_app


@pytest.fixture
async def mcp_server(mcp_app):
    async with run_server_async(mcp_app) as url:
        yield url


@pytest.fixture
def service_app():
    app = web.Application()

    config_filename = "tests/test_data/config.yaml"
    secrets_dir = os.environ.get("TEST_SECRETS_DIR", "tests/test_data/secrets")

    config: ServiceConfig = ServiceConfig.from_yaml(config_filename, secrets_dir)

    app = app_init(app, config)

    return app
