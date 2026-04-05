# main.py
import sys, os
sys.path.append(os.path.dirname(__file__))

from langchain_core.messages import HumanMessage
from graph.graph import build_graph

graph = build_graph()

print("🤖 RevyAI Multi-Agent is running. Type 'exit' to quit.\n")

while True:
    msg = input("You: ")
    if msg.lower() == "exit":
        break

    result = graph.invoke({
        "messages": [HumanMessage(content=msg)],
        "next_agent": "",
        "rag_context": "",
        "lead": {},
        "summary": ""
    })

    print(f"RevyAI: {result['messages'][-1].content}\n")