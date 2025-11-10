import os
from aiohttp import web

from chatbot import config_app_create, keys, metrics_app_create
from chatbot.config import ServiceConfig
from chatbot.llmconversationhandler import LLMConversationHandler, langchain_app_create, langchain_model
from chatbot.mcp_client import mcp_app_create
import pytest
from botbuilder.schema import ConversationAccount

from deepeval.models.base_model import DeepEvalBaseLLM



@pytest.fixture
def enable_livellm(request):
    return request.config.getoption("--enable-livellm")


@pytest.fixture
def config() -> ServiceConfig:
    config_filename = "tests/test_data/config.yaml"
    secrets_dir = os.environ.get(
        "TEST_SECRETS_DIR", "tests/test_data/secrets"
    )

    config: ServiceConfig = ServiceConfig.from_yaml(config_filename, secrets_dir)

    return config


@pytest.fixture
def llm_model(config: ServiceConfig):
    return langchain_model(config.aiclient)


class LangChainDeepEval(DeepEvalBaseLLM):
    def __init__(
        self,
        model
    ):
        self.model = model

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        chat_model = self.load_model()
        return chat_model.invoke(prompt).content

    async def a_generate(self, prompt: str) -> str:
        chat_model = self.load_model()
        res = await chat_model.ainvoke(prompt)
        return res.content

    def get_model_name(self):
        return "Langchain based model"

@pytest.fixture
def llm_deep_eval(llm_model):
    return LangChainDeepEval(llm_model)


@pytest.fixture
def llm_app(enable_livellm):
    app = web.Application()

    if enable_livellm:
        config_filename = "tests/test_data/config.yaml"
        secrets_dir = os.environ.get(
            "TEST_SECRETS_DIR", "tests/test_data/secrets"
        )

        config: ServiceConfig = ServiceConfig.from_yaml(config_filename, secrets_dir)

        config_app_create(app, config)
        metrics_app_create(app)
        mcp_app_create(app, config)

        langchain_app_create(app, config)

    return app


@pytest.fixture
async def service_client(aiohttp_client, llm_app):
    client = await aiohttp_client(llm_app)
    return client





@pytest.fixture
async def llm_conversation_handler(config: ServiceConfig) -> LLMConversationHandler:
    """
    Fixture to provide the LLMConversationHandler instance for testing.
    This can be used to test the conversation handler methods directly.
    """

    model = langchain_model(config.aiclient)

    llm_handler = LLMConversationHandler(config.myai, model)

    # Do not include MCP here
    llm_handler.bind_tools()
    llm_handler.compile()

    return llm_handler







@pytest.mark.asyncio
@pytest.mark.skip(
    "Skipping LLM conversation handler test as it requires solving duplicates for prometheus"
)
async def test_llm_chat(llm_conversation_handler):
    converation_account = ConversationAccount(
        id="test-conversation", name="Test Conversation", conversation_type="test-type"
    )
    reply = await llm_conversation_handler.chat(
        converation_account, "my-identity", "Hello, how are you?"
    )
    assert reply is not None


@pytest.mark.asyncio
async def test_llm_chat_post_valid(service_client, enable_livellm):
    if not enable_livellm:
        pytest.skip("Skipped unless --enable-livellm is set")

    # Test POST with valid data

    payload = {
        "messages": [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm fine, thank you!"},
        ]
    }
    resp = await service_client.post("/pie/v0/llm/chat", json=payload)
    assert resp.status == 404





from deepeval import assert_test
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import GEval





async def test_llmconversation_handler(llm_conversation_handler, llm_deep_eval, enable_livellm):

    if not enable_livellm:
        pytest.skip("Skipped unless --enable-livellm is set")

    my_question = "What tools do you have available"
    my_reply = await llm_conversation_handler.chat("Convo0", "id0", my_question)

    correctness_metric = GEval(
        name="Correctness",
        criteria="Determine if the 'actual output' is correct based on the 'expected output'.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        threshold=0.3,
        model=llm_deep_eval
    )

    test_case = LLMTestCase(
        input=my_question,
        # Replace this with the actual output from your LLM application
        actual_output=my_reply,
        expected_output="I have the following tools available: 'search', 'calculator', 'weather'.",
    )

    assert_test(test_case, [correctness_metric])

    reply = await llm_conversation_handler.chat("Convo0", "id0", "Hello")

    assert reply is not None
    assert reply is "NFNF"
