# graph/nodes/intent_node.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import json
import re
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from state.state import AgentState

llm = ChatOllama(model="llama3", temperature=0)

SYSTEM_PROMPT = """You are an intent classifier for RevyAI, a business AI automation company.
Analyze the user message and return JSON only (no extra text) in this format:
{
  "intent": "hr | sales | cs | booking | greeting | other",
  "lead_info": {
    "name": "<customer name or null>",
    "phone": "<phone number or null>",
    "day": "<preferred day or null>",
    "time": "<preferred time or null>",
    "topic": "<meeting topic or null>"
  }
}

Intent definitions:
- hr: jobs, hiring, careers, vacancies, working at RevyAI
- sales: pricing, AI solutions, negotiation, business needs
- cs: company info, services, who are you, what do you do
- booking: wants to book a meeting or demo (e.g. "I want to book", "schedule a call")
- greeting: general greeting or small talk
- other: anything unrelated

Rules:
- Always return valid JSON only, no extra text
- If unsure, default to "cs"
- User may write in Arabic, English, or mixed — understand all"""


def intent_node(state: AgentState) -> AgentState:
    message = state["messages"][-1].content

    # ضيف الـ summary كـ context لو موجود
    summary = state.get("summary", "")
    system = SYSTEM_PROMPT
    if summary:
        system += f"\n\nPrevious conversation summary:\n{summary}"

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=message)
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group()) if match else {}
    except Exception:
        data = {}

    intent = data.get("intent", "cs")
    if intent not in ["hr", "sales", "cs", "booking", "greeting", "other"]:
        intent = "cs"

    # دمج الـ lead info مع اللي موجود
    lead_info = data.get("lead_info", {})
    existing_lead = state.get("lead", {})
    for key in ["name", "phone", "day", "time", "topic"]:
        if lead_info.get(key):
            existing_lead[key] = lead_info[key]

    print(f"[Intent Node] intent={intent} | lead={existing_lead}")

    return {
        **state,
        "intent": intent,
        "lead": existing_lead
    }