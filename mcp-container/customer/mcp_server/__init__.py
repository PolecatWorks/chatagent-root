

from fastmcp import FastMCP
from pydantic import BaseModel

from  random import randint
import logging
from fastmcp.server.context import Context

logger = logging.getLogger(__name__)



class Customer(BaseModel):
    name: str
    id: int



class MCPConfig(BaseModel):
    """
    Configuration of the MCP server
    """
    name: str
    instructions: str


def mcp_init(config: MCPConfig):
    fastmcp_app = FastMCP(
        name=config.name,
        instructions=config.instructions
    )



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
    async def get_customer(ctx: Context, id: str)->Customer:
        logger.error(f"get_customer: {id}")
        return Customer(name="John Doe", id=id)

    @fastmcp_app.tool(description="return a customer")
    def create_customer(ctx: Context, customer: Customer) -> Customer:
        return Customer(name=customer.name, id=customer.id)



    return fastmcp_app
