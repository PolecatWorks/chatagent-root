

from fastmcp import FastMCP
from pydantic import BaseModel

from  random import randint


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
    def hello():
        return "hello"

    @fastmcp_app.tool(description="return a random number")
    def random_number():
        return randint(1, 100)


    return fastmcp_app
