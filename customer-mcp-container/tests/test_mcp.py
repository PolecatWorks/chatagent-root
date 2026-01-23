from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


async def test_mcp_app(mcp_app):
    assert mcp_app is not None

    async with Client(mcp_app) as client:
        result = await client.call_tool("hello", {})
        assert len(result.content) > 0
        assert result.content[0].text == "hello"


async def test_http_transport(mcp_server: str):
    """Test actual HTTP transport behavior."""
    async with Client(transport=StreamableHttpTransport(mcp_server)) as client:
        result = await client.ping()
        assert result is True

        result = await client.call_tool("hello", {})

        assert len(result.content) > 0
        assert result.content[0].text == "hello"
