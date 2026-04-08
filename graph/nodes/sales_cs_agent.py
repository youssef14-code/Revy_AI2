# graph/nodes/sales_cs_agent.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from langchain_core.messages import SystemMessage, AIMessage
from langchain_ollama import ChatOllama
from state.state import AgentState
from retrival.retriever import RetrievalService 
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
LANGUAGE RULE
====================
Always respond in the same language the user is speaking.
If the user writes in Arabic, respond in Arabic.
If the user writes in English, respond in English.
Mixed language? Follow the dominant language used.
"""


def sales_cs_agent_node(state: AgentState) -> AgentState:
    user_message = state["messages"][-1].content
    summary = state.get("summary", "")

    # RAG مباشرة
    query = state.get("refined_query") or user_message
    context = RetrievalService().search(query)
    print(f"📄 RAG context: {len(context)} chars")


    messages = [
        SystemMessage(content=SYSTEM_PROMPT + f"\n\nContext:\n{context}\n\nPrevious summary:\n{summary}"),
        *state["messages"]
        
        ]
    

    response = llm.invoke(messages)
    print("🔍 Searching knowledge base...")
    print(f"[Sales & CS Agent] responded ✅")
    print(f"🔢 Tokens: input={response.usage_metadata['input_tokens']} | output={response.usage_metadata['output_tokens']} | total={response.usage_metadata['total_tokens']}")
    return {**state, "messages": [AIMessage(content=response.content)]}
    
