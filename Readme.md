# DataSage

> **Ask questions in plain English. Get deterministic answers—not AI guesses.**

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
              (Optional) AI Insight Generation
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

- FastAPI
- Pandas
- Python

---

## Frontend

- React
- Vite

---

## Planned AI Layer

The AI layer is intentionally designed as an optional reasoning component.

Rather than answering every question, it will activate only for reasoning-heavy requests such as:

- Why did sales decrease?
- Explain this trend.
- Compare these regions.
- Summarize these results.
- Recommend possible actions.

This architecture keeps deterministic queries fast while minimizing inference costs.

---

# Project Structure

```
backend/

├── api/
├── core/
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

---

## In Progress

- AI Insight Engine
- Conversation-aware analytical reasoning
- Frontend integration

---

## Planned

- Interactive dashboards
- Exportable reports
- Additional visualization types
- Multi-turn analytical conversations
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