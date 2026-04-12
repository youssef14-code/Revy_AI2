# graph/nodes/hr_agent.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import re
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from state.state import AgentState
from tools.services import MemoryService
from langchain_core.messages import ToolMessage
from app import app
from models.models import Job
from langchain_openai import ChatOpenAI
from graph.nodes.base import safe_invoke

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
- Name: Revy Ai
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
MEMORY RULES (MANDATORY)
====================
You MUST include the following tags at the END of your response. 
DO NOT skip them.

<LAST_BOT_REPLY>
[Repeat your full conversational reply to the user here]
</LAST_BOT_REPLY>

<SUMMARY>
[Update the summary of the entire conversation so far, including the latest interaction. Keep it to 2-3 lines.]
</SUMMARY>
====================
LANGUAGE RULE
====================
Always respond in the same language the user is speaking.
If the user writes in Arabic, respond in Arabic.
If the user writes in English, respond in English.
Mixed language? Follow the dominant language used.
"""

@safe_invoke
def hr_agent_node(state: AgentState) -> AgentState:
    
    current_summary = state.get("summary", "")
    last_bot_reply = state.get("last_bot_reply", "") or ""

    messages = [
        SystemMessage(
             content=SYSTEM_PROMPT
            + f"\n\n====================\nCONVERSATION CONTEXT\n====================\nPrevious summary:\n{current_summary}\n\nLast bot reply:\n{last_bot_reply}\n===================="
        ),
        *state["messages"]
    ]
    
    response = llm_with_tools.invoke(messages)

    # Handle Tool Calls
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "get_jobs_from_db":
                filter_val = tool_call["args"].get("filter", "all")
                tool_result = get_jobs_from_db.invoke({"filter": filter_val})

                messages.append(response)
                messages.append(ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"]
                ))
                # Re-invoke to get the final response with the tags
                response = llm_with_tools.invoke(messages)
    
    content = response.content

    # =========================
    # Extract SUMMARY
    # =========================
    summary_match = re.search(r"<SUMMARY>(.*?)</SUMMARY>", content, re.DOTALL)
    new_summary = summary_match.group(1).strip() if summary_match else current_summary

    # =========================
    # Extract LAST_BOT_REPLY
    # =========================
    reply_match = re.search(r"<LAST_BOT_REPLY>(.*?)</LAST_BOT_REPLY>", content, re.DOTALL)
    last_reply = reply_match.group(1).strip() if reply_match else ""

    # =========================
    # Update Database (MemoryService)
    # =========================
    client_obj = state.get("client")
    if client_obj:
        print(f"[HR Agent] Updating DB for client: {client_obj}")
        MemoryService.update(
            client=client_obj,
            summary=new_summary,
            last_reply=last_reply
        )
    else:
        print("[HR Agent] WARNING: 'client' is None in state. Data NOT saved to Database.")

    # =========================
    # Clean message for user
    # =========================
    clean_reply = re.sub(r"<SUMMARY>.*?</SUMMARY>", "", content, flags=re.DOTALL)
    clean_reply = re.sub(r"<LAST_BOT_REPLY>.*?</LAST_BOT_REPLY>", "", clean_reply, flags=re.DOTALL).strip()
    
    if not clean_reply and last_reply:
        clean_reply = last_reply

    print("[HR Agent] responded ✅")
    
    return {
        **state,
        "messages": [AIMessage(content=clean_reply)],
        "summary": new_summary,
        "last_bot_reply": last_reply
    }