# graph/nodes/supervisor.py

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from state.state import AgentState

llm = ChatOllama(model="llama3.2", temperature=0)

SYSTEM_PROMPT = """You are a router. Read the user message and decide which agent should handle it.

Agents:
- hr        → employee info, leave requests, HR policies, payroll
- support   → complaints, tickets, returns, warranty

Reply with ONE word only:
hr
support"""


def supervisor_node(state: AgentState) -> AgentState:
    user_message = state["messages"][-1].content

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ])

    next_agent = response.content.strip().lower()

    # validation - لو الـ LLM رجع حاجة غلط
    if next_agent not in ["hr", "support"]:
        next_agent = "support"

    print(f"[Supervisor] → {next_agent}")

    return {
        **state,
        "next_agent": next_agent
    }