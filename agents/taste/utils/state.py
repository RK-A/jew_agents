
from typing import TypedDict, List, Dict, Optional


class JewelryState(TypedDict, total=False):
    """State for jewelry preference detection agent"""
    user_id: str
    message: str
    conversation_history: List[Dict[str, str]]
    current_question_index: int
    answers: Dict[str, str]  # question -> user_answer
    jewelry_profile: Optional[Dict[str, any]]  # Detected jewelry preferences
    response: str
