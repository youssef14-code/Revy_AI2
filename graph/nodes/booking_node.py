# graph/nodes/booking_node.py

import sys, os 
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import re
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage , HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from state.state import AgentState
from tools.tools import create_booking_tool
from tools.services import MemoryService
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
- time:  preferred time MUST be in 12-hour format with AM/PM (e.g. 10:00 AM or 07:30 PM)
  IMPORTANT:
  - Always include AM or PM
  - If user does not specify AM/PM, ask a clarification question
  - Never return ambiguous time like "10:00" only
- phone_number: client phone number
- description: meeting purpose in details

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
[Your reply to the user. This will be used as context in the next conversation turn.]
</LAST_BOT_REPLY>

<SUMMARY>
[Cumulative conversation summary. STRICT RULES:
1. Build on the previous summary — copy it first, then update only what changed
2. Always capture in this structure:
   - User Info: any personal details mentioned (name, phone, company, role, etc.)
   - Intent: what the user is trying to accomplish
   - Key Points: important topics, questions, or concerns raised
   - Status: what just happened + what is still pending
3. Extract User Info from ANY message — not just booking context
4. Use English regardless of conversation language.]
</SUMMARY>

<LEAD_INFO>
[Structured lead data. STRICT RULES:
1. Continuously collect and update fields as the user provides information
2. Never remove or overwrite existing data unless the user explicitly corrects it
3. After booking is CONFIRMED:
   - Move essential info (name, phone, email, booking reference) to SUMMARY under "Retained Info"
   - Then CLEAR all fields in this section and replace with: "✅ Booking confirmed — lead data cleared."]
</LEAD_INFO>

===============

====================
LANGUAGE PROTOCOL
====================
Detect and match the client's language automatically.
Arabic input → Arabic response.
English input → English response.
Mixed input → Default to the dominant language used.
Never mix languages within a single response.
"""

@safe_invoke
def booking_node(state: AgentState) -> AgentState:
    # ── جيب الـ client من الـ state ──
    user_message = state["messages"][-1].content
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
        HumanMessage(content=user_message)
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

        args = response.tool_calls[0]["args"]
        lang = "ar" if any("\u0600" <= c <= "\u06ff" for c in state["messages"][-1].content) else "en"
        if lang == "ar":
            content = f"✅ تم تأكيد حجزك!\n\n📅 اليوم: {args.get('day')}\n⏰ الوقت: {args.get('time')}\n📞 الهاتف: {args.get('phone_number')}\n📝 الموضوع: {args.get('description', 'غير محدد')}"
        else:
            content = f"✅ Your booking is confirmed!\n\n📅 Day: {args.get('day')}\n⏰ Time: {args.get('time')}\n📞 Phone: {args.get('phone_number')}\n📝 Topic: {args.get('description', 'Not specified')}"    
        booking_stage = "confirmed"
    else:
        content = response.content
        booking_stage = "collecting"

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
    # =========================
    # Clean response for user
    # =========================
    

    print(f"[Booking Node] responded ✅ | stage={booking_stage}")

    print(f"🔢 Tokens: input={response.usage_metadata['input_tokens']} | output={response.usage_metadata['output_tokens']} | total={response.usage_metadata['total_tokens']}")
    

    return {
        **state,
        "messages": [AIMessage(content=last_reply)],
        "summary": new_summary,
        "last_bot_reply": last_reply,
         "booking_stage": "done" if booking_stage == "confirmed" else "collecting",
        "lead": {} if booking_stage == "confirmed" else state.get("lead", {})
    }