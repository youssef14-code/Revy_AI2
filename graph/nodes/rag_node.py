# graph/nodes/rag_node.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "retrival"))

from state.state import AgentState
from retrival.retriever import RetrievalService

retriever = RetrievalService()


def rag_node(state: AgentState) -> AgentState:
    user_message = state["messages"][-1].content

    context = retriever.search(user_message, top_k=2)

    print(f"[RAG] context retrieved ✅")

    return {
        **state,
        "rag_context": context
    }