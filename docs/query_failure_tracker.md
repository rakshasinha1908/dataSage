| ID    | Category                | Example                                    | Root Cause                                                                  | Priority  | Status |
| ----- | ----------------------- | ------------------------------------------ | --------------------------------------------------------------------------- | --------- | ------ |
| DS-01 | Filter                  | Show female patients                       | Value→Column inference missing                                              | 🔴 High   | ⏳      |
| DS-02 | Ranking                 | Top 5 oldest patients                      | RankingAnalytics incomplete                                                 | 🔴 High   | ⏳      |
| DS-03 | Sort                    | Sort by age                                | Sort parsing missing                                                        | 🔴 High   | ⏳      |
| DS-04 | Query Decomposition     | Average cost for female patients           | Entire phrase sent to ColumnMatcher instead of separating measure & filters | 🔴 High   | ⏳      |
| DS-05 | Multi-filter Queries    | Average cost of female cancer patients     | Multiple filters not extracted independently                                | 🔴 High   | ⏳      |
| DS-06 | Filter Value Mapping    | Recovered patients                         | Values cannot infer owning column (Recovered → Outcome)                     | 🔴 High   | ⏳      |
| DS-07 | Numeric Filters         | Patients older than 60                     | Comparison operators not converted into filter expressions                  | 🔴 High   | ⏳      |
| DS-08 | Context-aware Analytics | Average stay for stroke patients           | Domain values treated as column names                                       | 🔴 High   | ⏳      |
| DS-09 | Dataset Understanding   | Summarize this dataset                     | Routed to analytics instead of Dataset AI                                   | 🔴 High   | ⏳      |
| DS-10 | Dataset Understanding   | Tell me about this dataset                 | Missing IntentClassifier                                                    | 🔴 High   | ⏳      |
| DS-11 | Dataset Understanding   | What information does this dataset contain | Missing IntentClassifier                                                    | 🔴 High   | ⏳      |
| DS-12 | Insight Routing         | Explain this result                        | Insight queries reaching analytics                                          | 🔴 High   | ⏳      |
| DS-13 | Insight Routing         | Why is cancer maximum                      | Insight routing missing                                                     | 🔴 High   | ⏳      |
| DS-14 | Insight Context         | What does this suggest                     | Previous analytical result not reused                                       | 🟠 Medium | ⏳      |
| DS-15 | Pattern Discovery       | What patterns do you observe               | Routed to analytics instead of Insight Engine                               | 🟠 Medium | ⏳      |
| DS-16 | Recommendations         | Any recommendations                        | Recommendation engine not routed                                            | 🟠 Medium | ⏳      |
| DS-17 | Invalid Queries         | Average banana                             | Error message should suggest available columns                              | 🟢 Low    | ⏳      |
| DS-18 | Conversation Context    | Explain this result                        | Previous query/result memory not used                                       | 🟠 Medium | ⏳      |
