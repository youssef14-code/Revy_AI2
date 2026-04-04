from typing import TypedDict, Annotated, Optional, Dict, Any
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    next_agent: str
    rag_context: str
    intent: Optional[str]
    lead: Dict[str, Any]
    summary: Optional[str]