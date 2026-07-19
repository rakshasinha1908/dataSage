# DataSage V2 Architecture

## Philosophy

DataSage is built around one simple idea:

> Understand the user's intent first. Execute it second.

The backend is divided into independent subsystems, where every subsystem has exactly one responsibility.

Instead of executing directly from natural language, DataSage first converts every user query into a structured **QueryPlan**. The QueryPlan acts as the contract between query understanding and analytics execution.

This separation keeps the system generic, scalable, and independent of any specific dataset.

---

# System Flow

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

---

# Backend Subsystems

## 1. Query Understanding

### Responsibility

Convert natural language into a structured QueryPlan.

### Owns

- Query normalization
- Operation extraction
- Condition extraction
- Ranking extraction
- Dimension extraction
- Column matching

### Does NOT Own

- Analytics execution
- Response formatting
- Visualization
- Session management

---

## 2. QueryPlan

### Responsibility

Represent the complete analytical intent of the user.

Every subsystem after Query Understanding works only with QueryPlan instead of the original natural language question.

QueryPlan acts as the shared language between the NLP layer and the analytics layer.

---

## 3. Intent Validation

### Responsibility

Validate whether the generated QueryPlan is logically valid.

Examples include:

- Missing target column
- Invalid aggregation
- Unsupported operations
- Invalid combinations of dimensions and measures

Validation should never execute analytics.

---

## 4. Analytics Engine

### Responsibility

Execute deterministic analytical operations.

Owns

- Filtering
- Aggregation
- Grouping
- Ranking
- Dataset preview
- Metadata generation

Does NOT own

- Natural language understanding
- Column matching
- Response formatting

---

## 5. Visualization Selector

### Responsibility

Choose the most appropriate visualization for the analytical result.

It decides *how* the result should be presented, not *what* the result is.

---

## 6. Response Builder

### Responsibility

Convert analytical results into a frontend-friendly response format.

Owns

- Final response structure
- Human-readable summaries
- Visualization payloads

---

# Core Design Principles

## 1. DataSage never knows the dataset.

The backend must never contain hardcoded knowledge about any dataset.

Forbidden examples:

- Specific column names
- Business-specific terminology
- Dataset-specific rules
- Customer-specific assumptions

Everything should work only from schema inference.

---

## 2. Every module has one responsibility.

Each module should solve one problem only.

If a module begins solving multiple unrelated problems, it should be split into smaller components.

---

## 3. QueryPlan is the source of truth.

Once a QueryPlan has been created, no downstream component should inspect the original user question.

Analytics should operate only on structured intent.

---

## 4. Prefer abstractions over condition chains.

Long if/elif blocks should eventually become registries or strategy-based implementations.

Adding new functionality should require extending the system rather than modifying unrelated code.

---

## 5. Keep components dataset agnostic.

Every parser, validator, matcher, and executor should work for any structured dataset.

The architecture should never depend on whether the dataset contains customers, products, hospitals, students, finance, or any other domain.

---

## 6. Communication happens through models.

Subsystems should communicate through strongly typed models instead of loosely coupled dictionaries or multiple independent arguments.

Examples include:

- QueryPlan
- Condition
- Ranking
- Dimension
- QueryContext

---

# Current Architecture Status

## Stable

- FastAPI application structure
- Session management
- Schema Engine
- Dataset model
- Query normalization
- Analytics execution
- Response generation

---

## Under Improvement

- Query Understanding orchestration
- Validation pipeline
- Analytics operation dispatching

---

## Planned Enhancements

- QueryUnderstanding facade
- Registry-based operation execution
- Multiple grouping dimensions
- Date operators
- BETWEEN support
- DISTINCT support
- Advanced aggregations
- Improved validation pipeline

---

# Development Philosophy

DataSage is designed with long-term maintainability in mind.

When adding a new feature, the preferred approach is to introduce the correct abstraction rather than extending existing conditional logic.

The goal is not only to make features work, but to keep the architecture clean enough that future features become easier to implement.

Every architectural decision should answer one question:

> Will this make DataSage easier to extend six months from now?

If the answer is no, the design should be reconsidered.