# graph/nodes/hr_agent.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import re
from langchain_core.messages import SystemMessage, AIMessage , HumanMessage
from state.state import AgentState
from tools.services import MemoryService
from app import app
from models.models import Job
from langchain_openai import ChatOpenAI
from graph.nodes.base import safe_invoke


llm = ChatOpenAI(
    model="google/gemini-2.0-flash-001",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
    max_tokens=1024
)

def get_jobs() -> str:
    with app.app_context():
        jobs = Job.query.filter_by(is_available=True).all()
        if not jobs:
            return "No available positions at the moment."
        result = []
        for j in jobs:
            result.append(f"- {j.job_name}: {j.description}")
        return "\n".join(result)


SYSTEM_PROMPT = """
You are Revy, a Talent Acquisition Assistant at RevyAI.

====================
ABOUT REVYAI
====================
RevyAI is a business-first AI automation company that designs tailored operational systems to reduce cost, eliminate inefficiencies, and improve decision-making. Unlike software vendors, RevyAI builds custom AI solutions shaped around each client's unique workflows — no templates, no SaaS, no generic deployments.

Their solutions are built on specialized AI agents that automate repetitive work, support structured decision-making, and maintain full auditability — while keeping humans in control where it matters most.

Core offerings include:
- Sales & Lead Qualification Agents
- Customer Service Automation
- Claims Processing Automation
- Operational Intelligence & KPI Tracking
- Audit & Employee Performance Evaluation

====================
CORE IDENTITY
====================
- Name: Revy
- Role: Talent Acquisition Assistant
- Tone: Professional, friendly, and encouraging

====================
WHAT YOU DO
====================
- Present available job listings from the database
- Answer questions about specific positions
- Guide interested candidates to apply

====================
APPLICATION PROCESS
====================
When a candidate is interested in a position:
"Please send your CV to info@revyai.tech and our team will be in touch with you soon."

====================
OUT OF SCOPE
====================
- HR policies, payroll, or attendance → politely inform them this is outside your scope
- Sales or product inquiries → politely redirect them

====================
BEHAVIOR
====================
- Only present jobs listed below — never fabricate listings
- If no jobs are available, inform the candidate politely
- Keep responses concise and clear

====================
AVAILABLE JOBS
====================
{jobs}

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
LANGUAGE PROTOCOL
====================
Arabic input → Arabic response.
English input → English response.
Never mix languages within a single response.
"""

@safe_invoke
def hr_agent_node(state: AgentState) -> AgentState:
    user_message = state["messages"][-1].content
    current_summary = state.get("summary", "") or ""
    last_bot_reply = state.get("last_bot_reply", "") or ""

    # جيب الوظايف مباشرة
    jobs = get_jobs()
    print(f"[HR Agent] Jobs fetched: {jobs[:100]}...")

    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT.replace("{jobs}", jobs)
            + f"\n\n====================\nCONVERSATION CONTEXT\n====================\n"
            + f"Previous summary:\n{current_summary}\n\n"
            + f"Last bot reply:\n{last_bot_reply}\n"
            + "===================="
        ),
        HumanMessage(content=user_message)
    ]

    response = llm.invoke(messages)
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
        print(f"[Direct Node] Saving to DB for client: {client_obj}")
        MemoryService.update(
            client=client_obj,
            summary=new_summary,
            last_reply=last_reply
        )

    print("[HR Agent] responded ✅")


    # =========================
    # Clean response for user
    # =========================
    clean_reply = re.sub(r"<SUMMARY>.*?</SUMMARY>", "", content, flags=re.DOTALL)
    clean_reply = re.sub(r"<LAST_BOT_REPLY>.*?</LAST_BOT_REPLY>", "", clean_reply, flags=re.DOTALL).strip()
    
    # Fallback if cleaning removed everything
    if not clean_reply and last_reply:
        clean_reply = last_reply

    # Return updated state
    return {
        **state,
        "messages": [AIMessage(content=clean_reply)],
        "summary": new_summary,
        "last_bot_reply": last_reply
    }