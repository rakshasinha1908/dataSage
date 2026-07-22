# DataSage V2 Roadmap

> "A roadmap is a list of promises we make to ourselves."

This document tracks everything required before DataSage V2 reaches production.

If a task is not listed here, it should not delay deployment.

---

# Current Milestone

🎯 Target: Deploy DataSage V2 within one week.

Current Phase:

➡️ Stabilization

Goal:

Transform DataSage from a working prototype into a reliable product.

No new features.

No architecture experiments.

No premature optimizations.

---

# Definition of Done

DataSage V2 is considered deployable when all of the following are true.

## Backend

- [ ] Regression suite passes
- [ ] Query understanding is stable
- [ ] Validation catches invalid analytical requests
- [ ] Analytics engine behaves deterministically
- [ ] No dataset-specific logic exists

---

## Frontend

- [ ] Dataset upload works
- [ ] Chat interface is stable
- [ ] Visualizations render correctly
- [ ] Error handling is polished
- [ ] Loading states are polished

---

## Infrastructure

- [ ] Environment configuration
- [ ] Production build
- [ ] Deployment
- [ ] Public URL

---

# Backend Roadmap

---

## Phase 1 — Query Understanding Stabilization

Priority:

🔴 Critical

This is currently the weakest subsystem.

Goal:

Produce a correct QueryPlan for common analytical questions.

Tasks:

- [ ] Ranking semantics
- [ ] Aggregation target detection
- [ ] Grouping detection
- [ ] Measure detection
- [ ] Improve validation before execution

Exit Criteria:

Regression suite passes consistently.

---

## Phase 2 — Validation

Priority:

🔴 Critical

Tasks:

- [ ] Invalid aggregations
- [ ] Missing target columns
- [ ] Unsupported combinations
- [ ] Better user-facing errors

Exit Criteria:

Invalid queries never reach Analytics Engine.

---

## Phase 3 — Analytics

Priority:

🟡 High

Tasks:

- [ ] Regression testing
- [ ] Cross-dataset testing
- [ ] Edge case verification

Exit Criteria:

Analytics produces deterministic results.

---

## Phase 4 — Frontend Integration

Priority:

🟡 High

Tasks:

- [ ] Upload flow
- [ ] Chat responses
- [ ] Charts
- [ ] Error handling
- [ ] Empty states

---

## Phase 5 — Deployment

Priority:

🟢 Final

Tasks:

- [ ] Environment variables
- [ ] Production build
- [ ] Deploy backend
- [ ] Deploy frontend
- [ ] Smoke testing

---

# Backlog (Not Blocking Deployment)

These ideas are intentionally postponed.

## Query Understanding

- [ ] Multiple grouping dimensions
- [ ] DISTINCT
- [ ] BETWEEN
- [ ] Advanced date operators

---

## Analytics

- [ ] Advanced statistics
- [ ] Window functions
- [ ] Forecasting

---

## Product

- [ ] Saved queries
- [ ] Dashboard mode
- [ ] Export improvements
- [ ] User accounts

---

# Engineering Rules

Every code change must satisfy at least one roadmap item.

If it doesn't, it belongs in the backlog.

---

# Daily Workflow

Before writing code:

1. Pick exactly one roadmap task.
2. Finish it completely.
3. Test it.
4. Commit it.
5. Move to the next task.

Never work on two roadmap items simultaneously.

---

# Success Metrics

Deployment is more important than perfection.

A feature is complete when it is:

- Correct
- Generic
- Maintainable
- Tested

—not when every imaginable edge case has been solved.

---

# Progress

Overall Progress:

🟩🟩🟩🟩🟩🟩🟩⬜⬜⬜ 70%

Current Focus:

➡️ Query Understanding Stabilization

Next Milestone:

Regression Suite: 45 / 45

Final Milestone:

🚀 Public Deployment