

from collections.abc import Sequence
from chatbot.chathistory import ChatHistory
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    AIMessage,
)
from langchain_core.language_models import BaseChatModel


from langgraph.graph import StateGraph, END, START
from prometheus_client import REGISTRY, CollectorRegistry, Summary
import langgraph
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools.structured import StructuredTool

from .agentstate import AgentState

from chatbot.langgraph import toolregistry

import logging
# Set up logging
logger = logging.getLogger(__name__)




class LanggraphHandler:
    """
    General Interface for interacting with LLM AI.
    This class handles the interaction with the LLM, handles the context and
    calls tools as needed.

    It is based off: https://ai.google.dev/api?lang=python

    Attributes:
        config (GeminiConfig): Configuration for the AI
        client (genai.Client): The AI client eg Gemini for making requests
        function_registry (toolutils.FunctionRegistry): Registry for tools that can be called by the AI
    """

    def __init__(
        self,
        config: MyAiConfig,
        client: BaseChatModel,
        registry: CollectorRegistry | None = REGISTRY,
    ):
        self.config = config
        self.function_registry = toolregistry.ToolRegistry(
            config.toolbox, registry=registry
        )
        self.client = client
        self.llm_summary_metric = Summary(
            "llm_usage", "Summary of LLM usage", registry=registry
        )

        # Initialize the graph
        workflow = StateGraph(AgentState)
        workflow.add_node("chatbot", self._call_llm)
        # workflow.add_node("my_tools", self._call_tool)

        workflow.add_edge(START, "chatbot")
        workflow.add_edge("my_tools", "chatbot")
        workflow.add_edge("chatbot", END)

        # Add edges
        workflow.add_conditional_edges(
            "chatbot",
            self._should_call_tool,
            {
                "call_tool": "my_tools",
                END: END,
            },
        )

        self.workflow = workflow

        self.memory = InMemorySaver()

    @staticmethod
    def get_graph_config(conversation_id: str, **kwargs) -> RunnableConfig:
        """
        Returns a configuration dictionary for the graph, given a ConversationAccount.
        This can be used to pass context or metadata to the graph execution.

        Args:
            conversation (ConversationAccount): The conversation context

        Returns:
            dict: Configuration for the graph
        """

        config_dict = {"configurable": {"thread_id": conversation_id, **kwargs}}
        print(f"Graph config: {config_dict}")
        # return config_dict
        return RunnableConfig(configurable={"thread_id": conversation_id, **kwargs})

    async def _call_llm(self, state: AgentState) -> dict:
        """
        Node to call the language model.
        """
        messages = state.messages
        with self.llm_summary_metric.time():
            response = await self.client.ainvoke(messages)
        # The response from ainvoke is already an AIMessage if no tool calls,
        # or an AIMessage with tool_calls if tools are called.
        # We append it to the list of messages to be included in the state.

        new_state = state.model_copy(update={"messages": state.messages + [response]})
        return new_state

    async def _call_tool(self, *args, **kwargs) -> dict:
        """
        Node to execute tool calls.
        """

        print(f"ToolNode called with args: {args}, kwargs: {kwargs}")

        logger.error(f"State is {state}")

        messages = state["messages"]
        last_message = messages[-1]
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            # Should not happen if routed correctly
            logger.error("Call tool node received state without tool calls.")
            # todo: Handle this case more gracefully, maybe raise an exception or return an error message
            return {}

        tool_responses = await self.function_registry.perform_tool_actions(
            last_message.tool_calls
        )
        # Append tool responses to the messages list
        return {"messages": messages + tool_responses}

    def _should_call_tool(self, state: AgentState) -> str:
        """
        Determines whether to call a tool or end the conversation turn.
        """
        messages = state.messages
        last_message = messages[-1]

        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            logger.info("Graph: Deciding to call tool.")
            return "call_tool"

        logger.info("Graph: Deciding to end.")

        return langgraph.graph.END  # is also an option if imported

    def bind_tools(self):
        """Binds the tools to the client and initializes the ToolNode.
        This is seperated out as some of the tool elements (eg MCP) are not available until the async runtime is available.
        """

        all_tools = self.function_registry.all_tools()

        logger.info(f"Binding tools: {[tool.name for tool in all_tools]}")

        self.client = self.client.bind_tools(all_tools)
        self.toolnode = ToolNode(tools=all_tools, name="my_tools")

        # self.workflow.add_node("my_tools", self._call_tool)
        self.workflow.add_node("my_tools", self.toolnode)

    def compile(self) -> StateGraph:
        """
        Compiles the graph with the current configuration.
        This is essentiall as we want to add some tools and generate the ToolNode dynamically.
        This is useful if you want to change the graph dynamically.
        """

        self.graph = self.workflow.compile(checkpointer=self.memory)

        print(self.graph.get_graph().draw_ascii())

        print("Workflow as Mermaid")
        print(self.graph.get_graph().draw_mermaid())

        logger.info("Graph compiled successfully.")

        return self.graph

    def register_tools(self, tools: Sequence[StructuredTool]):
        """Registers the tools with the client."""
        self.function_registry.register_tools(tools)

    # async def upload(
    #     self,
    #     conversation: ConversationAccount,
    #     name: str,
    #     mime_type: str,
    #     file_bytes: bytes,
    # ) -> None:
    #     """Uploads a file to the AI model messages.
    #     This method encodes the file bytes to base64 and prepares it for the AI model.

    #     Returns:
    #         None
    #     """
    #     messages = self.get_conversation(conversation)

    #     encoded = base64.b64encode(file_bytes).decode("utf-8")

    #     messages.append(
    #         HumanMessage(
    #             content=[
    #                 {
    #                     "type": "file",
    #                     "source_type": "base64",
    #                     "data": encoded,
    #                     "mine_type": mime_type,
    #                     "filename": name,
    #                 }
    #             ]
    #         )
    #     )

    #     logger.debug("File added to conversation but not sent to LLM yet.")
    #     return None

    async def ainvoke_agent(
        self, prompt: str, chat_history: ChatHistory
    ) -> str:
        """Invoke the agent with the given prompt and chat history.
        This method prepares the messages, calls the graph, and returns the response.

        Args:
            prompt (str): The user prompt
            chat_history (list[BaseMessage]): The chat history

        Returns:
            str: The response from the agent
        """
        print(f"ainvoke_agent called with prompt: {prompt} for chat_history: {chat_history}")

        if not hasattr(self, "graph"):
            raise ValueError("Graph not yet compiled")

        # Update the messages object to add the new prompt as a human message (this is necessary for the store function later)
        chat_history.messages.append(HumanMessage(content=prompt))

        agent_state = AgentState.from_chat_history(chat_history)

        temp_graph_config = RunnableConfig(configurable={"thread_id": "ABC"})

        final_graph_state = await self.graph.ainvoke(agent_state, config=temp_graph_config)

        # Extract the final messages from the graph's output state
        final_messages = final_graph_state["messages"]

        # The last message in the final_messages list should be the AI's response
        final_response_message = final_messages[-1] if final_messages else None

        logger.debug(f"Final response from graph: {final_response_message}")

        if isinstance(final_response_message, AIMessage):
            return final_response_message.content
        elif final_response_message is None:
            logger.error("Graph execution resulted in no messages.")
            return "Sorry, I encountered an issue and couldn't generate a response."
        else:
            logger.error(
                f"Unexpected final response type from graph: {type(final_response_message)}"
            )
            return "Sorry, I encountered an error processing your request."


    async def chat(
        self, conversation_id: str, identity: str, prompt: str
    ) -> str:
        """Make a chat request to the AI model with the provided prompt.
        This method sends a prompt to the model and processes the response.
        It handles tool calls made by the model, executes the corresponding tool,
        and returns the final response from the model.

        Args:
            conversation (Conversation): The conversation context
            identity (str): The identity of the user or bot in the conversation
            prompt (str): Prompt from the user

        Returns:
            str: text response for the bot
        """

        graph_config = self.get_graph_config(conversation_id, identity=identity)
        logger.debug(f"Graph config: {graph_config}")

        agent_state = {"messages": [HumanMessage(content=prompt)]}

        if not hasattr(self, "graph"):
            raise ValueError("Graph not yet compiled")

        final_graph_state = await self.graph.ainvoke(agent_state, config=graph_config)

        # Extract the final messages from the graph's output state
        final_messages = final_graph_state["messages"]

        # The last message in the final_messages list should be the AI's response
        final_response_message = final_messages[-1] if final_messages else None

        logger.debug(f"Final response from graph: {final_response_message}")

        if isinstance(final_response_message, AIMessage):
            return final_response_message.content
        elif final_response_message is None:
            logger.error("Graph execution resulted in no messages.")
            return "Sorry, I encountered an issue and couldn't generate a response."
        else:
            logger.error(
                f"Unexpected final response type from graph: {type(final_response_message)}"
            )
            return "Sorry, I encountered an error processing your request."
