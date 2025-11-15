from aiohttp import web
from aiohttp.web import Response, json_response, Request
from chatbot.service.state import Events
from pydantic import BaseModel, ValidationError
import logging
from botbuilder.schema import Activity, ActivityTypes
from chatbot import keys
from http import HTTPStatus

# Set up logging
logger = logging.getLogger(__name__)


class AzureBotView(web.View):

    async def options(self) -> Response:
        """
        Prepare to handle CORS preflight requests. (needed for Teams integration)
        Needed for this: https://learn.microsoft.com/en-us/azure/bot-service/bot-builder-basics-teams?view=azure-bot-service-4.0&tabs=csharp


        Handle OPTIONS request for CORS preflight.
        Returns an OK
        """

        headers = {
            "Access-Control-Allow-Origin": "*",  # Be specific in production!
            "Access-Control-Allow-Headers": "Content-Type,Authorization,x-ms-client-request-id,x-ms-client-session-id,x-ms-effective-locale",
            "Access-Control-Allow-Methods": "POST,OPTIONS,GET",
            "Access-Control-Max-Age": "5",  # Cache preflight response for 1 minute
        }

        reply = json_response(status=HTTPStatus.OK, headers=headers)
        print(f"Reply: {reply}")
        return reply

    async def post(self) -> Response:

        req: Request = self.request

        # Main bot message handler.
        logger.debug(f"Received request: {req}")
        if "application/json" in req.headers["Content-Type"]:
            body = await req.json()
        else:
            return Response(status=415)

        activity = Activity().deserialize(body)
        auth_header = (
            req.headers["Authorization"] if "Authorization" in req.headers else ""
        )
        logger.debug(f"Activity: {activity}")

        response = await req.app[keys.botadapter].process_activity(
            activity, auth_header, req.app[keys.bot].on_turn
        )
        logger.debug(f"Response: {response}")
        if response:
            return json_response(data=response.body, status=response.status)
        return Response(status=201)
