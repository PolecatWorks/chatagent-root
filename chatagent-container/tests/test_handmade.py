from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from chatbot.chathistory import ChatHistory
from langchain_core.messages import AnyMessage
from langchain_core.load import load
from langchain_core.load import dumps, loads


def test_human_message():
    values = {
        "content": "test me 0",
        "additional_kwargs": {},
        "response_metadata": {},
        "type": "human",
        "name": None,
        "id": "2ae6fb58-5098-4bc7-a959-f963347096af",
    }

    hm = HumanMessage(content="test me 0")

    hm_json = dumps(hm)
    print(f"hm_json={hm_json}")

    hm2 = loads(hm_json)
    print(f"hm2={hm2}")
    assert isinstance(hm2, HumanMessage)
    assert hm2 == hm


def test_tool_message():
    tm = ToolMessage(content="tool used", tool_call_id="call-123")
    print(f"tm={tm}")
    tm_json = dumps(tm)

    print(f"tm_json={tm_json}")

    tm2 = loads(tm_json)
    print(f"tm2={tm2}")

    assert isinstance(tm2, ToolMessage)
    assert tm2 == tm


def test_all_messages():
    messages = [
        HumanMessage(content="test me 0"),
        SystemMessage(content="system here"),
        ToolMessage(content="tool used", tool_call_id="call-123"),
    ]

    am_json = dumps(messages)
    print(f"am_json={am_json}")

    am2 = loads(am_json)
    print(f"am2={am2}")
    assert isinstance(am2, list)
    assert len(am2) == len(messages)
    for i in range(len(messages)):
        assert isinstance(am2[i], type(messages[i]))
        assert am2[i] == messages[i]
