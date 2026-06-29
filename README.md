# Intelligent Next Best Action Platform
### Agentic Decision Intelligence for Customer Success Teams

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-purple.svg)](https://langchain-ai.github.io/langgraph)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![React Flow](https://img.shields.io/badge/ReactFlow-11-orange.svg)](https://reactflow.dev)

---

## Overview

A reusable **Agentic Decision Intelligence Platform** that transforms customer interactions and enterprise knowledge into actionable next-best-action recommendations.

Built with a true **multi-agent architecture** using **LangGraph** for orchestration, **ChromaDB** for semantic memory, **PostgreSQL/SQLite** for persistence, and a **React + React Flow** frontend for real-time agent visualization.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     NEXT BEST ACTION PLATFORM                           │
│                                                                         │
│  ┌──────────────┐    ┌──────────────────────────────────────────────┐  │
│  │   FRONTEND   │    │              BACKEND AGENTS                  │  │
│  │  React + RF  │◄──►│                                              │  │
│  │  Dashboard   │    │  ┌──────────┐   ┌─────────────────────────┐ │  │
│  │  Agent Graph │    │  │ Planner  │──►│ Dynamic AgentExecutor   │ │  │
│  │  HITL UX     │    │  │  Agent   │   │  - Customer Agent        │ │  │
│  └──────────────┘    │  └──────────┘   │  - Knowledge Agent       │ │  │
│                       │       │         │  - Sentiment Agent       │ │  │
│  ┌──────────────┐    │       ▼         │  - Risk Agent            │ │  │
│  │   FastAPI    │    │  ┌──────────┐   │  - Opportunity Agent     │ │  │
│  │   REST API   │    │  │  Memory  │   │  - Memory Agent          │ │  │
│  │  /upload     │    │  │  Agent   │   └─────────────────────────┘ │  │
│  │  /recommend  │    │  └──────────┘            │                  │  │
│  │  /approve    │    │                           ▼                  │  │
│  │  /approve    │    │              ┌───────────────────────┐       │  │
│  │   _action    │    │              │  Recommendation Agent │       │  │
│  └──────────────┘    │              │  Explanation Agent    │       │  │
│                       │              └───────────────────────┘       │  │
│  ┌──────────────┐    │                    HITL INTERRUPT             │  │
│  │  DATABASES   │    │                         │                     │  │
│  │              │    │              ┌───────────────────────┐       │  │
│  │  PostgreSQL  │◄──►│              │  Action Executor Agent│       │  │
│  │  SQLite(FB)  │    │              │  Outcome Agent        │       │  │
│  │  ChromaDB    │    │              └───────────────────────┘       │  │
│  └──────────────┘    └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Flow

```
Customer Transcript
        │
        ▼
  ┌─────────────┐
  │ Planner     │  Analyzes transcript → selects required agents → plan
  │ Agent       │  Consults semantic memory for past similar cases
  └──────┬──────┘
         │  Dynamic plan
         ▼
  ┌─────────────────────────────────────────────────────┐
  │              PARALLEL ANALYSIS AGENTS                │
  │  Customer Agent    → CRM profile, usage metrics      │
  │  Knowledge Agent   → RAG search across playbooks     │
  │  Sentiment Agent   → LLM tone + urgency analysis     │
  │  Risk Agent        → Rules-based risk scoring        │
  │  Opportunity Agent → Upsell/training opportunities   │
  │  Memory Agent      → Similar past cases from ChromaDB│
  └──────────────────────────┬──────────────────────────┘
                             │
                             ▼
                  ┌──────────────────┐
                  │ Recommendation   │  LLM-synthesized actions
                  │ Agent            │  with priority + confidence
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │ Explanation      │  Structured evidence with
                  │ Agent            │  source attribution
                  └────────┬─────────┘
                           │
                    ⏸ HITL INTERRUPT
                    Human reviews + approves
                           │
                  ┌────────▼─────────┐
                  │ Action Executor  │  send_email / crm_task /
                  │ Agent            │  notify_owner tools
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │ Outcome Agent    │  Logs before/after health
                  │                  │  score delta + success flag
                  └──────────────────┘
```

---

## Database Design

### SQL (PostgreSQL / SQLite fallback)

| Table | Purpose | Key Columns |
|---|---|---|
| `customers` | Customer profiles, usage, health | `customer_id`, `health_score`, `renewal_date`, `dashboard_usage_pct` |
| `interactions` | Transcript ingestion log | `customer_id`, `transcript_text`, `sentiment`, `confidence` |
| `recommendations` | Generated next-best actions | `id`, `session_id`, `customer_id`, `action_description`, `confidence` |
| `approvals` | Human approval decisions | `session_id`, `customer_id`, `recommendation_id` |
| `outcomes` | Post-execution metrics | `customer_id`, `action`, `before_score`, `after_score`, `success` |

### ChromaDB Vector Collections

| Collection | Purpose |
|---|---|
| `knowledge_memory` | Enterprise playbooks, SOPs, integration guides — powers RAG |
| `decision_memory` | Past approved actions — powers semantic case retrieval |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Orchestration** | LangGraph (StateGraph + MemorySaver + interrupt) |
| **LLM** | Groq (llama3-70b) / Ollama (qwen2.5) fallback |
| **Tools** | LangChain `@tool` decorator |
| **Vector Store** | ChromaDB + SentenceTransformers |
| **SQL** | PostgreSQL (primary) / SQLite (fallback) |
| **API** | FastAPI + Pydantic |
| **Frontend** | React 18 + Vite + React Flow |
| **Styling** | Tailwind CSS |
| **Containerization** | Docker + Docker Compose |

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.ai) (for local LLM) OR Groq API key

### 1. Clone and configure environment

```bash
git clone <repo-url>
cd xlventures
cp .env.example .env
# Edit .env and add your GROQ_API_KEY (optional — Ollama works without it)
```

### 2. Backend setup

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r project/backend/requirements.txt
```

### 3. Pull local LLM (optional — skip if using Groq)

```bash
ollama pull qwen2.5:0.5b
```

### 4. Run backend

```bash
cd project/backend
uvicorn main:app --reload --port 8000
```

Backend auto-seeds the database from CSV/JSON on first startup.

### 5. Frontend setup

```bash
cd frontend
npm install
echo "VITE_API_BASE_URL=http://127.0.0.1:8000" > .env
npm run dev
```

Open http://localhost:5173

---

## Docker Setup

```bash
# Copy and configure environment
cp .env.example .env
# Add GROQ_API_KEY to .env if desired

# Start all services
docker-compose up --build

# Services:
#   Frontend  → http://localhost:5173
#   Backend   → http://localhost:8000
#   PostgreSQL→ localhost:5432
#   ChromaDB  → http://localhost:8001
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload_transcript` | Start a new session with a transcript |
| `GET`  | `/recommendation/{session_id}` | Run the agent pipeline (pauses at HITL) |
| `POST` | `/approve` | Store approval decision in memory |
| `POST` | `/approve_action` | Resume LangGraph execution after approval |
| `GET`  | `/history/{customer_id}` | Get approval history for a customer |
| `GET`  | `/agent_trace/{session_id}` | Get real-time agent execution trace |
| `GET`  | `/graph_structure` | Get agent pipeline graph for visualization |
| `GET`  | `/docs` | Interactive Swagger API docs |

---

## Demo Steps

1. **Start both servers** (backend on :8000, frontend on :5173)

2. **Upload a transcript:**
   ```
   Customer: ABC Manufacturing
   Transcript: "Team is exporting to Excel instead of using dashboards.
   Renewal is in 20 days. SAP sync takes 20 min daily. Management
   is evaluating BambooHR and Workday."
   ```

3. **Watch the Agent Graph** — nodes turn green as each agent completes

4. **Review the Dashboard:**
   - Customer Health score + bar chart
   - Risk signals with severity badges
   - Next Best Actions with confidence scores + evidence pills

5. **Approve a recommendation** → stored in ChromaDB decision memory

6. **Execute an action** → LangGraph HITL resumes:
   - `ActionExecutorAgent` sends email / creates CRM task / notifies owner
   - `OutcomeAgent` logs before/after health score to `outcomes` table

7. **Check Approval History** — past decisions with timestamps

---

## Project Structure

```
xlventures/
├── project/
│   └── backend/
│       ├── agents/
│       │   ├── planner.py              # Orchestrator + HITL state store
│       │   ├── planner_agent.py        # LLM-based plan generator
│       │   ├── customer_agent.py       # CRM + usage data retrieval
│       │   ├── knowledge_agent.py      # RAG knowledge search
│       │   ├── sentiment_agent.py      # LLM sentiment analysis
│       │   ├── risk_agent.py           # Rules-based risk assessment
│       │   ├── opportunity_agent.py    # Upsell/training opportunities
│       │   ├── recommendation_agent.py # LLM recommendation synthesis
│       │   ├── explanation_agent.py    # Structured evidence builder
│       │   ├── memory_agent.py         # ChromaDB semantic memory
│       │   ├── action_executor_agent.py# HITL action execution
│       │   └── outcome_agent.py        # Post-action outcome logging
│       ├── graph/
│       │   └── agent_executor.py       # Dynamic executor + LangGraph graph
│       ├── tools/
│       │   ├── crm_tool.py             # @tool: CRM data
│       │   ├── customer_history_tool.py # @tool: Approval history
│       │   ├── knowledge_search_tool.py # @tool: ChromaDB search
│       │   ├── usage_analysis_tool.py  # @tool: Usage metrics
│       │   ├── playbook_tool.py        # @tool: Playbook loader
│       │   ├── notification_tool.py    # @tool: Alert sender
│       │   ├── send_email_tool.py      # @tool: Email simulation
│       │   ├── create_crm_task_tool.py # @tool: CRM task creation
│       │   └── notify_owner_tool.py    # @tool: Owner alert
│       ├── database/
│       │   ├── connection.py           # PostgreSQL/SQLite manager
│       │   ├── models.py               # SQL table schemas
│       │   └── repository.py           # CRUD helpers
│       ├── rag/
│       │   ├── loader.py               # ChromaDB knowledge ingestion
│       │   └── retriever.py            # Semantic search
│       └── main.py                     # FastAPI app + all routes
├── frontend/
│   └── src/
│       └── App.jsx                     # React Flow + dashboard
├── data/                               # Seed CSV/JSON files
├── tests/
│   └── test_phase_1_to_4.py           # End-to-end validation
├── docker-compose.yml
└── README.md
```

---

## Key Design Decisions

- **No hardcoded logic** — all agents use `@tool` functions; adding a new tool requires zero changes to orchestration.
- **HITL via checkpoint store** — after recommendations, state is saved and execution pauses until `/approve_action` is called.
- **Dual memory** — ChromaDB for semantic case retrieval, PostgreSQL for structured history and outcome tracking.
- **Fallbacks everywhere** — Groq → Ollama → heuristic LLM fallback; PostgreSQL → SQLite; ChromaDB auto-rebuilds on first call.
- **Observable** — every agent execution is traced with input/output snapshots; the frontend displays the live graph.
