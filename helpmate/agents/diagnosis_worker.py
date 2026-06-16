import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, Any
from datetime import datetime
from openai import AzureOpenAI
from agents.state import AgentState
from core.config import Config
import json

class DiagnosisWorkerAgent:
    """
    Diagnosis worker that analyzes retrieved context and drafts resolution notes.
    Ensures all claims are grounded in retrieved sources.
    """
    
    def __init__(self, client: AzureOpenAI):
        self.client = client
        self.name = "DiagnosisWorker"
    
    def generate_resolution(self, state: AgentState) -> Dict[str, Any]:
        """Generate resolution note from retrieved context"""
        
        ticket = state['ticket']
        retrieved_docs = state.get('retrieved_docs', [])
        
        # Prepare context from retrieved documents
        context = self._prepare_context(retrieved_docs)
        
        prompt = f"""You are the Diagnosis Worker Agent. Generate a structured resolution note.

TICKET:
- ID: {ticket['ticket_id']}
- Subject: {ticket['subject']}
- Description: {ticket['description']}
- Category: {ticket['category']}
- Priority: {ticket['priority']}
- System: {ticket.get('affected_system', 'N/A')}
- Department: {ticket.get('department', 'N/A')}

RETRIEVED CONTEXT:
{context}

CRITICAL GROUNDING RULES:
1. EVERY claim about diagnosis, resolution, or procedures MUST cite a source
2. Use format: "According to [Ticket TCK-XXXXX]..." or "As documented in [KB-XXXX]..."
3. If no relevant context exists, explicitly state "No similar cases found" and recommend escalation
4. DO NOT invent solutions - only use information from retrieved context
5. If context contradicts itself, acknowledge and note which sources disagree

Generate a resolution note with these sections:

**SUMMARY**: One paragraph overview of incident (what, who, when)

**AFFECTED_SCOPE**: Details about impacted users, systems, departments. Include any similar/duplicate tickets if found.

**DIAGNOSIS**: Most probable root cause. MUST cite retrieved sources. If unsure, state assumptions clearly.

**RESOLUTION**: Step-by-step fix. MUST be based on retrieved KB articles or past resolutions. Cite sources.

**VERIFICATION**: How to confirm the fix worked. Based on retrieved verification procedures.

**PREVENTIVE_ACTION**: Recommendations to prevent recurrence. Based on retrieved preventive measures.

**REFERENCES**: List ALL ticket IDs and KB article IDs used. Format as:
- Ticket: TCK-XXXXX
- KB Article: KB-XXXX
- Resolution Note: TCK-XXXXX

Output as JSON with these keys: summary, affected_scope, diagnosis, resolution, verification, preventive_action, references

REMEMBER: Every technical claim needs a citation. If no context available, say so explicitly.
"""
        
        response = self.client.chat.completions.create(
            model=Config.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=Config.TEMPERATURE,
            response_format={"type": "json_object"}
        )
        
        resolution_text = response.choices[0].message.content
        
        try:
            resolution_note = json.loads(resolution_text)
        except json.JSONDecodeError:
            resolution_note = {
                'summary': 'Failed to parse resolution',
                'error': 'JSON parsing failed',
                'raw': resolution_text
            }
        
        # Extract references for tracking
        references = self._extract_references(retrieved_docs, resolution_note)
        
        # Log trajectory
        trajectory_entry = {
            'timestamp': datetime.now().isoformat(),
            'agent': self.name,
            'action': 'generate_resolution',
            'input': {
                'ticket_id': ticket['ticket_id'],
                'context_docs': len(retrieved_docs)
            },
            'output': {
                'resolution_generated': True,
                'sections_complete': len(resolution_note.keys()),
                'references_count': len(references)
            }
        }
        
        # Determine next agent
        next_agent = 'critic_agent'
        
        return {
            'current_agent': self.name,
            'next_agent': next_agent,
            'resolution_note': resolution_note,
            'references': references,
            'diagnosis': resolution_note.get('diagnosis', ''),
            'resolution_steps': resolution_note.get('resolution', ''),
            'verification_steps': resolution_note.get('verification', ''),
            'preventive_actions': resolution_note.get('preventive_action', ''),
            'trajectory': [trajectory_entry],
            'messages': [f"DiagnosisWorker: Generated resolution note with {len(references)} references."],
            'completed_steps': ['Resolution note drafted']
        }
    
    def _prepare_context(self, retrieved_docs: list) -> str:
        """Prepare context string from retrieved documents"""
        if not retrieved_docs:
            return "NO RETRIEVED CONTEXT AVAILABLE - This is a cold retrieval scenario."
        
        context_parts = []
        
        for i, doc in enumerate(retrieved_docs[:10], 1):  # Limit to top 10
            metadata = doc['metadata']
            doc_type = metadata['type']
            
            context_parts.append(f"\n--- Document {i} ({doc_type}) ---")
            
            if doc_type == 'resolution_note':
                context_parts.append(f"Ticket ID: {metadata['ticket_id']}")
            elif doc_type == 'kb_article':
                context_parts.append(f"KB Article: {metadata['kb_id']} - {metadata['title']}")
            elif doc_type == 'historical_ticket':
                context_parts.append(f"Ticket ID: {metadata['ticket_id']}")
            
            context_parts.append(f"Relevance Score: {doc['distance']:.3f}")
            context_parts.append(doc['document'][:800])  # Truncate long docs
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _extract_references(self, retrieved_docs: list, resolution_note: dict) -> list:
        """Extract all referenced tickets and KB articles"""
        references = []
        
        # Get explicit references from resolution note
        ref_text = resolution_note.get('references', '')
        
        # Also include all retrieved documents as potential references
        for doc in retrieved_docs:
            metadata = doc['metadata']
            if metadata['type'] == 'resolution_note':
                ref_id = f"Ticket {metadata['ticket_id']}"
            elif metadata['type'] == 'kb_article':
                ref_id = f"KB {metadata['kb_id']}"
            elif metadata['type'] == 'historical_ticket':
                ref_id = f"Ticket {metadata['ticket_id']}"
            else:
                continue
            
            if ref_id not in references:
                references.append(ref_id)
        
        return references
