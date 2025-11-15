from microsoft_agents.hosting.core import AgentApplication, AgentAuthConfiguration
from microsoft_agents.hosting.aiohttp import (
    start_agent_process,
    jwt_authorization_middleware,
    CloudAdapter,
)
from aiohttp.web import Response, Request

from aiohttp import web
from typing import Optional
from chatbot import keys

import logging

# Set up logging
logger = logging.getLogger(__name__)


class AzureBotView(web.View):
    async def post(self) -> Optional[Response]:
        req: Request = self.request

        app_agent: AgentApplication = req.app[keys.agent_app]
        cloud_adapter: CloudAdapter = req.app[keys.cloud_adapter]
        return await start_agent_process(
            req,
            app_agent,
            cloud_adapter,
        )
