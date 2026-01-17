
from langchain_core.messages.base import BaseMessage
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    AIMessage,
    FunctionMessage # Include all types you use
)


from pydantic import BaseModel
from typing import Union


# Define the union of allowed message types
MessageType = Union[
    ToolMessage,
    FunctionMessage,
    AIMessage,
    HumanMessage,
    SystemMessage,
]


class ChatHistory(BaseModel):
    messages: list[MessageType] = []
    current_tool_name: str = ""
