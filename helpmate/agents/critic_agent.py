import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, Any
from datetime import datetime
from openai import AzureOpenAI
from agents.state import AgentState
from core.config import Config

class CriticAgent:
    """
    Critic agent that reviews resolution notes for grounding, citation quality,
    and logical consistency. Triggers revisions if claims are ungrounded.
    """
    
    def __init__(self, client: AzureOpenAI):
        self.client = client
        self.name = "Critic"
    
    def review_resolution(self, state: AgentState) -> Dict[str, Any]:
        """Review resolution note for quality and grounding"""
        
        resolution_note = state.get('resolution_note', {})
        references = state.get('references', [])
        retrieved_docs = state.get('retrieved_docs', [])
        ticket = state['ticket']
        revision_count = state.get('revision_count', 0)
        
        # Prepare review context
        review_prompt = f"""You are the Critic Agent. Review the resolution note for quality and grounding.

RESOLUTION NOTE TO REVIEW:
{self._format_resolution(resolution_note)}

AVAILABLE REFERENCES:
{', '.join(references) if references else 'None'}

RETRIEVED DOCUMENTS COUNT: {len(retrieved_docs)}

REVIEW CRITERIA:

1. GROUNDING CHECK:
   - Does every technical claim cite a source (ticket ID or KB article)?
   - Are diagnosis and resolution steps backed by retrieved context?
   - If no context available, does it acknowledge cold retrieval and recommend escalation?

2. CITATION QUALITY:
   - Are citations specific (includes ticket/KB IDs)?
   - Do citations match the available references?
   - Are there unsupported claims or hallucinations?

3. COMPLETENESS:
   - Are all required sections present (summary, diagnosis, resolution, verification, preventive action)?
   - Is the resolution actionable and clear?
   - Are verification steps specific?

4. LOGICAL CONSISTENCY:
   - Does the diagnosis match the ticket symptoms?
   - Do resolution steps follow from the diagnosis?
   - Are there any contradictions?

5. SAFETY:
   - Does it recommend appropriate escalation for P1/complex issues?
   - Are there any unsafe or policy-violating recommendations?

Provide your review in this format:

GROUNDING_SCORE: [PASS / FAIL]
GROUNDING_ISSUES: [List specific claims without citations, or "None" if all grounded]

CITATION_QUALITY: [GOOD / FAIR / POOR]
CITATION_ISSUES: [List problems with citations, or "None"]

COMPLETENESS: [COMPLETE / INCOMPLETE]
MISSING_ELEMENTS: [List missing sections, or "None"]

SAFETY_CHECK: [PASS / FAIL]
SAFETY_CONCERNS: [List concerns, or "None"]

OVERALL_VERDICT: [APPROVED / NEEDS_REVISION / ESCALATE]
REVISION_INSTRUCTIONS: [If needs revision, specific instructions]
REASONING: [Brief explanation of verdict]
"""
        
        response = self.client.chat.completions.create(
            model=Config.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[{"role": "user", "content": review_prompt}],
            temperature=0.0  # Deterministic for consistency
        )
        
        review_text = response.choices[0].message.content
        
        # Parse verdict
        verdict = self._parse_verdict(review_text)
        
        # Log trajectory
        trajectory_entry = {
            'timestamp': datetime.now().isoformat(),
            'agent': self.name,
            'action': 'review_resolution',
            'input': {
                'ticket_id': ticket['ticket_id'],
                'revision_count': revision_count
            },
            'output': {
                'verdict': verdict,
                'review': review_text
            }
        }
        
        # Determine next action
        if verdict == 'APPROVED':
            next_agent = 'COMPLETE'
            approved = True
            message = "Critic: Resolution approved. All claims properly grounded."
        elif verdict == 'NEEDS_REVISION' and revision_count < 2:
            next_agent = 'diagnosis_worker'  # Send back for revision
            approved = False
            message = f"Critic: Revision needed (attempt {revision_count + 1}/2). Found grounding issues."
        elif verdict == 'ESCALATE' or revision_count >= 2:
            next_agent = 'COMPLETE'
            approved = False
            message = "Critic: Issue requires escalation or max revisions reached."
            # Mark for escalation
            state['should_escalate'] = True
            state['escalation_reason'] = "Failed critic review or too complex for autonomous resolution"
        else:
            next_agent = 'COMPLETE'
            approved = False
            message = "Critic: Proceeding with best-effort resolution despite issues."
        
        return {
            'current_agent': self.name,
            'next_agent': next_agent,
            'critic_approved': approved,
            'critic_feedback': review_text,
            'revision_count': revision_count + 1,
            'trajectory': [trajectory_entry],
            'messages': [message],
            'completed_steps': [f'Critic review - {verdict}']
        }
    
    def _format_resolution(self, resolution_note: Dict) -> str:
        """Format resolution note for review"""
        sections = []
        for key, value in resolution_note.items():
            sections.append(f"{key.upper()}: {value}")
        return "\n\n".join(sections)
    
    def _parse_verdict(self, review_text: str) -> str:
        """Parse overall verdict from review"""
        review_lower = review_text.lower()
        
        if 'overall_verdict: approved' in review_lower:
            return 'APPROVED'
        elif 'overall_verdict: needs_revision' in review_lower:
            return 'NEEDS_REVISION'
        elif 'overall_verdict: escalate' in review_lower:
            return 'ESCALATE'
        elif 'grounding_score: fail' in review_lower:
            return 'NEEDS_REVISION'
        elif 'safety_check: fail' in review_lower:
            return 'ESCALATE'
        else:
            # Default to approved if uncertain
            return 'APPROVED'
