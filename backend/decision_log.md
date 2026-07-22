# DataSage V2 Decision Log

> "Good architecture is a series of conscious decisions."

This document records the major engineering decisions made during the development of DataSage V2.

The purpose of this log is to preserve **context**, not implementation.

Whenever a significant architectural decision is made, record:

- What was decided.
- Why it was decided.
- Alternatives considered.
- Consequences of the decision.

If a future decision replaces an earlier one, create a new entry instead of modifying the original.

---

# ADR-001

## Date

2026-07-22

## Title

DataSage will use QueryPlan as the contract between Query Understanding and Analytics.

## Status

✅ Accepted

## Context

Natural language is ambiguous and should not propagate throughout the backend.

Allowing downstream components to inspect user queries creates tight coupling between analytics and NLP.

## Decision

All natural language will be converted into a structured QueryPlan before analytics begins.

Every subsystem after Query Understanding will consume only QueryPlan.

## Alternatives Considered

- Pass the original user question throughout the backend.
- Allow individual modules to re-parse the question.

Rejected because they duplicate logic and tightly couple components.

## Consequences

Advantages

- Clear separation of concerns.
- Easier testing.
- Deterministic execution.
- Easier future extensions.

Trade-offs

- QueryPlan becomes a critical model that must remain well-designed.

---

# ADR-002

## Date

2026-07-22

## Title

The backend must remain completely dataset agnostic.

## Status

✅ Accepted

## Context

DataSage should work for arbitrary structured datasets.

Embedding business-specific logic would reduce generality.

## Decision

The backend will never contain:

- hardcoded column names
- business terminology
- customer-specific rules
- dataset-specific heuristics

Everything must be inferred from schema and metadata.

## Alternatives Considered

Dataset-specific adapters.

Rejected because they reduce portability.

## Consequences

Advantages

- Generic architecture.
- Easier maintenance.
- Better scalability.

Trade-offs

- Query understanding becomes more challenging.

---

# ADR-003

## Date

2026-07-22

## Title

Execution must remain deterministic.

## Status

✅ Accepted

## Context

LLMs are useful for understanding language but unsuitable for deterministic analytics.

## Decision

Natural language understanding may use AI.

Analytics execution will always remain deterministic.

The same QueryPlan must always produce the same result.

## Consequences

Predictable behaviour.

Reliable testing.

Repeatable analytics.

---

# ADR-004

## Date

2026-07-22

## Title

Deployment takes priority over feature expansion.

## Status

✅ Accepted

## Context

The project experienced scope creep during frontend integration.

New ideas repeatedly delayed deployment.

## Decision

Only work that directly contributes to deployment will be implemented before V2 is released.

Ideas that improve the product but are not deployment blockers will be moved to the backlog.

## Consequences

Advantages

- Faster deployment.
- Better focus.
- Reduced architecture drift.

Trade-offs

- Some desirable features will intentionally be postponed.

---

# ADR-005

## Date

2026-07-22

## Title

Every architectural layer must own exactly one responsibility.

## Status

✅ Accepted

## Context

As the project grew, there was a risk of parsers, validators, and executors taking on overlapping responsibilities.

## Decision

Whenever a component begins solving multiple unrelated problems, introduce a new layer rather than expanding its responsibilities.

## Consequences

Advantages

- Clear module boundaries.
- Easier debugging.
- Better long-term maintainability.

Trade-offs

- Slightly more files and abstractions.

---

# ADR-006

## Date

2026-07-22

## Title

DataSage V2 enters Stabilization Phase.

## Status

✅ Accepted

## Context

The core architecture is complete.

Recent work has focused on patching edge cases instead of systematically improving the system.

## Decision

The engineering focus shifts from feature development to stabilization.

Current priorities are:

1. Query Understanding
2. Validation
3. Regression Testing
4. Frontend Integration
5. Deployment

No new features will be introduced before deployment.

## Consequences

Advantages

- Clear engineering direction.
- Reduced context switching.
- Higher confidence before release.

Trade-offs

- Nice-to-have improvements will wait until V2.1.

---

# Future Decisions

Every new architectural decision should follow the same template.

Older decisions should never be modified.

Instead, create a new ADR that supersedes the previous one.

The goal is to preserve the reasoning behind the evolution of the system.


---

# Architecture Observations

These are observations discovered during architecture reviews.

An observation is **not** a decision.

Observations help identify weaknesses in the current design and may eventually lead to an ADR.

---

## OBS-001

### Date

2026-07-22

### Observation

Current parsers communicate by progressively removing text (`cleaned_text`).

This makes the pipeline destructive: once information is consumed, downstream stages cannot reason about it.

Before changing anything, we need to determine whether this design is intentional or whether QueryUnderstanding should orchestrate parser outputs without relying solely on destructive text mutation.

### Status

Open

## OBS-002

### Date

2026-07-22

### Observation

QueryPlan currently models execution-oriented fields such as `operation` and `target_column`.

Some analytical questions (for example "Top 5 categories by transaction amount") do not map cleanly to this representation.

Before introducing new parsers or heuristics, evaluate whether QueryPlan fully captures analytical intent or whether multiple user intents are being forced into the current structure.

### Status

Open


## OBS-003

### Date

2026-07-22

### Observation

`OperationParser` currently identifies multiple unrelated concepts under the single field `operation`.

These include:

- analytical aggregations (sum, average, count)
- metadata requests (schema, columns)
- dataset preview (top rows, bottom rows)
- row retrieval (show rows)

Although this works functionally, the field currently represents multiple semantic meanings.

Before introducing additional parsing logic, evaluate whether these concepts should continue sharing the same abstraction.

### Status

Open


## OBS-004

### Date

2026-07-22

### Observation

DimensionParser currently performs both parsing and schema resolution.

It identifies grouping expressions and immediately resolves them into dataset columns using ColumnMatcher.

This couples language parsing with schema interpretation and makes it difficult to reason about grouping semantics independently.

### Status

Open

## OBS-005

### Date

2026-07-22

### Observation

IntentValidator validates only the operation and matched target column.

Some analytical requests depend on relationships between multiple parsed entities (for example, grouping dimensions, measures, and ranking), which are not currently available during validation.

The validator itself appears appropriately scoped, but its inputs may be insufficient for validating more complex analytical queries.

### Status

Open


## OBS-006

Some analytical queries omit the aggregation operation.

Example:

Top 5 categories by transaction amount

Users expect the system to infer a default aggregation (typically SUM) when ranking groups by a numeric measure.

Currently QueryPlan reaches execution with operation=None.

