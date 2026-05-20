# graph/graph.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from langgraph.graph import StateGraph, END
from state.state import AgentState
from graph.nodes.supervisor import intent_node
from graph.nodes.hr_agent import hr_agent_node
from graph.nodes.sales_cs_agent import sales_cs_agent_node
from graph.nodes.direct_node import direct_node
from graph.nodes.booking_node import booking_node


def route(state: AgentState) -> str:
    return state["next_agent"]


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", intent_node)
    graph.add_node("direct", direct_node)
    graph.add_node("sales_cs", sales_cs_agent_node)
    graph.add_node("hr", hr_agent_node)
    graph.add_node("booking", booking_node)

    graph.set_entry_point("supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route,
        {
            "hr": "hr",
            "direct": "direct",
            "sales_cs": "sales_cs",
            "booking": "booking"
        }
    )

    graph.add_edge("hr", END)
    graph.add_edge("direct", END)
    graph.add_edge("sales_cs", END)
    graph.add_edge("booking", END)

    return graph.compile()