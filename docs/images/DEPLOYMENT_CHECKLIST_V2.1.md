# 🚀 DataSage V2.1 Deployment Checklist

Current Status: 🟡 In Progress

---

# Phase 1 — Core Functionality (Must Complete First)

## Analytics Pipeline

- [ ] Investigate why valid analytical questions sometimes route to AI.
- [ ] Ensure semantically identical analytical questions produce the same query plan.
- [ ] Improve parser robustness (e.g. "average age" vs "what is the average age").
- [ ] Verify all deterministic operations work correctly.
- [ ] Test analytical queries across multiple datasets.

---

## AI Routing

- [ ] Redesign routing philosophy.
- [ ] Dataset Description should only trigger for explicit dataset-understanding requests.
- [ ] Ensure conversational questions don't default to Dataset Description.
- [ ] Verify follow-up questions correctly use the latest analytical context.
- [ ] Prevent routing regressions.

---

## Insight Generation

- [x] Rewrite PromptBuilder.
- [ ] Test AI follow-up quality.
- [ ] Verify "Why?" questions.
- [ ] Verify "How?" questions.
- [ ] Verify recommendation questions.
- [ ] Verify comparison questions.
- [ ] Verify evaluation questions.
- [ ] Reduce repetitive AI responses.

---

## Dataset Description

- [x] Executive summary prompt.
- [ ] Improve wording.
- [ ] Make responses feel less documentation-like.
- [ ] Improve generated analytical questions.

---

# Phase 2 — Product Testing

Test every feature using multiple datasets.

Datasets:

- [ ] Healthcare
- [ ] Iris
- [ ] Sales
- [ ] Netflix
- [ ] Pokemon
- [ ] Employee Attrition
- [ ] IPL
- [ ] Cartoon Dataset

For every dataset verify:

- [ ] Dataset Overview
- [ ] Analytics
- [ ] AI Follow-up
- [ ] Charts
- [ ] Conversation Flow

---

# Phase 3 — Edge Cases

## Dataset

- [ ] Empty dataset
- [ ] Single-column dataset
- [ ] Missing values
- [ ] Duplicate columns
- [ ] Boolean-heavy dataset
- [ ] Date-heavy dataset
- [ ] Numeric-only dataset
- [ ] Text-only dataset

---

## Conversation

- [ ] No previous analysis
- [ ] Multiple follow-up questions
- [ ] Invalid analytical question
- [ ] Unsupported analytical operation
- [ ] Random conversational questions

---

# Phase 4 — UI Polish

- [ ] Improve spacing.
- [ ] Improve typography.
- [ ] Review Dataset Overview card.
- [ ] Review Insight card.
- [ ] Improve loading states.
- [ ] Improve error states.
- [ ] Remove any inconsistent labels.

---

# Phase 5 — Final QA

Run a complete end-to-end session.

Example flow:

- [ ] Upload dataset
- [ ] Understand dataset
- [ ] Ask analytical questions
- [ ] Ask follow-up questions
- [ ] Switch topics
- [ ] Verify charts
- [ ] Verify AI explanations
- [ ] Verify no crashes
- [ ] Verify no console errors

---

# Ready for Deployment

- [ ] Backend stable
- [ ] Frontend stable
- [ ] AI stable
- [ ] Analytics stable
- [ ] Manual QA complete
- [ ] Final deployment