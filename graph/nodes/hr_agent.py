# graph/nodes/hr_agent.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from langchain_core.messages import SystemMessage, AIMessage
from langchain_ollama import ChatOllama
from state.state import AgentState

llm = ChatOllama(model="llama3", temperature=0)

SYSTEM_PROMPT = """You are a professional HR assistant.
You help with employee info, leave requests, HR policies, and payroll.

Use the context below to answer. If the answer is not in the context, say so honestly.

Context:
{context}"""


def hr_agent_node(state: AgentState) -> AgentState:
    user_message = state["messages"][-1].content
    context = state["rag_context"]

    messages = [
        SystemMessage(content=SYSTEM_PROMPT.format(context=context)),
        *state["messages"]
    ]

    response = llm.invoke(messages)
    print(f"[HR Agent] responded ✅")

    return {
        **state,
        "messages": [AIMessage(content=response.content)]
    }