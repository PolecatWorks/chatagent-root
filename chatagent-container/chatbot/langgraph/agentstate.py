from typing import Annotated
from chatbot.chathistory import ChatHistory
from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel


class AgentState(BaseModel):
    """
    Represents the state of our graph.

    Attributes:
        messages: The list of messages that have been exchanged in the conversation.
    """

    messages: Annotated[list[AnyMessage], add_messages]

    @classmethod
    def from_chat_history(cls, chat_history: ChatHistory) -> "AgentState":
        """
        Create an AgentState from a ChatHistory-like object.
        """

        # Pass through items; validation will be performed by pydantic on construction.
        return cls(messages=list(chat_history.messages))
