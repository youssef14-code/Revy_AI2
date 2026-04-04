# graph/nodes/supervisor.py

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from state.state import AgentState

llm = ChatOllama(model="llama3", temperature=0)

SYSTEM_PROMPT = """You are a router. Read the user message and decide which agent should handle it.

Agents:
- hr       → jobs, hiring, careers, vacancies
- sales_cs → pricing, services, booking, company info, who are you

Reply with ONE word only:
hr
sales
support"""


def supervisor_node(state: AgentState) -> AgentState:
    user_message = state["messages"][-1].content

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ])

    next_agent = response.content.strip().lower()

    # validation - لو الـ LLM رجع حاجة غلط
    if next_agent not in ["hr", "sales_cs"]:
        next_agent = "sales_cs"

    print(f"[Supervisor] → {next_agent}")

    return {
        **state,
        "next_agent": next_agent
    }