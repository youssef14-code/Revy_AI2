# graph/nodes/booking_node.py

import sys, os 
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import re
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from state.state import AgentState
from tools.tools import create_booking_tool
from tools.services import MemoryService
from graph.nodes.base import safe_invoke

llm = ChatOpenAI(
    model="google/gemini-3-flash-preview",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
    max_tokens=1500
)

SYSTEM_PROMPT = """You are Revy, a professional booking assistant for RevyAI.
Your job is to collect the required information and book a business meeting or consultation.

====================
COMPANY INFO
====================
- Company: RevyAI
- Services: AI automation, intelligent agents, system integration
- Contact: info@revyai.tech

====================
REQUIRED FIELDS
====================
- name: client full name
- day: preferred day (e.g. Monday, March 15)
- time: preferred time (e.g. 10:00 AM)
- phone_number: client phone number
- description: meeting purpose (optional, e.g. AI consultation, product demo)

====================
STEPS
====================
1. Check what fields are already collected from the conversation context
2. Ask ONLY for the missing fields — never re-ask for info already provided
3. Once ALL required fields are collected AND client confirms → call book_appointment tool
4. Confirm the booking with a professional summary

====================
BEHAVIOR
====================
- Be concise and professional
- Never fabricate or assume information
- Never confirm a booking without calling the tool first

====================
MEMORY RULES (MANDATORY)
====================
You MUST include the following tags at the END of your response.
DO NOT skip them.

<LAST_BOT_REPLY>
[Repeat your full conversational reply to the user here]
</LAST_BOT_REPLY>

<SUMMARY>
[Update the summary of the entire conversation so far. Keep it to 2-3 lines.]
</SUMMARY>

====================
LANGUAGE RULE
====================
Always respond in the same language the user is speaking.
"""

@safe_invoke
def booking_node(state: AgentState) -> AgentState:
    # ── جيب الـ client من الـ state ──
    client = state.get("client")
    booking_tool = create_booking_tool(client)     # ← هنا جوه الـ function
    llm_with_tools = llm.bind_tools([booking_tool])
    current_summary = state.get("summary") or ""
    last_bot_reply = state.get("last_bot_reply") or ""
    lead = state.get("lead") or {}


    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT
            + f"\n\n====================\nCONVERSATION CONTEXT\n====================\n"
            + f"Previous summary:\n{current_summary}\n\n"
            + f"Last bot reply:\n{last_bot_reply}\n\n"
            + f"Already collected info:\n{lead}\n"
            + "===================="
        ),  
        *state["messages"]
    ]

    response = llm_with_tools.invoke(messages)

    if getattr(response, "tool_calls", None):
        messages.append(response)

        for tool_call in response.tool_calls:
            print(f"🔧 Tool used: {tool_call['name']}")
            tool_result = booking_tool.invoke(tool_call["args"])
            messages.append(ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call["id"]
            ))

        final = llm_with_tools.invoke(messages)
        content = final.content
        booking_stage = "confirmed"
    else:
        content = response.content
        booking_stage = "collecting"
    # استخرج الـ summary والـ reply
    summary_match = re.search(r"<SUMMARY>(.*?)</SUMMARY>", content, re.DOTALL)
    new_summary = summary_match.group(1).strip() if summary_match else current_summary  

    reply_match = re.search(r"<LAST_BOT_REPLY>(.*?)</LAST_BOT_REPLY>", content, re.DOTALL)
    new_last_reply = reply_match.group(1).strip() if reply_match else ""
    
    # حفظ في DB
    if client:
        MemoryService.update(client=client, summary=new_summary, last_reply=new_last_reply)
   
    # نظف الرد
    clean_reply = re.sub(r"<SUMMARY>.*?</SUMMARY>", "", content, flags=re.DOTALL)
    clean_reply = re.sub(r"<LAST_BOT_REPLY>.*?</LAST_BOT_REPLY>", "", clean_reply, flags=re.DOTALL).strip()
    if not clean_reply and new_last_reply:
         clean_reply = new_last_reply
    print(f"[Booking Node] responded ✅ | stage={booking_stage}")

    return {
        **state,
        "messages": [AIMessage(content=clean_reply)],
        "summary": new_summary,
        "last_bot_reply": new_last_reply,
        "booking_stage": booking_stage
    }