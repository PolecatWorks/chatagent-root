import os
from fastmcp import Client
from aiohttp import web
from customer import app_init
from customer.mcp_server import mcp_init
from customer.config import ServiceConfig
import pytest

from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters, types
from fastmcp.utilities.tests import run_server_async
from fastmcp.client.transports import StreamableHttpTransport


def create_app():
    app = web.Application()
    app.router.add_route("GET", "/", hello)
    return app


async def hello(request):
    return web.Response(body=b"Hello, world")


async def test_hello(aiohttp_client):
    client = await aiohttp_client(create_app())
    resp = await client.get("/")
    assert resp.status == 200
    text = await resp.text()
    assert "Hello, world" in text


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


async def test_mcp_app(mcp_app):
    assert mcp_app is not None

    async with Client(mcp_app) as client:
        result = await client.call_tool("hello", {})
        assert len(result.content) > 0
        assert result.content[0].text == "hello"


async def test_http_transport(mcp_server: str):
    """Test actual HTTP transport behavior."""
    async with Client(
        transport=StreamableHttpTransport(mcp_server)
    ) as client:
        result = await client.ping()
        assert result is True

        result = await client.call_tool("hello", {})

        assert len(result.content) > 0
        assert result.content[0].text == "hello"
