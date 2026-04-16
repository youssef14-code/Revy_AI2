# graph/nodes/direct_node.py

from langchain_core.messages import SystemMessage, AIMessage , HumanMessage
from langchain_openai import ChatOpenAI
from state.state import AgentState
import re
from models.models import Client 
from tools.services import MemoryService
from graph.nodes.base import safe_invoke



llm = ChatOpenAI(
    model="google/gemini-2.0-flash-001",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
    max_tokens=1024
)

SYSTEM_PROMPT = """
You are Revy, a friendly and intelligent AI assistant.
You handle general conversations that are not related to sales or HR topics.

====================
CORE IDENTITY
====================
- Name: Revy
- Role: General Assistant
- Tone: Friendly, natural, and conversational

====================
SCOPE
====================
- General knowledge questions
- Casual conversation and small talk
- Greetings and farewells
- General advice (non-specialized)
- Answering "what can you do" type questions

====================
OUT OF SCOPE
====================
- Sales, pricing, or product inquiries → handled by another specialist
- HR, hiring, or employee-related topics → handled by another specialist
- If user asks about these, inform them you'll connect them with the right specialist

====================
BEHAVIOR
====================
- Be natural and conversational
- Keep responses concise and friendly
- Do not over-explain or add unnecessary detail
- Do not pretend to know things outside your knowledge

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
Detect and match the client's language automatically.
Arabic input → Arabic response.
English input → English response.
Mixed input → Default to the dominant language used.
Never mix languages within a single response.
"""
@safe_invoke
def direct_node(state: AgentState) -> AgentState:
    
  
    # Get current summary from state (defaults to empty string if None)
    user_message = state["messages"][-1].content
    current_summary = state.get("summary") or ""
    last_bot_reply = state.get("last_bot_reply") or ""
    print(f"[Direct Node] Received Summary from State: '{current_summary}'")

    

    # Build messages with the previous summary injected into SystemMessage
    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT
            + f"\n\n====================\nCONVERSATION CONTEXT\n====================\nPrevious summary:\n{current_summary}\n\nLast bot reply:\n{last_bot_reply}\n===================="
        ),
        HumanMessage(content=user_message),
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
    else:
        print("[Direct Node] WARNING: 'client' is None in state. Data NOT saved to Database.")

    # =========================
    # Clean response for user
    # =========================
    clean_reply = re.sub(r"<SUMMARY>.*?</SUMMARY>", "", content, flags=re.DOTALL)
    clean_reply = re.sub(r"<LAST_BOT_REPLY>.*?</LAST_BOT_REPLY>", "", clean_reply, flags=re.DOTALL).strip()
    
    # Fallback if cleaning removed everything
    if not clean_reply and last_reply:
        clean_reply = last_reply

    print(f"[Direct Node] responded ✅ | New Summary Length: {len(new_summary)}")
    
    return {
        **state,
        "messages": [AIMessage(content=clean_reply)],
        "summary": new_summary,
        "last_bot_reply": last_reply
    }
