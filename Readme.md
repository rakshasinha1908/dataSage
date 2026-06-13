# DataSage

> **DataSage is an experimental AI-powered analytics engine that converts natural language questions into structured analytical operations on datasets.**
>
> The project combines dataset intelligence, query planning, deterministic execution, and explainable analytics to make data exploration more accessible without sacrificing transparency.

---

# Overview

DataSage is a natural-language analytics platform designed to help users explore and analyze structured datasets without writing SQL, formulas, or complex analytical code.

Users can upload a dataset and ask questions such as:

* What is the average transaction amount?
* Show the top 10 products by revenue.
* Which region generated the highest sales?
* How many prepaid orders were completed?
* Show monthly sales trends.
* Compare revenue across customer segments.

Instead of relying solely on text generation, DataSage attempts to understand the structure of the dataset, build an execution plan, perform deterministic calculations, and present results in a meaningful format.

---

# Why DataSage?

A common question is:

> "Why build DataSage when ChatGPT, Claude, Gemini, and other AI tools can already analyze datasets?"

It's a fair question.

The answer is that DataSage is not trying to replace general-purpose AI assistants. Instead, it focuses on a different problem: turning dataset analysis into a structured, repeatable, and explainable process.

Large language models are extremely capable at understanding questions and generating insights. However, business analytics often requires more than natural language understanding:

* Consistent interpretation of dataset schemas
* Reliable aggregation and filtering
* Deterministic calculations
* Explainable analytical decisions
* Validation and error handling
* Reproducible results

A general AI assistant may answer a question correctly, but the reasoning process is often hidden and may vary between runs.

DataSage aims to bridge the gap between conversational AI and analytical systems by combining natural language interaction with structured execution.

Instead of directly generating answers, DataSage attempts to:

1. Understand the dataset structure.
2. Identify the user's analytical intent.
3. Build an execution plan.
4. Execute calculations deterministically.
5. Present results with context and explanations.

The objective is not to compete with ChatGPT or Claude.

The objective is to build a specialized analytics layer that can work alongside them.

In the same way that a spreadsheet is different from a word processor, DataSage is designed to solve a different category of problems than a general-purpose AI assistant.

---

# Key Features

## Dataset Intelligence

Before answering questions, DataSage analyzes uploaded datasets and attempts to understand:

* Numeric columns
* Categorical columns
* Date/time columns
* Identifier fields
* Boolean fields
* Free-text fields
* Semantic column roles

This enables the system to reason about what analyses are possible and which columns are most relevant for a given question.

---

## Natural Language Querying

Users can interact with datasets conversationally.

Example:

**Question**

```text
Average sales by product category
```

**Internal Understanding**

```text
Intent: Aggregation
Metric: Sales
Group By: Product Category
Operation: Average
```

This intermediate planning layer helps improve consistency and explainability.

---

## Deterministic Analytics

Whenever possible, DataSage performs calculations directly on the dataset instead of relying on generated answers.

Supported analytical operations include:

* Sum
* Average
* Count
* Median
* Ranking
* Trend Analysis
* Distribution Analysis
* Comparison Analysis
* Correlation Analysis

This approach reduces hallucinations and improves result reliability.

---

## Explainable Query Processing

DataSage is designed to expose how it interprets a query.

The system can surface information such as:

* Detected intent
* Selected metric
* Grouping dimensions
* Applied filters
* Confidence indicators
* Execution strategy

The goal is to make analytical decisions transparent rather than hidden behind a black box.

---

# Example Queries

### KPI Queries

```text
What is the average transaction amount?
```

```text
How many prepaid orders were completed?
```

---

### Ranking Queries

```text
Show the top 10 products by revenue.
```

```text
Which region generated the highest sales?
```

---

### Trend Queries

```text
Show monthly sales trends.
```

```text
How has revenue changed over time?
```

---

### Distribution Queries

```text
What are the most common customer segments?
```

```text
Show the distribution of order statuses.
```

---

### Comparison Queries

```text
Compare revenue across regions.
```

```text
Compare average order value by category.
```

---

# Current Architecture

## Frontend

* React
* Vite

## Backend

* FastAPI
* Pandas
* Python

## Core Components

### Query Understanding

Responsible for:

* Intent detection
* Operation detection
* Group-by detection
* Filter extraction
* Semantic interpretation

---

### Query Planning

Responsible for:

* Query plans
* Resolution logic
* Execution routing
* Query metadata

---

### Validation Layer

Responsible for:

* Query validation
* Ambiguity detection
* Confidence checks
* Result verification

---

### Execution Layer

Responsible for:

* KPI execution
* Aggregation execution
* Ranking execution
* Trend execution
* Distribution execution
* Comparison execution
* Raw data retrieval

---

### Response Layer

Responsible for:

* Response formatting
* Visualization selection
* API response standardization

---

# Current Project Status

⚠️ Active Development

The project is currently undergoing a major architectural refactor from a large monolithic backend into a modular analytics engine.

Current focus areas include:

* Improving query accuracy
* Better schema understanding
* Stronger query planning
* Improved execution reliability
* Better frontend-backend consistency
* Modular architecture

---

# Roadmap

## Phase 1 – Analytics Foundation

* Deterministic query execution
* Query planning engine
* Dataset intelligence layer
* Validation framework

## Phase 2 – Advanced Query Understanding

* Better semantic matching
* Multi-step query planning
* Query repair
* Ambiguity resolution
* Improved schema awareness

## Phase 3 – Analytics Platform

* Multi-file analysis
* Cross-dataset operations
* Saved dashboards
* User workspaces
* Report generation

## Phase 4 – AI-Assisted Analytics

* Automated insight discovery
* Root-cause analysis
* Forecasting
* Anomaly detection
* Executive summaries

---

# Vision

DataSage is being built around a simple idea:

**Data should be accessible through questions, not tools.**

Today, extracting insights from data often requires familiarity with spreadsheets, dashboards, SQL, BI tools, or statistical software.

DataSage aims to reduce that barrier by allowing users to interact with data conversationally while still benefiting from structured analytical execution.

The long-term goal is to create a system that combines:

* Natural language understanding
* Dataset intelligence
* Deterministic analytics
* Explainable reasoning

to make data exploration more accessible, reliable, and efficient.

Rather than replacing analysts, DataSage is intended to amplify their productivity and reduce the friction involved in answering everyday business questions.

---

# Repository Status

This repository represents an active work-in-progress project.

Expect:

* Frequent architecture changes
* Ongoing refactoring
* Experimental features
* Accuracy improvements
* Breaking changes between versions

Feedback, testing, and contributions are welcome.

---

## Author

**Raksha Sinha**


Building DataSage as an experiment in combining conversational AI with deterministic data analytics.
