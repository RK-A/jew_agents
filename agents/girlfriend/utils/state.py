"""State definition for girlfriend agent."""

from typing import TypedDict, List, Dict, Optional


class GirlfriendState(TypedDict, total=False):
    """State for girlfriend conversation agent"""

    user_id: str
    message: str
    conversation_history: List[Dict[str, str]]
    zodiac_sign: Optional[str]
    response: str
