from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import pandas as pd

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.helpmate_agent import HelpMateAgent
from core.config import Config

# Initialize FastAPI app
app = FastAPI(
    title="HelpMate API",
    description="Intelligent IT Support Ticket Resolution Agent",
    version="1.0.0"
)

# Initialize agent system
try:
    Config.validate()
    agent_system = HelpMateAgent()
except Exception as e:
    print(f"Error initializing agent system: {e}")
    agent_system = None

# Request/Response models
class TicketInput(BaseModel):
    ticket_id: Optional[str] = None
    priority: str
    category: str
    subject: str
    description: str
    department: Optional[str] = None
    affected_system: Optional[str] = None
    requester_id: Optional[str] = None
    channel: Optional[str] = "API"

class ResolutionResponse(BaseModel):
    ticket_id: str
    status: str
    resolution_note: Optional[Dict[str, Any]]
    should_escalate: bool
    escalation_reason: Optional[str]
    critic_approved: bool
    processing_time_seconds: float
    trajectory_summary: List[str]
    references: List[str]

class SystemHealth(BaseModel):
    status: str
    agent_system: str
    rag_index_loaded: bool
    total_documents: int

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "HelpMate",
        "description": "Intelligent IT Support Ticket Resolution Agent",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "process_ticket": "/api/v1/process_ticket",
            "test_scenarios": "/api/v1/test_scenarios",
            "evaluate_scenario": "/api/v1/evaluate_scenario/{scenario_id}"
        }
    }

@app.get("/health", response_model=SystemHealth)
def health_check():
    """System health check"""
    if agent_system is None:
        return SystemHealth(
            status="unhealthy",
            agent_system="not_initialized",
            rag_index_loaded=False,
            total_documents=0
        )
    
    return SystemHealth(
        status="healthy",
        agent_system="initialized",
        rag_index_loaded=agent_system.rag.index is not None,
        total_documents=len(agent_system.rag.documents)
    )

@app.post("/api/v1/process_ticket", response_model=ResolutionResponse)
def process_ticket(ticket_input: TicketInput):
    """
    Process an IT support ticket through the multi-agent system.
    Returns a resolution note with diagnosis and fix steps.
    """
    if agent_system is None:
        raise HTTPException(status_code=503, detail="Agent system not initialized")
    
    start_time = datetime.now()
    
    # Auto-generate ticket ID if not provided
    if not ticket_input.ticket_id:
        ticket_input.ticket_id = f"TCK-API-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Convert to dict for processing
    ticket_dict = ticket_input.model_dump()
    
    try:
        # Process through agent system
        result = agent_system.process_ticket(ticket_dict)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Extract trajectory summary
        trajectory_summary = [
            f"{entry.get('agent', 'Unknown')}: {entry.get('action', 'Unknown')}"
            for entry in result.get('trajectory', [])
        ]
        
        return ResolutionResponse(
            ticket_id=ticket_input.ticket_id,
            status="completed",
            resolution_note=result.get('resolution_note'),
            should_escalate=result.get('should_escalate', False),
            escalation_reason=result.get('escalation_reason'),
            critic_approved=result.get('critic_approved', False),
            processing_time_seconds=processing_time,
            trajectory_summary=trajectory_summary,
            references=result.get('references', [])
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing ticket: {str(e)}")

@app.get("/api/v1/test_scenarios")
def get_test_scenarios():
    """
    Get list of adaptive test scenarios for evaluation.
    """
    try:
        with open(Config.TEST_SCENARIOS_FILE, 'r') as f:
            test_data = json.load(f)
        
        scenarios = test_data.get('adaptive_scenarios', [])
        
        return {
            "total_scenarios": len(scenarios),
            "scenarios": [
                {
                    "scenario_name": s['scenario_name'],
                    "ticket_id": s['ticket_id'],
                    "category": s['category'],
                    "priority": s['priority'],
                    "subject": s['subject']
                }
                for s in scenarios
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading test scenarios: {str(e)}")

@app.post("/api/v1/evaluate_scenario/{scenario_name}")
def evaluate_scenario(scenario_name: str):
    """
    Evaluate agent on a specific adaptive test scenario.
    Returns detailed behavior analysis.
    """
    if agent_system is None:
        raise HTTPException(status_code=503, detail="Agent system not initialized")
    
    try:
        # Load test scenarios
        with open(Config.TEST_SCENARIOS_FILE, 'r') as f:
            test_data = json.load(f)
        
        scenarios = test_data.get('adaptive_scenarios', [])
        
        # Find matching scenario
        scenario = next((s for s in scenarios if s['scenario_name'] == scenario_name), None)
        
        if not scenario:
            raise HTTPException(status_code=404, detail=f"Scenario '{scenario_name}' not found")
        
        start_time = datetime.now()
        
        # Process scenario
        result = agent_system.process_ticket(scenario)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Analyze agent behavior
        behavior_analysis = analyze_agent_behavior(scenario, result)
        
        return {
            "scenario_name": scenario_name,
            "ticket_id": scenario['ticket_id'],
            "processing_time_seconds": processing_time,
            "expected_behavior": scenario.get('expected_behavior', []),
            "actual_behavior": behavior_analysis,
            "resolution_note": result.get('resolution_note'),
            "trajectory": result.get('trajectory', []),
            "should_escalate": result.get('should_escalate', False),
            "critic_approved": result.get('critic_approved', False)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating scenario: {str(e)}")

def analyze_agent_behavior(scenario: Dict, result: Dict) -> Dict[str, Any]:
    """Analyze agent behavior against expected criteria"""
    
    trajectory = result.get('trajectory', [])
    completed_steps = result.get('completed_steps', [])
    
    # Tool selection correctness
    tools_used = [
        entry.get('tool', entry.get('action'))
        for entry in trajectory
        if 'tool' in entry or 'action' in entry
    ]
    
    # Trajectory efficiency
    total_steps = len(trajectory)
    retrieval_attempts = result.get('retrieval_attempts', 0)
    revision_count = result.get('revision_count', 0)
    
    # Failure recovery
    cold_retrieval_detected = len(result.get('retrieved_docs', [])) == 0
    recovery_attempted = retrieval_attempts > 1
    
    # Escalation correctness
    priority = scenario.get('priority')
    should_have_escalated = priority == 'P1'
    actually_escalated = result.get('should_escalate', False)
    escalation_correct = should_have_escalated == actually_escalated
    
    # Grounding check
    references = result.get('references', [])
    resolution_note = result.get('resolution_note', {})
    has_references = len(references) > 0
    
    return {
        "tool_selection": {
            "tools_used": tools_used,
            "tool_count": len(tools_used),
            "unique_tools": len(set(tools_used))
        },
        "trajectory_efficiency": {
            "total_steps": total_steps,
            "retrieval_attempts": retrieval_attempts,
            "revision_count": revision_count,
            "efficiency_score": "efficient" if total_steps < 15 else "inefficient"
        },
        "failure_recovery": {
            "cold_retrieval_detected": cold_retrieval_detected,
            "recovery_attempted": recovery_attempted,
            "recovery_successful": recovery_attempted and len(result.get('retrieved_docs', [])) > 0
        },
        "escalation_correctness": {
            "should_escalate": should_have_escalated,
            "actually_escalated": actually_escalated,
            "correct": escalation_correct
        },
        "grounding_faithfulness": {
            "has_references": has_references,
            "reference_count": len(references),
            "critic_approved": result.get('critic_approved', False)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
