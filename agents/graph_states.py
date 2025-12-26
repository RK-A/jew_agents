"""LangGraph state definitions for multi-agent jewelry consultation system"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from datetime import datetime
import operator


class OrchestratorState(TypedDict):
    """State for multi-agent orchestrator workflow"""
    task_type: str
    user_id: Optional[str]
    message: Optional[str]
    content: Optional[str]
    conversation_history: Optional[List[Dict[str, str]]]
    
    # Results from different agents
    consultant_result: Optional[Dict[str, Any]]
    analysis_result: Optional[Dict[str, Any]]
    trend_result: Optional[Dict[str, Any]]
    taste_result: Optional[Dict[str, Any]]
    girlfriend_result: Optional[Dict[str, Any]]
    
    # Taste-specific state
    current_question_index: Optional[int]
    answers: Optional[Dict[str, str]]
    
    # Final output
    status: str
    final_result: Dict[str, Any]
    error: Optional[str]
    
    # Workflow tracking
    agents_to_run: Annotated[List[str], operator.add]
    completed_agents: Annotated[List[str], operator.add]
    step: str


class AgentMessage(TypedDict):
    """Standard message format between agents"""
    agent_type: str
    timestamp: str
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]]

