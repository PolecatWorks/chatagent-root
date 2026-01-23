from fastmcp import FastMCP
from pydantic import BaseModel

from random import randint
import logging
from fastmcp.server.context import Context
import httpx

logger = logging.getLogger(__name__)


class Customer(BaseModel):
    name: str
    id: int


class ChaserAggregate(BaseModel):
    """
    Represents the aggregate state of a chaser event.

    Based on the response from /k8s-micro/v0/chaser/{key}
    Example: {"type":"com.polecatworks.chaser.Aggregate",
              "names":["Ben01"],"count":22950,
              "latest":1768516413076752931,"longest":10000}
    """

    type: str
    names: list[str]
    count: int
    latest: int  # timestamp in nanoseconds
    longest: int  # duration in milliseconds


class MCPConfig(BaseModel):
    """
    Configuration of the MCP server
    """

    name: str
    instructions: str
    chaser_service_url: str = "http://dev.k8s/k8s-micro/v0/chaser"


def mcp_init(config: MCPConfig):
    fastmcp_app = FastMCP(name=config.name, instructions=config.instructions)

    @fastmcp_app.tool(description="say hello")
    def hello(ctx: Context):
        return "hello"

    @fastmcp_app.tool(description="return a random number")
    def random_number(ctx: Context):
        randnum = randint(1, 100)
        print(f"Random number: {randnum}")
        logger.error(f"Random number: {randnum}")
        return randnum

    @fastmcp_app.tool(description="return a customer")
    async def get_customer(ctx: Context, id: str) -> Customer:
        logger.error(f"get_customer: {id}")
        return Customer(name="John Doe", id=id)

    @fastmcp_app.tool(description="return a customer")
    def create_customer(ctx: Context, customer: Customer) -> Customer:
        return Customer(name=customer.name, id=customer.id)

    @fastmcp_app.tool(description="List all active chaser keys")
    async def list_chasers(ctx: Context) -> list[str]:
        """Fetch the list of chaser keys from the internal service."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(config.chaser_service_url)
            resp.raise_for_status()
            return resp.json()

    @fastmcp_app.tool(description="Get details for a specific chaser key")
    async def get_chaser(ctx: Context, key: str) -> ChaserAggregate:
        """Fetch details for a specific chaser key."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{config.chaser_service_url}/{key}")
            resp.raise_for_status()
            data = resp.json()
            return ChaserAggregate(**data)

    return fastmcp_app
