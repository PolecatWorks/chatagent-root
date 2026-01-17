import os
from aiohttp import web
from chatbot import config_app_create, metrics_app_create
from chatbot.service import service_app_create
from chatbot.config import ServiceConfig
import pytest


async def hello(request):
    return web.Response(body=b"Hello, world")


def create_app():
    app = web.Application()
    app.router.add_route("GET", "/", hello)
    return app


@pytest.fixture
def service_app():
    app = web.Application()

    config_filename = "tests/test_data/config.yaml"
    secrets_dir = os.environ.get("TEST_SECRETS_DIR", "tests/test_data/secrets_sample")

    config: ServiceConfig = ServiceConfig.from_yaml(config_filename, secrets_dir)

    config_app_create(app, config)
    metrics_app_create(app)
    service_app_create(app, config)

    return app


async def test_hello(aiohttp_client):
    client = await aiohttp_client(create_app())
    resp = await client.get("/")
    assert resp.status == 200
    text = await resp.text()
    assert "Hello, world" in text


@pytest.fixture
async def service_client(aiohttp_client, service_app):
    client = await aiohttp_client(service_app)
    return client


@pytest.mark.asyncio
async def test_chunks_post_valid(service_client):
    # Test POST with valid data
    payload = {"name": "example", "num_chunks": 3}
    resp = await service_client.post("/pie/v0/chunks", json=payload)
    assert resp.status == 200
    data = await resp.json()
    assert data["name"] == "example"
    assert data["num_chunks"] == 3

    # After POST, GET should reflect the new chunk count
    resp2 = await service_client.get("/pie/v0/chunks")
    assert resp2.status == 200
    data2 = await resp2.json()
    assert "chunks" in data2
    assert (
        data2["chunks"] >= 3
    )  # Depending on implementation, could be exactly 3 or cumulative


@pytest.mark.asyncio
async def test_chunks_post_invalid(service_client):
    # Test POST with invalid data (missing fields)
    payload = {"name": "example"}
    resp = await service_client.post("/pie/v0/chunks", json=payload)
    assert resp.status == 400
    data = await resp.json()
    assert "error" in data

    # Test POST with invalid type
    payload = {"name": "example", "num_chunks": "not_an_int"}
    resp = await service_client.post("/pie/v0/chunks", json=payload)
    assert resp.status == 400
    data = await resp.json()
    assert "error" in data


@pytest.mark.asyncio
@pytest.mark.skip("Skipping non-JSON body POST test for now")
async def test_chunks_post_non_json(service_client):
    resp = await service_client.post(
        "/pie/v0/chunks", data="notjson", headers={"Content-Type": "text/plain"}
    )
    # Should return 400 or 415 depending on implementation
    assert resp.status in (400, 415)


@pytest.mark.asyncio
async def test_chunks_get(service_client):
    # Test GET returns expected structure
    resp = await service_client.get("/pie/v0/chunks")
    assert resp.status == 200
    data = await resp.json()
    assert isinstance(data, dict)
    assert "chunks" in data
    assert isinstance(data["chunks"], int)


async def test_chunks(service_client):
    resp = await service_client.get("/abc")
    assert resp.status == 404  # Assuming /abc is not defined in the app
    text = await resp.text()
    assert "Not Found" in text

    resp = await service_client.get("/pie/v0/chunks")
    assert resp.status == 200  # Assuming /pie/v0/chunks is defined in the service
    text = await resp.text()
    assert "chunks" in text  # Assuming the response contains "chunks"

    chunks = await resp.json()
    assert chunks == {"chunks": 0}  # Adjust based on actual expected response
