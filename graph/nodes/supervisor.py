# graph/nodes/intent_node.py

import json, re
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from state.state import AgentState

llm = ChatOllama(model="llama3.2", temperature=0)

SYSTEM_PROMPT = """You are a router for RevyAI. Analyze the user message and return JSON only:
{
  "next_agent": "hr | sales_cs",
  "intent": "hr | sales | cs | booking | greeting | other",
  "lead_info": {
    "name": "<or null>",
    "phone": "<or null>",
    "day": "<or null>",
    "time": "<or null>",
    "topic": "<or null>"
  }
}

<<<<<<< HEAD
Routing rules:
- hr: jobs, hiring, careers, vacancies
- sales_cs: everything else (pricing, services, booking, company info)

Intent rules:
- hr: jobs related
- sales: pricing, negotiation, AI solutions
- cs: company info, who are you, what do you do
- booking: wants to book a meeting
- greeting: hi, hello
- other: unrelated"""
=======
Agents:
- hr        → employee info, leave requests, HR policies, payroll
- support   → complaints, tickets, returns, warranty

Reply with ONE word only:
hr
support"""
>>>>>>> abdo


def intent_node(state: AgentState) -> AgentState:
    message = state["messages"][-1].content

    try:
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ])
        raw = response.content.strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group()) if match else {}
    except Exception:
        data = {}

    next_agent = data.get("next_agent", "sales_cs")
    if next_agent not in ["hr", "sales_cs"]:
        next_agent = "sales_cs"

<<<<<<< HEAD
    intent = data.get("intent", "cs")
    
    lead_info = data.get("lead_info", {})
    existing_lead = state.get("lead", {})
    for key in ["name", "phone", "day", "time", "topic"]:
        if lead_info.get(key):
            existing_lead[key] = lead_info[key]
=======
    # validation - لو الـ LLM رجع حاجة غلط
    if next_agent not in ["hr", "support"]:
        next_agent = "support"
>>>>>>> abdo

    print(f"[Supervisor] → {next_agent} | intent={intent} | lead={existing_lead}")

    return {
        **state,
        "next_agent": next_agent,
        "intent": intent,
        "lead": existing_lead
    }