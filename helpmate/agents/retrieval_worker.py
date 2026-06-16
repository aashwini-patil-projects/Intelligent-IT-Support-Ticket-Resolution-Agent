import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, Any, List
from datetime import datetime
from openai import AzureOpenAI
from agents.state import AgentState
from tools.agent_tools import AgentTools
from core.config import Config

class RetrievalWorkerAgent:
    """
    Retrieval worker that executes semantic searches, handles failed retrievals,
    and adapts search strategies dynamically.
    """
    
    def __init__(self, client: AzureOpenAI, tools: AgentTools):
        self.client = client
        self.tools = tools
        self.name = "RetrievalWorker"
    
    def execute_retrieval(self, state: AgentState) -> Dict[str, Any]:
        """Execute retrieval with adaptive strategy"""
        
        ticket = state['ticket']
        plan = state.get('plan', [])
        retrieval_attempts = state.get('retrieval_attempts', 0)
        
        # Determine what to retrieve based on plan and previous attempts
        retrieval_strategy = self._determine_strategy(ticket, plan, retrieval_attempts)
        
        prompt = f"""You are the Retrieval Worker Agent. Your job is to find relevant information.

TICKET:
- Subject: {ticket['subject']}
- Description: {ticket['description']}
- Category: {ticket['category']}
- Priority: {ticket['priority']}

RETRIEVAL ATTEMPT: {retrieval_attempts + 1}
STRATEGY: {retrieval_strategy}

Previous queries: {state.get('retrieval_queries', [])}
Previous results count: {len(state.get('retrieved_docs', []))}

Based on the ticket, formulate 2-3 search queries for:
1. Similar past tickets
2. KB articles
3. Detailed resolution notes (if needed)

If this is a retry (attempt > 1), make queries BROADER and use different keywords.

Provide queries in this format:
QUERY_1: <search query for similar tickets>
QUERY_2: <search query for KB articles>
QUERY_3: <optional - resolution notes query>

REASONING: <Why these queries will find relevant information>
"""
        
        response = self.client.chat.completions.create(
            model=Config.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        queries_text = response.choices[0].message.content
        queries = self._parse_queries(queries_text)
        
        # Execute searches
        all_results = []
        trajectory_entries = []
        
        for query_info in queries:
            query = query_info['query']
            query_type = query_info['type']
            
            # Execute appropriate tool
            if query_type == 'similar_tickets':
                result = self.tools.similar_ticket_search(query, category=ticket.get('category'), top_k=5)
            elif query_type == 'kb_articles':
                result = self.tools.kb_article_search(query, category=ticket.get('category'), top_k=3)
            elif query_type == 'resolution_notes':
                result = self.tools.resolution_note_search(query, category=ticket.get('category'), top_k=3)
            else:
                continue
            
            # Log tool call
            trajectory_entries.append({
                'timestamp': datetime.now().isoformat(),
                'agent': self.name,
                'action': f'tool_call_{query_type}',
                'tool': query_type,
                'input': {'query': query, 'category': ticket.get('category')},
                'output': {'count': result.get('count', 0), 'success': result['success']}
            })
            
            if result['success'] and result.get('results'):
                all_results.extend(result['results'])
        
        # Check if retrieval was successful
        retrieval_quality = self._assess_retrieval_quality(all_results, ticket)
        
        # Decide next action
        if retrieval_quality == 'GOOD':
            next_agent = 'diagnosis_worker'
            message = f"Retrieved {len(all_results)} relevant documents. Proceeding to diagnosis."
        elif retrieval_quality == 'POOR' and retrieval_attempts < 2:
            next_agent = 'retrieval_worker'  # Retry with different strategy
            message = f"Retrieved {len(all_results)} documents but quality is low. Will retry with broader queries."
        else:
            next_agent = 'diagnosis_worker'  # Proceed anyway, let diagnosis handle low context
            message = f"Retrieved {len(all_results)} documents (cold retrieval scenario). Proceeding with available context."
        
        return {
            'current_agent': self.name,
            'next_agent': next_agent,
            'retrieved_docs': all_results,
            'retrieval_queries': [q['query'] for q in queries],
            'retrieval_attempts': retrieval_attempts + 1,
            'trajectory': trajectory_entries,
            'messages': [f"RetrievalWorker: {message}"],
            'completed_steps': [f'Retrieval attempt {retrieval_attempts + 1} - {len(all_results)} documents found']
        }
    
    def _determine_strategy(self, ticket: Dict, plan: List, attempts: int) -> str:
        """Determine retrieval strategy based on context"""
        if attempts == 0:
            return "Initial retrieval - focused on category and keywords"
        elif attempts == 1:
            return "Retry - broader queries with alternative keywords"
        else:
            return "Final attempt - very broad queries across all categories"
    
    def _parse_queries(self, queries_text: str) -> List[Dict[str, str]]:
        """Parse queries from LLM response"""
        queries = []
        
        for line in queries_text.split('\n'):
            line = line.strip()
            if line.startswith('QUERY_1:'):
                queries.append({
                    'query': line.replace('QUERY_1:', '').strip(),
                    'type': 'similar_tickets'
                })
            elif line.startswith('QUERY_2:'):
                queries.append({
                    'query': line.replace('QUERY_2:', '').strip(),
                    'type': 'kb_articles'
                })
            elif line.startswith('QUERY_3:'):
                queries.append({
                    'query': line.replace('QUERY_3:', '').strip(),
                    'type': 'resolution_notes'
                })
        
        return queries
    
    def _assess_retrieval_quality(self, results: List[Dict], ticket: Dict) -> str:
        """Assess if retrieval found relevant information"""
        if not results:
            return 'EMPTY'
        
        # Check if any results are from same category
        same_category = sum(1 for r in results if r['metadata'].get('category') == ticket.get('category'))
        
        # Check relevance by distance (lower is better)
        avg_distance = sum(r['distance'] for r in results) / len(results) if results else float('inf')
        
        if same_category >= 2 and avg_distance < 1.0:
            return 'GOOD'
        elif same_category >= 1 or len(results) >= 3:
            return 'FAIR'
        else:
            return 'POOR'
