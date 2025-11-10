from typing import (
    Annotated,
    TypedDict,
)  # TODO: Review Annotated and TypedDict for Python version compatibility
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        messages: The list of messages that have been exchanged in the conversation.
    """

    messages: Annotated[list[BaseMessage], add_messages]
