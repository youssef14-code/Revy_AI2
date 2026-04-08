# graph/nodes/intent_node.py

import json, re
from langchain_core.messages import SystemMessage, HumanMessage
from state.state import AgentState
from langchain_openai import ChatOpenAI

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
- sales_cs: pricing, services, booking, company info, AI solutions
- direct: greetings, small talk, unrelated topics

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
}

"""



def intent_node(state: AgentState) -> AgentState:
    user_message = state["messages"][-1].content

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

    intent = data.get("intent", "cs")

    # ← الـ routing هنا
    raw_agent = data.get("next_agent", "sales_cs")
    if raw_agent == "hr":
        next_agent = "hr"
    elif intent in ["greeting", "other"]:
        next_agent = "direct"
    else:
        next_agent = "sales_cs"

    lead_info = data.get("lead_info", {})
    existing_lead = state.get("lead", {})
    for key in ["name", "phone", "day", "time", "topic"]:
        if lead_info.get(key):
            existing_lead[key] = lead_info[key]

    print(f"[Supervisor] → {next_agent} | intent={intent} | lead={existing_lead}")

    return {
        **state,
        "next_agent": next_agent,
        "intent": intent,
        "lead": existing_lead
    }