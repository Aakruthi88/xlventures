# Intelligent Next Best Action Platform
An agentic decision intelligence platform that transforms customer interactions and enterprise knowledge into actionable Customer Success recommendations.

---

## What Has Been Completed So Far (Phases 1 - 5)

### 📊 Phase 2: Synthetic Data Generation Pipeline
- Built a programmatic data generation script at `scripts/generate_enterprise_data.py`.
- Generates customer lists, support ticket histories, product usage metrics, meeting transcripts, and a detailed markdown-based knowledge base.
- Includes a 24-check self-validation suite ensuring consistent company records, correct health scores, and matching technical issue profiles.

### 🧩 Phase 3: Agent Skeletons & Schema Contracts
- Structured the backend codebase (`project/backend/`) with modular subdirectories for agents, vector indexing (RAG), and memory databases.
- Created stub files for all specialized agents:
  - `planner.py` (Orchestrator)
  - `customer_agent.py` (Unified summary)
  - `knowledge_agent.py` (Product playbooks)
  - `sentiment_agent.py` (Emotional tone)
  - `risk_agent.py` (Churn & renewal warnings)
  - `opportunity_agent.py` (Training & upsell triggers)
  - `recommendation_agent.py` (Decision engine)
  - `explanation_agent.py` (Evidence and logic mapping)
  - `memory_agent.py` (Context learning)

### ⚡ Phase 4: FastAPI Web Server Layer
- Developed API endpoints inside `project/backend/main.py` with custom Pydantic input-body validation.
- Configured CORS policy to allow parallel development of the frontend (`http://localhost:5173`).
- Created endpoints to upload meeting transcripts, trigger recommendation pipelines, approve recommended actions, and query history logs.

### 🧠 Phase 5: LangGraph Planner & Dynamic Routing
- Designed and compiled a **LangGraph StateGraph workflow** that routes state transitions securely.
- Built a **Hybrid Router** that dynamically selects which analysis nodes to execute:
  1. **Local LLM (Ollama / Qwen-0.5B):** Runs in-context prompt analysis on transcripts to select target agents.
  2. **Rule-Based Fallback:** Instantly parses keywords (e.g. `renewal` -> `risk_agent`) if the local Ollama server is offline.
- Ensured failure resilience: if individual agent modules raise exceptions, the planner catches them, logs the error, falls back to mock responses, and proceeds without crashing.

---

## Project Structure
```text
xlventures/
├── data/                         # CSV and JSON source records
│   ├── knowledge_base/           # Customer Success markdown docs
│   └── meeting_transcripts/      # Text files of customer calls
├── project/
│   └── backend/
│       ├── main.py               # FastAPI application server
│       ├── database/
│       │   └── sqlite.db         # Empty memory storage
│       ├── agents/               # Multi-agent logic and state
│       │   ├── planner.py        # LangGraph StateGraph coordinator
│       │   ├── planner_router.py # Ollama & keyword-based router
│       │   ├── planner_state.py  # Shared AgentState TypedDict
│       │   ├── llm.py            # Local model connectivity helper
│       │   └── ...               # Specialized agents (stubs)
│       └── rag/                  # Retriever & document loaders
│           ├── loader.py         # KB chunk indexing placeholder
│           └── retriever.py      # Vector similarity query placeholder
├── scripts/                      # Validation and generation utilities
│   ├── generate_enterprise_data.py
│   ├── validate_phase3.py
│   ├── validate_phase4.py
│   └── validate_phase5.py
└── tests/
    └── test_phase_1_to_4.py      # System integration test suite
```

---

## Setup & Running the Code

### 1. Requirements & Dependencies
Make sure you have Python 3.10+ installed. In your terminal, run:
```bash
pip install -r project/backend/requirements.txt
```

### 2. local LLM Setup (Ollama)
The platform uses the lightweight **`qwen2.5:0.5b`** model (394 MB) for local orchestration:
1. Download and start **Ollama** from [ollama.com](https://ollama.com).
2. Open a terminal and download the model:
   ```bash
   ollama pull qwen2.5:0.5b
   ```
*If Ollama is not running, the platform will automatically fall back to rule-based routing, so the server never crashes.*

### 3. Generate the Dataset
Create the synthetic files by running:
```bash
python scripts/generate_enterprise_data.py
```

### 4. Run the Web Server
Launch the FastAPI backend server:
```bash
uvicorn project.backend.main:app --reload
```
The server will start on [http://127.0.0.1:8000](http://127.0.0.1:8000).

### 5. Running the Tests
To verify all components (data, stubs, Graph routing, and web endpoints) are functioning correctly, run the validation script:
```bash
python scripts/validate_phase5.py
```
