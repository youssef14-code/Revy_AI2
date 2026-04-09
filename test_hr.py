# test_hr.py

import sys, os


from langchain_core.messages import HumanMessage
from graph import AgentState
from graph.nodes.hr_agent import hr_agent_node

# state تجريبي
state: AgentState = {
    "messages": [HumanMessage(content="what are the available jobs?")],
    "next_agent": "hr",
    "rag_context": ""
}

result = hr_agent_node(state)
print("\n── HR Agent Response ──")
print(result["messages"][-1].content)