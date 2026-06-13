from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Literal

@dataclass
class AggregationSpec:
    operation: Literal["sum","avg","count","min","max","pct","stddev","median"] = "sum"
    column: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
    

@dataclass
class QueryPlan:
    query_type:       Literal["ranking","aggregation","comparison","trend",
                              "distribution","correlation","raw_retrieval",
                              "explanation","kpi"] = "explanation"
    operation: Optional[str] = None
    metric_column:    Optional[str]           = None
    aggregation:      Optional[AggregationSpec] = None
    group_by_column:  Optional[str]           = None
    filters:          Dict[str, Any]          = field(default_factory=dict)
    sort_by:          Optional[str]           = None
    sort_order:       Literal["asc","desc"]   = "desc"
    limit:            int                     = 5
    visualization:    Optional[str]           = None
    execution_mode:   Optional[str]           = None
    relevant_columns: List[str]               = field(default_factory=list)
    roles: Dict[str, Any]                     = field(default_factory=dict)
    confidence:       float                   = 0.0
    is_followup:      bool                    = False
    raw_query:        str                     = ""
    clarification_needed: bool                = False
    clarification_reason: str                 = ""
    # FIX #18: context inheritance
    inherited_filters:  Dict[str, Any]        = field(default_factory=dict)
    inherited_entity:   Optional[str]         = None
    inherited_metric:   Optional[str]         = None
    # FIX #17: ambiguity
    is_ambiguous:       bool                  = False
    ambiguity_reason:   str                   = ""
    # FIX #20: repaired query
    repaired_query:     Optional[str]         = None
    # TIME-SERIES: Granularity storage & inference
    temporal_granularity: Optional[str]       = None  # Y, Q, M, W, D (period)
    temporal_column:    Optional[str]         = None  # The date/time column used
    # private routing extras (excluded from to_dict)
    _cat_dist_col:      Optional[str]         = field(default=None, repr=False)
    _is_count:          bool                  = field(default=False, repr=False)
    _sort_by_date_desc: bool                  = field(default=False, repr=False)
    _comparison_cols:   List[str]             = field(default_factory=list, repr=False)

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.aggregation:
            d["aggregation"] = self.aggregation.to_dict()
        for k in ["_cat_dist_col","_is_count","_sort_by_date_desc","_comparison_cols"]:
            d.pop(k, None)
        return d


@dataclass
class QueryResolution:
    """Multi-stage query resolution result with explicit stage outputs."""
    intent: str                          # Stage 1: detected intent (trend, aggregation, etc.)
    operations: List[str]                # Stage 2: detected operations (sum, group_by, filter, etc.)
    semantic_mapping: Dict[str, str]     # Stage 3: query term → column mapping (e.g., "sales" → "revenue")
    filters: Dict[str, Any]              # Stage 4: extracted constraints (value/range filters)
    execution_plan: Optional[QueryPlan]  # Stage 5: final QueryPlan for execution
    confidence: float                    # Overall confidence score (0.0-1.0)
    resolution_score: float              # Quality of resolution (0.0-1.0)
    issues: List[str]                   # Any ambiguities or concerns discovered
    metadata: Dict[str, Any]             # Additional debug/resolution info

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "operations": self.operations,
            "semantic_mapping": self.semantic_mapping,
            "filters": self.filters,
            "confidence": self.confidence,
            "resolution_score": self.resolution_score,
            "issues": self.issues,
            "metadata": self.metadata
        }


@dataclass
class SemanticMatch:
    """Result of semantic matching with ranked candidates."""
    query_term: str
    column_name: str
    score: float                        # 0.0-1.0 confidence
    match_type: str                     # exact, synonym, semantic, heuristic
    explanation: str                    # Why this match


