# graph/graph.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from langgraph.graph import StateGraph, END
from state.state import AgentState
from graph.nodes.supervisor import supervisor_node
from graph.nodes.rag_node import rag_node
from graph.nodes.hr_agent import hr_agent_node
from graph.nodes.sales_cs_agent import sales_cs_agent_node



def route(state: AgentState) -> str:
    return state["next_agent"]


def build_graph():
    graph = StateGraph(AgentState)

    # Nodes
    ##graph.add_node("supervisor", supervisor_node)
    graph.add_node("rag", rag_node)
    graph.add_node("hr", hr_agent_node)
    graph.add_node("sales_cs", sales_cs_agent_node)
    

    # Entry point
<<<<<<< HEAD
    ###graph.set_entry_point("supervisor")
    graph.set_entry_point("intent")
=======
    graph.set_entry_point("supervisor")

>>>>>>> 7b90e73cd77df491ebe55d22b9e137ba5b1bc4e0

    # Supervisor يقرر مين
    graph.add_conditional_edges(
        "intent",
        route,
        {
            "hr": "hr",
            "sales_cs": "sales_cs"  # Sales & CS محتاج RAG الأول
        }
    )

    # HR مش محتاج RAG يروح للـ END مباشرة
    graph.add_edge("hr", END)

    # RAG بعدين Sales & CS
    graph.add_edge("hr", END)
    graph.add_edge("rag", "sales_cs")
    graph.add_edge("sales_cs", END)
<<<<<<< HEAD
    ##graph.add_edge("intent", "supervisor")
=======

>>>>>>> 7b90e73cd77df491ebe55d22b9e137ba5b1bc4e0

    return graph.compile()