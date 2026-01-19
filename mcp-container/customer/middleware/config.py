from typing import Any
from fastmcp.server.middleware import Middleware
from customer import ServiceConfig


class ConfigMiddleware(Middleware):

    service_config_key = "ServiceConfig"
    config: ServiceConfig

    def __init__(self, config: ServiceConfig):
        self.config = config

    async def on_call_tool(self, context: Any, call_next: Any) -> Any:
        context.fastmcp_context.set_state(self.service_config_key, self.config)
        result = await call_next(context)

        return result
