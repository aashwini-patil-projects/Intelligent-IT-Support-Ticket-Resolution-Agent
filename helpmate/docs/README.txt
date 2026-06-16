# HelpMate - Intelligent IT Support Ticket Resolution Agent

An agentic AI system that autonomously diagnoses and resolves IT support tickets using multi-agent orchestration, RAG (Retrieval-Augmented Generation), and adaptive reasoning.

## Overview

HelpMate is a multi-agent system designed to assist IT service desks by:
- **Drafting resolution notes** with root cause analysis and fix procedures
- **Retrieving relevant context** from past tickets and knowledge base articles
- **Orchestrating workflows** through intelligent agent coordination
- **Ensuring grounding** via critic agent verification of all claims

## Architecture

### Multi-Agent Design (Coordinator-Worker-Critic Pattern)

```
┌─────────────────┐
│   Coordinator   │  - Analyzes tickets, creates execution plans
│     Agent       │  - Routes to appropriate workers
└────────┬────────┘  - Handles priority-based branching
         │
    ┌────┴────┐
    ▼         ▼
┌──────────┐ ┌──────────────┐
│Retrieval │ │  Diagnosis   │
│  Worker  │ │   Worker     │
└────┬─────┘ └──────┬───────┘
     │              │
     │ ◄────────────┘
     ▼
┌──────────────┐
│    Critic    │  - Validates grounding & citations
│    Agent     │  - Triggers revisions if needed
└──────────────┘
```

### Key Components

1. **Coordinator Agent** (`coordinator_agent.py`)
   - Initial ticket analysis and validation
   - Execution plan creation
   - Priority-based routing (P1 → escalate, P3/P4 → autonomous)
   - Security checks for prompt injection

2. **Retrieval Worker Agent** (`retrieval_worker.py`)
   - Semantic search across tickets and KB articles
   - Adaptive retry strategies for cold retrieval
   - Multiple tool selection (similar tickets, KB articles, resolution notes)

3. **Diagnosis Worker Agent** (`diagnosis_worker.py`)
   - Generates structured resolution notes
   - Ensures all claims cite retrieved sources
   - Handles missing context gracefully

4. **Critic Agent** (`critic_agent.py`)
   - Validates grounding of all technical claims
   - Checks citation quality and completeness
   - Triggers revision loop if needed (max 2 revisions)

### RAG System (`rag_system.py`)

- **Embedding Model**: Azure OpenAI text-embedding-3-large
- **Vector Store**: FAISS (Facebook AI Similarity Search)
- **Document Types**: 
  - Resolution notes (25 detailed past resolutions)
  - KB articles (7 comprehensive troubleshooting guides)
  - Historical tickets (150 past tickets)

### Tools Available to Agents (`agent_tools.py`)

- `similar_ticket_search`: Find past tickets with similar issues
- `kb_article_search`: Search knowledge base for procedures
- `resolution_note_search`: Find detailed resolution workflows
- `ticket_lookup`: Get specific ticket details
- `user_ticket_history`: Identify recurring issues
- `category_ticket_search`: Detect trends/patterns
- `asset_lookup`: User equipment and access info (mocked)
- `create_escalation`: Escalate complex issues (mocked)
- `send_notification`: Stakeholder alerts (mocked)
- `request_human_approval`: HITL for sensitive actions (mocked)

## Setup Instructions

### Prerequisites

- Python 3.10+
- Azure OpenAI API access with:
  - GPT-4 deployment (or GPT-3.5)
  - text-embedding-3-large deployment

### Installation

1. **Clone and navigate to project**
```bash
cd d:\AI\AEI\helpmate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Azure OpenAI credentials**

Create `.env` file from template:
```bash
copy .env.template .env
```

Edit `.env` with your Azure OpenAI credentials:
```
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-gpt4-deployment-name
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=your-embedding-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

4. **Generate synthetic data**
```bash
python generate_tickets.py
python generate_knowledge_corpus.py
python generate_test_scenarios.py
```

5. **Build FAISS index**
```bash
python rag_system.py
```

This will:
- Embed all documents (resolution notes, KB articles, tickets)
- Build FAISS index
- Save to `data/faiss_index.index` and `data/faiss_index.pkl`

## Usage

### Option 1: Run Live Demo (Recommended for Interview)

```bash
python demo.py
```

Demonstrates 5 key scenarios:
1. Happy path - Email stuck in outbox
2. Cold retrieval - Rare custom software issue
3. P1 escalation - Company-wide outage
4. Adversarial input - Prompt injection attempt
5. Out-of-scope - HR issue misrouted

### Option 2: Run FastAPI Server

```bash
python app.py
```

Then access:
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Process ticket: POST http://localhost:8000/api/v1/process_ticket

Example API request:
```bash
curl -X POST "http://localhost:8000/api/v1/process_ticket" \
  -H "Content-Type: application/json" \
  -d '{
    "priority": "P3",
    "category": "VPN",
    "subject": "VPN keeps disconnecting",
    "description": "VPN connection drops every 10 minutes",
    "department": "Sales",
    "affected_system": "VPN"
  }'
```

### Option 3: Run Full Evaluation

```bash
python evaluate_agent.py
```

Evaluates all 10 adaptive test scenarios and generates report with:
- Tool selection correctness
- Trajectory efficiency
- Failure recovery
- Escalation correctness
- Grounding faithfulness
- Guardrail effectiveness

## Adaptive Scenario Battery

The system is tested against 10 challenging scenarios:

| Scenario | Tests |
|----------|-------|
| Cold Retrieval | Handles no similar past cases, retries with broader queries |
| Missing/Contradictory Data | Detects inconsistencies, asks for clarification |
| Out-of-Scope Input | Routes non-IT issues correctly |
| Priority Branching (P1) | Escalates critical incidents immediately |
| Priority Branching (P4) | Handles low-priority autonomously |
| Adversarial Input (2 scenarios) | Resists prompt injection, ignores malicious commands |
| Complex Multi-Issue | Intelligently sequences multiple tool calls |
| Recurring Issue | Detects patterns, recommends root cause fix |
| Happy Path | Successful autonomous resolution with citations |

## Resolution Note Structure

Each resolution note contains:

```json
{
  "summary": "One-paragraph incident overview",
  "affected_scope": "Impacted users, systems, departments",
  "diagnosis": "Root cause with CITED sources",
  "resolution": "Step-by-step fix from KB/past tickets",
  "verification": "Steps to confirm resolution",
  "preventive_action": "Recommendations to prevent recurrence",
  "references": ["Ticket TCK-00042", "KB KB-0001"]
}
```

**Critical**: Every technical claim MUST cite a source (ticket ID or KB article ID).

## Grounding & Citation System

The **Critic Agent** ensures:
- All diagnosis claims reference retrieved tickets/KB articles
- Resolution steps are based on documented procedures
- No hallucinated solutions from empty context
- If no relevant context found, explicitly acknowledges and recommends escalation

Example citation format:
```
"According to Ticket TCK-00042, VPN timeout issues were resolved by updating 
the client to version 5.2.1..."
```

## Guardrails & Security

### Prompt Injection Protection
- All ticket descriptions treated as user input, not system commands
- Malicious instructions (IGNORE, OVERRIDE, etc.) are ignored
- Agent follows standard workflows regardless of embedded commands

### Safety Checks
- P1 incidents require HITL approval
- Admin privilege requests follow approval workflow
- Sensitive operations flagged for human review
- Suspicious content logged for security team

## Evaluation Metrics

| Metric | Description | Scoring |
|--------|-------------|---------|
| Tool Selection Correctness | Chose appropriate tools for each ticket | 0-1.0 |
| Trajectory Efficiency | Reached outcome without redundant loops | 0-1.0 |
| Failure Recovery | Handled cold retrieval and missing data | 0-1.0 |
| Escalation Correctness | Escalated P1, autonomous for P4 | 0-1.0 |
| Grounding Faithfulness | All claims cited with sources | 0-1.0 |
| Guardrail Effectiveness | Resisted prompt injection | 0-1.0 |

## Project Structure

```
helpmate/
├── data/                       # Generated data and indices
│   ├── tickets.csv            # 150 synthetic IT tickets
│   ├── knowledge_corpus.json  # Resolution notes + KB articles
│   ├── test_scenarios.json    # 10 adaptive test scenarios
│   └── faiss_index.*          # Vector index
├── agents/                    # Agent implementations
│   ├── state.py              # Shared state definition
│   ├── coordinator_agent.py  # Planning and routing
│   ├── retrieval_worker.py   # Semantic search
│   ├── diagnosis_worker.py   # Resolution generation
│   └── critic_agent.py       # Grounding validation
├── tools/                     # Agent tools
│   └── agent_tools.py        # All available tools
├── config.py                  # Configuration
├── rag_system.py             # RAG with FAISS
├── helpmate_agent.py         # Main LangGraph orchestration
├── app.py                    # FastAPI server
├── demo.py                   # Interactive demo
├── evaluate_agent.py         # Comprehensive evaluation
├── generate_tickets.py       # Data generation
├── generate_knowledge_corpus.py
├── generate_test_scenarios.py
└── requirements.txt
```

## Key Design Decisions

### Why Multi-Agent?
- **Separation of concerns**: Each agent has focused responsibility
- **Adaptive behavior**: Coordinator can dynamically route based on ticket
- **Quality control**: Critic validates before output, preventing hallucination
- **Scalability**: Easy to add specialized workers (e.g., network specialist)

### Why NOT Hard-Coded Pipeline?
- Pipeline would always: retrieve → diagnose → output
- Agents dynamically decide: P1 → escalate immediately (skip retrieval), cold retrieval → retry with different strategy, low quality → revision loop
- Tool selection based on ticket analysis, not fixed sequence

### Reasoning Approach
- **ReAct-inspired**: Coordinator reasons about plan, workers act with tools, critic reflects on output
- **Plan-and-execute**: Coordinator creates plan, but adapts based on execution results
- **Stopping conditions**: Critic approval, max iterations (10), escalation decision

## Trade-offs & Future Enhancements

### Current Limitations
- Mock external actions (notifications, ticket updates)
- Small corpus (25 resolutions, 7 KB articles)
- Azure OpenAI dependency (could add fallback to local models)

### With More Time
- **Expanded corpus**: 500+ resolutions, 50+ KB articles
- **Real integrations**: ServiceNow API, Teams notifications, CMDB queries
- **Advanced RAG**: Reranking, query rewriting, multi-hop reasoning
- **Learning loop**: Feedback from technicians improves future resolutions
- **Specialized workers**: Network agent, security agent, access management agent
- **Production hardening**: Rate limiting, caching, monitoring, audit logs

## Interview Talking Points

### Why This Architecture?
"I chose a coordinator-worker-critic pattern because IT support requires dynamic decision-making. A P1 outage needs immediate escalation without retrieval overhead, while a P4 mouse issue can be handled fully autonomously. Hard-coded pipelines can't adapt to these different workflows."

### How Does Grounding Work?
"The Diagnosis Worker is prompted to cite sources for every claim. The Critic Agent then validates that citations exist and match retrieved documents. If grounding fails, it triggers a revision loop (max 2 attempts). This prevents hallucination especially in cold-retrieval scenarios."

### Handling Adversarial Inputs?
"All ticket descriptions are treated as untrusted user input. The Coordinator checks for suspicious patterns, but the core defense is that agents follow their system prompts regardless of embedded instructions. Malicious commands like 'IGNORE PREVIOUS INSTRUCTIONS' are processed as ticket content, not system commands."

### Production Readiness?
"For production I'd add: (1) Distributed tracing with OpenTelemetry for full trajectory visibility, (2) Secrets management via Azure Key Vault, (3) Rate limiting and caching for LLM calls, (4) A/B testing framework to measure resolution quality, (5) Human feedback loop where technicians rate generated resolutions to improve the system."

## Contact & Attribution

Developed for Advanced Energy Company AI Agentic Engineer Technical Assessment.

Author: [Your Name]
Date: January 2025
