import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from openai import AzureOpenAI

from agents.state import AgentState
from agents.coordinator_agent import CoordinatorAgent
from agents.retrieval_worker import RetrievalWorkerAgent
from agents.diagnosis_worker import DiagnosisWorkerAgent
from agents.critic_agent import CriticAgent
from tools.agent_tools import AgentTools
from core.rag_system import RAGSystem
from core.config import Config

class HelpMateAgent:
    """
    Main multi-agent system using LangGraph for orchestration.
    Implements coordinator-worker-critic pattern with dynamic routing.
    """
    
    def __init__(self):
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=Config.AZURE_OPENAI_API_KEY,
            api_version=Config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT
        )
        
        # Initialize RAG system
        self.rag = RAGSystem()
        try:
            self.rag.load_index()
        except:
            print("FAISS index not found. Please run rag_system.py first to build the index.")
            raise
        
        # Initialize tools
        self.tools = AgentTools(self.rag)
        
        # Initialize agents
        self.coordinator = CoordinatorAgent(self.client)
        self.retrieval_worker = RetrievalWorkerAgent(self.client, self.tools)
        self.diagnosis_worker = DiagnosisWorkerAgent(self.client)
        self.critic = CriticAgent(self.client)
        
        # Build graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("coordinator", self._coordinator_node)
        workflow.add_node("retrieval_worker", self._retrieval_node)
        workflow.add_node("diagnosis_worker", self._diagnosis_node)
        workflow.add_node("critic_agent", self._critic_node)
        workflow.add_node("escalation_handler", self._escalation_node)
        
        # Set entry point
        workflow.set_entry_point("coordinator")
        
        # Add conditional routing from coordinator
        workflow.add_conditional_edges(
            "coordinator",
            self._route_from_coordinator,
            {
                "retrieval_worker": "retrieval_worker",
                "escalation_handler": "escalation_handler",
                "END": END
            }
        )
        
        # Retrieval worker can loop back to itself or proceed to diagnosis
        workflow.add_conditional_edges(
            "retrieval_worker",
            self._route_from_retrieval,
            {
                "retrieval_worker": "retrieval_worker",
                "diagnosis_worker": "diagnosis_worker"
            }
        )
        
        # Diagnosis always goes to critic
        workflow.add_edge("diagnosis_worker", "critic_agent")
        
        # Critic can send back to diagnosis or complete
        workflow.add_conditional_edges(
            "critic_agent",
            self._route_from_critic,
            {
                "diagnosis_worker": "diagnosis_worker",
                "END": END
            }
        )
        
        # Escalation ends workflow
        workflow.add_edge("escalation_handler", END)
        
        return workflow.compile()
    
    def _coordinator_node(self, state: AgentState) -> Dict[str, Any]:
        """Coordinator agent node"""
        return self.coordinator.analyze_and_plan(state)
    
    def _retrieval_node(self, state: AgentState) -> Dict[str, Any]:
        """Retrieval worker agent node"""
        return self.retrieval_worker.execute_retrieval(state)
    
    def _diagnosis_node(self, state: AgentState) -> Dict[str, Any]:
        """Diagnosis worker agent node"""
        return self.diagnosis_worker.generate_resolution(state)
    
    def _critic_node(self, state: AgentState) -> Dict[str, Any]:
        """Critic agent node"""
        return self.critic.review_resolution(state)
    
    def _escalation_node(self, state: AgentState) -> Dict[str, Any]:
        """Handle escalation"""
        ticket = state['ticket']
        reason = state.get('escalation_reason', 'P1 incident or complex issue')
        
        # Create escalation
        escalation = self.tools.create_escalation(
            ticket['ticket_id'],
            reason,
            ticket['priority']
        )
        
        # Notify stakeholders for P1
        if ticket['priority'] == 'P1':
            self.tools.send_notification(
                recipient='on-call-engineer@company.com',
                subject=f"P1 Incident: {ticket['subject']}",
                message=f"Ticket {ticket['ticket_id']} escalated for immediate attention."
            )
        
        return {
            'current_agent': 'EscalationHandler',
            'next_agent': 'END',
            'should_escalate': True,
            'escalation_reason': reason,
            'resolution_note': {
                'summary': f"Ticket escalated: {ticket['subject']}",
                'escalation_details': escalation,
                'reason': reason
            },
            'trajectory': [{
                'timestamp': datetime.now().isoformat(),
                'agent': 'EscalationHandler',
                'action': 'escalate',
                'output': escalation
            }],
            'messages': [f"EscalationHandler: Ticket escalated. Case ID: {escalation.get('case_id')}"]
        }
    
    def _route_from_coordinator(self, state: AgentState) -> Literal["retrieval_worker", "escalation_handler", "END"]:
        """Route from coordinator based on analysis"""
        next_agent = state.get('next_agent', 'retrieval_worker')
        
        if next_agent == 'escalation_handler':
            return "escalation_handler"
        elif next_agent == 'COMPLETE':
            return "END"
        else:
            return "retrieval_worker"
    
    def _route_from_retrieval(self, state: AgentState) -> Literal["retrieval_worker", "diagnosis_worker"]:
        """Route from retrieval worker"""
        next_agent = state.get('next_agent', 'diagnosis_worker')
        
        if next_agent == 'retrieval_worker':
            return "retrieval_worker"
        else:
            return "diagnosis_worker"
    
    def _route_from_critic(self, state: AgentState) -> Literal["diagnosis_worker", "END"]:
        """Route from critic"""
        next_agent = state.get('next_agent', 'END')
        
        if next_agent == 'diagnosis_worker':
            return "diagnosis_worker"
        else:
            return "END"
    
    def process_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Process a ticket through the agent system"""
        
        # Initialize state
        initial_state = {
            'ticket': ticket,
            'retrieved_docs': [],
            'retrieval_queries': [],
            'retrieval_attempts': 0,
            'diagnosis': None,
            'root_cause': None,
            'similar_tickets': [],
            'resolution_steps': None,
            'verification_steps': None,
            'preventive_actions': None,
            'references': [],
            'current_agent': 'coordinator',
            'next_agent': None,
            'plan': [],
            'completed_steps': [],
            'should_escalate': False,
            'escalation_reason': None,
            'requires_hitl': False,
            'critic_feedback': None,
            'critic_approved': False,
            'revision_count': 0,
            'resolution_note': None,
            'trajectory': [],
            'messages': []
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state

from datetime import datetime

if __name__ == "__main__":
    # Test the agent system
    Config.validate()
    
    agent = HelpMateAgent()
    
    # Test ticket
    test_ticket = {
        'ticket_id': 'TCK-00050',
        'priority': 'P3',
        'category': 'VPN',
        'subject': 'VPN disconnecting frequently',
        'description': 'My VPN connection drops every 10 minutes. Have to reconnect constantly. Started yesterday.',
        'department': 'Sales',
        'affected_system': 'VPN'
    }
    
    print("Processing test ticket...")
    result = agent.process_ticket(test_ticket)
    
    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)
    print(f"\nFinal Agent: {result['current_agent']}")
    print(f"Critic Approved: {result['critic_approved']}")
    print(f"Should Escalate: {result['should_escalate']}")
    print(f"\nCompleted Steps: {len(result['completed_steps'])}")
    for step in result['completed_steps']:
        print(f"  - {step}")
    
    if result['resolution_note']:
        print("\n" + "="*60)
        print("RESOLUTION NOTE")
        print("="*60)
        for key, value in result['resolution_note'].items():
            print(f"\n{key.upper()}:")
            print(value)
