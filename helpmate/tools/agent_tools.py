import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import pandas as pd
from core.rag_system import RAGSystem
from core.config import Config

class AgentTools:
    """Tools available to the multi-agent system"""
    
    def __init__(self, rag_system: RAGSystem):
        self.rag = rag_system
        self.tickets_df = pd.read_csv(Config.TICKETS_FILE)
        
    def similar_ticket_search(self, query: str, category: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
        """
        Search for similar historical tickets using semantic search.
        Returns past tickets that match the query.
        """
        try:
            if category:
                results = self.rag.search_by_category(query, category, top_k)
            else:
                results = self.rag.search(query, top_k)
            
            # Filter for historical tickets
            ticket_results = [r for r in results if r['metadata']['type'] == 'historical_ticket']
            
            return {
                'success': True,
                'results': ticket_results[:top_k],
                'count': len(ticket_results)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def kb_article_search(self, query: str, category: Optional[str] = None, top_k: int = 3) -> Dict[str, Any]:
        """
        Search knowledge base articles for troubleshooting guides and procedures.
        Returns relevant KB articles.
        """
        try:
            if category:
                results = self.rag.search_by_category(query, category, top_k)
            else:
                results = self.rag.search(query, top_k)
            
            # Filter for KB articles
            kb_results = [r for r in results if r['metadata']['type'] == 'kb_article']
            
            return {
                'success': True,
                'results': kb_results[:top_k],
                'count': len(kb_results)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def resolution_note_search(self, query: str, category: Optional[str] = None, top_k: int = 3) -> Dict[str, Any]:
        """
        Search past resolution notes for detailed diagnostic and fix procedures.
        Returns structured resolution notes from similar past tickets.
        """
        try:
            if category:
                results = self.rag.search_by_category(query, category, top_k)
            else:
                results = self.rag.search(query, top_k)
            
            # Filter for resolution notes
            resolution_results = [r for r in results if r['metadata']['type'] == 'resolution_note']
            
            return {
                'success': True,
                'results': resolution_results[:top_k],
                'count': len(resolution_results)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def ticket_lookup(self, ticket_id: str) -> Dict[str, Any]:
        """
        Look up details of a specific ticket by ID.
        Returns full ticket information.
        """
        try:
            ticket = self.tickets_df[self.tickets_df['ticket_id'] == ticket_id]
            
            if ticket.empty:
                return {
                    'success': False,
                    'error': f'Ticket {ticket_id} not found'
                }
            
            return {
                'success': True,
                'ticket': ticket.iloc[0].to_dict()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def user_ticket_history(self, requester_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Retrieve ticket history for a specific user.
        Useful for identifying recurring issues.
        """
        try:
            user_tickets = self.tickets_df[
                self.tickets_df['requester_id'] == requester_id
            ].sort_values('created_at', ascending=False).head(limit)
            
            return {
                'success': True,
                'tickets': user_tickets.to_dict('records'),
                'count': len(user_tickets)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tickets': []
            }
    
    def category_ticket_search(self, category: str, days: int = 7, limit: int = 20) -> Dict[str, Any]:
        """
        Search for recent tickets in a specific category.
        Useful for identifying patterns or outages.
        """
        try:
            category_tickets = self.tickets_df[
                self.tickets_df['category'] == category
            ].sort_values('created_at', ascending=False).head(limit)
            
            return {
                'success': True,
                'tickets': category_tickets.to_dict('records'),
                'count': len(category_tickets),
                'category': category
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tickets': []
            }
    
    def asset_lookup(self, requester_id: str) -> Dict[str, Any]:
        """
        Mock asset/CMDB lookup for user equipment and access.
        In production, this would query asset management system.
        """
        # Mock data for demonstration
        return {
            'success': True,
            'requester_id': requester_id,
            'assets': {
                'laptop': f'LAPTOP-{requester_id[-5:]}',
                'assigned_groups': ['All_Employees', 'VPN_Users'],
                'software_entitlements': ['Office365', 'VPN_Client', 'Teams']
            }
        }
    
    def create_escalation(self, ticket_id: str, reason: str, priority: str) -> Dict[str, Any]:
        """
        Mock escalation creation.
        In production, this would create case in ticketing system.
        """
        case_id = f"CASE-ESC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            'success': True,
            'action': 'escalation_created',
            'case_id': case_id,
            'ticket_id': ticket_id,
            'priority': priority,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
    
    def send_notification(self, recipient: str, subject: str, message: str) -> Dict[str, Any]:
        """
        Mock notification system.
        In production, this would send email/Teams message.
        """
        return {
            'success': True,
            'action': 'notification_sent',
            'recipient': recipient,
            'subject': subject,
            'timestamp': datetime.now().isoformat()
        }
    
    def request_human_approval(self, ticket_id: str, action: str, justification: str) -> Dict[str, Any]:
        """
        Mock human-in-the-loop approval request.
        In production, this would create approval task.
        """
        return {
            'success': True,
            'action': 'approval_requested',
            'ticket_id': ticket_id,
            'approval_action': action,
            'justification': justification,
            'status': 'pending_approval',
            'timestamp': datetime.now().isoformat()
        }
    
    def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock ticket update.
        In production, this would update ticketing system.
        """
        return {
            'success': True,
            'action': 'ticket_updated',
            'ticket_id': ticket_id,
            'updates': updates,
            'timestamp': datetime.now().isoformat()
        }

# Tool descriptions for LLM to understand what each tool does
TOOL_DESCRIPTIONS = {
    'similar_ticket_search': 'Search for similar past tickets using semantic search. Use when you need examples of how similar issues were handled.',
    'kb_article_search': 'Search knowledge base for troubleshooting guides. Use when you need step-by-step procedures or best practices.',
    'resolution_note_search': 'Search detailed resolution notes from past tickets. Use when you need complete diagnostic and resolution workflows.',
    'ticket_lookup': 'Look up specific ticket by ID. Use when you have a ticket reference and need details.',
    'user_ticket_history': 'Get recent ticket history for a user. Use to identify recurring issues or patterns.',
    'category_ticket_search': 'Find recent tickets in a category. Use to detect trends or widespread issues.',
    'asset_lookup': 'Look up user assets and entitlements. Use for access issues or equipment problems.',
    'create_escalation': 'Escalate ticket to higher tier. Use for complex issues or P1 incidents.',
    'send_notification': 'Send notification to stakeholders. Use for updates or escalations.',
    'request_human_approval': 'Request human approval for sensitive actions. Use before autonomous resolution of critical issues.',
    'update_ticket': 'Update ticket fields. Use to record progress or change status.'
}
