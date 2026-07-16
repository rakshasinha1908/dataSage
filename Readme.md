# DataSage

> **Ask questions in plain English. Get deterministic answers—not AI guesses.**

> **"Python computes. AI explains."**

DataSage is a deterministic analytics platform that combines natural language understanding with reliable data analysis.

Users can upload structured datasets (CSV files) and interact with them using natural language, while every analytical computation is executed deterministically using Python—not by a large language model.

Rather than replacing analytics with AI, DataSage uses AI only where it genuinely adds value: explanation, reasoning, and insight generation.

---

# Why DataSage?

Most AI-powered analytics tools send every question directly to an LLM.

While this makes natural language interaction easy, it also introduces several problems:

- Hallucinated calculations
- Inconsistent answers
- High inference costs
- Slower response times
- Limited explainability

DataSage follows a different philosophy.

Natural language is used only to understand **what** the user is asking.

The actual computation is always executed through a deterministic analytics engine built using Python and Pandas.

This makes every analytical result:

- Accurate
- Reproducible
- Explainable
- Fast
- Cost-efficient

---

# Core Philosophy

## Deterministic before Generative

If Python can compute the answer deterministically, Python should compute it.

Large language models should never replace mathematics.

---

## AI as an Analyst—not a Calculator

DataSage does not ask AI to calculate averages, totals, rankings, or statistics.

Instead, AI is reserved for higher-level reasoning such as:

- Explaining trends
- Generating insights
- Answering "Why?"
- Business interpretation
- Follow-up analytical discussions

---

## One Module. One Responsibility.

Every major capability is implemented as an independent module.

Examples include:

- Operation Parser
- Condition Parser
- Dimension Parser
- Ranking Parser
- Query Planner
- Analytics Engine
- Visualization Selector

This keeps the codebase modular, maintainable, and easy to extend.

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

# Current Features

## Dataset Intelligence

- CSV upload
- Automatic schema generation
- Dataset metadata extraction
- Session management
- Dataset-aware query execution

---

## Natural Language Understanding

Supports analytical questions such as:

- Average Cost
- Total Revenue
- Maximum Sales
- Count Orders
- Average Transaction Amount by City
- Top 3 Products by Revenue
- Average Sales in Delhi

---

## Deterministic Analytics

Supported analytical operations include:

- Mean
- Sum
- Count
- Minimum
- Maximum

---

## Filtering

Supports contextual filtering using natural language.

Examples:

```
Average Revenue in Delhi

Average Salary for Managers

Total Sales using Card
```

---

## Grouping

Supports grouped analytics.

Examples:

```
Average Revenue by City

Total Sales by Category

Count Patients by Gender
```

---

## Ranking

Supports ranked analytical queries.

Examples:

```
Top 5 Cities by Revenue

Bottom 10 Products by Sales

Top 3 Average Transaction Amount by City
```

---

## Visualization Recommendation

Automatically recommends the most suitable visualization for grouped analytical results.

Current support includes:

- Bar Charts

Future support:

- Line Charts
- Pie Charts
- Scatter Plots
- Histograms

---

## AI Insight Engine

Unlike traditional analytics assistants, DataSage does not use AI to perform calculations.

Every analytical query is first executed deterministically using Python. AI is invoked only after a verified result has been produced, allowing it to explain, summarize, or interpret the result without modifying the underlying computation.

Current capabilities include:

- Explain deterministic analytical results
- Answer follow-up questions using session context
- Context-aware reasoning (e.g. "Why?")
- Ground every explanation in verified analytical output
- Refuse unsupported explanations when insufficient data is available

---

## Context-Aware AI

DataSage remembers the most recent analytical query within a session.

This enables natural follow-up questions without asking users to repeat the full analytical context.

Example

Average Transaction Amount by City

↓

Mumbai has the highest average transaction amount.

↓

User:

Why?

↓

DataSage automatically understands that "Why?" refers to the previous analytical result and generates an explanation grounded in verified computations.

Unlike traditional chatbots, DataSage does not retain conversations across sessions.

---

# Example Queries

```
Average Cost
```

↓

```
8367.48
```

---

```
Average Transaction Amount in Delhi
```

↓

```
5345.16
```

---

```
Average Transaction Amount by City
```

↓

```
{
    "Delhi": ...,
    "Mumbai": ...,
    "Chennai": ...
}
```

↓

Recommended Visualization

```
Bar Chart
```

---

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

| Traditional LLM Analytics | DataSage |
|----------------------------|----------|
| LLM performs calculations | Python performs calculations |
| Can hallucinate numerical answers | Deterministic computations |
| Every query consumes inference tokens | AI invoked only when required |
| Difficult to explain execution | Transparent analytical pipeline |
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

---

# Project Structure

```
backend/

├── api/
├── core/
│   ├── ai/
├── models/
├── query/
├── storage/
├── utils/

└── app.py
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

Activate the environment.

Windows

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

API

```
http://127.0.0.1:8000
```

Swagger

```
http://127.0.0.1:8000/docs
```

---

# Roadmap

## Completed

- Dataset upload
- Schema generation
- Session management
- Natural language query parsing
- Deterministic analytics engine
- Query planning
- Filtering
- Grouping
- Ranking
- Visualization recommendation
- Production query API
- AI Insight Engine
- Conversation-aware analytical reasoning

---

## In Progress

- Frontend integration

---

## Planned

- Multi-provider AI fallback
- Interactive dashboards
- Exportable reports
- Additional visualization types
- Deployment

---

# Engineering Principles

Every capability in DataSage is built incrementally.

Each feature follows the same development process.

```
Requirements

↓

Architecture

↓

Implementation

↓

Testing

↓

Integration
```

No feature is considered complete until it has been independently tested.

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

## Author

**Raksha Sinha**

Building DataSage to explore how deterministic analytics and selective AI reasoning can work together to create trustworthy data analysis systems.

---

## License

This project is licensed under the MIT License.