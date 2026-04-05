# graph/nodes/hr_agent.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from state.state import AgentState

llm = ChatOllama(model="llama3.2", temperature=0)


# ── Tool: جيب الوظايف من الـ DB ──
@tool
def get_jobs_from_db(filter: str = "all") -> str:
    """Get jobs from the database. filter: 'all', 'available', 'closed'"""
    with app.app_context():
        if filter == "available":
            jobs = Job.query.filter_by(is_available=True).all()
        elif filter == "closed":
            jobs = Job.query.filter_by(is_available=False).all()
        else:
            jobs = Job.query.all()

        if not jobs:
            return "No jobs found."

        result = []
        for j in jobs:
            status = "Available" if j.is_available else "Closed"
            result.append(f"- {j.job_name} ({status}): {j.description}")

        return "\n".join(result)


tools = [get_jobs_from_db]
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """You are a professional HR assistant.
You help with job listings, employee info, leave requests, and HR policies.

You have access to a tool to get job listings from the database.
Use it when someone asks about available jobs or positions.

Use the context below for other HR questions:
{context}"""


def hr_agent_node(state: AgentState) -> AgentState:
    context  = state["rag_context"]
    messages = [
        SystemMessage(content=SYSTEM_PROMPT.format(context=context)),
        *state["messages"]
    ]

    response = llm_with_tools.invoke(messages)

    # لو الـ LLM طلب tool
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "get_jobs_from_db":
                filter_val = tool_call["args"].get("filter", "all")
                tool_result = get_jobs_from_db.invoke({"filter": filter_val})

                # ابعت النتيجة للـ LLM يصيغها
                from langchain_core.messages import ToolMessage
                messages.append(response)
                messages.append(ToolMessage(
                    content=tool_result,
                    tool_call_id=tool_call["id"]
                ))
                final = llm_with_tools.invoke(messages)
                print("[HR Agent] responded with DB data ✅")
                return {
                    **state,
                    "messages": [AIMessage(content=final.content)]
                }

    print("[HR Agent] responded ✅")
    return {
        **state,
        "messages": [AIMessage(content=response.content)]
    }