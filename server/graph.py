import json
from collections.abc import Sequence
from typing import Annotated, Literal

from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.ui import AnyUIMessage, push_ui_message, ui_message_reducer
from langgraph.types import interrupt
from typing_extensions import TypedDict

from flows.llm.azure_apim import get_chat_model

# 正式 demo agent：與業務 graphs 共用單一 LLM factory（flows.llm）
llm = get_chat_model(temperature=0)


class AgentState(TypedDict):
    """除了原本 messages 外，加上 ui 欄位讓 graph 可以推 GenUI 元件給前端。"""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
    llm_calls: int


# Define tools
@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a / b


@tool
def get_weather(city: str) -> str:
    """Look up current weather for a city.

    Returns JSON string with city / temp / condition / humidity.

    Args:
        city: city name, e.g. "Taipei"
    """
    # Human-in-the-loop：查詢天氣前先請使用者核准（可順手改 city）
    response = interrupt(
        {
            "action": "get_weather",
            "city": city,
            "message": f"Approve looking up weather for '{city}'?",
        }
    )

    if not (isinstance(response, dict) and response.get("action") == "approve"):
        return json.dumps({"city": city, "error": "Weather lookup cancelled by user"})

    final_city = response.get("city", city)

    # Demo 用假資料；實務上可以串接氣象 API
    fake_db = {
        "taipei": {"temp": 28, "condition": "Cloudy", "humidity": 78},
        "tokyo": {"temp": 22, "condition": "Sunny", "humidity": 55},
        "new york": {"temp": 18, "condition": "Light rain", "humidity": 82},
        "london": {"temp": 15, "condition": "Foggy", "humidity": 88},
    }
    default = {"temp": 25, "condition": "Unknown", "humidity": 60}
    info = fake_db.get(final_city.strip().lower(), default)
    return json.dumps({"city": final_city, **info})


# Augment the LLM with tools
tools = [add, multiply, divide, get_weather]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = llm.bind_tools(tools)


def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""

    ai_msg = model_with_tools.invoke(
        [
            SystemMessage(
                content=(
                    "You are a helpful assistant tasked with performing arithmetic, "
                    "looking up weather, and working with uploaded file references. "
                    "Never ask the user to paste file binaries into the chat. "
                    "Use read_uploaded_file(uri) when you need text content from an uploaded file. "
                    "Use write_markdown_file(filename, content) when the user asks you to create "
                    "a markdown report or downloadable markdown artifact."
                )
            )
        ]
        + state["messages"]
    )

    # 若上一個 ToolMessage 是 get_weather，把結果以 GenUI 卡片形式推給前端，
    # 並用 message= 綁到剛產生的 AIMessage，前端就能依 metadata.message_id 對位渲染。
    msgs = state.get("messages") or []
    last = msgs[-1] if msgs else None
    if isinstance(last, ToolMessage) and getattr(last, "name", None) == "get_weather":
        try:
            payload = json.loads(last.content)
            push_ui_message("weather", payload, message=ai_msg)
        except Exception:  # demo 用，避免 UI 錯誤把整個對話打掛
            pass

    return {"messages": [ai_msg], "llm_calls": state.get("llm_calls", 0) + 1}


def tool_node(state: dict, config: RunnableConfig):
    """Performs the tool call"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        # 帶上 name，方便下一輪 llm_call 判斷是哪個 tool 的結果（用來決定要不要 push UI）
        result.append(
            ToolMessage(
                content=observation,
                tool_call_id=tool_call["id"],
                name=tool_call["name"],
            )
        )
    return {"messages": result}


def should_continue(state: AgentState) -> Literal["tool_node", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    last_message = state["messages"][-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "tool_node"

    # Otherwise, we stop (reply to the user)
    return END


# Build workflow
agent_builder = StateGraph(AgentState)

agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
agent_builder.add_edge("tool_node", "llm_call")

agent = agent_builder.compile()
