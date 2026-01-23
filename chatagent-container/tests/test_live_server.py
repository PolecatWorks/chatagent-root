import os
from aiohttp import web

from chatbot import config_app_create, keys, metrics_app_create
from chatbot.config import ServiceConfig
from chatbot.langgraph import LanggraphHandler, langgraph_app_create
from chatbot.mcp_client import mcp_app_create
import pytest

import pytest
import asyncio

from aiohttp import web, ClientSession


TEST_SERVER_PORT = 8080  # Define your test server port here


@pytest.fixture
def server():
    """
    Fixture to create and start the aiohttp test server.
    """

    config_filename = "tests/test_data/config.yaml"
    default_secrets = "tests/test_data/secrets" if os.path.exists("tests/test_data/secrets") else "tests/test_data/secrets_sample"
    secrets_dir = os.environ.get("TEST_SECRETS_DIR", default_secrets)

    config: ServiceConfig = ServiceConfig.from_yaml_and_secrets_dir(config_filename, secrets_dir)
    config.myai.toolbox.mcps = []  # Disable MCP connections for tests

    app = web.Application()

    # Initialize the app with the configuration
    # app = app_init(app, config)

    config_app_create(app, config)
    metrics_app_create(app)
    mcp_app_create(app, config)
    langgraph_app_create(app, config)

    runner = web.AppRunner(app)
    asyncio.run(runner.setup())
    site = web.TCPSite(runner, "localhost", TEST_SERVER_PORT)
    asyncio.run(site.start())

    yield

    asyncio.run(site.stop())
    asyncio.run(runner.cleanup())


async def test_llm_chat(server):
    """
    Test the LLM conversation handler's chat functionality.
    """
    async with ClientSession() as session:
        print("test not implemented yet")
        # Create a conversation account
        # conversation_account = ConversationAccount(
        #     id="test-conversation", name="Test Conversation", conversation_type="test-type"
        # )

        # # Create an instance of LLMConversationHandler
        # llm_handler = LLMConversationHandler(session)

        # # Call the chat method
        # reply = await llm_handler.chat(
        #     conversation_account, "my-identity", "Hello, how are you?"
        # )

        # # Assert that the reply is not None
        # assert reply is not None
        # assert isinstance(reply, str)  # Assuming the reply is a string
        # assert "Hello" in reply
