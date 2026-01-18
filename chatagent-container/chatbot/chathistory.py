
from langchain_core.messages.base import BaseMessage
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    AIMessage,
    FunctionMessage # Include all types you use
)


from pydantic import BaseModel, Field
from typing import Union, Annotated


# Define the union of allowed message types with a discriminator for efficiency and correctness
MessageType = Annotated[
    Union[
        ToolMessage,
        FunctionMessage,
        AIMessage,
        HumanMessage,
        SystemMessage,
    ],
    Field(discriminator='type')
]


class ChatHistory(BaseModel):
    messages: list[MessageType] = []
    current_tool_name: str = ""
