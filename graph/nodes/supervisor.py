# graph/nodes/intent_node.py

import json, re
from langchain_core.messages import SystemMessage, HumanMessage
from state.state import AgentState
from langchain_openai import ChatOpenAI
from graph.nodes.base import safe_invoke
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model="google/gemini-2.5-flash-lite-preview-09-2025",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key="OPENROUTER_API_KEY",
    max_tokens=1700
)

SYSTEM_PROMPT = """
You are an intelligent routing assistant for RevyAI.
Your ONLY job is to analyze the user message + context and return a JSON object.
No explanation. No markdown. No extra text. JSON only.

====================
OUTPUT FORMAT
====================
{
  "next_agent": "hr | sales_cs | direct | booking",
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
Route to exactly ONE agent based on the user's primary intent:

| Agent     | When to use                                                                |
|-----------|----------------------------------------------------------                  |
| hr        | Jobs, hiring, careers, vacancies, CV submission                            |
| sales_cs  | Pricing, services, company info, AI solutions, support                     |
| booking   | User wants to schedule a meeting or appointment or confirm a book          |
| direct    | Greetings, small talk, out-of-scope, unrelated topics                      |

====================
INTENT RULES
====================
| Intent   | Description                                             |
|----------|---------------------------------------------------------|
| hr       | Job-related inquiries                                   |
| sales    | Pricing, negotiation, AI solutions                      |
| cs       | Company info, capabilities, how it works                |
| booking  | Scheduling a meeting or demo or confirm a book          |
| greeting | Hi, hello, how are you, greetings in any language       |
| other    | Unrelated, out-of-scope, unclear                        |

====================
REFINED QUERY RULES
====================
- ONLY fill if next_agent is "sales_cs" AND intent is NOT "greeting" or "other"
- Rewrite the user message as a clear English search query for RAG retrieval
- Be specific and include "RevyAI" where relevant

Examples:
  "ليه اسعاركو غاليه"  → "RevyAI pricing cost value propositio"
  "بتقدموا ايه"        → "RevyAI services offerings solutions"
  "how does it work"   → "RevyAI how it works process methodology"


====================
LEAD INFO RULES
====================
- Extract ONLY values explicitly stated by the user
- NEVER assume, infer, or fabricate any value
- If not clearly mentioned → null

====================
ROUTING EXAMPLES
====================
User: "hi"
→ next_agent: "direct", intent: "greeting"

User: "I want to book a meeting"
→ next_agent: "booking", intent: "booking"

User: "what services do you offer?"
→ next_agent: "sales_cs", intent: "cs"

User: "are there any open positions?"
→ next_agent: "hr", intent: "hr"

====================
CONVERSATION CONTEXT
====================
Previous summary:
{summary}

Last bot reply:
{last_bot_reply}
"""




@safe_invoke
def intent_node(state: AgentState) -> AgentState:
    user_message = state["messages"][-1].content
    summary = state.get("summary") or ""
    last_bot_reply = state.get("last_bot_reply") or ""
    prompt = SYSTEM_PROMPT.replace("{summary}", summary).replace("{last_bot_reply}", last_bot_reply)

    # exit keywords check
    if state.get("booking_stage") == "collecting":
        exit_keywords = ["cancel", "never mind", "forget it", "إلغاء", "مش عايز", "خلاص"]
        if any(word in user_message.lower() for word in exit_keywords):
            print(f"[Supervisor] → exiting booking flow")
            return {
                **state,
                "next_agent": "direct",
                "booking_stage": None,
                "lead": {}
            }

    # LLM call دايماً بتحصل
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

    intent = data.get("intent", "other")
    raw_agent = data.get("next_agent", "sales_cs")

    # routing
    if state.get("booking_stage") == "collecting":
        next_agent = "booking"  # ← لو في booking flow، روح booking دايماً
    elif raw_agent == "hr":
        next_agent = "hr"
    elif raw_agent == "booking" or intent == "booking":
        next_agent = "booking"
    elif raw_agent == "direct" or intent in ["greeting", "other"]:
        next_agent = "direct"
    else:
        next_agent = "sales_cs"

    # lead merge
    lead_info = data.get("lead_info") or {}
    existing_lead = dict(state.get("lead") or {})
    refined_query = data.get("refined_query") or ""

    for key in ["name", "phone", "day", "time", "topic"]:
        val = lead_info.get(key)
        if val:
            existing_lead[key] = val

    print(f"[Supervisor] → {next_agent} | intent={intent} | lead={existing_lead}")

    return {
        **state,
        "next_agent": next_agent,
        "intent": intent,
        "lead": existing_lead,
        "refined_query": refined_query
    }