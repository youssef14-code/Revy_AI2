# graph/nodes/direct_node.py

from langchain_core.messages import SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from state.state import AgentState

llm = ChatOpenAI(
    model="google/gemini-3-flash-preview",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
    max_tokens=1500
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
LANGUAGE RULE
====================
Always respond in the same language the user is speaking.
If the user writes in Arabic, respond in Arabic.
If the user writes in English, respond in English.
Mixed language? Follow the dominant language used.
"""

def direct_node(state: AgentState) -> AgentState:
    intent = state.get("intent", "other")
    
    # لو السؤال عن الشركة وده وده وده
    if intent in ["sales", "cs", "booking", "hr"]:
        # ودّيه للـ RAG
        return {**state, "next_agent": "rag"}
    
    # غير كده رد مباشرة
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"]
    ]
    response = llm.invoke(messages)
    print(f"[Direct Node] responded ✅")
    return {**state, "messages": [AIMessage(content=response.content)]}