# DataSage V2 Architecture

> Architecture is not a collection of modules.
> It is a collection of decisions.

This document defines the architectural principles, system boundaries, engineering philosophy, and deployment goals for DataSage V2.

Every future change should be evaluated against this document before implementation.

---

# Mission

DataSage is a generic analytics engine that enables users to explore structured datasets using natural language.

Given any structured tabular dataset, a user should be able to ask analytical questions in plain English and receive accurate analytical results without writing SQL or code.

DataSage should never depend on dataset-specific logic.

---

# Vision

DataSage V2 is **not** a chatbot.

It is **not** an LLM wrapper.

It is an analytics engine whose interface happens to be natural language.

Natural language exists only to express analytical intent.

The system itself remains deterministic.

---

# Deployment Goal

A deployable V1 satisfies the following requirements.

- Upload any structured CSV
- Infer schema automatically
- Understand common analytical questions
- Execute analytics correctly
- Produce suitable visualizations
- Operate without dataset-specific logic
- Return structured frontend responses

Everything else belongs in future versions.

---

# High-Level System Pipeline

```
                User Question
                      │
                      ▼
            Query Normalizer
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

# Query Understanding Pipeline

The Query Understanding subsystem converts natural language into a deterministic QueryPlan.

```
User Question
      │
      ▼
QueryNormalizer
      │
      ▼
OperationParser
      │
      ▼
ConditionParser
      │
      ▼
RankingParser
      │
      ▼
RankingAnalyticsParser
      │
      ▼
DimensionParser
      │
      ▼
ColumnMatcher
      │
      ▼
QueryPlan
```

Every parser extracts one aspect of intent.

No parser performs analytics.

---

# Architectural Principles

## 1. QueryPlan is the contract.

Natural language exists only before QueryPlan.

After QueryPlan has been created, no downstream component should inspect the original question.

---

## 2. Every component owns one responsibility.

Each module should solve exactly one problem.

When responsibilities begin to overlap, introduce a new layer instead of expanding an existing one.

---

## 3. The backend never knows the dataset.

No component may depend on

- column names
- business terminology
- dataset type
- industry assumptions
- hardcoded rules

Everything must be inferred from schema.

---

## 4. Execution is deterministic.

Natural language understanding may evolve.

Execution must remain deterministic.

The same QueryPlan must always produce the same analytical result.

---

## 5. Validation happens before execution.

Execution should never attempt to recover from an invalid QueryPlan.

Validation rejects unsupported or logically inconsistent requests.

---

## 6. Models communicate between subsystems.

Subsystems exchange structured models rather than dictionaries.

Examples include

- QueryPlan
- Dataset
- ColumnSchema
- Condition
- Ranking
- QueryResult

---

## 7. Regression stability comes before feature velocity.

Every parser improvement must preserve existing behaviour.

Every architectural change should pass the regression suite before being merged.

Bug fixes should improve general behaviour rather than introduce dataset-specific patches.

---

## 8. Genericity is measured by behaviour.

The absence of dataset-specific code is not sufficient.

The same query should behave correctly across unrelated datasets.

Generic behaviour is validated through cross-domain regression testing.

---

# Backend Responsibilities

## Query Understanding

Responsible for converting natural language into structured analytical intent.

Owns

- normalization
- operation extraction
- condition extraction
- ranking extraction
- grouping extraction
- aggregation target extraction
- column matching

Does not own

- analytics
- validation
- visualization

---

## QueryPlan

Represents analytical intent.

Every downstream subsystem consumes QueryPlan rather than raw language.

---

## Intent Validation

Ensures QueryPlan is logically executable.

Examples

- invalid aggregation
- unsupported operation
- incompatible dimensions
- missing measure

Validation never performs analytics.

---

## Analytics Engine

Pure deterministic computation.

Responsible for

- filtering
- grouping
- aggregation
- sorting
- ranking
- descriptive statistics

Never performs NLP.

---

## Visualization Selector

Chooses the most appropriate visualization.

It never changes analytical results.

---

## Response Builder

Converts analytical output into frontend-friendly responses.

Responsible for

- summaries
- visualization payloads
- metadata
- formatting

---

# Current Project Status

## Stable

✅ FastAPI application

✅ Session management

✅ Dataset loading

✅ Schema inference

✅ Query normalization

✅ Query understanding

✅ QueryPlan generation

✅ Intent validation

✅ Analytics engine

✅ Response generation

✅ Cross-dataset regression suite

---

## Current Engineering Focus

- Frontend integration
- Visualization refinement
- User experience
- Deployment readiness
- Documentation

---

# Deferred Until V2.1

The following ideas are intentionally postponed.

- Multiple grouping dimensions
- BETWEEN operator
- DISTINCT
- Advanced date operations
- Conversational memory
- SQL export
- Plugin architecture
- Advanced statistical analysis

These features must not delay deployment.

---

# Definition of Done

DataSage V2 is considered deployable when

- regression suite passes
- frontend is fully integrated
- backend contains no dataset-specific logic
- QueryPlan generation is stable
- validation catches invalid requests
- analytics engine produces correct results
- visualizations render correctly
- application is deployable through FastAPI + React

Perfection is not required.

Correctness, maintainability, and stability are.

---

# Engineering Rules

Every proposed change should answer three questions.

## 1.

Does this move the product closer to deployment?

If not, postpone it.

---

## 2.

Does this solve an architectural problem instead of a single example?

If not, avoid patching.

---

## 3.

Does this responsibility belong to an existing component?

If yes, extend that component.

If not, introduce a new layer.

Keep the architecture simple.

---

# Engineering Philosophy

Prefer small, isolated changes.

When a regression appears

1. Identify the component that owns the responsibility.
2. Fix only that component.
3. Validate against the regression suite.

Correct architecture reduces the number of files required for each fix.

---

# Current Milestone

The backend architecture is now considered stable.

The remaining work focuses on transforming the engine into a deployable product.

Priority

1. Freeze backend architecture.
2. Complete frontend integration.
3. Improve visualization quality.
4. Polish user experience.
5. Expand regression coverage.
6. Deploy V1.

---

# Final Principle

DataSage V2 is a product.

Not a research project.

Every engineering decision should move the project toward a stable, maintainable deployment.

If a change improves elegance but delays deployment, it belongs in the backlog—not in V1.