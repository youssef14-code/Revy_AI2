# graph/nodes/base.py

from langchain_core.messages import AIMessage
from state.state import AgentState

def safe_invoke(node_func):
    """Decorator to handle errors in any node"""
    def wrapper(state: AgentState) -> AgentState:
        try:
            return node_func(state)
        except Exception as e:
            print(f"❌ Error in {node_func.__name__}: {e}")
            return {
                **state,
                "messages": [AIMessage(content="عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.")]
            }
    return wrapper