from typing import TypedDict, List, Dict, Any, Optional, Annotated
from datetime import datetime
import operator

class AgentState(TypedDict):
    """State shared across all agents"""
    # Input
    ticket: Dict[str, Any]
    
    # Retrieval results
    retrieved_docs: Annotated[List[Dict[str, Any]], operator.add]
    retrieval_queries: Annotated[List[str], operator.add]
    retrieval_attempts: int
    
    # Analysis
    diagnosis: Optional[str]
    root_cause: Optional[str]
    similar_tickets: List[str]
    
    # Resolution
    resolution_steps: Optional[str]
    verification_steps: Optional[str]
    preventive_actions: Optional[str]
    references: List[str]
    
    # Agent coordination
    current_agent: str
    next_agent: Optional[str]
    plan: List[str]
    completed_steps: Annotated[List[str], operator.add]
    
    # Decision tracking
    should_escalate: bool
    escalation_reason: Optional[str]
    requires_hitl: bool
    
    # Critic feedback
    critic_feedback: Optional[str]
    critic_approved: bool
    revision_count: int
    
    # Output
    resolution_note: Optional[Dict[str, Any]]
    
    # Trajectory logging
    trajectory: Annotated[List[Dict[str, Any]], operator.add]
    messages: Annotated[List[str], operator.add]

class ToolCallLog(TypedDict):
    """Log entry for tool calls"""
    timestamp: str
    agent: str
    tool: str
    input: Dict[str, Any]
    output: Any
    success: bool
    error: Optional[str]
