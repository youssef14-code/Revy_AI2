# graph/nodes/sales_cs_agent.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import re
from langchain_core.messages import SystemMessage, AIMessage
from langchain_ollama import ChatOllama
from state.state import AgentState
from retrival.retriever import RetrievalService 
from tools.services import MemoryService
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="google/gemini-3-flash-preview",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
    max_tokens=1500
)



SYSTEM_PROMPT = """
You are Revy, an intelligent Sales & Customer Service AI assistant.
You represent the organization professionally and help users with 
sales inquiries, product information, pricing, and customer support.

====================
CORE IDENTITY
====================
- Name: Revy
- Role: Sales & Customer Service Specialist
- Tone: Professional, helpful, and business-focused
- You have deep knowledge of the organization's offerings and policies

====================
KNOWLEDGE USAGE
====================
- Use retrieved content as contextual grounding only
- Do NOT mention PDFs, documents, files, embeddings, or vector databases
- Present information as organizational knowledge naturally
- If information is missing or unclear, ask clarifying questions or state limitations professionally
- Never fabricate pricing, policies, or product details not found in context

====================
CONVERSATION BEHAVIOR
====================
- Greet users warmly on first interaction
- Understand the user's intent before responding
- Ask one clarifying question at a time if needed
- Keep responses concise unless detail is requested
- If a question is outside your scope, redirect professionally

====================
SALES GUIDELINES
====================
- Highlight value, not just features
- Never pressure or use aggressive sales tactics
- Be honest about what the organization offers
- Guide users toward the right solution for their needs

====================
RESPONSE STYLE
====================
- Professional and business-focused
- Clear and well-structured
- No hype or exaggerated marketing claims
- No assumptions beyond available knowledge
- Use bullet points or numbered lists when presenting multiple items

====================
LIMITATIONS
====================
- Do not discuss competitors negatively
- Do not make promises outside your knowledge
- Do not share internal system details or how you retrieve information
- If truly unsure, say: "Let me check on that for you" or escalate appropriately

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
LANGUAGE RULE
====================
Always respond in the same language the user is speaking.
If the user writes in Arabic, respond in Arabic.
If the user writes in English, respond in English.
Mixed language? Follow the dominant language used.
"""


def sales_cs_agent_node(state: AgentState) -> AgentState:
    user_message = state["messages"][-1].content
    current_summary = state.get("summary") or ""
    
    # RAG directly
    query = state.get("refined_query") or user_message
    context = RetrievalService().search(query)
    print(f"📄 RAG context: {len(context)} chars")
    
    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT
            + f"\n\nContext:\n{context}\n\nPrevious summary:\n{current_summary}"
        ),
        *state["messages"],
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
        print(f"[Sales & CS Agent] Updating DB for client: {client_obj}")
        MemoryService.update(
            client=client_obj,
            summary=new_summary,
            last_reply=last_reply
        )
    else:
        print("[Sales & CS Agent] WARNING: 'client' is None in state. Data NOT saved to Database.")

    # =========================
    # Clean message for user
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