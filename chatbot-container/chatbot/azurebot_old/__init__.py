# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount
from botbuilder.schema import Activity, ActivityTypes
from aiohttp import web
from chatbot import keys

from datetime import datetime
import traceback
import logging

from chatbot.config import ServiceConfig

from botbuilder.core import (
    BotFrameworkAdapterSettings,
    BotFrameworkAdapter,
    TurnContext,
)
from chatbot.azurebot_old.webview import AzureBotView
from chatbot.llmconversationhandler import LLMConversationHandler
from prometheus_client import REGISTRY, CollectorRegistry, Summary
import base64
import aiohttp

# Set up logging
logger = logging.getLogger(__name__)


# Catch-all for errors.
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    logger.error(f"\n [on_turn_error] unhandled error: {error}")
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
    await context.send_activity(
        "To continue to run this bot, please fix the bot source code."
    )
    # Send a trace activity if we're talking to the Bot Framework Emulator
    if context.activity.channel_id == "emulator":
        # Create a trace activity that contains the error object
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
        )
        # Send a trace activity, which will be displayed in Bot Framework Emulator
        await context.send_activity(trace_activity)


class AzureBot(ActivityHandler):
    """
    AzureBot is a bot that handles incoming messages and responds using an AI model.
    """

    # See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.

    def __init__(
        self, app: web.Application, registry: CollectorRegistry | None = REGISTRY
    ):
        super().__init__()
        self.app = app

        self.prometheus_registry = registry
        self.chat_metric = Summary(
            "chat_usage",
            "Summary of Chat actions",
            ["action"],
            registry=registry,
        )

    async def on_message_activity(self, turn_context: TurnContext):

        logger.debug(f"turn_context: {turn_context}")
        logger.debug("Received message activity: %s", turn_context.activity)

        # Check if the incoming message is a file attachment
        if (
            turn_context.activity.attachments
            and len(turn_context.activity.attachments) > 0
        ):
            for attachment in turn_context.activity.attachments:
                content_url = attachment.content_url
                content_type = attachment.content_type
                name = attachment.name if hasattr(attachment, "name") else "attachment"
                print(
                    f"Received file attachment: {name}, type: {content_type}, URL: {content_url}"
                )
                print(f"Attachment: {attachment}")
                # Read the file content as bytes
                # if "http_session" not in self.app:
                #     self.app["http_session"] = aiohttp.ClientSession()
                # async with self.app["http_session"].get(content_url) as resp:
                #     file_bytes = await resp.read()
                async with aiohttp.ClientSession() as session:
                    async with session.get(content_url) as resp:
                        file_bytes = await resp.read()

                await turn_context.send_activity(
                    f"Received file '{name}' (type: {content_type}). Length ({len(file_bytes)}). Base64 encoded content prepared for attachment."
                )
                await self.app[keys.llmhandler].upload(
                    turn_context.activity.conversation, name, content_type, file_bytes
                )
            return
            # Optionally, you can send the base64 string or process it further here

        llmHandler: LLMConversationHandler = self.app[keys.llmhandler]

        with self.chat_metric.labels("on_message").time():
            llm_reply = await llmHandler.chat(
                turn_context.activity.conversation,
                "my-identity",
                turn_context.activity.text,
            )

        logger.debug("LLM reply: %s", llm_reply)
        await turn_context.send_activity(llm_reply)

    async def on_members_added_activity(
        self, members_added: ChannelAccount, turn_context: TurnContext
    ):
        with self.chat_metric.labels("on_members_added").time():
            for member_added in members_added:
                if member_added.id != turn_context.activity.recipient.id:
                    await turn_context.send_activity("Hello and welcome!")


def azure_app_create(app: web.Application, config: ServiceConfig) -> web.Application:
    """
    Create the service with the given configuration file
    """
    # Add the bot settings and adapter to the app
    app[keys.botsettings] = BotFrameworkAdapterSettings(
        config.bot.app_id, config.bot.app_password.get_secret_value()
    )
    app[keys.botadapter] = BotFrameworkAdapter(app[keys.botsettings])

    app[keys.botadapter].on_turn_error = on_error

    registry = REGISTRY if keys.metrics not in app else app[keys.metrics]

    app[keys.bot] = AzureBot(app, registry=registry)

    app.add_routes([web.view(config.bot.api_path, AzureBotView)])
    logger.info(
        f"Bot: {app[keys.config].webservice.url.host}:{app[keys.config].webservice.url.port}{app[keys.config].bot.api_path}"
    )
    return app
