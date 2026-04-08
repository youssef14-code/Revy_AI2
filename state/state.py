from typing import TypedDict, Annotated, Optional, Dict, Any
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    client: Optional[Any]   
    # Routing
    next_agent: str
    intent: Optional[str]
    refined_query: Optional[str]
    
    # RAG
    rag_context: Optional[str]
    
    # Lead info
    lead: Optional[Dict[str, Any]]
    
    # Memory
    summary: Optional[str]
    last_bot_reply: Optional[str]