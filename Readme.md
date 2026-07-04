# DataSage

> **DataSage is an analytics engine that understands datasets before answering questions.**

DataSage allows users to upload structured datasets (CSV files) and interact with them using natural language.

Unlike general-purpose AI assistants, DataSage does **not** rely on large language models to perform calculations. Instead, it combines deterministic data analysis with natural language understanding to produce reliable, reproducible, and explainable analytical results.

---

# Why DataSage?

Most AI assistants can understand questions.

Most analytics tools can execute calculations.

DataSage is designed to bridge those two worlds.

Instead of asking users to write SQL or Pandas code, DataSage translates natural language into deterministic analytical operations executed directly in Python.

This approach provides:

- Reliable calculations
- Reproducible results
- Explainable execution
- Dataset-aware reasoning
- Minimal hallucinations

---

# Design Philosophy

DataSage follows a few core engineering principles.

### Correctness over cleverness

Reliable analytical results are more valuable than complex AI reasoning.

### Python first. AI second.

If Python can perform an operation deterministically, Python should perform it.

AI is only used where language understanding genuinely adds value.

### One module. One responsibility.

Each component has a clearly defined purpose, making the codebase easy to understand, maintain, and extend.

### Dataset intelligence before question answering.

Every uploaded dataset is understood first through schema generation before any user query is processed.

---

# How It Works

```
             Upload Dataset
                    │
                    ▼
           Dataset Manager
                    │
                    ▼
            Schema Generation
                    │
                    ▼
          Query Understanding
                    │
                    ▼
         Deterministic Analytics
                    │
                    ▼
            Response Generation
```

---

# Current Progress

## Completed

- Dataset upload pipeline
- Session management
- Automatic schema generation
- Schema inspection API
- Dataset metadata extraction
- Modular backend architecture

## In Progress

- Query parsing
- Operation detection
- Column matching

## Planned

- Analytics engine
- Filtering
- Grouping
- Ranking
- Trend analysis
- AI-powered insights
- Interactive visualizations

---

# Project Structure

```
backend/
│
├── api/
├── core/
├── models/
├── query/
├── storage/
├── utils/
│
└── app.py
```

---

# Technology Stack

### Backend

- FastAPI
- Pandas

### Frontend

- React
- Vite

### Future Integrations

- Grok API (Natural Language Understanding)
- Vector Search
- Plotly / Chart.js

---

# Running Locally

Clone the repository.

```bash
git clone <repository-url>
```

Navigate into the backend.

```bash
cd backend
```

Create a virtual environment.

```bash
python -m venv venv
```

Activate the environment.

```bash
venv\Scripts\activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Start the server.

```bash
uvicorn app:app --reload
```

The API will be available at:

```
http://127.0.0.1:8000
```

Swagger documentation:

```
http://127.0.0.1:8000/docs
```

---

# Engineering Principles

DataSage is intentionally built using incremental milestones.

Every feature follows the same workflow:

```
Requirements
      │
      ▼
Behavior
      │
      ▼
Architecture
      │
      ▼
Implementation
      │
      ▼
Testing
```

No feature is added until the previous one is reliable.

---

# Vision

DataSage is not trying to become another conversational AI.

Its goal is to become a specialized analytics engine that combines:

- Natural language interaction
- Deterministic computation
- Dataset intelligence
- Explainable reasoning
- Modular software architecture

The focus is not on maximizing AI usage.

The focus is on building an analytics system that users can trust.


---

## Author

**Raksha Sinha**


Building DataSage as an experiment in combining conversational AI with deterministic data analytics.
