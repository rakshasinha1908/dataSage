# DataSage V1 — Regression Test Specification

This document defines the expected behaviour of DataSage V1.

The purpose of regression testing is to verify existing functionality
before deployment.

A failed test does NOT automatically justify adding new parser logic.

Failures must first be classified as:

- BUG — existing supported behaviour is incorrect
- REGRESSION — previously working behaviour has broken
- LIMITATION — reasonable natural-language variation not supported in V1
- FUTURE — capability intentionally deferred beyond V1


# ============================================================
# MILESTONE 0 — FOUNDATION
# ============================================================

## F01 — CSV Upload

Expected:
- Valid CSV uploads successfully
- Dataset session is created
- Dataset remains accessible through session ID


## F02 — Schema Detection

Test with:
- hospital dataset
- sales dataset
- cartoon dataset
- flower dataset

Expected:
- All columns detected
- Numeric columns identified correctly
- Categorical columns identified correctly
- Boolean columns identified correctly when present
- Sample values generated
- Aliases generated without dataset-specific hardcoding


## F03 — Dataset Independence

Expected:
The analytics architecture must work across datasets without
dataset-specific column names or business-domain rules.


# ============================================================
# MILESTONE 1 — ANALYTICS ENGINE
# ============================================================

## A01 — Basic Aggregations

Queries:

average height
sum height
maximum height
minimum height

Expected:
- Correct operation detected
- Correct target column detected
- Scalar result returned


## A02 — Count

Examples:

count patients
count viewers
count species

Expected:
- COUNT operation
- Correct row count / entity interpretation
- No unnecessary target measure


## A03 — Numeric Filters

Queries:

average cost for age > 40
average cost for age < 40
average cost for age >= 40
average cost for age <= 40

Natural-language variants:

average cost for age greater than 40
average cost for age above 40
average cost for age over 40
average cost for age less than 40
average cost for age below 40
average cost for age under 40
average cost for age at least 40
average cost for age at most 40
average cost for age equals 40

Expected:
- Correct numeric column
- Correct operator
- Correct numeric value
- Correct aggregation


## A04 — Categorical Filters

Examples:

average height for roses
show rows where species is rose
show rows where fragrance is mild
average viewing time where city is hyderabad

Expected:
- Correct categorical column
- Correct categorical value
- Filter applied before analytics


## A05 — Multiple Filters

Example:

show species with height < 150 and fragrance strong

Expected:
- Both conditions parsed
- Conditions use AND semantics
- Matching rows returned


## A06 — Zero Matching Rows

Example:

show species with height > 150 and fragrance strong

Expected:
- No backend crash
- HTTP request completes normally
- Structured failure returned
- Helpful message such as:

  "No records match the specified filters."


## A07 — Grouped Analytics

Queries:

average height by species
average height by fragrance
average viewing time by city
average viewing time by favorite cartoon
average cost by condition

Expected:
- Correct target measure
- Correct grouping dimension
- Correct aggregation
- One result per group


## A08 — Grouped Count

Examples:

count species by size
count viewers by city
count patients by outcome

Expected:
- COUNT operation
- Correct grouping dimension
- Group counts returned


## A09 — Ranking

Examples:

top 5 species by height
bottom 5 fragrances by height
top 5 cities by viewing time
top 5 conditions by cost

Expected:
- Ranking detected
- Correct direction
- Correct limit
- Correct dimension
- Correct measure


## A10 — Singular Ranking

Example:

which cartoon has the highest average viewing time?

Expected:
- MEAN operation
- Viewing Time target
- Favorite Cartoon dimension
- DESC ranking
- limit = 1
- Only highest result returned


## A11 — Row Retrieval

Queries:

show rows
show me rows
display rows
list rows
show 10 rows
show all rows

Expected:
- SHOW_ROWS operation
- Correct preview behaviour
- Explicit limits respected
- No accidental aggregation


## A12 — Dataset Preview

Queries:

top 10 rows
bottom 10 rows
first 15 rows
last 20 rows

Expected:
- Correct HEAD / TAIL semantics
- Correct requested limit


## A13 — Unknown Concepts

Example:

count flowers by size

For a dataset where "flower" cannot be resolved from schema:

Expected:
- Do not hallucinate a column
- Do not guess dataset semantics
- Return helpful validation error


## A14 — Invalid Aggregation

Examples:

average fragrance
sum species
average viewer name

Expected:
- Query rejected when operation is incompatible with column type
- Helpful error
- No server crash


# ============================================================
# MILESTONE 2 — VISUALIZATION ENGINE
# ============================================================

## V01 — Grouped Numeric Analytics

Example:

average height by species

Expected:
- Structured table
- Chart generated automatically
- Chart labels correspond to species
- Chart values correspond to analytical result


## V02 — Ranked Analytics

Example:

top 3 species by height

Expected:
- Chart reflects ranked subset
- Table and chart contain the same groups
- Correct ordering


## V03 — Singular Ranking

Example:

which species has the highest average height?

Expected:
- Single result
- Visualization must not reintroduce excluded groups


## V04 — Scalar Analytics

Example:

average height

Expected:
- KPI-style response
- No unnecessary grouped chart


## V05 — Table Fallback

Expected:
If a meaningful visualization is not appropriate,
DataSage must still return a usable structured result.


# ============================================================
# MILESTONE 3 — AI ENGINE
# ============================================================

## AI01 — Dataset Description

Query:

describe this dataset

Expected:
- DATASET_DESCRIPTION route
- AI-generated overview
- Description grounded in actual schema


## AI02 — Dataset Contents

Queries:

what does this dataset contain?
what information is in this dataset?

Expected:
- DATASET_DESCRIPTION route
- Explanation of available information


## AI03 — Exploration Suggestions

Queries:

what can I analyze?
what should I analyze next?
what can I explore?

Expected:
- DATASET_DESCRIPTION route
- Suggestions grounded in available columns
- No invented fields


## AI04 — Result Explanation

Prerequisite:
Run a successful analytical query first.

Example:

which cartoon has the highest average viewing time?

Follow-up:

why is it the highest?

Expected:
- INSIGHT route
- Latest verified result supplied to AI
- Explanation distinguishes evidence from hypotheses


## AI05 — Interpretation

Follow-up:

what does this suggest?

Expected:
- INSIGHT route
- Previous analytical result remembered
- Interpretation based on verified result


## AI06 — Evidence / Causality Safety

Follow-ups:

does this prove that people prefer Mickey Mouse?
can we conclude Mickey Mouse is more popular?

Expected:
- INSIGHT route
- AI must not claim unsupported causality
- AI distinguishes viewing duration from preference/popularity
- Additional evidence requirements may be explained


# ============================================================
# MILESTONE 4 — CONVERSATION
# ============================================================

V1 conversation scope is intentionally limited.

The goal is useful analytical continuity, NOT a complete
general-purpose conversational agent.


## C01 — Latest Result Memory

Sequence:

1. which cartoon has the highest average viewing time?
2. what does this suggest?

Expected:
Second query understands the latest verified analysis.


## C02 — Pronoun Follow-Up

Sequence:

1. which cartoon has the highest average viewing time?
2. why is it the highest?

Expected:
"it" refers to the latest analytical result through
the insight context.


## C03 — Contextual Interpretation

Sequence:

1. Run analytical query
2. what does this mean?

Expected:
- INSIGHT route
- No attempt to parse "this" as a dataset column


## C04 — Context Switching

Sequence:

1. Run analytical query
2. Ask explanatory follow-up
3. Ask a completely new analytical query

Expected:
- Follow-up uses previous result
- New analytical query returns to deterministic analytics


# ============================================================
# ERROR HANDLING
# ============================================================

## E01 — Unknown Column

Expected:
- Helpful validation error
- No HTTP 500


## E02 — Unknown Filter Value

Expected:
- Helpful validation error
- No fabricated match


## E03 — Zero Matching Rows

Expected:
- Structured failure response
- No