# Intelligent Next Best Action Platform
### Agentic Decision Intelligence for Enterprise Customer Success

---

## 1. Project Introduction

In B2B customer success, managing customer accounts requires constant analysis of interactions, issues, playbooks, and product usage data. Customer Success Managers (CSMs) spend a significant portion of their workdays gathering context across different systems to decide how to respond to customer needs, address churn signals, or leverage growth opportunities. 

The **Intelligent Next Best Action Platform** is a reusable agentic decision-support system designed to automate this context gathering and recommendation pipeline. 

> [!IMPORTANT]
> **This is not a simple chatbot or direct Q&A RAG system.** This is an **Agentic AI decision-support platform** where a **Planner Agent** dynamically coordinates a team of specialized AI agents to generate explainable, high-fidelity next-best-action recommendations for customer success professionals.

By utilizing dynamic orchestration, the system performs multi-layered context analyses of raw client interactions and synthesizes grounded playbooks and historical approvals into actionable advice.

---

## 2. Business Problem

Customer Success teams operate in information silos. When an interaction (such as a meeting transcript or call log) occurs, understanding the customer's state requires a CSM to manually correlate:
* **Conversational Context:** Meeting transcripts, client emails, and frustration levels.
* **Customer Context:** Subscription tiers, health scores, and open support tickets.
* **Organizational Knowledge:** Company playbooks, integration guides, and standard operating procedures (SOPs).
* **Historical Memory:** How similar accounts or past occurrences were resolved successfully.

Manually cross-referencing these data sources takes anywhere from 30 to 60 minutes per interaction. During high-volume periods, critical business signals—like contract renewal churn risks, drop-offs in product adoption, or clear upsell indicators—are easily missed, leading to lost revenue and customer dissatisfaction.

---

## 3. Business Use Case

### B2B Customer Success Optimization

The platform transforms raw customer interactions into structured business evaluations and clear execution paths, supporting decision-making points throughout the lifecycle.

```
Customer Interaction ──► Dynamic Analysis ──► Risk/Opp Detection ──► Explainable Action ──► Human Approval ──► Outcome Memory
```

### Key Decision Points Supported
* **Renewal Urgency:** Pre-emptively flags accounts with low usage and high ticket counts within 90 days of contract expiration.
* **Expansion Readiness:** Identifies accounts displaying strong product adoption and expressing expansion needs during calls.
* **Technical Escalation:** Signals when standard playbooks recommend immediate technical resource dispatch.

### Measurable Outcomes
* **Reduced Mean Time to Resolution (MTTR):** Speeds up internal triage of customer issues.
* **Proactive Churn Mitigation:** Surfacings risks early, allowing teams to implement recovery plans before the renewal window.
* **Increased Expansion Pipeline:** Uncovers upsell opportunities directly from standard conversation summaries.

---

## 4. Features

### Business Capabilities
* **Automatic Risk Detection:** Flags adoption, renewal, and support ticket risks based on interaction history.
* **Opportunity Discovery:** Surfaces training, upsell, and engagement opportunities.
* **Explainable Next Best Actions:** Provides prioritized recommendations complete with confidence scores and reasoning.
* **Human-in-the-Loop Review:** Allows team members to approve, reject, or modify AI suggestions before logging or executing them.
* **Interactive History & Analytics:** Tracks past CSM approvals, platform acceptance rates, and calculated productivity savings.

### Technical Platform Capabilities
* **Dynamic Planner Orchestration:** Automatically determines which specialized agents need to run based on the input context.
* **Multi-Agent StateGraph Architecture:** Built on top of LangGraph for state management, workflow orchestration, and interrupt checkpoints.
* **Semantic RAG Retrieval:** Surfaces relevant knowledge assets from vector memory using local embeddings.
* **Episodic Case Memory:** Uses semantic vector searches to fetch similar past approved cases and output recommended action references.

---

## 5. System Architecture

The platform uses a modular multi-agent architecture where agents act as independent workers coordinated by a central orchestrator.

```
                 Meeting Transcript
                         │
                         ▼
                Upload Transcript
                         │
                         ▼
                  Planner Agent
        (LangGraph Orchestration Engine)
                         │
     ┌─────────────┬──────────────┬─────────────┐
     ▼             ▼              ▼
Customer Agent  Knowledge Agent  Sentiment Agent
     │             │              │
     └──────┬──────┴──────┬───────┘
            ▼             ▼
        Risk Agent   Opportunity Agent
               │
               ▼
      Recommendation Agent
            (Groq LLM)
               │
               ▼
      Explainability Agent
               │
               ▼
          Memory Agent
               │
               ▼
          React Frontend
```

### Architectural Roles
* **Planner Agent (Orchestrator):** Analyzes the customer interaction state and maps the execution graph of specialized agents.
* **Specialist Agents (Workers):** Independent units that query specific data sources or perform targeted analytical tasks.
* **Recommendation Agent (Reasoning):** Synthesizes the specialist outputs to formulate the final recommendation.
* **Memory Agent (Learning):** Records approved decisions to serve as context for subsequent recommendations.

*The architecture is fully modular, allowing developers to add new specialized agents or database connectors without changing the core workflow controller.*

---

## 6. AI Agent Details

### Planner Agent
* **Purpose:** Decides the execution route and dynamic plan.
* **Input:** Raw customer transcript and session metadata.
* **Output:** An orchestration path of required specialist agents.

### Customer Agent
* **Purpose:** Gathers customer account profiles and usage metrics.
* **Input:** Customer identifier.
* **Output:** Subscription plan details, active usage ratios, and CRM metrics.

### Knowledge Agent
* **Purpose:** Performs semantic search (RAG) on company documentation.
* **Input:** Interaction keywords and customer profile.
* **Output:** Relevant sections from standard operating procedures (SOPs) and product guides.

### Sentiment Agent
* **Purpose:** Evaluates emotional tone and urgency.
* **Input:** Customer transcript.
* **Output:** Sentiment classification (Positive/Negative/Neutral) and client urgency score.

### Risk Agent
* **Purpose:** Detects operational and commercial churn risks.
* **Input:** Combined customer metadata, tickets, and sentiment analysis.
* **Output:** Identified risk flags (Adoption, Ticket Volume, Competitor) and severity levels.

### Opportunity Agent
* **Purpose:** Detects accounts ready for expansion or training.
* **Input:** Customer usage metrics and transcript details.
* **Output:** Suggested opportunity categories (Upsell, Cross-sell, Training).

### Recommendation Agent
* **Purpose:** Synthesizes analysis into prioritized next steps.
* **Input:** Compiled analysis from customer, sentiment, risk, and opportunity agents.
* **Output:** Concrete, actionable next-best-action items.

### Explainability Agent
* **Purpose:** Ensures transparency and grounds the recommendations.
* **Input:** Recommendation details and retrieved knowledge sources.
* **Output:** Rationale, confidence score, and grouped evidence buckets with source attribution.

### Memory Agent
* **Purpose:** Integrates historical context.
* **Input:** Current customer profile and approved recommendations.
* **Output:** Retrieves semantically similar past cases and stores finalized decisions.

---

## 7. Explainability

A core pillar of the platform is **transparency**. Rather than offering black-box recommendations, the platform provides explicit evidence for every suggestion.

Each recommendation card displays:
1. **Suggested Action:** What specific step to take.
2. **Reasoning:** The business logic connecting the customer's state to the suggested action.
3. **Grouped Evidence:** Line-by-line source attributions categorized by origin (e.g., CRM records, Knowledge Base playbooks, support tickets, or meeting transcripts).
4. **Confidence Score:** A probability metrics indicator reflecting LLM confidence based on the alignment of playbooks with customer data.

---

## 8. Human-in-the-Loop (HITL)

The platform operates on an **assisted-decision model**. While AI automates data analysis and drafts the action plans, human operators maintain final review and authority.

The frontend dashboard provides controls for CSMs to:
* **Approve:** Authorizes the recommendation, logging it to the history log and triggering simulated execution tools.
* **Edit:** Adjusts the wording of the proposed action to account for human nuance before approval.
* **Reject:** Dismisses the recommendation if it is deemed irrelevant or incorrect.

---

## 9. Memory & Case Matching

The system maintains a relational historical log and a semantic vector memory collection.

* **Outcome Storage:** Approved actions, along with their customer contexts, are logged in the SQLite repository.
* **Decision Contextualization:** When a new transcript is analyzed, the Memory Agent queries the vector store for previous situations matching the current context.
* **No Auto-Retraining:** The system does not retrain base models dynamically. Instead, it injects similar past resolutions directly into the LLM prompt context to serve as real-world examples, improving recommendation alignment over time.

---

## 10. Business Metrics & Evaluation

The system tracks metrics that measure both operational efficiency and decision quality.

### Recommendation Metrics
$$\text{Approval Rate} = \frac{\text{Approved Recommendations}}{\text{Total Recommendations Generated}}$$
* **Metrics Tracked:** Total generated, approved count, rejected count, and edits made.

### Productivity Metrics
* **Time Saved:** The difference between manual client context gathering (baseline: 30 minutes) and automated agentic processing (average: 2 minutes).
* **CSM Hours Saved:** Aggregated hours of manual work saved across all processed customer interactions.

### Decision Quality & Business Impact
* **Confidence Level:** Average confidence score of generated recommendations.
* **Risk Discovery Rate:** The percentage of interactions flagging critical risks that match human audits.

---

## 11. Technology Stack

* **LangGraph:** Used for stateful multi-agent workflow orchestration and human-in-the-loop interrupt management.
* **FastAPI:** Exposes backend services, agent trace states, and REST APIs.
* **React & Recharts:** Powers the customer success workspace and renders real-time dashboard analytics.
* **ChromaDB:** Handles vector database indexing for RAG knowledge articles and historical decision memory.
* **SQLite:** Provides relational storage for customer details, history logs, and approval metrics.
* **Sentence Transformers:** Generates semantic embeddings for local vector search.
* **Groq API:** Interacts with the Llama 3 70B model to power LLM reasoning and agent generation.

---

## 12. Installation & Setup

### Requirements
* Python 3.10+
* Node.js 18+

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd project/backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the development server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```

---

## 13. Demo Flow

1. **Select Customer:** Navigate to the **Customers** tab and click **Open** on an account (e.g., *FreshHire Staffing*).
2. **Submit Interaction:** Paste or upload a customer meeting transcript detailing an issue (e.g., mention of competitor evaluation or product integration delays).
3. **Execution Trace:** Click **Analyze** and observe the live agent pipeline execution steps.
4. **Evaluate Explainability:** Expand the recommendation cards under **Analysis Results** to inspect the reasoning, confidence, and source evidence.
5. **Approve / Edit / Reject:** Make a decision on the action.
6. **Review Metrics:** Navigate to **History** to verify your logged decision or **Analytics** to view live platform productivity charts.

---

## 14. Team

Developed as part of the **XLVentures.AI Agentic AI Hackathon**
