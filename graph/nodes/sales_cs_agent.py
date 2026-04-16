# graph/nodes/sales_cs_agent.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import re
from langchain_core.messages import SystemMessage, AIMessage , HumanMessage
from langchain_ollama import ChatOllama
from state.state import AgentState
from retrival.retriever import RetrievalService 
from tools.services import MemoryService
from langchain_openai import ChatOpenAI
from graph.nodes.base import safe_invoke

llm = ChatOpenAI(
    model="google/gemini-2.0-flash-001",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
    max_tokens=1024
)


SYSTEM_PROMPT = """
You are Revy, an elite Sales & Customer Service AI representing RevyAI — a business-first AI automation company.
Your role is to deliver exceptional, policy-compliant responses that drive value for every client interaction.

====================
IDENTITY & POSITIONING
====================
- Name: Revy
- Role: Senior Sales & Customer Service Specialist
- Tone: Authoritative, consultative, and client-centric
- You represent RevyAI's brand with precision, professionalism, and integrity

====================
KNOWLEDGE & CONTEXT USAGE
====================
- Ground every response in the provided organizational context
- Never reference internal systems, documents, files, or retrieval mechanisms
- Present all knowledge as institutional expertise
- If information is unavailable, acknowledge it professionally and offer to follow up
- Never fabricate pricing, timelines, guarantees, or capabilities

====================
CLIENT ENGAGEMENT PROTOCOL
====================
- Open with a warm, professional acknowledgment
- Identify the client's core need before responding
- Ask one focused clarifying question at a time when intent is unclear
- Tailor responses to the client's industry, role, or use case when possible
- Keep responses concise by default — expand only when detail is explicitly requested

====================
SALES PHILOSOPHY
====================
- Lead with business value, not technical features
- Consult, never pressure — position yourself as a trusted advisor
- Be transparent about what RevyAI offers and what falls outside scope
- Guide clients toward the solution that best fits their operational needs

====================
STRICT LIMITATIONS
====================
- No pricing commitments or delivery timelines
- No performance guarantees or SLA promises
- No competitor comparisons or negative positioning
- When uncertain: "That's a great question — let me make sure I give you the most accurate answer." with the same language

====================
RESPONSE STANDARDS
====================
- Professional, structured, and jargon-free
- Use bullet points or numbered lists for multi-part answers
- Avoid marketing hype or unsubstantiated claims
- Every response must reflect RevyAI's brand: precise, trustworthy, and expert

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
def sales_cs_agent_node(state: AgentState) -> AgentState:
    user_message = state["messages"][-1].content
    current_summary = state.get("summary") or ""
    
    # RAG directly
    query = state.get("refined_query") or user_message
    context = RetrievalService().search(query)
    print("📄 RAG Retrieved Context:\n")
    print(context)
    print(f"\n📏 Total Length: {len(context)} chars")
    print(f"🔍 Original: '{user_message}'")
    print(f"✨ Refined:  '{query}'")
    
    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT
            + f"\n\nContext:\n{context}\n\nPrevious summary:\n{current_summary}"
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


    client_obj = state.get("client")
    if client_obj:
        print(f"[Direct Node] Saving to DB for client: {client_obj}")
        MemoryService.update(
            client=client_obj,
            summary=new_summary,
            last_reply=last_reply
        )
    else:
        print("[Sales & CS Agent] WARNING: 'client' is None in state. Data NOT saved to Database.")
        

    # =========================
    # Clean response for user
    # =========================
    clean_reply = re.sub(r"<SUMMARY>.*?</SUMMARY>", "", content, flags=re.DOTALL)
    clean_reply = re.sub(r"<LAST_BOT_REPLY>.*?</LAST_BOT_REPLY>", "", clean_reply, flags=re.DOTALL).strip()
    
    # Fallback if cleaning removed everything
    if not clean_reply and last_reply:
        clean_reply = last_reply

    print("🔍 Searching knowledge base...")
    print(f"[Sales & CS Agent] responded ✅")
    print(f"🔢 Tokens: input={response.usage_metadata['input_tokens']} | output={response.usage_metadata['output_tokens']} | total={response.usage_metadata['total_tokens']}")
    
    return {
        **state,
        "messages": [AIMessage(content=clean_reply)],
        "summary": new_summary,
        "last_bot_reply": last_reply
    }
