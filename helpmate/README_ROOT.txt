HELPMATE - AI AGENT SYSTEM
==========================

Intelligent IT Support Ticket Resolution Agent using Multi-Agent Architecture

FOLDER STRUCTURE
================

helpmate/
│
├── agents/              Agent implementations
│   ├── coordinator_agent.py    - Plans & routes tickets
│   ├── retrieval_worker.py     - Adaptive search
│   ├── diagnosis_worker.py     - Generates resolutions
│   ├── critic_agent.py         - Validates grounding
│   └── state.py                - Shared state definition
│
├── core/                Core system files
│   ├── config.py               - Configuration
│   ├── rag_system.py           - FAISS vector search
│   └── helpmate_agent.py       - LangGraph orchestration
│
├── tools/               Agent tools
│   └── agent_tools.py          - 11 tools (search, escalate, etc.)
│
├── scripts/             Executable scripts
│   ├── app.py                  - FastAPI server
│   ├── demo.py                 - Interactive demo
│   ├── evaluate_agent.py       - Evaluation framework
│   ├── generate_tickets.py     - Data generation
│   ├── generate_knowledge_corpus.py
│   └── generate_test_scenarios.py
│
├── data/                Generated data (after setup)
│   ├── tickets.csv
│   ├── knowledge_corpus.json
│   ├── test_scenarios.json
│   └── faiss_index.*
│
└── docs/                Documentation
    ├── README.txt              - Complete guide
    ├── ARCHITECTURE.txt        - Design document
    ├── ASSUMPTIONS.txt         - Assumptions & future work
    ├── INTERVIEW_GUIDE.txt     - Quick reference
    ├── QUICKSTART.txt          - Setup guide
    ├── PRE_INTERVIEW_CHECKLIST.txt
    └── PROJECT_SUMMARY.txt

QUICK START
===========

1. Configure credentials:
   copy .env.template .env
   (Edit .env with Azure OpenAI credentials)

2. Install dependencies:
   pip install -r requirements.txt

3. Run setup:
   python setup.py

4. Run demo:
   python scripts/demo.py

COMMANDS
========

Setup & Demo:
  python setup.py                 - Initialize system
  python scripts/demo.py          - Interactive demo

Run Application:
  python scripts/app.py           - Start FastAPI server
  python scripts/evaluate_agent.py - Full evaluation

Documentation:
  docs/QUICKSTART.txt            - 10-minute setup guide
  docs/README.txt                - Complete documentation
  docs/INTERVIEW_GUIDE.txt       - Interview preparation

REQUIREMENTS
============

- Python 3.10+
- Azure OpenAI API access (GPT-4 + embeddings)
- 2GB RAM for FAISS index

For detailed setup instructions, see: docs/QUICKSTART.txt
