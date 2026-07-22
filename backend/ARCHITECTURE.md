# DataSage V2 Architecture

> Architecture is not a collection of modules.
> It is a collection of decisions.

This document defines the architectural principles, system boundaries, and deployment goals for DataSage V2.

Every future change should be evaluated against this document before being implemented.

---

# Mission

DataSage is a generic analytics engine that enables users to explore structured datasets using natural language.

Given any tabular dataset, a user should be able to ask analytical questions in plain English and receive accurate results without writing SQL or code.

DataSage should never rely on dataset-specific logic.

---

# Vision for V2

DataSage V2 is **not** a chatbot.

It is **not** an LLM wrapper.

It is an analytics engine whose input happens to be natural language.

Natural language is only the interface.

The system itself should remain deterministic.

---

# Deployment Goal

A deployable V1 satisfies these requirements:

- Upload any structured CSV.
- Infer its schema automatically.
- Understand common analytical questions.
- Produce correct analytical results.
- Return appropriate visualizations.
- Operate without dataset-specific rules.

Nothing more is required for deployment.

---

# System Pipeline

```
                User Question
                      │
                      ▼
            Query Normalization
                      │
                      ▼
          Query Understanding
                      │
                      ▼
                QueryPlan
                      │
                      ▼
           Intent Validation
                      │
                      ▼
            Analytics Engine
                      │
                      ▼
       Visualization Selector
                      │
                      ▼
            Response Builder
                      │
                      ▼
                 Frontend
```

Every stage owns exactly one responsibility.

---

# Architectural Principles

## 1. QueryPlan is the contract.

Natural language exists only before QueryPlan.

After QueryPlan has been created, no downstream component should inspect the original user question.

---

## 2. Every component owns one responsibility.

Each module should solve exactly one problem.

If multiple unrelated concerns appear inside one module, introduce a new layer instead of expanding responsibilities.

---

## 3. The backend never knows the dataset.

No component may depend on:

- specific column names
- business terminology
- industry assumptions
- dataset-specific rules

Everything must be inferred from schema.

---

## 4. Execution is deterministic.

LLMs may help understand language.

Execution must always remain deterministic.

The same QueryPlan should always produce the same result.

---

## 5. Validation happens before execution.

Execution should never attempt to recover from an invalid QueryPlan.

Invalid intent should be rejected by the validation layer.

---

## 6. Models communicate between subsystems.

Subsystems exchange structured models instead of dictionaries.

Examples:

- QueryPlan
- Condition
- Ranking
- QueryResult
- Dataset
- ColumnSchema

---

# Backend Responsibilities

## Query Understanding

Responsible for converting natural language into structured intent.

Owns:

- normalization
- operation extraction
- condition extraction
- ranking extraction
- grouping extraction
- aggregation target extraction
- column matching

Does not own:

- analytics
- validation
- visualization

---

## QueryPlan

Represents analytical intent.

Every downstream subsystem consumes QueryPlan instead of raw language.

---

## Intent Validation

Ensures QueryPlan is logically executable.

Examples:

- invalid aggregation
- missing measure
- unsupported operation
- incompatible dimensions

Validation never performs analytics.

---

## Analytics Engine

Pure deterministic computation.

Responsible for:

- filtering
- grouping
- aggregation
- ranking
- sorting
- statistics

Never performs NLP.

---

## Visualization Selector

Chooses the most suitable visualization.

It never changes analytical results.

---

## Response Builder

Converts execution output into frontend-friendly responses.

Owns summaries, visualization payloads, metadata, and formatting.

---

# Current Project Status

## Stable

✅ FastAPI structure

✅ Dataset loading

✅ Schema inference

✅ Analytics execution

✅ Response generation

✅ Session management

---

## Needs Stabilization

Query Understanding

Specifically:

- semantic interpretation
- ranking understanding
- aggregation target detection
- validation

This is currently the primary engineering focus.

---

## Deferred Until After Deployment

The following ideas are intentionally postponed.

- multiple grouping dimensions
- BETWEEN
- DISTINCT
- advanced date operators
- conversational memory
- SQL export
- advanced statistical operations
- plugin architecture

These are V2.1 features.

They must not delay deployment.

---

# Definition of Done

DataSage V2 is considered deployable when:

- regression suite passes
- frontend communicates correctly
- no dataset-specific logic exists
- QueryPlan generation is stable
- validation catches invalid queries
- analytics engine produces correct results
- project is deployable through FastAPI + React

Perfection is not required.

Correctness, maintainability, and stability are.

---

# Engineering Rules

Every proposed change must answer three questions.

## 1.

Does this move us closer to deployment?

If not, postpone it.

---

## 2.

Does this solve an architectural problem instead of a single failing example?

If not, avoid patching.

---

## 3.

Can this responsibility belong to an existing component?

If not, introduce a new layer.

Otherwise, keep the architecture simple.

---

# Current Milestone

We are now in the stabilization phase.

Priority order:

1. Stabilize Query Understanding.
2. Eliminate remaining regressions.
3. Perform broad query testing.
4. Polish frontend.
5. Deploy.

No new features will be added before deployment.

---

# Final Principle

DataSage V2 is a product.

Not a research project.

Every engineering decision should move the project toward a stable, maintainable deployment.

If a change improves elegance but delays deployment, it belongs in the backlog—not in V1.