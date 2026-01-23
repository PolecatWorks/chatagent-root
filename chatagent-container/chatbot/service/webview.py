from aiohttp import web
from chatbot.service.state import Events
from pydantic import BaseModel, ValidationError
import logging
from chatbot import keys


# Set up logging
logger = logging.getLogger(__name__)


class ChunkRequestModel(BaseModel):
    name: str
    num_chunks: int


class ChunkState(BaseModel):
    chunks: int


class ChunkView(web.View):
    async def post(self):
        # curl -X POST http://localhost:8000/pie/v0/chunks \
        #     -H "Content-Type: application/json" \
        #     -d '{"name": "example", "num_chunks": 5}'

        try:
            data = await self.request.json()
            chunk_request = ChunkRequestModel(**data)
        except ValidationError as e:
            return web.json_response({"error": e.errors()}, status=400)

        events: Events = self.request.app[keys.events]
        chunks = events.addChunks(chunk_request.num_chunks)

        logger.info(f"Chunks updated to {chunks}")

        return web.json_response(chunk_request.model_dump())

    async def get(self):
        events: Events = self.request.app[keys.events]
        reply = ChunkState(chunks=events.chunkCount)

        return web.json_response(reply.model_dump())


class LLMChatView(web.View):
    async def get(self):
        try:
            prompt = self.request.query["prompt"]
        except KeyError:
            return web.json_response({"error": "Missing 'prompt' query parameter"}, status=400)

        llm_handler = self.request.app[keys.llmhandler]

        # Create a dummy ConversationAccount for now
        # In a real application, this would involve fetching or creating user/session specific details
        conversation_account = ConversationAccount(id="dummy_conversation_id")
        identity = "web_user"

        try:
            ai_response = await llm_handler.chat(conversation_account, identity, prompt)
            return web.json_response({"response": ai_response})
        except Exception as e:
            logger.error(f"Error during LLM chat: {e}", exc_info=True)
            return web.json_response({"error": "Error processing LLM request"}, status=500)
