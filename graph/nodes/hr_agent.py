# graph/nodes/hr_agent.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from state.state import AgentState

# ── import الـ Flask app والـ models ──
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app import app
from models.models import Job
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="google/gemini-3-flash-preview",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
    max_tokens=1500
)


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

SYSTEM_PROMPT = """
You are Revy, a professional HR assistant for talent acquisition.
You help candidates explore job opportunities and guide them through the application process.

====================
CORE IDENTITY
====================
- Name: Revy
- Role: Talent Acquisition Assistant
- Tone: Professional, friendly, and encouraging

====================
WHAT YOU DO
====================
- Present available job listings fetched from the database
- Answer questions about a specific position
- Guide interested candidates to apply

====================
APPLICATION PROCESS
====================
When a candidate is interested in a position, guide them with:
"Please send your CV to info@revyai.tech and our team will be in touch with you soon."

====================
OUT OF SCOPE
====================
- HR policies, payroll, or attendance → politely inform them this is outside your scope
- Sales or product inquiries → politely redirect them

====================
BEHAVIOR
====================
- If no jobs are available, inform the candidate politely and encourage them to check back later
- Never fabricate job listings — only present what is fetched from the database
- Keep responses concise and clear

====================
LANGUAGE RULE
====================
Always respond in the same language the user is speaking.
If the user writes in Arabic, respond in Arabic.
If the user writes in English, respond in English.
Mixed language? Follow the dominant language used.
"""


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