# DataSage

> **Ask questions in plain English. Get deterministic answers—not AI guesses.**

> **Python computes. AI explains.**

<p align="center">
  <img src="frontend/public/upload-ui.png" alt="DataSage Upload UI" width="900"/>
</p>

DataSage is an AI-assisted analytics platform that combines natural language understanding with deterministic data analysis.

Unlike traditional AI analytics tools that rely on Large Language Models for calculations, DataSage executes every analytical computation using Python and Pandas, ensuring that every numerical result is accurate, reproducible, and explainable.

Artificial Intelligence is used only where it genuinely adds value—explaining verified results rather than generating them.

---

# Why DataSage?

Most AI-powered analytics tools send every user query directly to a Large Language Model.

While this enables natural language interaction, it also introduces several challenges:

- Hallucinated calculations
- Inconsistent numerical answers
- Higher inference costs
- Slower response times
- Limited transparency

DataSage follows a different philosophy.

Natural language is used only to understand **what** the user wants.

Python determines **how** to compute the answer.

AI is then used to explain verified analytical results.

This approach makes DataSage:

- Deterministic
- Reproducible
- Explainable
- Fast
- Cost-efficient

---

# Core Philosophy

## Deterministic before Generative

If Python can compute the answer, Python should compute it.

Large Language Models should never replace mathematics.

---

## AI as an Analyst—not a Calculator

DataSage never asks AI to calculate:

- averages
- totals
- rankings
- statistics

Instead, AI is responsible for:

- Explaining trends
- Business reasoning
- Follow-up discussions
- Context-aware insights
- Interpretation

---

## Python Computes. AI Explains.

Every query follows the same philosophy.

```
Question
      │
      ▼
Natural Language Understanding
      │
      ▼
Deterministic Analytics Engine
      │
      ▼
Verified Result
      │
      ├────────────► Table
      │
      ├────────────► Chart
      │
      ▼
✨ Explain this result
      │
      ▼
AI Insight
```

---

# Architecture

```
                    Natural Language Question
                               │
                               ▼
                     Operation Parser
                               │
                               ▼
                     Condition Parser
                               │
                               ▼
                      Ranking Parser
                               │
                               ▼
                     Dimension Parser
                               │
                               ▼
                      Column Matcher
                               │
                               ▼
                     Intent Validator
                               │
                               ▼
                        Query Planner
                               │
                               ▼
                     Analytics Engine
                               │
                               ▼
                  Visualization Selector
                               │
                               ▼
                     Structured API Response
                               │
                               ▼
                     Query Context Storage
                               │
                               ▼
                  Insight Request Builder
                               │
                               ▼
                     Prompt Builder
                               │
                               ▼
                      AI Insight Engine
                               │
                               ▼
                      Gemini Provider
```

---

# Features

## Dataset Intelligence

- CSV Upload
- Automatic Schema Detection
- Metadata Extraction
- Session Management
- Dataset-aware Query Execution

---

## Natural Language Analytics

Supports analytical questions like:

```
Average Revenue

Total Sales

Top 5 Cities by Revenue

Average Salary by Department

Maximum Transaction Amount

Average Transaction Amount in Delhi
```

---

## Deterministic Analytics

Current operations include:

- Mean
- Sum
- Count
- Minimum
- Maximum
- Filtering
- Grouping
- Ranking

---

## Visualization Engine

Structured analytical results automatically generate visualizations.

Current support:

- ✅ Bar Charts

Upcoming:

- Line Charts
- Pie Charts
- Scatter Plots
- Histograms

---

## AI Insight Engine

Every analytical result is computed deterministically before AI is involved.

Current capabilities:

- Explain analytical results
- Context-aware follow-up questions
- Session-aware reasoning
- Business interpretation
- Verified insight generation

---

## Context-Aware Conversations

DataSage remembers the latest analytical result during a session.

Example:

```
Average Transaction Amount by City
```

↓

```
Mumbai has the highest average transaction amount.
```

↓

User:

```
Why?
```

↓

DataSage automatically understands that "Why?" refers to the previous analytical result and generates an explanation grounded in verified computations.

---

# Example Queries

### KPI

```
Average Revenue
```

↓

```
8367.48
```

---

### Filtering

```
Average Transaction Amount in Delhi
```

↓

```
5345.16
```

---

### Grouping

```
Average Transaction Amount by City
```

↓

```
Delhi
Mumbai
Chennai
...
```

↓

📊 Recommended Visualization

```
Bar Chart
```

---

### Ranking

```
Top 3 Average Transaction Amount by City
```

↓

```
Mumbai

Delhi

Bangalore
```

---

# Why Not Just Use an LLM?

| Traditional AI Analytics | DataSage |
|---------------------------|----------|
| LLM performs calculations | Python performs calculations |
| Hallucinated numerical answers | Deterministic computations |
| Every query consumes inference tokens | AI invoked only when required |
| Limited explainability | Transparent analytical pipeline |
| Higher operational cost | Cost-efficient architecture |

---

# Technology Stack

## Backend

- Python
- FastAPI
- Pandas
- Google Gemini API

---

## Frontend

- React
- Vite
- Recharts

---

# Project Structure

```
DataSage/

├── backend/
│   ├── api/
│   ├── core/
│   │   └── ai/
│   ├── models/
│   ├── query/
│   ├── storage/
│   ├── utils/
│   └── app.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── assets/
│   │   └── App.jsx
│
├── docs/
│   └── images/
│
└── README.md
```

---

# Running Locally

Clone the repository.

```bash
git clone <repository-url>
```

Navigate to the backend.

```bash
cd backend
```

Create a virtual environment.

```bash
python -m venv venv
```

Activate it.

Windows

```bash
venv\Scripts\activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Run the backend.

```bash
uvicorn app:app --reload
```

Backend:

```
http://127.0.0.1:8000
```

Swagger:

```
http://127.0.0.1:8000/docs
```

---

# Roadmap

## Completed

- [x] CSV Upload
- [x] Schema Detection
- [x] Session Management
- [x] Natural Language Query Parsing
- [x] Deterministic Analytics Engine
- [x] Filtering
- [x] Grouping
- [x] Ranking
- [x] Visualization Recommendation
- [x] Interactive Charts
- [x] AI Insight Engine
- [x] Frontend Integration (MVP)

---

## Next

- [ ] Explain This Result workflow
- [ ] Line Charts
- [ ] Pie Charts
- [ ] Scatter Plots
- [ ] Download Reports
- [ ] Interactive Dashboard
- [ ] Multi-provider AI Support
- [ ] Deployment

---

# Design Principles

Every architectural decision in DataSage follows three simple principles:

- Python computes.
- AI explains.
- Deterministic results always take priority over generated responses.

These principles guide every new feature added to the platform.

---

# Vision

DataSage is not trying to become another AI chatbot.

Its goal is to become a trustworthy analytics platform where deterministic computation and selective AI reasoning work together.

Every numerical answer should be:

- Correct
- Explainable
- Reproducible

Every AI-generated insight should be grounded in verified analytical results—not generated guesses.

---

# Author

**Raksha Sinha**

Building DataSage to explore how deterministic analytics and selective AI reasoning can work together to create trustworthy, AI-assisted analytics systems.

---

# License

This project is licensed under the MIT License.