import os
from aiohttp import web
# from customer import config_app_create, metrics_app_create
# from customer.service import service_app_create
from customer import app_init
from customer.config import ServiceConfig
import pytest

from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters, types



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
def service_app():
    app = web.Application()

    config_filename = "tests/test_data/config.yaml"
    secrets_dir = os.environ.get("TEST_SECRETS_DIR", "tests/test_data/secrets")

    config: ServiceConfig = ServiceConfig.from_yaml(config_filename, secrets_dir)

    app = app_init(app, config)

    return app


@pytest.fixture
async def service_client(aiohttp_client, service_app):
    client = await aiohttp_client(service_app)
    return client


# async def test_chunks_post_valid(service_client):
#     # Test POST with valid data
#     payload = {"name": "example", "num_chunks": 3}
#     resp = await service_client.post("/mcp", json=payload)
#     print(f"body = {await resp.text()}")
#     assert resp.status == 200
#     data = await resp.json()
#     assert data["name"] == "example"
#     assert data["num_chunks"] == 3

# async def test_mcp_api(service_client):

#     async with stdio_client(server_params) as (read, write):
#         async with ClientSession(read, write, sampling_callback=handle_sampling_message) as session:
#             # Initialize the connection
#             await session.initialize()
#             prompts = await session.list_prompts()
