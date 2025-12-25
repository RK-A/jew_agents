"""Node functions for girlfriend agent graph"""

import logging
from typing import Any, Dict
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode

from .state import GirlfriendState
from .tools import get_horoscope, detect_zodiac_sign

logger = logging.getLogger(__name__)

# Create tool node
tool_node = ToolNode([get_horoscope, detect_zodiac_sign])


def create_girlfriend_node(llm_with_tools):
    """Create girlfriend conversation node.
    
    Args:
        llm_with_tools: LLM bound with tools
    
    Returns:
        Node function for girlfriend agent
    """
    
    async def girlfriend_node(state: GirlfriendState) -> Dict[str, Any]:
        """Process girlfriend conversation.
        
        Args:
            state: Current conversation state
        
        Returns:
            Updated messages
        """
        try:
            logger.info(f"Girlfriend agent processing message for user {state.get('user_id', 'unknown')}")
            
            # Invoke LLM with tools
            response = await llm_with_tools.ainvoke(state["messages"])
            
            return {"messages": [response]}
        
        except Exception as e:
            logger.error(f"Error in girlfriend node: {e}", exc_info=True)
            error_message = AIMessage(
                content="Ой, я немного запуталась. Повтори, пожалуйста, ещё раз."
            )
            return {"messages": [error_message]}
    
    return girlfriend_node


def should_continue(state: GirlfriendState) -> str:
    """Determine if conversation should continue to tools or end.
    
    Args:
        state: Current conversation state
    
    Returns:
        Next node name ('tools' or '__end__')
    """
    last_message = state["messages"][-1]
    
    # Check if there are tool calls
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        logger.info(f"Routing to tools: {[tc['name'] for tc in last_message.tool_calls]}")
        return "tools"
    
    logger.info("Conversation complete, ending")
    return "__end__"
