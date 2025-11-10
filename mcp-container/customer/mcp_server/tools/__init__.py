import datetime
from zoneinfo import ZoneInfo

from aiohttp_mcp import AiohttpMCP, setup_mcp_subapp

import logging

logger = logging.getLogger(__name__)


mcp = AiohttpMCP(debug=False)

myCount = 0


@mcp.tool()
def count_calls() -> int:
    """Count the number of calls made to the function"""
    global myCount
    myCount += 1
    logger.info(f"Count the call updated to {myCount}")
    return myCount


@mcp.tool()
def get_time(timezone: str) -> str:
    """Get the current time in the specified timezone."""
    tz = ZoneInfo(timezone)
    return datetime.datetime.now(tz).isoformat()
