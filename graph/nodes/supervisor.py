# graph/nodes/intent_node.py

import json, re
from langchain_core.messages import SystemMessage, HumanMessage
from state.state import AgentState
from langchain_openai import ChatOpenAI
from graph.nodes.base import safe_invoke

llm = ChatOpenAI(
    model="google/gemini-3-flash-preview",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
    max_tokens=1500
)

SYSTEM_PROMPT = """
You are a routing assistant for RevyAI.
Analyze the user message and return JSON only — no explanation, no markdown.

{
  "next_agent": "hr | sales_cs | direct",
  "intent": "hr | sales | cs | booking | greeting | other",
  "refined_query": "<string or null>",
  "lead_info": {
    "name": "<or null>",
    "phone": "<or null>",
    "day": "<or null>",
    "time": "<or null>",
    "topic": "<or null>"
  }
}

====================
ROUTING RULES
====================
- hr: jobs, hiring, careers, vacancies
- sales_cs: pricing, services, company info, AI solutions
- direct: greetings, small talk, unrelated topics
- booking:  wants to book a meeting or appointment

====================
INTENT RULES
====================
- hr: jobs related
- sales: pricing, negotiation, AI solutions
- cs: company info, who are you, what do you do
- booking: wants to book a meeting
- greeting: hi, hello, how are you
- other: unrelated or out of scope

====================
REFINED QUERY RULES
====================
- Only fill if next_agent is sales_cs AND intent is NOT greeting or other
- Convert user message to a clear English search query for RAG retrieval
- Examples:
  - "ليه اسعاركو غاليه" → "RevyAI pricing cost value justification"
  - "بتقدموا ايه" → "RevyAI services offerings solutions"
  - "كيف تعملون" → "RevyAI how it works process methodology"
- Otherwise → null

====================
LEAD INFO RULES
====================
- Extract only if explicitly mentioned by the user
- Never assume or fabricate values
- If not mentioned → null

====================
Exmpales
====================
- if any one send hi or hello or hola
response with this

  "next_agent": "direct",
  "intent": "greeting | other",
  "refined_query": "<string or null>",
  "lead_info": {
    "name": "<or null>",
    "phone": "<or null>",
    "day": "<or null>",
    "time": "<or null>",
    "topic": "<or null>"
  }

====================
CONVERSATION CONTEXT
====================
Previous conversation summary:
{summary}

Last bot reply:
{last_bot_reply}

  
}

"""


@safe_invoke
def intent_node(state: AgentState) -> AgentState:
    if state.get("booking_stage") == "collecting":
        print(f"[Supervisor] → booking (continuing) | lead={state.get('lead', {})}")
        return {**state, "next_agent": "booking"}
    

    user_message = state["messages"][-1].content
    summary = state.get("summary") or ""
    last_bot_reply = state.get("last_bot_reply") or ""
    prompt = SYSTEM_PROMPT.replace("{summary}", summary).replace("{last_bot_reply}", last_bot_reply)
    
    try:
        response = llm.invoke([
            SystemMessage(content=prompt),
            HumanMessage(content=user_message)
        ])
        raw = response.content.strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group()) if match else {}
    except Exception:
        data = {}

    intent = data.get("intent", "cs")

    # ← الـ routing هنا
    raw_agent = data.get("next_agent", "sales_cs")
    if raw_agent == "hr":
        next_agent = "hr"
    elif raw_agent == "booking" or intent == "booking":
        next_agent = "booking"    
    elif intent in ["greeting", "other"]:
        next_agent = "direct"
    else:
        next_agent = "sales_cs"

    lead_info = data.get("lead_info", {})
    existing_lead = state.get("lead", {})
    refined_query = data.get("refined_query") or ""
    for key in ["name", "phone", "day", "time", "topic"]:
        if lead_info.get(key):
            existing_lead[key] = lead_info[key]

    print(f"[Supervisor] → {next_agent} | intent={intent} | lead={existing_lead}")

    return {
        **state,
        "next_agent": next_agent,
        "intent": intent,
        "lead": existing_lead,
        "refined_query": refined_query
    }