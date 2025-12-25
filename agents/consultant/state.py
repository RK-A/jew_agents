from typing import TypedDict, List, Dict, Any, Optional, Annotated
from datetime import datetime
import operator

class ConsultantState(TypedDict):
    """State for ConsultantAgent workflow"""
    user_id: str
    message: str
    conversation_history: Optional[List[Dict[str, str]]]
    user_profile: Optional[Dict[str, Any]]
    extracted_preferences: Dict[str, Any]
    products: List[Dict[str, Any]]
    response: str
    recommendations: List[str]
    error: Optional[str]
    step: str