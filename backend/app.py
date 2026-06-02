from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import io
import os
import re
import requests
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from fastapi.responses import FileResponse
from typing import Optional, Dict, List, Any, Tuple, Literal
from dataclasses import dataclass, field, asdict
import hashlib
import logging
import math
from difflib import SequenceMatcher
from collections import defaultdict
from abc import ABC, abstractmethod

# ─────────────────── LOGGING ───────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────── ENV ───────────────────
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

# ─────────────────── APP ───────────────────
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────── SESSION STORAGE ───────────────────
datasets:             Dict[str, pd.DataFrame] = {}
dataset_meta:         Dict[str, dict]         = {}
ai_call_count:        Dict[str, int]          = {}
ai_response_cache:    Dict[str, str]          = {}
conversation_history: Dict[str, List[dict]]   = {}
AI_CALL_LIMIT = 30

# ═══════════════════════════════════════════════════════════════════════════════
# IMPROVEMENTS #1, #4, #20, #22, #23: UNIFIED RESPONSE SCHEMA & OBSERVABILITY
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class QueryExecutionMetrics:
    """Tracks execution statistics and reliability metrics."""
    query_received_ms: int = 0
    resolution_ms: int = 0
    execution_ms: int = 0
    total_ms: int = 0
    execution_type: str = "unknown"  # deterministic, llm_based, retrieval
    ai_calls_used: int = 0
    confidence_score: float = 0.0
    resolution_score: float = 0.0
    cache_hit: bool = False
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class UnifiedResponse:
    """Standardized response schema for all endpoints."""
    status: Literal["success", "error", "warning", "clarification", "fallback"] = "success"
    message: str = ""
    query_type: Optional[str] = None
    query_processed: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    metrics: Optional[QueryExecutionMetrics] = None
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    debug: Optional[Dict[str, Any]] = None  # Improvement #21: Debug mode data
    
    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "message": self.message,
            "query_type": self.query_type,
            "query_processed": self.query_processed,
            "data": self.data,
            "metadata": self.metadata,
            "confidence": round(self.confidence, 2),
            "metrics": self.metrics.to_dict() if self.metrics else None,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "debug": self.debug if self.debug else None,
        }


class QueryLogger:
    """Improvement #20: Structured query logging for debugging and optimization."""
    
    @staticmethod
    def log_query_attempt(session_id: str, query: str, plan: Optional['QueryPlan'] = None):
        """Log query reception and initial planning."""
        logger.info(
            f"[QUERY] Session={session_id} | Query='{query[:60]}' | "
            f"PlanType={plan.query_type if plan else 'none'} | "
            f"MetricCol={plan.metric_column if plan else 'none'}"
        )
    
    @staticmethod
    def log_resolution_stage(session_id: str, stage: int, intent: str, confidence: float):
        """Log resolution pipeline progress."""
        logger.info(
            f"[RESOLUTION] Session={session_id} | Stage={stage} | "
            f"Intent={intent} | Confidence={confidence:.2f}"
        )
    
    @staticmethod
    def log_execution_start(session_id: str, query_type: str, execution_mode: str):
        """Log execution pipeline start."""
        logger.info(
            f"[EXECUTE_START] Session={session_id} | Type={query_type} | "
            f"Mode={execution_mode}"
        )
    
    @staticmethod
    def log_execution_result(session_id: str, query_type: str, status: str, 
                            rows: int, ms: int):
        """Log execution completion."""
        logger.info(
            f"[EXECUTE_RESULT] Session={session_id} | Type={query_type} | "
            f"Status={status} | Rows={rows} | Ms={ms}"
        )
    
    @staticmethod
    def log_validation_failure(session_id: str, validation_type: str, reason: str):
        """Log validation failures."""
        logger.warning(
            f"[VALIDATION_FAIL] Session={session_id} | Type={validation_type} | "
            f"Reason={reason}"
        )
    
    @staticmethod
    def log_error(session_id: str, error_type: str, message: str):
        """Log errors."""
        logger.error(
            f"[ERROR] Session={session_id} | Type={error_type} | Message={message}"
        )


class ExecutionMetricsTracker:
    """Improvement #22: Track execution reliability metrics."""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: {
            "total_queries": 0,
            "successful": 0,
            "empty_results": 0,
            "unsupported": 0,
            "errors": 0,
            "cache_hits": 0,
            "avg_ms": 0,
            "total_ms": 0
        })
    
    def record_success(self, query_type: str, ms: int, cache_hit: bool = False):
        """Record successful query execution."""
        m = self.metrics[query_type]
        m["total_queries"] += 1
        m["successful"] += 1
        m["total_ms"] += ms
        m["avg_ms"] = m["total_ms"] / m["successful"]
        if cache_hit:
            m["cache_hits"] += 1
    
    def record_empty(self, query_type: str):
        """Record empty result."""
        m = self.metrics[query_type]
        m["total_queries"] += 1
        m["empty_results"] += 1
    
    def record_unsupported(self, query_type: str):
        """Record unsupported query type."""
        m = self.metrics[query_type]
        m["total_queries"] += 1
        m["unsupported"] += 1
    
    def record_error(self, query_type: str):
        """Record execution error."""
        m = self.metrics[query_type]
        m["total_queries"] += 1
        m["errors"] += 1
    
    def get_stats(self) -> dict:
        """Get reliability statistics."""
        return dict(self.metrics)


metrics_tracker = ExecutionMetricsTracker()


def sanitize_for_json(obj):
    """Recursively sanitize an object for JSON serialization.
    Converts NaN/Infinity to None, numpy types to native Python types,
    pandas Timestamps to ISO strings, and handles nested dicts/lists.
    """
    if obj is None:
        return None
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        val = float(obj)
        return None if math.isnan(val) or math.isinf(val) else val
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())
    if isinstance(obj, pd.Timestamp):
        return None if pd.isna(obj) else obj.isoformat()
    if isinstance(obj, pd.Timedelta):
        return None if pd.isna(obj) else str(obj)
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(v) for v in obj]
    try:
        if pd.isna(obj):
            return None
    except (TypeError, ValueError):
        pass
    return obj

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


ID_COL_PATTERNS = re.compile(
    r'(^|[\s_\-])id($|[\s_\-])|_id$|^id_|transaction[_\s]?id|order[_\s]?id'
    r'|invoice[_\s]?id|customer[_\s]?id|product[_\s]?id|user[_\s]?id'
    r'|row[_\s]?id|record[_\s]?id|serial|uuid|guid|ref[_\s]?no|^code$|^key$|^index$',
    re.IGNORECASE
)


def is_id_like_col(col: str, series: pd.Series) -> bool:
    if not ID_COL_PATTERNS.search(col.lower().strip()):
        return False
    n_unique = series.nunique()
    n_total  = max(len(series.dropna()), 1)
    return (n_unique / n_total) > 0.7


# ═══════════════════════════════════════════════════════════════════════════════
# FIX #34: PERCENTAGE COLUMN DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def is_percentage_col(col: str, series: pd.Series) -> bool:
    col_lower = col.lower()
    pct_names = ["pct","percent","rate","ratio","share","proportion",
                 "margin","growth_rate","churn_rate","conversion"]
    if not any(p in col_lower for p in pct_names):
        return False
    s = series.dropna()
    if len(s) == 0:
        return False
    return ((s >= 0) & (s <= 100)).mean() > 0.95 or ((s >= 0) & (s <= 1)).mean() > 0.95


def classify_column_role(col: str, series: pd.Series, df: pd.DataFrame) -> str:
    col_lower = col.lower().strip()
    s         = series.dropna()
    n_unique  = s.nunique()
    n_total   = max(len(s), 1)

    if pd.api.types.is_datetime64_any_dtype(series):
        return "temporal"

    unique_vals = set(
        str(v).strip().lower()
        for v in s.unique()
    )

    boolean_patterns = {
        "true",
        "false",
        "yes",
        "no",
        "y",
        "n",
        "1",
        "0",
        "active",
        "inactive",
        "enabled",
        "disabled",
        "paid",
        "unpaid",
        "approved",
        "rejected",
        "completed",
        "cancelled"
    }

    if (
        len(unique_vals) <= 6
        and unique_vals.issubset(boolean_patterns)
    ):
        return "boolean"


    if pd.api.types.is_numeric_dtype(series):
        if is_id_like_col(col, series):
            return "identifier"
        if is_percentage_col(col, series):
            return "percentage"
        derived_hints = ["ratio","index","score","rate","factor","coefficient",
                         "multiplier","growth","change","delta","diff","var"]
        if any(h in col_lower for h in derived_hints):
            return "derived"
        return "metric"

    if is_id_like_col(col, series):
        return "identifier"

    # FIX #35: High-cardinality free text
    if n_unique > min(200, n_total * 0.5):
        return "free_text"

    return "dimension"

def normalize_boolean_value(value):

    val = str(value).strip().lower()

    true_values = {
        "true",
        "yes",
        "y",
        "1",
        "active",
        "enabled",
        "paid",
        "approved",
        "completed",
        "member",
        "subscribed",
        "successful",
        "verified",
        "applied"
    }

    false_values = {
        "false",
        "no",
        "n",
        "0",
        "inactive",
        "disabled",
        "unpaid",
        "rejected",
        "cancelled",
        "failed",
        "expired",
        "refunded"
    }

    if val in true_values:
        return True

    if val in false_values:
        return False

    return value

# ═══════════════════════════════════════════════════════════════════════════════
# IMPROVEMENTS #3, #5, #6, #7, #8, #14, #15, #16, #17, #18: VALIDATION FRAMEWORK
# ═══════════════════════════════════════════════════════════════════════════════

class QueryValidator:
    """Comprehensive validation framework for query plans and execution."""
    
    # Improvement #18: Dataset capability detection
    @staticmethod
    def detect_dataset_capabilities(df: pd.DataFrame, meta: dict) -> Dict[str, bool]:
        """Dynamically detect analytical capabilities based on dataset structure."""
        numeric_cols = set(meta.get("numeric_cols", []))
        categorical_cols = set(meta.get("categorical_cols", []))
        datetime_cols = set(meta.get("datetime_cols", []))
        
        return {
            "can_aggregate": len(numeric_cols) > 0,
            "can_rank": len(numeric_cols) > 0 and len(categorical_cols) > 0,
            "can_trend": len(datetime_cols) > 0 and len(numeric_cols) > 0,
            "can_distribute": len(categorical_cols) > 0,
            "can_compare": len(numeric_cols) >= 2,
            "can_correlate": len(numeric_cols) >= 2,
            "can_retrieve": len(df) > 0
        }
    
    # Improvement #7: Metric validation
    @staticmethod
    def validate_metric_column(metric_col: Optional[str], df: pd.DataFrame, 
                               meta: dict) -> Tuple[bool, str]:
        """Validate metric column is suitable for aggregation."""
        if not metric_col:
            return False, "No metric column specified"
        
        if metric_col not in df.columns:
            return False, f"Metric column '{metric_col}' not found in dataset"
        
        # Improvement #6: Don't allow forced fallbacks - be strict
        numeric_cols = set(meta.get("numeric_cols", []))
        if metric_col not in numeric_cols:
            return False, f"Column '{metric_col}' is not numeric and cannot be aggregated"
        
        # Check for high-cardinality identifiers
        if "identifier" in str(meta.get("column_roles", {}).get(metric_col, "")):
            return False, f"Cannot aggregate identifier column '{metric_col}'"
        
        return True, ""
    
    # Improvement #8: Group-by validation
    @staticmethod
    def validate_group_by_column(groupby_col: Optional[str], df: pd.DataFrame, 
                                 meta: dict) -> Tuple[bool, str]:
        """Validate group-by column is suitable for grouping."""
        if not groupby_col:
            return True, ""  # Optional grouping is OK
        
        if groupby_col not in df.columns:
            return False, f"Group-by column '{groupby_col}' not found in dataset"
        
        col_role = meta.get("column_roles", {}).get(groupby_col, "")
        
        # Improvement #8: Prevent grouping on identifiers
        if "identifier" in col_role:
            return False, f"Cannot group by identifier column '{groupby_col}' (too many unique values)"
        
        # Improvement #8: Prevent grouping on free-text
        if "free_text" in col_role:
            return False, f"Cannot group by free-text column '{groupby_col}' (too many unique values)"
        
        # Check cardinality
        cardinality = df[groupby_col].nunique() / max(len(df), 1)
        if cardinality > 0.8:
            return False, f"Column '{groupby_col}' has too many unique values ({df[groupby_col].nunique()}) for grouping"
        
        return True, ""
    
    # Improvement #3: Empty result detection
    @staticmethod
    def validate_non_empty_result(result_df: pd.DataFrame) -> Tuple[bool, str]:
        """Check if result is empty or too sparse."""
        if result_df.empty:
            return False, "No results found matching your query"
        
        if len(result_df) == 0:
            return False, "Query returned no rows"
        
        return True, ""
    
    # Improvement #15: Output sanity validation
    @staticmethod
    def validate_output_sanity(result_df: pd.DataFrame, plan: QueryPlan, 
                               original_row_count: int) -> Tuple[bool, str]:
        """Verify output aligns with user intent and data size."""
        
        # Check result size didn't explode (prevents cross-join accidents)
        if len(result_df) > original_row_count * 10:
            return False, "Result unexpectedly large - possible data join error"
        
        # For aggregations, should have significantly fewer rows
        if plan.query_type in ["aggregation", "kpi"] and plan.group_by_column:
            if len(result_df) > 1000:
                return False, "Aggregation result has too many groups"
        
        # For ranking, limit check
        if plan.query_type == "ranking" and len(result_df) > plan.limit + 10:
            return False, "Ranking result exceeds expected limit"
        
        # Check for all-null columns (bad aggregation)
        null_cols = result_df.columns[result_df.isnull().all()].tolist()
        if null_cols:
            return False, f"Result contains null-only columns: {null_cols}"
        
        return True, ""
    
    # Improvement #14: Visualization eligibility
    @staticmethod
    def validate_visualization_eligible(result_df: pd.DataFrame, 
                                       plan: QueryPlan) -> Tuple[bool, str]:
        """Determine if result is suitable for visualization."""
        
        if result_df.empty:
            return False, "Cannot visualize empty result"
        
        # KPI: scalar values only
        if plan.query_type == "kpi":
            if len(result_df) == 1 and len(result_df.columns) == 1:
                return True, ""
            return False, "KPI should return single value"
        
        # Trend: needs temporal dimension
        if plan.query_type == "trend":
            if len(result_df) < 2:
                return False, "Trend needs multiple data points"
            return True, ""
        
        # Distribution/ranking: needs dimension + metric
        if plan.query_type in ["distribution", "ranking"]:
            if len(result_df.columns) < 2:
                return False, "Distribution needs dimension and value"
            return True, ""
        
        return True, ""  # Others are visualizable
    
    # Improvement #5: Confidence thresholding
    @staticmethod
    def validate_confidence_threshold(confidence: float, threshold: float = 0.35) -> Tuple[bool, str]:
        """Check if confidence exceeds execution threshold."""
        if confidence < 0.15:
            return False, "Confidence too low - unable to process"
        
        if confidence < threshold:
            return False, f"Confidence {confidence:.0%} below execution threshold {threshold:.0%}"
        
        return True, ""


# Improvement #10: Ambiguity detection
class AmbiguityDetector:
    """Detect multiple equally plausible query interpretations."""
    
    @staticmethod
    def detect_ambiguous_metric(query: str, candidates: List['SemanticMatch'], 
                                df: pd.DataFrame) -> bool:
        """Check if multiple metrics are equally likely."""
        if len(candidates) < 2:
            return False
        
        # If top 2 scores are within 10%, it's ambiguous
        top_two_scores = sorted([c.score for c in candidates], reverse=True)[:2]
        if len(top_two_scores) == 2:
            score_diff = abs(top_two_scores[0] - top_two_scores[1])
            return score_diff < 0.1
        
        return False
    
    @staticmethod
    def detect_ambiguous_grouping(query: str, candidates: List['SemanticMatch']) -> bool:
        """Check if multiple grouping columns are equally likely."""
        if len(candidates) < 2:
            return False
        
        top_two_scores = sorted([c.score for c in candidates], reverse=True)[:2]
        if len(top_two_scores) == 2:
            score_diff = abs(top_two_scores[0] - top_two_scores[1])
            return score_diff < 0.1
        
        return False
    
    @staticmethod
    def detect_query_intent_ambiguity(query: str, 
                                     possible_intents: List[Tuple[str, float]]) -> bool:
        """Check if query could match multiple intent types equally."""
        if len(possible_intents) < 2:
            return False
        
        scores = [score for _, score in possible_intents]
        top_two = sorted(scores, reverse=True)[:2]
        
        if len(top_two) == 2:
            return abs(top_two[0] - top_two[1]) < 0.1
        
        return False


# Improvement #16: Enhanced schema intelligence
class SchemaIntelligence:
    """Dataset-agnostic schema understanding based on metadata and roles."""
    
    @staticmethod
    def get_best_metric_candidates(df: pd.DataFrame, meta: dict, 
                                   limit: int = 5) -> List[str]:
        """Get metrics based on role detection, not naming."""
        numeric_cols = meta.get("numeric_cols", [])
        roles = meta.get("column_roles", {})
        
        candidates = []
        for col in numeric_cols:
            role = roles.get(col, "metric")
            
            # Improvement #16: Skip identifiers and percentages at first
            if "identifier" in role or "percentage" in role:
                continue
            
            candidates.append(col)
        
        return candidates[:limit]
    
    @staticmethod
    def get_best_dimension_candidates(df: pd.DataFrame, meta: dict, 
                                     limit: int = 10) -> List[str]:
        """Get dimensions based on cardinality and role."""
        roles = meta.get("column_roles", {})
        
        candidates = []
        for col, role in roles.items():
            if any(r in role for r in ["temporal", "dimension"]):
                candidates.append(col)
        
        return candidates[:limit]
    
    @staticmethod
    def get_temporal_columns(df: pd.DataFrame, meta: dict) -> List[str]:
        """Get all temporal columns."""
        return meta.get("datetime_cols", [])


# Improvement #17: Enhanced boolean normalization  
def normalize_boolean_extended(value, column_name: str = "") -> Any:
    """Extended boolean normalization across various patterns."""
    normalized = normalize_boolean_value(value)
    
    if normalized is not value:
        return normalized  # Already normalized by basic function
    
    val_str = str(value).strip().lower()
    
    # Improvement #17: Additional patterns
    active_patterns = ["active", "enabled", "on", "approved", "paid", "verified", 
                      "completed", "success", "true", "yes", "1", "y"]
    inactive_patterns = ["inactive", "disabled", "off", "rejected", "unpaid", 
                        "cancelled", "failed", "false", "no", "0", "n"]
    
    if any(pattern in val_str for pattern in active_patterns):
        return True
    
    if any(pattern in val_str for pattern in inactive_patterns):
        return False
    
    return value


# ═══════════════════════════════════════════════════════════════════════════════
# FIX #36: SEMANTIC SYNONYM EXPANSION - Business terminology mapping
# ═════════════════════════════════════════════════════════════════════════════════
# Enables generic, dataset-independent query understanding by mapping business
# synonyms to columns. E.g., "revenue" matches "sales", "income", "amount"
# This expands query coverage without requiring dataset-specific configuration.

BUSINESS_SYNONYM_MAP: Dict[str, List[str]] = {
    # Financial Metrics
    "revenue":   ["revenue","sales","income","earnings","turnover","gross_sales",
                  "total_sales","net_sales","amount","value","total_amount",
                  "sale_amount","revenue_usd","gross_revenue","total_revenue"],
    "profit":    ["profit","margin","net_profit","net_income","ebitda",
                  "gross_profit","profit_margin","operating_income","bottom_line"],
    "cost":      ["cost","expense","cogs","expenditure","spend","spending",
                  "cost_of_goods","total_cost","unit_cost","overhead","expenses"],
    "price":     ["price","rate","unit_price","fee","charge","selling_price",
                  "list_price","cost_per_unit","avg_price","sticker_price"],
    
    # Transaction & Commerce
    "discount":  ["discount","rebate","deduction","markdown","offer","promo",
                  "promotional","reduction"],
    "quantity":  ["quantity","qty","units","volume","count","units_sold",
                  "num_units","pieces","items","stock","amount_sold"],
    "orders":    ["orders","transactions","purchases","invoices","receipts",
                  "deals","order_count","num_orders","order_number"],
    
    # Entities & Dimensions
    "customer":  ["customer","client","buyer","user","account","person",
                  "name","customer_name","client_name","consumer","shopper"],
    "employee":  ["employee","staff","worker","agent","rep","sales_rep",
                  "associate","headcount","personnel"],
    "product":   ["product","item","sku","good","service","offering",
                  "product_name","item_name","product_type","merchandise"],
    "category":  ["category","type","segment","class","group","department",
                  "kind","product_category","genre","sector","vertical"],
    
    # Time & Dates
    "date":      ["date","order_date","created_at","updated_at","timestamp",
                  "purchase_date","transaction_date","invoice_date","period",
                  "month","year","day","week","quarter"],
    
    # Geography & Location
    "region":    ["region","area","location","country","city","state",
                  "territory","zone","market","store","branch","site",
                  "district","geography","locale"],
    
    # Metrics & Scores
    "score":     ["score","rating","rank","grade","points","nps","csat",
                  "satisfaction","review","stars","rating_score"],
    "age":       ["age","tenure","duration","years","days_old","customer_age",
                  "account_age","lifetime"],
    
    # Status & State
    "status":    ["status","state","stage","phase","condition","order_status",
                  "payment_status","fulfillment","order_state"],
    "profit_margin": ["profit_margin","margin_pct","gross_margin","net_margin","margin"],
}


def build_synonyms(columns: List[str]) -> Dict[str, str]:
    """FIX #2 + #33: Synonym map with auto-generation from column tokens."""
    result: Dict[str, str] = {}
    col_lower_map = {col.lower(): col for col in columns}

    for user_term, aliases in BUSINESS_SYNONYM_MAP.items():
        for alias in aliases:
            for col_lower, col_orig in col_lower_map.items():
                if alias == col_lower or alias in col_lower or col_lower in alias:
                    result.setdefault(user_term, col_orig)
                    result.setdefault(alias, col_orig)
                    break

    # FIX #33: Auto-generate from column name tokens
    for col_lower, col_orig in col_lower_map.items():
        result.setdefault(col_lower, col_orig)
        for tok in re.split(r'[\s_\-/]+', col_lower):
            if len(tok) > 2:
                result.setdefault(tok, col_orig)
        result.setdefault(col_lower.replace("_", " "), col_orig)

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# FIX #31 + #32: DATASET INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════

def _col_stats(df: pd.DataFrame, col: str, series: pd.Series) -> dict:
    return {
        "min":    float(series.min()),
        "max":    float(series.max()),
        "mean":   float(series.mean()),
        "median": float(series.median()),
        "std":    float(series.std()),
        "nulls":  int(df[col].isna().sum()),
    }

def build_value_index(df: pd.DataFrame, meta: dict) -> Dict[str, List[dict]]:
    """
    Creates semantic lookup index from categorical column values.

    Example:
    {
        "prepaid": [
            {"column": "prepaid_order", "value": "True"}
        ],
        "bad service": [
            {"column": "comments", "value": "Bad Service"}
        ]
    }
    """

    value_index = {
        "exact_values": {},
        "token_map": defaultdict(list),
        "column_value_map": defaultdict(list),
        "boolean_aliases": {}
    }

    categorical_cols = (
        meta.get("low_cardinality_cols", [])
        + meta.get("categorical_cols", [])
        + meta.get("boolean_cols", [])
    )

    for col in categorical_cols:
        try:
            unique_values = (
                df[col]
                .dropna()
                .astype(str)
                .unique()
            )

            # Avoid gigantic columns
            if len(unique_values) > 200:
                continue

            for val in unique_values:
                val_clean = str(val).strip().lower()

                if len(val_clean) < 2:
                    continue

                entry = {
                    "column": col,
                    "value": val,
                    "normalized": val_clean,
                    "frequency": int((df[col].astype(str).str.lower() == val_clean).sum())
                }

                # ─────────────────────────────
                # Exact value index
                # ─────────────────────────────
                value_index["exact_values"].setdefault(
                    val_clean,
                    []
                ).append(entry)

                # ─────────────────────────────
                # Token index
                # ─────────────────────────────
                tokens = [
                    t for t in re.split(r'[\s_\-/]+', val_clean)
                    if len(t) > 1
                ]

                for token in tokens:
                    value_index["token_map"][token].append(entry)

                # ─────────────────────────────
                # Column-wise lookup
                # ─────────────────────────────
                value_index["column_value_map"][col].append(entry)

        except Exception:
            continue
    
    # ─────────────────────────────
    # Boolean semantic aliases
    # ─────────────────────────────

    boolean_aliases = {
        "true": [
            "active",
            "enabled",
            "yes",
            "paid",
            "prepaid",
            "completed",
            "member",
            "subscribed",
            "successful",
            "approved",
            "verified",
            "applied",
        ],

        "false": [
            "inactive",
            "disabled",
            "no",
            "unpaid",
            "cancelled",
            "failed",
            "rejected",
            "not applied",
            "expired",
            "refunded",
        ]
    }

    value_index["boolean_aliases"] = boolean_aliases

    return value_index

def detect_semantic_role(col: str, dtype: str) -> str:

    c = col.lower()

    # ─────────────────────────────
    # Identifier
    # ─────────────────────────────
    if any(k in c for k in [
        "id",
        "uuid",
        "code",
        "number"
    ]):
        return "identifier"

    # ─────────────────────────────
    # Temporal
    # ─────────────────────────────
    if any(k in c for k in [
        "date",
        "time",
        "year",
        "month",
        "day"
    ]):
        return "temporal"

    # ─────────────────────────────
    # Geographic
    # ─────────────────────────────
    if any(k in c for k in [
        "country",
        "state",
        "city",
        "region",
        "location",
        "area"
    ]):
        return "geographic"

    # ─────────────────────────────
    # Category
    # ─────────────────────────────
    if any(k in c for k in [
        "category",
        "segment",
        "department",
        "group",
        "type"
    ]):
        return "category"

    # ─────────────────────────────
    # Business state
    # ─────────────────────────────
    if any(k in c for k in [
        "status",
        "stage",
        "condition"
    ]):
        return "business_state"

    # ─────────────────────────────
    # Entity labels
    # ─────────────────────────────
    if any(k in c for k in [
        "name",
        "title",
        "product",
        "customer",
        "vendor",
        "employee"
    ]):
        return "entity"

    # ─────────────────────────────
    # Percentage
    # ─────────────────────────────
    if any(k in c for k in [
        "percent",
        "ratio",
        "rate"
    ]):
        return "percentage"

    # ─────────────────────────────
    # Boolean
    # ─────────────────────────────
    if dtype == "boolean":
        return "boolean"

    # ─────────────────────────────
    # Metric
    # ─────────────────────────────
    if dtype in ("int64", "float64"):
        return "metric"

    # ─────────────────────────────
    # Free text fallback
    # ─────────────────────────────
    return "free_text"

def build_schema_registry(df: pd.DataFrame, meta: dict) -> Dict[str, dict]:

    registry = {}

    for col in df.columns:

        role = meta["column_roles"].get(col)
        semantic_role = meta["semantic_roles"].get(col)

        registry[col] = {
            "role": role,
            "semantic_role": semantic_role,

            # ─────────────────────────────
            # Aggregation eligibility
            # ─────────────────────────────
            "is_aggregatable": role in (
                "metric",
                "derived",
                "percentage"
            ),

            # ─────────────────────────────
            # Grouping eligibility
            # ─────────────────────────────
            "is_groupable": role in (
                "dimension",
                "temporal"
            ),

            # ─────────────────────────────
            # High-value grouping priority
            # ─────────────────────────────
            "group_priority": (
                100 if semantic_role == "category" else
                90 if semantic_role == "geographic" else
                85 if semantic_role == "business_state" else
                80 if semantic_role == "temporal" else
                60 if semantic_role == "entity" else
                20
            )
        }

    return registry

def build_dataset_meta(df: pd.DataFrame) -> dict:
    meta: Dict[str, Any] = {
        "numeric_cols":         [],
        "categorical_cols":     [],
        "datetime_cols":        [],
        "boolean_cols":         [],
        "high_cardinality_cols":[],
        "low_cardinality_cols": [],
        "id_like_cols":         [],
        "percentage_cols":      [],
        "free_text_cols":       [],
        "derived_cols":         [],
        "column_roles":         {},
        "primary_entity_col":   None,
        "date_col":             None,
        "col_stats":            {},
        "row_count":            len(df),
        "col_count":            len(df.columns),
        "synonyms":             {},
        "semantic_roles":       {},
    }

    for col in df.columns:
        col_lower = col.lower().strip()
        series    = df[col].dropna()

        # Datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            meta["datetime_cols"].append(col)
            meta["column_roles"][col] = "temporal"
            if meta["date_col"] is None:
                meta["date_col"] = col
            continue

        # Try parsing date from object cols
        if series.dtype == object:
            date_kw = ["date","time","month","year","week","day",
                       "created","updated","timestamp","period","quarter"]
            if any(k in col_lower for k in date_kw):
                try:
                    parsed = pd.to_datetime(series, errors="coerce")
                    if parsed.notna().sum() / max(len(series), 1) > 0.7:
                        df[col] = parsed
                        meta["datetime_cols"].append(col)
                        meta["column_roles"][col] = "temporal"
                        if meta["date_col"] is None:
                            meta["date_col"] = col
                        continue
                except Exception:
                    pass

        role = classify_column_role(col, series, df)
        meta["column_roles"][col] = role
        
        semantic_role = detect_semantic_role(
            col,
            str(df[col].dtype)
        )

        meta["semantic_roles"][col] = semantic_role

        if role == "boolean":
            df[col] = df[col].apply(
                normalize_boolean_value
            )
            meta["boolean_cols"].append(col)
        elif role == "identifier":
            meta["id_like_cols"].append(col)
        elif role == "percentage":
            meta["percentage_cols"].append(col)
            meta["numeric_cols"].append(col)
            meta["col_stats"][col] = _col_stats(df, col, series)
        elif role == "derived":
            meta["derived_cols"].append(col)
            meta["numeric_cols"].append(col)
            meta["col_stats"][col] = _col_stats(df, col, series)
        elif role == "metric":
            meta["numeric_cols"].append(col)
            meta["col_stats"][col] = _col_stats(df, col, series)
        elif role == "free_text":
            meta["free_text_cols"].append(col)
            meta["high_cardinality_cols"].append(col)
        elif role == "dimension":
            meta["categorical_cols"].append(col)
            n_unique = series.nunique()
            if n_unique > 50:
                meta["high_cardinality_cols"].append(col)
            else:
                meta["low_cardinality_cols"].append(col)

    meta["primary_entity_col"] = _detect_primary_entity(df, meta)
    
    meta["synonyms"] = build_synonyms(
        df.columns.tolist()
    )
    meta["value_index"] = build_value_index(
        df, 
        meta
    )
    
    meta["schema_registry"] = build_schema_registry(
        df,
        meta
    )
    
    logger.info(
        "Schema registry built for %d columns",
        len(meta.get("schema_registry", {}))
    )

    logger.info(
        "Meta: %d rows | %d metric | %d dimension | %d temporal | "
        "%d id | %d pct | %d free_text",
        meta["row_count"], len(meta["numeric_cols"]),
        len(meta["categorical_cols"]), len(meta["datetime_cols"]),
        len(meta["id_like_cols"]), len(meta["percentage_cols"]),
        len(meta["free_text_cols"])
    )
    return meta


# ═══════════════════════════════════════════════════════════════════════════════
# FIX #43: IMPROVED DATASET UPLOAD METADATA GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def enhance_dataset_meta(df: pd.DataFrame, meta: dict) -> dict:
    """
    FIX #43: Generate comprehensive reusable metadata at upload time.
    Includes: numeric summaries, categorical summaries, distributions,
    temporal ranges, value cardinalities, and data quality metrics.
    """
    
    # Numeric column summaries
    meta["numeric_summaries"] = {}
    for col in meta.get("numeric_cols", []):
        if col in df.columns:
            series = df[col].dropna()
            if len(series) > 0:
                meta["numeric_summaries"][col] = {
                    "mean": float(series.mean()),
                    "median": float(series.median()),
                    "std": float(series.std()),
                    "min": float(series.min()),
                    "max": float(series.max()),
                    "q25": float(series.quantile(0.25)),
                    "q75": float(series.quantile(0.75)),
                    "nulls": int(df[col].isna().sum()),
                    "unique_count": int(series.nunique())
                }
    
    # Categorical column summaries
    meta["categorical_summaries"] = {}
    for col in meta.get("categorical_cols", []):
        if col in df.columns:
            series = df[col].dropna()
            if len(series) > 0:
                value_counts = series.value_counts()
                meta["categorical_summaries"][col] = {
                    "unique_count": int(series.nunique()),
                    "top_values": value_counts.head(10).to_dict(),
                    "nulls": int(df[col].isna().sum()),
                    "cardinality_ratio": float(series.nunique() / max(len(series), 1))
                }
    
    # Value distributions (for common query optimization)
    meta["value_distributions"] = {}
    for col in meta.get("low_cardinality_cols", []):
        if col in df.columns and col not in meta.get("id_like_cols", []):
            try:
                dist = df[col].value_counts().to_dict()
                if len(dist) <= 100:  # Only store if reasonable size
                    meta["value_distributions"][col] = dist
            except Exception:
                pass
    
    # Temporal ranges (for time-series optimization)
    meta["temporal_ranges"] = {}
    for col in meta.get("datetime_cols", []):
        if col in df.columns:
            series = pd.to_datetime(df[col], errors="coerce").dropna()
            if len(series) > 0:
                meta["temporal_ranges"][col] = {
                    "min_date": str(series.min()),
                    "max_date": str(series.max()),
                    "date_range_days": int((series.max() - series.min()).days),
                    "unique_dates": int(series.nunique())
                }
    
    # Data quality metrics
    meta["data_quality"] = {
        "total_nulls": int(df.isna().sum().sum()),
        "null_ratio": float(df.isna().sum().sum() / (len(df) * len(df.columns))),
        "duplicate_rows": int(df.duplicated().sum()),
        "complete_rows": int(len(df) - df.isna().any(axis=1).sum())
    }
    
    # Column compatibility matrix (for join suggestions)
    meta["column_types"] = {
        col: str(df[col].dtype)
        for col in df.columns
    }
    
    logger.info(f"Enhanced metadata: {len(meta.get('numeric_summaries', {}))} numeric, "
               f"{len(meta.get('categorical_summaries', {}))} categorical, "
               f"{len(meta.get('temporal_ranges', {}))} temporal columns")
    
    return meta


def _detect_primary_entity(df: pd.DataFrame, meta: dict) -> Optional[str]:
    """FIX #31: Prefer name-like dimension over arbitrary first column."""
    entity_signals = ["name","product","customer","client","item","category",
                      "region","store","city","country","brand","channel"]
    for col in meta.get("low_cardinality_cols", []):
        if any(s in col.lower() for s in entity_signals):
            return col
    if meta.get("low_cardinality_cols"):
        return meta["low_cardinality_cols"][0]
    if meta.get("categorical_cols"):
        return meta["categorical_cols"][0]
    id_set = set(meta.get("id_like_cols", []))
    for col in df.columns:
        if col not in id_set:
            return col
    return None


def tokenize(text: str) -> List[str]:
    return [
        t for t in re.split(r'[\s_\-/]+', text.lower())
        if len(t.strip()) > 1
    ]

def score_column_match(
    query: str,
    column: str,
    synonyms: Dict[str, str],
    meta: dict,
    expected_type: str = None
) -> float:

    query_lower = query.lower()
    col_lower = column.lower()

    query_tokens = tokenize(query_lower)
    col_tokens = tokenize(col_lower)

    score = 0.0

    # ─────────────────────────────
    # 1. Exact match
    # ─────────────────────────────
    if query_lower == col_lower:
        score += 100

    # ─────────────────────────────
    # 2. Exact token overlap
    # ─────────────────────────────
    overlap = set(query_tokens) & set(col_tokens)
    score += len(overlap) * 20

    # ─────────────────────────────
    # 3. Partial token similarity
    # ─────────────────────────────
    for qt in query_tokens:
        for ct in col_tokens:
            similarity = SequenceMatcher(None, qt, ct).ratio()

            if similarity > 0.85:
                score += 12
            elif similarity > 0.70:
                score += 6

    # ─────────────────────────────
    # 4. Semantic synonym boost
    # ─────────────────────────────
    for token in query_tokens:
        if token in synonyms:
            if synonyms[token] == column:
                score += 25

    # ─────────────────────────────
    # 5. Whole column phrase inside query
    # ─────────────────────────────
    if col_lower.replace("_", " ") in query_lower:
        score += 30

    # ─────────────────────────────
    # 6. Datatype compatibility
    # ─────────────────────────────
    role = meta.get("column_roles", {}).get(column)

    if expected_type == "metric":
        if role in ("metric", "derived", "percentage"):
            score += 20
        else:
            score -= 15

    elif expected_type == "dimension":
        if role in ("dimension", "temporal", "boolean"):
            score += 20
        else:
            score -= 10

    # ─────────────────────────────
    # 7. Penalize identifiers
    # ─────────────────────────────
    if role == "identifier":
        score -= 25

    # ─────────────────────────────
    # 8. Penalize free text
    # ─────────────────────────────
    if role == "free_text":
        score -= 15

    return score

def find_column(
    query: str,
    candidates: List[str],
    synonyms: Dict[str, str] = None,
    meta: dict = None,
    expected_type: str = None
) -> Optional[str]:

    if not candidates:
        return None

    synonyms = synonyms or {}
    meta = meta or {}

    scored = []

    for col in candidates:
        score = score_column_match(
            query=query,
            column=col,
            synonyms=synonyms,
            meta=meta,
            expected_type=expected_type
        )

        scored.append((col, score))

    schema_registry = meta.get("schema_registry", {})

    scored.sort(
        key=lambda x: (
            x[1],
            schema_registry.get(
                x[0],
                {}
            ).get("group_priority", 0)
        ),
        reverse=True
    )

    logger.info(f"Top column scores: {scored[:5]}")

    best_col, best_score = scored[0]

    logger.info(
        f"[COLUMN MATCH] Query='{query}' → Selected='{best_col}' Score={best_score}"
    )

    # confidence threshold
    if best_score < 15:
        return None

    return best_col

def resolve_semantic_value(
    query: str,
    meta: dict
) -> Optional[dict]:

    q = query.lower()

    value_index = meta.get("value_index", {})

    best_match = None
    
    # ─────────────────────────────
    # Boolean semantic inference
    # ─────────────────────────────

    boolean_cols = meta.get("boolean_cols", [])

    for col in boolean_cols:
        col_lower = col.lower()

        # prepaid_order
        normalized = (
            col_lower
            .replace("_", " ")
            .replace("is ", "")
            .replace("has ", "")
        )

        if normalized in q:
            return {
                "column": col,
                "value": True
            }

        # prepaid
        simplified = normalized.replace(" order", "").replace(" status", "")

        if simplified in q:
            return {
                "column": col,
                "value": True
            }

        boolean_aliases = value_index.get(
            "boolean_aliases",
            {}
        )

        for bool_value, aliases in boolean_aliases.items():
            for alias in aliases:
                if alias in q:
                    normalized_bool = (
                        True if bool_value == "true"
                        else False
                    )
                    return {
                        "column": col,
                        "value": normalized_bool
                    }

    return None



def suggest_closest_column(hint: str, meta: dict) -> str:
    numeric_cols     = meta.get("numeric_cols", [])
    categorical_cols = meta.get("categorical_cols", [])
    synonyms         = meta.get("synonyms", {})
    hint_lower       = hint.lower()
    for term, col in synonyms.items():
        if term in hint_lower and col in numeric_cols + categorical_cols:
            return f"Did you mean '{col}'?"
    available = ", ".join((numeric_cols + categorical_cols)[:6])
    return f"Available columns: {available}" if available else ""


def is_count_query(query: str) -> bool:
    q = query.lower()
    patterns = [
        r'\bhow many\b', r'\bnumber of\b', r'\bcount of\b',
        r'\bcount\b.+\bby\b', r'\bcount\b.+\bper\b',
        r'\bhow many\b.+\bper\b', r'\bhow many\b.+\bby\b',
        r'\bhow many\b.+\beach\b', r'\btotal count\b', r'\bfrequency\b',
    ]
    return any(re.search(p, q) for p in patterns)

def is_kpi_query(query: str) -> bool:
    q = query.lower()

    kpi_patterns = [
        r"\b(total|sum|average|avg|mean|min|max|count)\b",
        r"\bhow many\b",
        r"\bwhat is the total\b",
        r"\bwhat is the average\b",
        r"\boverall\b",
    ]

    grouping_patterns = [
        r"\bby\b",
        r"\bper\b",
        r"\bfor each\b",
        r"\bgrouped by\b",
    ]

    has_kpi = any(re.search(p, q) for p in kpi_patterns)
    has_grouping = any(re.search(p, q) for p in grouping_patterns)

    return has_kpi and not has_grouping


def is_ranking_query(query: str) -> bool:
    q = query.lower()

    ranking_patterns = [
        r"\btop\b",
        r"\bbottom\b",
        r"\bbest\b",
        r"\bworst\b",
        r"\bhighest\b",
        r"\blowest\b",
        r"\bmost\b",
        r"\bleast\b",
        r"\brank\b",
    ]

    return any(re.search(p, q) for p in ranking_patterns)


def is_trend_query(query: str) -> bool:
    q = query.lower()

    trend_patterns = [
        r"\btrend\b",
        r"\bover time\b",
        r"\bmonthly\b",
        r"\byearly\b",
        r"\bdaily\b",
        r"\bgrowth\b",
        r"\bchange over\b",
        r"\btime series\b",
        r"\bweekly\b",
        r"\bquarterly\b",
        r"\breport\b.+\bmonth\b",
        r"\breport\b.+\byear\b",
        r"\bgrowth rate\b",
        r"\byear over year\b",
        r"\byoy\b",
        r"\bmonth over month\b",
        r"\bmom\b",
        r"\bperiod-on-period\b",
        r"\bcumulative\b",
    ]

    return any(re.search(p, q) for p in trend_patterns)


def is_comparison_query(query: str) -> bool:
    q = query.lower()

    comparison_patterns = [
        r"\bcompare\b",
        r"\bcomparison\b",
        r"\bvs\b",
        r"\bversus\b",
        r"\bdifference between\b",
    ]

    return any(re.search(p, q) for p in comparison_patterns)


def is_raw_retrieval_query(query: str) -> bool:
    q = query.lower()

    retrieval_patterns = [
        r"\bshow\b",
        r"\blist\b",
        r"\bdisplay\b",
        r"\bgive me\b",
        r"\bretrieve\b",
        r"\bfetch\b",
        r"\bget\b",
        r"\bshow all\b",
        r"\blist all\b",
        r"\bdisplay all\b",
        r"\bshow records\b",
        r"\bshow rows\b",
        r"\bview\b",
    ]

    aggregation_patterns = [
        r"\btotal\b",
        r"\bsum\b",
        r"\baverage\b",
        r"\bavg\b",
        r"\bcount\b",
        r"\btop\b",
        r"\bhighest\b",
        r"\blowest\b",
        r"\bmaximum\b",
        r"\bminimum\b",
        r"\bdistribution\b",
        r"\bbreakdown\b",
    ]

    has_retrieval = any(re.search(p, q) for p in retrieval_patterns)
    has_aggregation = any(re.search(p, q) for p in aggregation_patterns)

    return has_retrieval and not has_aggregation

def detect_operation(query: str) -> str:
    q = query.lower()

    operation_patterns = {
        "count": [
            r"\bcount\b",
            r"\bhow many\b",
            r"\bnumber of\b",
            r"\bfrequency\b",
        ],
        
        "unique_count": [
            r"\bunique\b",
            r"\bdistinct\b",
            r"\bunique count\b",
            r"\bdistinct count\b",
        ],

        "unique_count": [
            r"\bunique\b",
            r"\bdistinct\b",
            r"\bunique count\b",
        ],

        "sum": [
            r"\btotal\b",
            r"\bsum\b",
            r"\boverall\b",
            r"\bcumulative\b",
        ],

        "avg": [
            r"\baverage\b",
            r"\bavg\b",
            r"\bmean\b",
        ],

        "min": [
            r"\bminimum\b",
            r"\bmin\b",
            r"\blowest\b",
            r"\bsmallest\b",
        ],

        "max": [
            r"\bmaximum\b",
            r"\bmax\b",
            r"\bhighest\b",
            r"\blargest\b",
            r"\bmost\b",
            r"\bbest\b",
            r"\btop\b",
        ],

        "trend": [
            r"\btrend\b",
            r"\bover time\b",
            r"\bgrowth\b",
        ],

        "comparison": [
            r"\bcompare\b",
            r"\bcomparison\b",
            r"\bvs\b",
            r"\bversus\b",
        ],
    }

    for operation, patterns in operation_patterns.items():
        if any(re.search(p, q) for p in patterns):
            return operation

    return "sum"

def is_categorical_distribution_query(query: str, meta: dict) -> Tuple[bool, Optional[str]]:
    q = query.lower()
    dist_patterns = [
        r'\bdistribution\b', r'\bbreakdown\b', r'\bspread\b',
        r'\bproportions?\b', r'\bshare\b', r'\bcomposition\b',
        r'\bfrequency\b', r'\bhow is\b.+\bdistributed\b',
    ]
    if not any(re.search(p, q) for p in dist_patterns):
        return False, None

    free_text = set(meta.get("free_text_cols", []))
    cat_cols  = (meta.get("low_cardinality_cols", []) +
                 meta.get("categorical_cols", []))
    safe_cat  = [c for c in cat_cols if c not in free_text]

    for col in safe_cat:
        words = [w for w in re.split(r'[\s_\-/]+', col.lower()) if len(w) > 2]
        if any(w in q for w in words):
            return True, col

    return (True, safe_cat[0]) if safe_cat else (False, None)


def detect_group_by(query: str, df: pd.DataFrame, meta: dict) -> Optional[str]:
    q         = query.lower()
    synonyms  = meta.get("synonyms", {})
    free_text = set(meta.get("free_text_cols", []))
    id_cols   = set(meta.get("id_like_cols", []))
    schema_registry = meta.get("schema_registry", {})

    safe_cat = [
        c for c in (
            meta.get("low_cardinality_cols", [])
            + meta.get("categorical_cols", [])
            + meta.get("boolean_cols", [])
        )
        if (
            c not in free_text
            and c not in id_cols
            and schema_registry.get(c, {}).get("is_groupable")
        )
    ]
    
    # ─────────────────────────────
    # Semantic grouping prioritization
    # ─────────────────────────────
    schema_registry = meta.get("schema_registry", {})

    safe_cat = sorted(
        safe_cat,
        key=lambda c: schema_registry.get(c, {}).get(
            "group_priority",
            0
        ),
        reverse=True
    )

    group_patterns = [
        r'\b(?:by|per|for each|grouped by|across|among|within|breakdown by)\s+'
        r'([a-z][\w\s]*?)(?:\s+and|\s+where|\s+with|\s+in\s+(?:the\s+)?(?:dataset|data)|[?.,]|$)',
        r'\beach\s+([a-z][\w\s]*?)(?:\s|$)',
    ]
    for pattern in group_patterns:
        m = re.search(pattern, q)
        if m:
            hint = (
                m.group(1)
                .strip()
                .rstrip("?.,")
            )

            hint = re.split(
                r'\b(where|with|having|from|in)\b',
                hint
            )[0].strip()

            scored_cols = []

            for col_candidate in safe_cat:
                score = score_column_match(
                    query=hint,
                    column=col_candidate,
                    synonyms=synonyms,
                    meta=meta,
                    expected_type="dimension"
                )

                # prefer lower cardinality
                nunique = df[col_candidate].nunique()

                if nunique <= 15:
                    score += 12
                elif nunique <= 40:
                    score += 6
                elif nunique > 200:
                    score -= 15

                # semantic grouping priority
                schema_registry = meta.get("schema_registry", {})
                score += schema_registry.get(
                    col_candidate,
                    {}
                ).get("group_priority", 0) * 0.1

                scored_cols.append((col_candidate, score))

            scored_cols.sort(
                key=lambda x: x[1],
                reverse=True
            )

            col = (
                scored_cols[0][0]
                if scored_cols
                and scored_cols[0][1] >= 15
                else None
            )
            if col:
                return col

    entity_map = {
        "city":       ["city", "location", "store", "branch"],
        "region":     ["region", "territory", "zone", "area", "market"],
        "store":      ["store", "branch", "location", "outlet"],
        "product":    ["product", "item", "sku", "category"],
        "customer":   ["customer", "client", "buyer", "name"],
        "category":   ["category", "segment", "type", "department"],
        "country":    ["country", "nation", "market"],
        "month":      ["month", "period"],
        "year":       ["year", "period"],
        "quarter":    ["quarter", "q1", "q2", "q3", "q4"],
        "department": ["department", "team", "division"],
        "channel":    ["channel", "medium", "source", "platform"],
        "brand":      ["brand", "label", "make"],
    }
    # low-priority fallback only

    best_col = None
    best_score = 0

    for entity, signals in entity_map.items():
        if entity in q:
            for cat_col in safe_cat:
                score = 0
                for s in signals:
                    if s in cat_col.lower():
                        score += 1

                # prefer lower cardinality
                nunique = df[cat_col].nunique()

                if nunique <= 20:
                    score += 3
                elif nunique <= 50:
                    score += 1

                if score > best_score:
                    best_score = score
                    best_col = cat_col

    if best_col:
        return best_col

    return None


def extract_filters(query: str, df: pd.DataFrame, meta: dict) -> Dict[str, Any]:
    filters  = {}
    q        = query.lower()
    synonyms = meta.get("synonyms", {})
    all_cols = df.columns.tolist()

    filter_patterns = [
        # explicit filters
        r'where\s+([\w\s]+?)\s+(?:is|=|equals?|==)\s+["\']?([^"\']+?)["\']?(?:\s+and|\s+or|\s*$)',

        # filtered by
        r'(?:filter|filtered)\s+(?:by|for)\s+([\w\s]+?)\s+(?:is|=|equals?)?\s*["\']?([^"\']+?)["\']?(?:\s|$)',

        # generic "with"
        r'with\s+([a-zA-Z][\w\s\-]+?)(?:\s|$)',

        # generic "having"
        r'having\s+([a-zA-Z][\w\s\-]+?)(?:\s|$)',

        # generic "from"
        r'from\s+([a-zA-Z][\w\s\-]+?)(?:\s|$)',

        # generic "in"
        r'in\s+([a-zA-Z][\w\s\-]+?)(?:\s|$)',
    ]

    for pattern in filter_patterns:
        for m in re.finditer(pattern, q):
            groups = m.groups()

            # ─────────────────────────────
            # explicit column=value filters
            # ─────────────────────────────
            if len(groups) >= 2:
                col_hint = groups[0].strip()
                val = groups[1].strip()

                matched = find_column(
                    col_hint,
                    all_cols,
                    synonyms,
                    meta,
                    expected_type="dimension"
                )

                if matched:
                    filters.setdefault(
                        matched,
                        normalize_boolean_value(val)
                    )

            # ─────────────────────────────
            # semantic value matching
            # ─────────────────────────────
            elif len(groups) == 1:
                semantic_text = groups[0].strip()

                semantic_match = resolve_semantic_value(
                    semantic_text,
                    meta
                )

                if semantic_match:
                    filters.setdefault(
                        semantic_match["column"],
                        semantic_match["value"]
                    )

    for val_hint in re.findall(
        r'\bfor\s+["\']?([a-zA-Z][\w\s\-]+?)["\']?(?:\s+in\s+|\s+from\s+|\s+by\s+|\s+where|\s*$)', q
    ):
        val_hint = val_hint.strip()
        if len(val_hint) < 2 or val_hint in ("each", "the", "all", "this", "that"):
            continue
        cat_cols = meta.get("low_cardinality_cols", []) + meta.get("categorical_cols", [])
        for col in cat_cols:
            if col in filters:
                continue
            col_vals = df[col].astype(str).str.lower().unique()
            if val_hint in col_vals:
                matched_val = next(
                    (
                        v for v in col_vals
                        if str(v).lower() == val_hint
                    ),
                    val_hint
                )
                filters[col] = matched_val
                break
            for cv in col_vals:
                cv_str = str(cv).lower()
                if (
                    val_hint in cv_str
                    or cv_str in val_hint
                ):
                    filters[col] = cv
                    break

    for val_hint in re.findall(r'\bin\s+["\']?([a-zA-Z][\w\s\-]+?)["\']?(?:\s|$)', q):
        val_hint = val_hint.strip()
        if len(val_hint) < 2 or val_hint in ("the", "this", "that", "a", "an"):
            continue
        cat_cols = meta.get("low_cardinality_cols", []) + meta.get("categorical_cols", [])
        for col in cat_cols:
            if col in filters:
                continue
            if val_hint in df[col].astype(str).str.lower().unique():
                filters[col] = val_hint
                break

    numeric_cols = meta.get("numeric_cols", [])
    for pattern, op in [
        (r'([\w\s]+?)\s+(?:above|greater than|more than|over|exceeds?|>)\s*(\d+(?:\.\d+)?)', ">"),
        (r'([\w\s]+?)\s+(?:below|less than|under|beneath|<)\s*(\d+(?:\.\d+)?)', "<"),
        (r'([\w\s]+?)\s+(?:at least|>=|minimum of)\s*(\d+(?:\.\d+)?)', ">="),
        (r'([\w\s]+?)\s+(?:at most|<=|maximum of)\s*(\d+(?:\.\d+)?)', "<="),
        (r'([\w\s]+?)\s+(?:!=|not equal to|excluding)\s*(\d+(?:\.\d+)?)', "!="),
    ]:
        for m in re.finditer(pattern, q):
            col_hint, val = m.group(1).strip(), m.group(2)
            matched = find_column(col_hint, numeric_cols, synonyms, meta, expected_type="metric")
            if matched:
                filters.setdefault(matched, {"op": op, "val": float(val)})
    
    # ─────────────────────────────
    # Semantic Value Matching
    # ─────────────────────────────
    semantic_match = resolve_semantic_value(query, meta)

    if semantic_match:
        semantic_col = semantic_match["column"]
        semantic_val = semantic_match["value"]

        if semantic_col not in filters:
            filters[semantic_col] = semantic_val

    return filters



def apply_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    result = df.copy()
    for col, cond in filters.items():
        if col not in result.columns:
            continue
        if isinstance(cond, dict):
            val, op = cond["val"], cond["op"]
            masks = {
                ">": result[col] > val, "<": result[col] < val,
                ">=": result[col] >= val, "<=": result[col] <= val,
                "!=": result[col] != val,
            }
            result = result[masks.get(op, result[col] > val)]
        else:
            if isinstance(cond, bool):
                mask = result[col] == cond
            else:
                mask = (
                    result[col]
                    .astype(str)
                    .str.lower()
                    == str(cond).lower()
                )
                if mask.sum() == 0:
                    mask = result[col].astype(str).str.lower().str.contains(
                        str(cond).lower(), na=False
                    )
            result = result[mask]
    return result


def is_meaningful_comparison(col1: str, col2: str, meta: dict) -> bool:
    id_cols     = set(meta.get("id_like_cols", []))
    numeric_set = set(meta.get("numeric_cols", []))
    if col1 in id_cols or col2 in id_cols:
        return False
    return col1 in numeric_set and col2 in numeric_set


def validate_query_plan(plan: QueryPlan, df: pd.DataFrame, meta: dict) -> Tuple[bool, str]:
    numeric_set = set(meta.get("numeric_cols", []))
    id_cols     = set(meta.get("id_like_cols", []))
    cat_set     = set(meta.get("categorical_cols", []) + meta.get("low_cardinality_cols", []))
    free_text   = set(meta.get("free_text_cols", []))

    # prevent metric on identifier columns
    if plan.metric_column in id_cols:
        alt = list(numeric_set - id_cols)[:3]
        return False, (
            f"'{plan.metric_column}' is an identifier column. "
            f"Try: {', '.join(alt) or 'a numeric column'}."
        )

    if plan.query_type in ("ranking", "aggregation", "kpi"):
        numeric_required_ops = {"sum", "avg", "mean", "min", "max", "median", "stddev"}
        requires_numeric = plan.operation in numeric_required_ops

        if (
            requires_numeric
            and plan.metric_column
            and plan.metric_column not in numeric_set
        ):
            alt = list(numeric_set)[:5]
            return False, (
                f"'{plan.metric_column}' cannot be used with "
                f"'{plan.operation}'. Numeric column required. "
                f"Try: {', '.join(alt) or 'none'}."
            )

        # count / unique_count allowed on categorical cols
        allowed_non_numeric_ops = {"count", "unique_count"}

        if (
            plan.operation not in allowed_non_numeric_ops
            and plan.metric_column
            and plan.metric_column not in numeric_set
            and requires_numeric
        ):
            return False, (
                f"Invalid aggregation on non-numeric column "
                f"'{plan.metric_column}'."
            )

        if not plan.metric_column and not numeric_set:
            return False, "No numeric columns to aggregate."

    # prevent aggregation on identifier columns (except count/unique_count)
    if (
        plan.metric_column
        and plan.metric_column in id_cols
        and plan.operation not in ("count", "unique_count")
    ):
        return False, (
            f"'{plan.metric_column}' is an identifier column "
            f"and cannot be aggregated meaningfully."
        )

    if plan.group_by_column:
        if plan.group_by_column in free_text:
            safe = list(cat_set - free_text)[:3]
            return False, (
                f"'{plan.group_by_column}' has too many unique values. "
                f"Try: {', '.join(safe)}."
            )

        # prevent continuous numeric grouping
        if plan.group_by_column in numeric_set and plan.group_by_column not in cat_set:
            nunique_ratio = df[plan.group_by_column].nunique() / max(len(df), 1)

            # allow only low-cardinality numeric grouping
            if nunique_ratio > 0.2:
                return False, (
                    f"'{plan.group_by_column}' is too continuous "
                    f"for grouping."
                )

        schema_registry = meta.get("schema_registry", {})
        if not schema_registry.get(plan.group_by_column, {}).get("is_groupable", False):
            return False, f"'{plan.group_by_column}' is not suitable for grouping."

    if plan.query_type == "trend" and not meta.get("date_col"):
        return False, "Trend analysis requires a date/time column."

    if plan.query_type == "correlation" and len(numeric_set) < 2:
        return False, "Correlation requires at least 2 numeric columns."

    return True, ""




VAGUE_QUERY_PATTERNS = [
    r'^(best|top|worst|bottom)\s+(products?|items?|customers?|regions?|stores?)\s*$',
    r'^performance\s*(analysis|overview|report|summary)?\s*$',
    r'^(growth|decline|trend)\s*$',
    r'^(analysis|analytics|report|overview|summary|insights?)\s*$',
    r'^(show|give me|display)\s+(me\s+)?(some|the)?\s*(data|information|insights?|numbers?)\s*$',
    r'^(how\s+is|what\s+is|tell\s+me\s+about)\s+(the\s+)?business\s*$',
    r'^(how\s+are|what\s+are)\s+(we|things|sales?|numbers?|stats?)\s+(doing|looking)?\s*$',
    r'^(compare|comparison)\s*$',
    r'^(breakdown|breakdown\s+of)\s*$',
]

VAGUE_SINGLE_WORDS = {
    "analysis", "analytics", "report", "overview", "summary", "insights", "numbers",
    "data", "stats", "statistics", "performance", "growth", "decline", "trends",
    "comparison", "breakdown", "distribution", "best", "worst",
}



def detect_ambiguity(query: str, plan: QueryPlan, meta: dict) -> Tuple[bool, str]:
    """FIX #17: Detect and explain vague/ambiguous queries."""
    q = query.lower().strip()

    words = [w for w in re.split(r'\W+', q) if w]
    if len(words) <= 2 and all(w in VAGUE_SINGLE_WORDS for w in words):
        num  = meta.get("numeric_cols", [])
        cat  = meta.get("low_cardinality_cols", [])
        opts = []
        if num:   opts.append(f"'Top 5 by {num[0]}'")
        if cat and num: opts.append(f"'Average {num[0]} by {cat[0]}'")
        opts.append("'Explain this dataset'")
        return True, f"'{query}' is too vague. Try: {', '.join(opts)}."

    for pattern in VAGUE_QUERY_PATTERNS:
        if re.match(pattern, q):
            num  = meta.get("numeric_cols", [])
            cat  = meta.get("low_cardinality_cols", [])
            date = meta.get("date_col")
            sugg = []
            if num:        sugg.append(f"'Top 5 by {num[0]}'")
            if cat and num: sugg.append(f"'Average {num[0]} by {cat[0]}'")
            if date and num: sugg.append(f"'Trend of {num[0]} over time'")
            sugg.append("'Explain this dataset'")
            return True, (f"'{query}' is too broad. Try: {', '.join(sugg[:3])}.")

    if (plan.confidence < 0.35
            and not plan.metric_column
            and not plan.group_by_column
            and plan.query_type == "explanation"
            and not plan.is_followup):
        num = meta.get("numeric_cols", [])[:3]
        cat = meta.get("low_cardinality_cols", [])[:3]
        return True, (
            f"I couldn't determine what to analyse from '{query}'. "
            f"Specify a metric ({', '.join(num)}) or grouping ({', '.join(cat)})."
        )

    return False, ""


# ═══════════════════════════════════════════════════════════════════════════════
# FIX #18 + #19: FOLLOW-UP CONTEXT INHERITANCE & ENTITY MEMORY
# ═══════════════════════════════════════════════════════════════════════════════

def detect_followup(query: str, history: List[dict]) -> bool:
    if not history:
        return False
    q = query.lower().strip()
    for p in [
        r'^(and|also|what about|how about|show me|now|next|then|but|for|in that case)',
        r'^(same|similar|like that|like this|do the same)',
        r'^(more|less|give me more|tell me more|expand|elaborate)',
        r'^(why|how|can you explain|what does that mean)',
    ]:
        if re.match(p, q):
            return True
    return len(q.split()) <= 3


def inherit_context(plan: QueryPlan, history: List[dict],
                    df: pd.DataFrame, meta: dict) -> QueryPlan:
    """FIX #18: Inherit metric/group/filters. FIX #19: Entity memory."""
    if not history:
        return plan

    last_plan_dict = history[-1].get("plan", {})

    if not plan.metric_column and last_plan_dict.get("metric_column"):
        plan.metric_column    = last_plan_dict["metric_column"]
        plan.inherited_metric = plan.metric_column

    if not plan.group_by_column and last_plan_dict.get("group_by_column"):
        plan.group_by_column = last_plan_dict["group_by_column"]

    if not plan.filters and last_plan_dict.get("filters"):
        plan.filters           = dict(last_plan_dict["filters"])
        plan.inherited_filters = plan.filters.copy()

    # FIX #19: Scan last 3 turns for entity-based filters
    if not plan.filters:
        for h in reversed(history[-3:]):
            prev_filters = h.get("plan", {}).get("filters", {})
            if prev_filters:
                plan.filters          = dict(prev_filters)
                plan.inherited_filters = plan.filters.copy()
                break

    if plan.metric_column and plan.aggregation and not plan.aggregation.column:
        plan.aggregation.column = plan.metric_column

    return plan



def repair_query(query: str, plan: QueryPlan, meta: dict) -> Tuple[QueryPlan, Optional[str]]:
    """FIX #20: Rewrite malformed/ambiguous queries into structured plans."""
    q        = query.lower().strip()
    repaired = None
    id_cols  = set(meta.get("id_like_cols", []))
    safe_num = [c for c in meta.get("numeric_cols", []) if c not in id_cols]
    cat_cols = meta.get("low_cardinality_cols", []) or meta.get("categorical_cols", [])
    synonyms = meta.get("synonyms", {})

    # Repair 1: "best/worst X" without metric
    best_m = re.match(r'^(best|top|leading|worst|bottom)\s+([\w\s]+)$', q)
    if best_m and not plan.metric_column and safe_num:
        direction         = "asc" if best_m.group(1) in ("worst","bottom") else "desc"
        plan.sort_order   = direction
        plan.metric_column = safe_num[0]
        plan.query_type   = "ranking"
        plan.limit        = 5
        repaired          = f"Top 5 by {safe_num[0]}"
        plan.repaired_query = repaired

    # Repair 2: Bare "trend"/"growth" without metric
    if q in ("trend","growth","trends","sales trend") and not plan.metric_column and safe_num:
        plan.metric_column = safe_num[0]
        plan.query_type    = "trend"
        repaired           = f"Trend of {safe_num[0]} over time"
        plan.repaired_query = repaired

    # Repair 3: "compare X and Y" — extract cols
    cmp_m = re.search(
        r'compare\s+([\w\s]+?)\s+(?:and|vs\.?|versus)\s+([\w\s]+?)(?:\s+by|\s*$)', q
    )
    if cmp_m and plan.query_type == "comparison":
        c1 = find_column(cmp_m.group(1).strip(), safe_num, synonyms, meta, expected_type="metric")
        c2 = find_column(cmp_m.group(2).strip(), safe_num, synonyms, meta, expected_type="metric")
        if c1 and c2:
            plan.metric_column      = c1
            plan._comparison_cols   = [c1, c2]
            repaired                = f"Compare {c1} and {c2}"
            plan.repaired_query     = repaired

    # Repair 4: Missing group-by when "by" present
    if "by" in q and not plan.group_by_column and cat_cols:
        by_m = re.search(r'\bby\s+([\w\s]+?)(?:\s|$)', q)
        if by_m:
            col = find_column(by_m.group(1).strip(), cat_cols, synonyms, meta, expected_type="dimension")
            if col:
                plan.group_by_column = col
                repaired             = (repaired or query) + f" (grouped by {col})"
                plan.repaired_query  = repaired

    # Repair 5: "average/sum/total X" without explicit col
    agg_m = re.match(r'^(average|avg|total|sum|mean|count|minimum|maximum|min|max)\s+([\w\s]+)$', q)
    if agg_m and not plan.metric_column and safe_num:
        agg_word = agg_m.group(1)
        col      = find_column(agg_m.group(2).strip(), safe_num, synonyms, meta, expected_type="metric")
        if col:
            agg_map = {"average":"avg","avg":"avg","total":"sum","sum":"sum",
                       "mean":"avg","count":"count","minimum":"min","min":"min",
                       "maximum":"max","max":"max"}
            plan.metric_column  = col
            plan.query_type     = "kpi" if not plan.group_by_column else "aggregation"
            plan.aggregation    = AggregationSpec(operation=agg_map.get(agg_word,"sum"), column=col)
            repaired            = f"{agg_word.title()} of {col}"
            plan.repaired_query = repaired

    return plan, repaired


def classify_query_intent(
    query: str,
    roles: Dict[str, Any],
    meta: dict,
    history: List[dict]
) -> str:
    """
    FIX #38: Rule-based intent classification (replaces regex-heavy logic).
    Uses structured rule engine to determine query type.
    """
    intent, _ = classify_query_intent_rule_based(query, roles)
    return intent




# Improvement #9: Business language intent mapping
BUSINESS_LANGUAGE_MAP = {
    "sales": ["revenue", "sales_amount", "sales_value", "total_sales", "sales"],
    "revenue": ["revenue_amount", "total_revenue", "sales_revenue", "revenue"],
    "orders": ["order_count", "order_id", "order_amount", "order_value", "orders"],
    "customers": ["customer_id", "customer_count", "num_customers", "customers", "client"],
    "products": ["product_id", "product_name", "product_count", "num_products", "products"],
    "transactions": ["transaction_id", "transaction_amount", "transaction_count", "transactions"],
    "profit": ["profit_amount", "profit_margin", "net_profit", "profit"],
    "cost": ["cost_amount", "total_cost", "cost_value", "cost"],
    "price": ["price_amount", "unit_price", "pricing", "price"],
}

def extract_semantic_roles(query: str, df: pd.DataFrame, meta: dict) -> Dict[str, Any]:
    q = query.lower()
    # remove filler phrases
    q = re.sub(
        r'\b(show|give me|display|tell me|what is|how many)\b',
        '',
        q
    )
    q = re.sub(r'\s+', ' ', q).strip()

    id_cols  = set(meta.get("id_like_cols", []))
    synonyms = meta.get("synonyms", {})
    safe_num = [c for c in meta.get("numeric_cols", []) if c not in id_cols]

    roles: Dict[str, Any] = {
        "metric": None, "aggregation": None, "operation": None, "grouping_entity": None,
        "filters": {}, "ranking": {"direction": None, "limit": 5},
        "date_range": None, "is_count": False,
        "is_cat_dist": False, "cat_dist_col": None,
    }

    roles["operation"] = detect_operation(query)
    if roles["operation"] == "unique_count":
        roles["is_count"] = True
    roles["aggregation"] = roles["operation"]

    if roles["operation"] == "count":
        roles["is_count"] = True
    
    # Improvement #1, #2: Explicit KPI pattern detection (total number, row count, dataset size)
    if re.search(r'\b(total\s+(number|count|records?|entries)|row\s+count|record\s+count|dataset\s+size)\b', q):
        roles["is_count"] = True
        roles["metric"] = None
        roles["grouping_entity"] = None
        logger.debug("KPI: Detected explicit row count query")
    
    # Improvement #2: How many → count query conversion
    if re.search(r'\bhow\s+many\b', q):
        roles["is_count"] = True
        if not roles.get("grouping_entity"):
            roles["metric"] = None
        logger.debug("KPI: Detected 'how many' count query")
        
    # implicit count/grouping queries
    if (
        not roles["metric"]
        and detect_group_by(query, df, meta)
        and re.search(
            r'\b(most|least|highest|lowest|top|bottom|used|common|frequent)\b',
            q
        )
    ):
        roles["is_count"] = True

        if roles["is_count"]:
            roles["metric"] = None

        # Scalar count queries should not force grouping
        if roles["is_count"] and not roles.get("grouping_entity"):
            roles["grouping_entity"] = None

    is_cat, cat_col       = is_categorical_distribution_query(q, meta)
    roles["is_cat_dist"]  = is_cat
    roles["cat_dist_col"] = cat_col

    # Metric detection should NOT run for pure count queries
    if not roles["is_count"]:
        for col in safe_num:
            words = [
                w for w in re.split(r'[\s_\-/]+', col.lower())
                if len(w) > 2
            ]

            if any(w in q for w in words):
                roles["metric"] = col
                logger.debug(f"Metric: Direct match found: {col}")
                break

        if not roles["metric"]:
            # Improvement #9: Business language mapping (sales → revenue, orders → transactions, etc.)
            for biz_term, col_patterns in BUSINESS_LANGUAGE_MAP.items():
                if biz_term in q.split():
                    for col in safe_num:
                        col_lower = col.lower()
                        if any(pattern in col_lower for pattern in col_patterns):
                            roles["metric"] = col
                            logger.debug(f"Metric: Business language match: '{biz_term}' → {col}")
                            break
                    if roles["metric"]:
                        break
            
            # avoid forcing metrics for grouped count queries
            if not roles["metric"] and not (
                roles.get("grouping_entity")
                and roles.get("is_count")
            ):
                roles["metric"] = find_column(
                    query,
                    safe_num,
                    synonyms,
                    meta,
                    expected_type="metric"
                )

    roles["grouping_entity"] = detect_group_by(query, df, meta)
    
    # Improvement #13: Improve group-by detection confidence - never lose explicit groupings
    if roles["grouping_entity"]:
        logger.debug(f"GroupBy: Detected grouping entity: {roles['grouping_entity']}")

    if re.search(r'\b(top|highest|largest|most|best|leading|greatest)\b', q):
        roles["ranking"]["direction"] = "desc"
    elif re.search(r'\b(bottom|lowest|least|worst|smallest|trailing|fewest)\b', q):
        roles["ranking"]["direction"] = "asc"

    for n in re.findall(r'\b(\d+)\b', query):
        n_int = int(n)
        if 1 <= n_int <= 1000:
            roles["ranking"]["limit"] = n_int
            break

    roles["filters"] = extract_filters(query, df, meta)
    
    # Improvement #10: Semantic value matching - create filters for dataset values automatically
    if meta.get("value_index"):
        value_index = meta["value_index"]
        for token, entries in value_index.get("token_map", {}).items():
            if token.lower() in q.split() and len(token) > 2:
                for entry in entries:
                    col = entry.get("column")
                    val = entry.get("value")
                    if col and val and col in df.columns:
                        if col not in roles["filters"]:
                            roles["filters"][col] = val
                            logger.debug(f"Filter: Auto-created from value index: {col}={val}")
    
    # Improvement #11: Fix boolean filter resolution - generate column==True/False
    boolean_cols = meta.get("boolean_cols", [])
    for col in boolean_cols:
        if col in df.columns:
            col_lower = col.lower()
            # Check for boolean value keywords indicating True
            for keyword in ["active", "enabled", "yes", "true", "paid", "completed", "member", "approved"]:
                if keyword in q and col_lower in q:
                    roles["filters"][col] = True
                    logger.debug(f"Filter: Boolean true detected: {col}=True")
                    break
            # Check for keywords indicating False
            if col not in roles["filters"]:
                for keyword in ["inactive", "disabled", "no", "false", "unpaid", "cancelled", "not approved", "rejected"]:
                    if keyword in q and col_lower in q:
                        roles["filters"][col] = False
                        logger.debug(f"Filter: Boolean false detected: {col}=False")
                        break

    return roles


# ═══════════════════════════════════════════════════════════════════════════════
# FIX #38: REDUCED REGEX DEPENDENCY + RULE-BASED INTENT DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class IntentRule:
    """Structured rule for intent detection without regex dependency."""
    name: str
    intent: str
    priority: int                      # Higher = checked first
    required_conditions: List[str]     # All must be true
    forbidden_conditions: List[str]    # None must be true
    role_checks: Dict[str, Any]        # Role keys/values to check

    def evaluate(self, query: str, roles: Dict[str, Any], conditions_map: Dict[str, bool]) -> bool:
        """Check if rule matches based on conditions and roles."""
        # Check all required conditions are true
        for cond in self.required_conditions:
            if not conditions_map.get(cond, False):
                return False
        
        # Check no forbidden conditions are true
        for cond in self.forbidden_conditions:
            if conditions_map.get(cond, False):
                return False
        
        # Check role conditions
        for key, expected_val in self.role_checks.items():
            actual_val = roles.get(key)
            if expected_val is True:
                if not actual_val:
                    return False
            elif expected_val is False:
                if actual_val:
                    return False
            else:
                if actual_val != expected_val:
                    return False
        
        return True


# FIX #38: Rule-based condition detector to replace inline regex
def detect_query_conditions(query: str) -> Dict[str, bool]:
    """
    FIX #38: Detect query conditions structurally (not regex).
    IMPROVEMENTS #1, #2, #3, #12: Enhanced KPI and ranking detection
    Maps query characteristics to boolean conditions.
    """
    q = query.lower()
    words = set(q.split())
    
    # Improvement #1: Explicit KPI patterns (total number, row count, record count, dataset size)
    has_explicit_kpi = bool(re.search(
        r'\b(total\s+(number|count|records?|entries)|row\s+count|record\s+count|dataset\s+size|how\s+many|entries)\b',
        q
    ))
    
    # Time-series indicators (structured keywords)
    has_temporal_keywords = bool(set(q.split()) & {
        "month", "year", "quarter", "week", "day", "trend", "growth",
        "monthly", "yearly", "quarterly", "daily", "weekly", "over",
        "period", "date", "time", "when", "increasing", "declining"
    })
    
    # Comparison indicators
    has_comparison_keywords = bool(set(q.split()) & {
        "vs", "versus", "compared", "compare", "between", "difference",
        "more", "less", "higher", "lower", "better", "worse"
    })
    
    # Improvement #3, #12: Explicit ranking/highest/lowest patterns
    has_ranking_keywords = bool(set(q.split()) & {
        "top", "bottom", "highest", "lowest", "best", "worst", "most", "least",
        "first", "last", "leading", "trailing", "rank"
    })
    has_which_pattern = bool(re.search(r'\bwhich\s+(\w+).*?(highest|lowest|most|least)', q))
    
    # Improvement #2: How many → count conversion
    has_how_many = bool(re.search(r'\bhow\s+many\b', q))
    
    # Distribution/count indicators
    has_count_keywords = bool(set(q.split()) & {
        "count", "how", "many", "number", "quantity", "distribution",
        "breakdown", "split", "category", "each", "by"
    }) or has_how_many
    
    # Retrieval indicators
    has_retrieval_keywords = bool(set(q.split()) & {
        "show", "list", "display", "get", "retrieve", "fetch", "all", "details"
    })
    
    # Filter indicators
    has_filter_keywords = bool(set(q.split()) & {
        "where", "filter", "find", "with", "only", "just", "specific"
    })
    
    # Aggregation indicators
    has_agg_keywords = bool(set(q.split()) & {
        "sum", "total", "average", "avg", "mean", "median", "min", "max",
        "aggregate", "combined", "overall"
    })
    
    # KPI/summary indicators (Improvement #1: explicit KPI recognition)
    has_kpi_keywords = bool(set(q.split()) & {
        "what", "how", "overview", "summary", "status", "metric", "kpi"
    }) or has_explicit_kpi
    
    return {
        "temporal": has_temporal_keywords,
        "comparison": has_comparison_keywords,
        "ranking": has_ranking_keywords or has_which_pattern,  # Improvement #3, #12
        "count": has_count_keywords,
        "retrieval": has_retrieval_keywords,
        "filter": has_filter_keywords,
        "aggregation": has_agg_keywords,
        "kpi": has_kpi_keywords,  # Improvement #1, #2
    }


# FIX #38: Configurable intent rule engine (replaces large classify_query_intent)
# IMPROVEMENTS #1, #2, #3, #12: Enhanced KPI and ranking routing
INTENT_RULES = [
    # Priority 1: Explicit KPI queries (Improvement #1: explicit KPI routing)
    IntentRule(
        name="count_query_how_many",  # Improvement #2: how many → count
        intent="kpi",
        priority=105,
        required_conditions=["count"],
        forbidden_conditions=[],
        role_checks={"is_count": True}
    ),
    IntentRule(
        name="dataset_size_kpi",  # Improvement #1: row count, record count, dataset size
        intent="kpi",
        priority=104,
        required_conditions=["kpi"],
        forbidden_conditions=[],
        role_checks={}
    ),
    
    # Priority 2: Explicit ranking queries (Improvement #3, #12)
    IntentRule(
        name="which_product_ranking",  # Improvement #12: which X → top 1
        intent="ranking",
        priority=102,
        required_conditions=["ranking"],
        forbidden_conditions=[],
        role_checks={}
    ),
    IntentRule(
        name="highest_lowest_ranking",  # Improvement #3: highest/lowest/most/least
        intent="ranking",
        priority=101,
        required_conditions=["ranking"],
        forbidden_conditions=[],
        role_checks={"metric": True}
    ),
    
    # Priority 3: Temporal trend queries
    IntentRule(
        name="growth_trend",
        intent="trend",
        priority=100,
        required_conditions=["temporal", "aggregation"],
        forbidden_conditions=["comparison"],
        role_checks={"metric": True}
    ),
    IntentRule(
        name="period_comparison",
        intent="comparison",
        priority=99,
        required_conditions=["temporal", "comparison"],
        forbidden_conditions=[],
        role_checks={}
    ),
    IntentRule(
        name="simple_trend",
        intent="trend",
        priority=98,
        required_conditions=["temporal"],
        forbidden_conditions=[],
        role_checks={"metric": True}
    ),
    
    # Priority 4: Distribution/count queries
    IntentRule(
        name="grouped_count",
        intent="distribution",
        priority=80,
        required_conditions=["count"],
        forbidden_conditions=[],
        role_checks={"grouping_entity": True}
    ),
    IntentRule(
        name="categorical_distribution",
        intent="distribution",
        priority=79,
        required_conditions=["count"],
        forbidden_conditions=["metric"],
        role_checks={"grouping_entity": True}
    ),
    
    # Priority 5: Aggregation queries
    IntentRule(
        name="grouped_aggregation",
        intent="aggregation",
        priority=70,
        required_conditions=["aggregation"],
        forbidden_conditions=[],
        role_checks={"metric": True, "grouping_entity": True}
    ),
    IntentRule(
        name="simple_aggregation",
        intent="aggregation",
        priority=69,
        required_conditions=["aggregation"],
        forbidden_conditions=[],
        role_checks={"metric": True}
    ),
    
    # Priority 6: Comparison queries (non-temporal)
    IntentRule(
        name="value_comparison",
        intent="comparison",
        priority=60,
        required_conditions=["comparison"],
        forbidden_conditions=["temporal"],
        role_checks={"metric": True}
    ),
    
    # Priority 7: Retrieval queries
    IntentRule(
        name="raw_retrieval",
        intent="raw_retrieval",
        priority=40,
        required_conditions=["retrieval"],
        forbidden_conditions=["aggregation"],
        role_checks={"metric": False}
    ),
]


def classify_query_intent_rule_based(query: str, roles: Dict[str, Any]) -> Tuple[str, int]:
    """
    FIX #38: Rule-based intent classification (replaces regex-heavy function).
    IMPROVEMENTS #4, #17, #18: Enhanced routing, lower rigidity, debug logging
    Returns (intent, confidence_score)
    """
    conditions = detect_query_conditions(query)
    
    # Sort rules by priority (highest first)
    sorted_rules = sorted(INTENT_RULES, key=lambda r: r.priority, reverse=True)
    
    # Find first matching rule
    for rule in sorted_rules:
        if rule.evaluate(query, roles, conditions):
            # Confidence based on how many conditions matched
            matched_conditions = sum(1 for c in rule.required_conditions if conditions.get(c))
            confidence = min(0.3 + (matched_conditions * 0.15), 1.0)
            
            # Improvement #18: Log query-plan debugging info
            logger.info(f"Intent Route: {rule.name} → {rule.intent} (confidence: {confidence:.2f})")
            logger.debug(f"  Resolved metric: {roles.get('metric')}")
            logger.debug(f"  Resolved groupby: {roles.get('grouping_entity')}")
            logger.debug(f"  Resolved filters: {roles.get('filters')}")
            logger.debug(f"  Resolved operation: {roles.get('operation')}")
            
            return rule.intent, confidence
    
    # Improvement #4, #17: Lower routing rigidity - prefer execution when possible
    # If we have enough information for execution, prefer that over explanation
    if roles.get("metric") or roles.get("grouping_entity") or roles.get("is_count"):
        logger.info("Route: Preferring aggregation over explanation (have metric/grouping/count)")
        logger.debug(f"  Metric: {roles.get('metric')}, Groupby: {roles.get('grouping_entity')}, IsCount: {roles.get('is_count')}")
        return "aggregation", 0.35
    
    if conditions.get("retrieval"):
        logger.info("Route: Preferring raw_retrieval over explanation")
        return "raw_retrieval", 0.3
    
    # Improvement #16: Add unsupported-query recovery with meaningful fallback
    logger.info("Route: No matching intent rule found, defaulting to explanation")
    return "explanation", 0.2


@dataclass
class SemanticMatch:
    """Result of semantic matching with ranked candidates."""
    query_term: str
    column_name: str
    score: float                        # 0.0-1.0 confidence
    match_type: str                     # exact, synonym, semantic, heuristic
    explanation: str                    # Why this match


# FIX #38 + #39: Semantic ranker (replaces heuristic matching)
class SemanticRanker:
    """Ranks column candidates by semantic relevance with scoring."""
    
    def __init__(self, df: pd.DataFrame, meta: dict):
        self.df = df
        self.meta = meta
        self.numeric_cols = set(meta.get("numeric_cols", []))
        self.categorical_cols = set(meta.get("categorical_cols", []))
        self.all_cols = set(df.columns)
    
    def rank_for_metric(self, query_term: str) -> List[SemanticMatch]:
        """Rank numeric columns for metric matching."""
        candidates = []
        q_words = set(query_term.lower().split())
        
        for col in self.numeric_cols:
            col_words = set(col.lower().split('_'))
            
            # Score 1: Exact word match
            exact_match_ratio = len(q_words & col_words) / max(len(q_words), 1)
            score = 0.0
            match_type = "heuristic"
            
            if exact_match_ratio == 1.0:
                score = 0.95
                match_type = "exact"
            elif exact_match_ratio >= 0.5:
                score = 0.75 + (exact_match_ratio * 0.2)
                match_type = "semantic"
            else:
                # Check synonym matches from BUSINESS_SYNONYM_MAP
                score = self._check_synonyms(query_term, col)
                if score > 0:
                    match_type = "synonym"
                else:
                    score = 0.2  # Default low score for fallback
            
            if score > 0.15:  # Filter weak matches
                candidates.append(SemanticMatch(
                    query_term=query_term,
                    column_name=col,
                    score=score,
                    match_type=match_type,
                    explanation=f"{match_type.capitalize()} match ({score:.2f})"
                ))
        
        return sorted(candidates, key=lambda x: x.score, reverse=True)
    
    def rank_for_grouping(self, query_term: str) -> List[SemanticMatch]:
        """Rank categorical columns for grouping matching."""
        candidates = []
        q_words = set(query_term.lower().split())
        
        for col in self.categorical_cols:
            col_words = set(col.lower().split('_'))
            
            exact_match_ratio = len(q_words & col_words) / max(len(q_words), 1)
            score = 0.0
            match_type = "heuristic"
            
            if exact_match_ratio == 1.0:
                score = 0.95
                match_type = "exact"
            elif exact_match_ratio >= 0.5:
                score = 0.7 + (exact_match_ratio * 0.2)
                match_type = "semantic"
            else:
                score = 0.2
            
            if score > 0.15:
                candidates.append(SemanticMatch(
                    query_term=query_term,
                    column_name=col,
                    score=score,
                    match_type=match_type,
                    explanation=f"{match_type.capitalize()} match ({score:.2f})"
                ))
        
        return sorted(candidates, key=lambda x: x.score, reverse=True)
    
    def _check_synonyms(self, query_term: str, col_name: str) -> float:
        """Check if query_term matches col_name via business synonyms."""
        from_map = BUSINESS_SYNONYM_MAP.get(query_term.lower(), [])
        if col_name.lower() in from_map:
            return 0.75
        
        # Reverse check
        col_lower = col_name.lower()
        for key, synonyms in BUSINESS_SYNONYM_MAP.items():
            if query_term.lower() in synonyms and key.lower() in col_lower:
                return 0.7
        
        return 0.0


# FIX #38: Pluggable execution layer (replaces centralized execute_query_plan)
@dataclass
class ExecutionStrategy:
    """Strategy for executing a specific query type."""
    query_type: str
    executor_name: str
    supports_filters: bool = True
    supports_grouping: bool = True
    supports_sorting: bool = True
    supports_limit: bool = True


EXECUTION_STRATEGIES = {
    "trend": ExecutionStrategy("trend", "execute_trend", True, True, True, False),
    "comparison": ExecutionStrategy("comparison", "execute_comparison", True, True, True, False),
    "ranking": ExecutionStrategy("ranking", "execute_ranking", True, True, True, True),
    "aggregation": ExecutionStrategy("aggregation", "execute_aggregation", True, True, True, True),
    "distribution": ExecutionStrategy("distribution", "execute_distribution", True, False, True, True),
    "kpi": ExecutionStrategy("kpi", "execute_kpi", True, False, False, False),
    "raw_retrieval": ExecutionStrategy("raw_retrieval", "execute_raw_retrieval", True, False, True, True),
    "explanation": ExecutionStrategy("explanation", "execute_explanation", False, False, False, False),
}


def get_execution_strategy(query_type: str) -> Optional[ExecutionStrategy]:
    """Get execution strategy for query type."""
    return EXECUTION_STRATEGIES.get(query_type)



class ConfidenceScorer:
    """Scores confidence of query resolution based on multiple factors."""
    
    def __init__(self, df: pd.DataFrame, meta: dict, ranker: SemanticRanker):
        self.df = df
        self.meta = meta
        self.ranker = ranker
    
    def score_column_match(self, query_term: str, column_name: str) -> float:
        """Score how well query_term matches column_name."""
        if not column_name:
            return 0.0
        
        # Check if column exists
        if column_name not in self.df.columns:
            return 0.0
        
        # Use semantic ranker scores
        if column_name in self.meta.get("numeric_cols", []):
            matches = self.ranker.rank_for_metric(query_term)
            for match in matches:
                if match.column_name == column_name:
                    return match.score
        elif column_name in self.meta.get("categorical_cols", []):
            matches = self.ranker.rank_for_grouping(query_term)
            for match in matches:
                if match.column_name == column_name:
                    return match.score
        
        return 0.25  # Default low score
    
    def score_intent_clarity(self, conditions: Dict[str, bool], intent: str) -> float:
        """Score how clear the intent is based on condition matches."""
        score = 0.3  # baseline
        
        # More conditions matched = clearer intent
        matched_conditions = sum(1 for v in conditions.values() if v)
        score += min(matched_conditions * 0.15, 0.4)
        
        # Strong intent keywords boost score
        if intent in ["ranking", "aggregation", "trend"]:
            score += 0.15
        elif intent in ["comparison", "distribution"]:
            score += 0.10
        elif intent in ["kpi"]:
            score += 0.05
        
        return min(score, 1.0)
    
    def score_role_clarity(self, roles: Dict[str, Any]) -> float:
        """Score how clear the semantic roles are."""
        score = 0.2
        
        if roles.get("metric"):
            score += 0.25
        if roles.get("grouping_entity"):
            score += 0.2
        if roles.get("filters"):
            score += 0.15
        if roles.get("aggregation"):
            score += 0.2
        
        return min(score, 1.0)
    
    def score_filter_confidence(self, filters: Dict[str, Any]) -> float:
        """Score confidence in filter interpretation."""
        if not filters:
            return 0.5  # Neutral for no filters
        
        score = 0.3
        for col, val in filters.items():
            if col in self.df.columns:
                score += 0.35 / max(len(filters), 1)
        
        return min(score, 1.0)
    
    def calculate_total_confidence(self, metric_col: str, grouping_col: str,
                                   conditions: Dict[str, bool], roles: Dict[str, Any],
                                   filters: Dict[str, Any], intent: str) -> float:
        """
        FIX #40: Calculate comprehensive confidence score.
        Combines: column matching + intent clarity + role clarity + filter confidence
        """
        # Component scores (weighted)
        metric_score = self.score_column_match("metric", metric_col) if metric_col else 0.0
        grouping_score = self.score_column_match("grouping", grouping_col) if grouping_col else 0.0
        intent_score = self.score_intent_clarity(conditions, intent)
        role_score = self.score_role_clarity(roles)
        filter_score = self.score_filter_confidence(filters)
        
        # Weighted average
        weights = {
            "metric": 0.25,
            "grouping": 0.15,
            "intent": 0.25,
            "role": 0.20,
            "filter": 0.15
        }
        
        total = (
            metric_score * weights["metric"] +
            grouping_score * weights["grouping"] +
            intent_score * weights["intent"] +
            role_score * weights["role"] +
            filter_score * weights["filter"]
        )
        
        return round(min(total, 1.0), 2)


# ═══════════════════════════════════════════════════════════════════════════════
# FIX #41: REDUCE UNNECESSARY API USAGE - DETERMINISTIC EXECUTOR
# ═══════════════════════════════════════════════════════════════════════════════

class DeterministicExecutor:
    """Execute simple analytical queries using pandas (no LLM)."""
    
    @staticmethod
    def is_query_deterministic(query: str, plan: QueryPlan, meta: dict) -> bool:
        """
        FIX #41: Detect if query can be answered deterministically.
        Simple analytics don't need LLM reasoning.
        """
        q = query.lower()
        
        # Simple count queries
        if "count" in q or "how many" in q:
            return True
        
        # Simple aggregations (sum, avg, min, max, median)
        if any(op in q for op in ["sum", "average", "avg", "total", "minimum", "min", 
                                   "maximum", "max", "median", "typical"]):
            return True
        
        # Top/bottom queries with simple grouping
        if any(op in q for op in ["top", "bottom", "highest", "lowest"]):
            return True
        
        # Simple filtering
        if any(op in q for op in ["where", "filter", "with", "find"]):
            if len(meta.get("numeric_cols", [])) <= 10:
                return True
        
        # Distribution (groupby count)
        if "distribution" in q or "each" in q:
            return True
        
        # Raw retrieval
        if plan.query_type == "raw_retrieval":
            return True
        
        return False
    
    @staticmethod
    def execute_count_query(df: pd.DataFrame, plan: QueryPlan) -> dict:
        """Execute simple count query."""
        if plan.group_by_column and plan.group_by_column in df.columns:
            counts = df.groupby(plan.group_by_column).size().reset_index(name="count")
            counts = counts.sort_values("count", ascending=False).head(plan.limit)
            return {
                "type": "structured",
                "table": counts.to_dict(orient="records"),
                "chart": {"type": "bar", "labels": counts[plan.group_by_column].astype(str).tolist(),
                         "values": counts["count"].tolist()}
            }
        else:
            return {
                "type": "kpi",
                "scalar": len(df)
            }
    
    @staticmethod
    def execute_aggregation_query(df: pd.DataFrame, plan: QueryPlan) -> dict:
        """Execute simple aggregation query. (Improvement #6, #7: Preserve & validate metrics)"""
        # Improvement #6: Ensure metric is preserved from plan
        metric_col = plan.metric_column
        if not metric_col or metric_col not in df.columns:
            logger.warning(f"Metric preservation failed: {metric_col} not found")
            return {"type": "error", "insight": f"Metric column '{metric_col}' not found in dataset"}
        
        agg_op = plan.aggregation.operation if plan.aggregation else "sum"
        
        # Improvement #7: Log the aggregation for sanity checking
        logger.debug(f"Executing aggregation: {agg_op}({metric_col})")
        
        if plan.group_by_column and plan.group_by_column in df.columns:
            grouped = df.groupby(plan.group_by_column)[metric_col].agg(agg_op).reset_index()
            grouped.columns = [plan.group_by_column, agg_op]
            grouped = grouped.sort_values(agg_op, ascending=False).head(plan.limit)
            
            # Improvement #19: Sanity check - verify aggregation result matches operation
            if agg_op in ["avg", "mean"] and grouped[agg_op].dtype != "float64":
                logger.warning(f"Sanity check: Expected float for AVG, got {grouped[agg_op].dtype}")
            
            result = {
                "type": "structured",
                "table": sanitize_for_json(grouped.to_dict(orient="records")),
                "chart": {"type": "bar", "labels": grouped[plan.group_by_column].astype(str).tolist(),
                         "values": grouped[agg_op].tolist()},
                "aggregation": agg_op,
                "metric": metric_col
            }
        else:
            result_val = getattr(df[metric_col].dropna(), agg_op)()
            
            # Improvement #19: Sanity check for scalar aggregation
            logger.debug(f"Aggregation result sanity check: {agg_op} returned {type(result_val).__name__}")
            
            result = {
                "type": "kpi",
                "scalar": float(result_val),
                "aggregation": agg_op,
                "metric": metric_col
            }
        
        return result
    
    @staticmethod
    def execute_ranking_query(df: pd.DataFrame, plan: QueryPlan) -> dict:
        """Execute top/bottom ranking query. (Improvement #8: Use metric-first selection)"""
        # Improvement #8: Prefer metric column over count for ranking
        metric_col = plan.metric_column
        if not metric_col or metric_col not in df.columns:
            logger.debug(f"Metric not available for ranking: {metric_col}, using record count instead")
            metric_col = None
        
        if metric_col:
            # Rank by metric (improvement #8)
            ascending = plan.sort_order == "asc"
            limit = plan.limit or 5
            
            top_rows = df.nlargest(limit, metric_col) if not ascending else \
                      df.nsmallest(limit, metric_col)
            
            logger.debug(f"Ranking: By metric column '{metric_col}'")
            
            return {
                "type": "structured",
                "table": sanitize_for_json(top_rows.to_dict(orient="records")),
                "chart": {"type": "bar"},
                "ranking_metric": metric_col
            }
        else:
            # Fallback: count by group
            if plan.group_by_column and plan.group_by_column in df.columns:
                counts = df.groupby(plan.group_by_column).size().reset_index(name="count")
                counts = counts.sort_values("count", ascending=False).head(plan.limit)
                
                logger.debug(f"Ranking: By record count grouped by '{plan.group_by_column}'")
                
                return {
                    "type": "structured",
                    "table": sanitize_for_json(counts.to_dict(orient="records")),
                    "chart": {"type": "bar"},
                    "ranking_metric": "count"
                }
        
        logger.warning("Ranking query: No metric or grouping available")
        return {"type": "error", "insight": "Unable to determine ranking metric"}
    
    @staticmethod
    def execute_raw_retrieval_query(df: pd.DataFrame, plan: QueryPlan) -> dict:
        """Execute raw data retrieval."""
        limit = plan.limit or 10
        sample = df.head(limit)
        
        return {
            "type": "table",
            "table": sample.to_dict(orient="records"),
            "row_count": len(df)
        }


# ═══════════════════════════════════════════════════════════════════════════════
# FIX #42: RESPONSE RENDERER LAYER
# IMPROVEMENTS #14, #15: Temporal serialization and response type standardization
# ═══════════════════════════════════════════════════════════════════════════════

def sanitize_for_json(obj):
    """
    IMPROVEMENTS #14, #15: Convert non-JSON-serializable objects to strings.
    Handles: Period, Timestamp, Quarter, datetime, date
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    elif hasattr(obj, 'strftime'):  # datetime/date-like
        return obj.isoformat()
    elif hasattr(obj, 'to_timestamp'):  # pandas Period
        return str(obj)
    elif hasattr(obj, 'freqstr'):  # pandas Period (alt check)
        return str(obj)
    elif isinstance(obj, (pd.Timestamp, pd.Period)):
        return str(obj)
    elif hasattr(obj, '__str__') and str(type(obj).__name__).startswith('Period'):
        return str(obj)
    elif pd.isna(obj):
        return None
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        # Fallback for unknown types
        return str(obj)

class ResponseRenderer:
    """Formats query responses appropriately based on query type."""
    
    @staticmethod
    def render_kpi(result: dict, title: str, plan: QueryPlan) -> dict:
        """Render key performance indicator (scalar value)."""
        return {
            "type": "kpi",  # Improvement #20: Standardized response type
            "title": title,
            "scalar": result.get("scalar"),
            "visualization": "scalar",
            "confidence_metrics": {}
        }
    
    @staticmethod
    def render_comparison(result: dict, title: str, plan: QueryPlan) -> dict:
        """Render comparison (side-by-side values)."""
        table = sanitize_for_json(result.get("table", []))
        if not table:
            return {"type": "error", "insight": "No data for comparison"}
        
        return {
            "type": "comparison",  # Improvement #20: Standardized response type
            "title": title,
            "visualization": "bar",
            "table": table,
            "chart": result.get("chart", {"type": "bar"}),
            "comparison_mode": True
        }
    
    @staticmethod
    def render_ranking(result: dict, title: str, plan: QueryPlan) -> dict:
        """Render ranked results."""
        table = sanitize_for_json(result.get("table", []))
        return {
            "type": "ranking",  # Improvement #20: Standardized response type
            "title": title,
            "visualization": "bar",
            "table": table,
            "chart": result.get("chart", {"type": "bar"}),
            "ranking_mode": True,
            "sort_order": plan.sort_order,
            "limit": plan.limit
        }
    
    @staticmethod
    def render_distribution(result: dict, title: str, plan: QueryPlan) -> dict:
        """Render distribution/categorical breakdown."""
        table = sanitize_for_json(result.get("table", []))
        return {
            "type": "distribution",  # Improvement #20: Standardized response type
            "title": title,
            "visualization": "pie",
            "table": table,
            "chart": result.get("chart", {"type": "pie"}),
            "distribution_mode": True
        }
    
    @staticmethod
    def render_table(result: dict, title: str, plan: QueryPlan) -> dict:
        """Render raw table data."""
        table = sanitize_for_json(result.get("table", []))
        return {
            "type": "table",  # Improvement #20: Standardized response type
            "title": title,
            "visualization": "table",
            "table": table,
            "row_count": len(table)
        }
    
    @staticmethod
    def render(result: dict, title: str, plan: QueryPlan) -> dict:
        """
        FIX #42: Route to appropriate renderer based on query type.
        IMPROVEMENTS #14, #15, #20: Serialize temporal values, standardize response types
        """
        query_type = plan.query_type
        
        if query_type == "kpi":
            return ResponseRenderer.render_kpi(result, title, plan)
        elif query_type == "comparison":
            return ResponseRenderer.render_comparison(result, title, plan)
        elif query_type == "trend":
            return ResponseRenderer.render_trend(result, title, plan)
        elif query_type == "ranking":
            return ResponseRenderer.render_ranking(result, title, plan)
        elif query_type == "distribution":
            return ResponseRenderer.render_distribution(result, title, plan)
        elif query_type == "raw_retrieval":
            return ResponseRenderer.render_table(result, title, plan)
        else:
            # Improvement #20: Standardize fallback response type to "chart"
            table = sanitize_for_json(result.get("table", []))
            return {
                "type": "chart",  # Standardized response type
                "title": title,
                "table": table,
                "chart": result.get("chart")
            }


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


def detect_operations(query: str, intent: str, roles: Dict[str, Any]) -> List[str]:
    """
    Stage 2: Detect what operations the query needs.
    Returns list of operations: filter, group_by, sum, avg, sort, limit, etc.
    """
    operations = []
    q = query.lower()
    
    # Filter operations
    if roles.get("filters"):
        operations.append("filter")
    
    # Grouping operations
    if roles.get("grouping_entity"):
        operations.append("group_by")
    
    # Aggregation operations
    if roles.get("aggregation"):
        operations.append(roles["aggregation"])
    elif roles.get("is_count"):
        operations.append("count")
    elif roles.get("metric"):
        operations.append("aggregate")
    
    # Temporal operations
    if intent in ["trend", "comparison"]:
        operations.append("temporal_aggregate")
        if roles.get("is_cumulative"):
            operations.append("cumulative_sum")
    
    # Ranking/sorting
    if intent == "ranking" or "top" in q or "bottom" in q:
        operations.append("sort")
        operations.append("limit")
    
    # Distribution
    if intent == "distribution":
        operations.append("distribution")
    
    # Pagination/limiting
    if re.search(r'\b(top\s+\d+|limit|first\s+\d+)\b', q):
        operations.append("limit")
    
    return operations


def perform_semantic_mapping(query: str, df: pd.DataFrame, meta: dict,
                           roles: Dict[str, Any]) -> Dict[str, str]:
    """
    Stage 3: Map query terms to actual columns using semantic understanding.
    Returns dict: query_term → column_name
    """
    mapping = {}
    q = query.lower()
    
    # Map metric
    if roles.get("metric"):
        mapping["metric"] = roles["metric"]
        # Add common synonyms for this metric
        metric_col = roles["metric"]
        if metric_col in df.columns:
            for synonym_term in ["amount", "value", "total", "quantity", "count"]:
                if synonym_term in q:
                    mapping[synonym_term] = metric_col
    
    # Map grouping entity
    if roles.get("grouping_entity"):
        mapping["grouping"] = roles["grouping_entity"]
        grouping_col = roles["grouping_entity"]
        if grouping_col in df.columns:
            for synonym_term in ["by", "per", "category", "type", "segment"]:
                if synonym_term in q:
                    mapping[synonym_term] = grouping_col
    
    # Map temporal column if present
    date_col = meta.get("date_col")
    if date_col and date_col in df.columns:
        if any(t in q for t in ["date", "time", "period", "month", "year", "day", "week"]):
            mapping["temporal"] = date_col
    
    # Map filter columns
    for filter_col, filter_val in roles.get("filters", {}).items():
        if filter_col in df.columns:
            mapping[f"filter_{filter_col}"] = filter_col
    
    return mapping


def validate_resolution_consistency(intent: str, operations: List[str],
                                    semantic_mapping: Dict[str, str],
                                    filters: Dict[str, Any],
                                    df: pd.DataFrame, meta: dict) -> Tuple[bool, List[str]]:
    """
    Validate that the multi-step resolution is internally consistent.
    Returns (is_valid, issues_list)
    """
    issues = []
    
    # Consistency check 1: temporal operations only valid for trend/comparison
    if any(op in ["temporal_aggregate", "cumulative_sum"] for op in operations):
        if intent not in ["trend", "comparison"]:
            issues.append(f"Temporal operations incompatible with intent '{intent}'")
    
    # Consistency check 2: grouping operations need grouping entity in semantic mapping
    if "group_by" in operations:
        if "grouping" not in semantic_mapping:
            issues.append("Group operation detected but no grouping column mapped")
    
    # Consistency check 3: aggregation operations need metric
    agg_ops = {"sum", "avg", "count", "min", "max", "median", "stddev", "aggregate"}
    if any(op in operations for op in agg_ops):
        if "metric" not in semantic_mapping:
            if intent not in ["distribution"]:  # distribution can work without explicit metric
                issues.append("Aggregation operation detected but no metric column mapped")
    
    # Consistency check 4: filters must map to actual columns
    numeric_cols = set(meta.get("numeric_cols", []))
    categorical_cols = set(meta.get("categorical_cols", []))
    all_mapped_cols = set(v for k, v in semantic_mapping.items() if not k.startswith("filter_"))
    
    for filter_col in filters.keys():
        if filter_col not in df.columns:
            issues.append(f"Filter column '{filter_col}' does not exist in dataset")
    
    return len(issues) == 0, issues


def calculate_resolution_confidence(intent: str, operations: List[str],
                                    semantic_mapping: Dict[str, str],
                                    filters: Dict[str, Any],
                                    roles: Dict[str, Any]) -> Tuple[float, float]:
    """
    Calculate overall confidence (0.0-1.0) and resolution score (0.0-1.0).
    Returns (confidence, resolution_score)
    """
    confidence = 0.3  # baseline
    
    # Intent detection confidence
    if intent in ["trend", "aggregation", "ranking", "kpi"]:
        confidence += 0.2
    else:
        confidence += 0.1
    
    # Operation clarity
    if len(operations) >= 2:  # clear operations detected
        confidence += 0.15
    elif len(operations) == 1:
        confidence += 0.08
    
    # Semantic mapping quality
    num_mapped_terms = len(semantic_mapping)
    if num_mapped_terms >= 3:
        confidence += 0.2
    elif num_mapped_terms >= 2:
        confidence += 0.15
    elif num_mapped_terms >= 1:
        confidence += 0.1
    
    # Filter quality
    if filters:
        confidence += 0.1
    
    # Role scoring from existing function
    confidence += score_plan_confidence(intent, roles) * 0.2
    
    confidence = min(confidence, 1.0)
    
    # Resolution score: how complete/consistent the resolution is
    resolution_score = 0.3
    
    if len(operations) >= 2:
        resolution_score += 0.2
    if num_mapped_terms >= 2:
        resolution_score += 0.2
    if filters:
        resolution_score += 0.15
    
    # Boost if all key elements present
    has_intent = bool(intent)
    has_operations = len(operations) >= 1
    has_mapping = num_mapped_terms >= 2
    
    if has_intent and has_operations and has_mapping:
        resolution_score += 0.15
    
    resolution_score = min(resolution_score, 1.0)
    
    return confidence, resolution_score


def resolve_query_multi_step(query: str, df: pd.DataFrame, meta: dict,
                            history: List[dict]) -> QueryResolution:
    """
    Multi-stage query resolution: intent → operations → semantic mapping →
    filter extraction → execution planning.
    
    This avoids fragile one-pass logic by explicitly separating concerns
    and validating consistency at each stage.
    """
    issues = []
    
    # ─────────────────────────────────────────────
    # Stage 1: INTENT DETECTION
    # ─────────────────────────────────────────────
    roles = extract_semantic_roles(query, df, meta)
    intent = classify_query_intent(query, roles, meta, history)
    
    # ─────────────────────────────────────────────
    # Stage 2: OPERATION DETECTION
    # ─────────────────────────────────────────────
    operations = detect_operations(query, intent, roles)
    
    # ─────────────────────────────────────────────
    # Stage 3: SEMANTIC MAPPING
    # ─────────────────────────────────────────────
    semantic_mapping = perform_semantic_mapping(query, df, meta, roles)
    
    # ─────────────────────────────────────────────
    # Stage 4: FILTER EXTRACTION
    # ─────────────────────────────────────────────
    # Filters already extracted in Stage 1, stored in roles
    filters = roles.get("filters", {})
    
    # ─────────────────────────────────────────────
    # Stage 5: EXECUTION PLANNING & VALIDATION
    # ─────────────────────────────────────────────
    is_valid, consistency_issues = validate_resolution_consistency(
        intent, operations, semantic_mapping, filters, df, meta
    )
    issues.extend(consistency_issues)
    
    if not is_valid:
        # Try to repair based on issues
        if "no grouping column mapped" in str(issues):
            if roles.get("grouping_entity"):
                semantic_mapping["grouping"] = roles["grouping_entity"]
                is_valid = True
                issues = [i for i in issues if "no grouping column" not in i]
    
    # Calculate confidence scores
    confidence, resolution_score = calculate_resolution_confidence(
        intent, operations, semantic_mapping, filters, roles
    )
    
    # Build QueryPlan with full context
    execution_plan = None
    try:
        execution_plan = build_query_plan(query, df, meta, history)
    except Exception as e:
        issues.append(f"Execution plan build failed: {str(e)[:50]}")
    
    # Compile metadata for debugging
    metadata = {
        "stage1_roles_count": len(roles),
        "stage2_operations_count": len(operations),
        "stage3_mappings_count": len(semantic_mapping),
        "stage4_filters_count": len(filters),
        "stage5_valid": is_valid,
        "debug_intent": intent,
        "debug_role_keys": list(roles.keys())
    }
    
    return QueryResolution(
        intent=intent,
        operations=operations,
        semantic_mapping=semantic_mapping,
        filters=filters,
        execution_plan=execution_plan,
        confidence=confidence,
        resolution_score=resolution_score,
        issues=issues,
        metadata=metadata
    )


def build_query_plan(query: str, df: pd.DataFrame, meta: dict,
                     history: List[dict]) -> QueryPlan:

    roles       = extract_semantic_roles(query, df, meta)

    # Filter-only KPI queries should remain scalar
    if (
        roles.get("is_count")
        and roles.get("filters")
        and not re.search(r"\bby\b|\bper\b", query.lower())
    ):
        roles["grouping_entity"] = None

    query_type  = classify_query_intent(query, roles, meta, history)
    is_followup = detect_followup(query, history)

    agg_operation = roles["aggregation"]

    if agg_operation == "unique_count":
        agg_operation = "count"

    agg_spec = (
        AggregationSpec(
            operation=agg_operation,
            column=roles["metric"]
        )
        if roles["aggregation"]
        else None
    )

    relevant_cols = select_relevant_columns(query, query_type, roles, df, meta)
    confidence    = score_plan_confidence(query_type, roles)

    # ─────────────────────────────
    # Dynamic Visualization Planning
    # ─────────────────────────────
    if query_type == "kpi":
        visualization = "scalar"
    elif query_type == "trend":
        visualization = "line"
    elif query_type == "comparison":
        visualization = "bar"
    elif query_type == "distribution":
        visualization = "pie"
    elif query_type in ("aggregation", "ranking") and roles.get("grouping_entity"):
        visualization = "bar"
    elif query_type == "raw_retrieval":
        visualization = "table"
    else:
        visualization = "table"

    # ─────────────────────────────
    # Dynamic Execution Planning
    # ─────────────────────────────
    if query_type == "ranking":
        execution_mode = "ranked"
    elif query_type == "kpi":
        execution_mode = "kpi"
    elif query_type == "aggregation":
        execution_mode = "grouped" if roles.get("grouping_entity") else "scalar"
    elif query_type == "distribution":
        execution_mode = "grouped"
    elif query_type == "trend":
        execution_mode = "trend"
    elif query_type == "comparison":
        execution_mode = "comparison"
    elif query_type == "raw_retrieval":
        execution_mode = "raw"
    else:
        execution_mode = "scalar"

    # Build and return the final QueryPlan
    plan = QueryPlan(
        query_type=query_type,
        operation=roles.get("operation"),
        metric_column=roles["metric"],
        aggregation=agg_spec,
        group_by_column=roles["grouping_entity"],
        filters=roles["filters"],
        sort_by=roles["metric"],
        sort_order="desc" if roles.get("ranking", {}).get("direction") != "asc" else "asc",
        limit=roles.get("ranking", {}).get("limit"),
        relevant_columns=relevant_cols,
        confidence=confidence,
        is_followup=is_followup,
        raw_query=query,
        visualization=visualization,
        execution_mode=execution_mode,
        roles=roles
    )

    # Extra flags
    plan._cat_dist_col      = roles.get("cat_dist_col")
    plan._is_count          = roles.get("is_count", False)
    plan._sort_by_date_desc = bool(
        re.search(r'\b(recent|latest|newest|last\s+\d+|most\s+recent)\b', query.lower())
    )

    # Handle follow-ups
    if is_followup:
        plan = inherit_context(plan, history, df, meta)

    # Repair query if needed
    plan, _ = repair_query(query, plan, meta)

    # Re-score after repair
    roles_after     = extract_semantic_roles(plan.repaired_query or query, df, meta)
    plan.confidence = score_plan_confidence(plan.query_type, roles_after)

    if plan.confidence < 0.3 and not is_followup:
        plan.clarification_needed = True
        plan.clarification_reason = generate_clarification(plan, meta)

    return plan


def select_relevant_columns(query: str, query_type: str, roles: Dict[str, Any],
                            df: pd.DataFrame, meta: dict) -> List[str]:
    id_cols  = set(meta.get("id_like_cols", []))
    free_txt = set(meta.get("free_text_cols", []))
    exclude  = id_cols | free_txt
    relevant = []

    if roles.get("metric") and roles["metric"] in df.columns and roles["metric"] not in exclude:
        relevant.append(roles["metric"])
    if roles.get("grouping_entity") and roles["grouping_entity"] in df.columns:
        relevant.append(roles["grouping_entity"])

    if query_type == "raw_retrieval":
        priority = []
        if meta.get("primary_entity_col") and meta["primary_entity_col"] not in exclude:
            priority.append(meta["primary_entity_col"])
        if meta.get("date_col"):
            priority.append(meta["date_col"])
        for col in meta.get("numeric_cols", []):
            if col not in exclude and col not in priority:
                priority.append(col)
        for col in meta.get("low_cardinality_cols", []):
            if col not in exclude and col not in priority:
                priority.append(col)
        return priority[:8]

    if query_type == "trend":
        dc = meta.get("date_col")
        if dc and dc not in relevant:
            relevant.insert(0, dc)

    if query_type == "comparison":
        for col in meta.get("numeric_cols", []):
            if col not in relevant and col not in exclude:
                relevant.append(col)

    label_col = next(
        (c for c in meta.get("low_cardinality_cols", [])
         if c not in relevant and c not in exclude),
        meta.get("primary_entity_col") if meta.get("primary_entity_col") not in exclude else None
    )
    if label_col and label_col not in relevant:
        relevant.insert(0, label_col)

    if not relevant:
        relevant = [c for c in df.columns if c not in exclude][:6]

    return relevant


def score_plan_confidence(query_type: str, roles: Dict[str, Any]) -> float:
    score = 0.3
    if roles.get("metric"):                        score += 0.2
    if roles.get("aggregation"):                   score += 0.15
    if roles.get("grouping_entity"):               score += 0.15
    if roles.get("filters"):                       score += 0.1
    if roles.get("ranking", {}).get("direction"):  score += 0.1
    return min(score, 1.0)


def generate_clarification(plan: QueryPlan, meta: dict) -> str:
    num = meta.get("numeric_cols", [])
    cat = meta.get("categorical_cols", [])
    if not plan.metric_column and num:
        return f"Which metric? E.g.: {', '.join(num[:5])}."
    sugg = []
    if num:         sugg.append(f"'Top 5 by {num[0]}'")
    if cat and num: sugg.append(f"'Average {num[0]} by {cat[0]}'")
    sugg.append("'Explain this dataset'")
    return f"Could you rephrase? Try: {', '.join(sugg)}"


# ═══════════════════════════════════════════════════════════════════════════════
# AI FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def hash_prompt(prompt: str) -> str:
    return hashlib.md5(prompt.encode()).hexdigest()


def call_ai(prompt: str, use_cache: bool = True,
            system: str = None, max_tokens: int = 500) -> Tuple[str, bool]:
    if not API_KEY:
        return "AI unavailable: OPENROUTER_API_KEY not configured.", False
    prompt_hash = hash_prompt((system or "") + prompt)
    if use_cache and prompt_hash in ai_response_cache:
        return ai_response_cache[prompt_hash], True
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        res  = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}",
                     "Content-Type": "application/json"},
            json={"model": "openrouter/auto", "messages": messages,
                  "max_tokens": max_tokens},
            timeout=25
        )
        data     = res.json()
        response = data.get("choices",[{}])[0].get("message",{}).get("content","No response.")
        if use_cache:
            ai_response_cache[prompt_hash] = response
        return response, False
    except Exception as e:
        logger.error("AI call failed: %s", e)
        return f"AI unavailable: {e}", False


def answer_with_ai(query: str, df: pd.DataFrame, meta: dict,
                   context: str = "", history: List[dict] = None) -> str:
    sample = df.head(15).to_dict(orient="records")
    hist_ctx = ""
    if history:
        hist_ctx = "\n".join(
            f"Q: {h['raw_query']}\nA: {str(h.get('response',{}).get('insight',''))[:150]}"
            for h in history[-2:]
        )
    system = ("You are a concise data analyst. Answer ONLY based on provided data. "
              "Specific numbers. Under 120 words.")
    prompt = (f"Dataset: {context}\nColumns: {json.dumps(meta.get('col_stats',{}), default=str)[:400]}\n"
              f"Sample: {json.dumps(sample, default=str)[:800]}\n")
    if hist_ctx:
        prompt += f"\nContext:\n{hist_ctx}\n"
    prompt += f"\nQuestion: {query}"
    response, _ = call_ai(prompt, system=system, max_tokens=300)
    return response


SPECULATIVE_PHRASES = [
    "likely","probably","appears to","seems to","suggests that","might be",
    "could be","may indicate","possibly","presumably","it looks like","i think",
    "i believe","perhaps","one might","this could mean","this may mean",
    "appears lower","appears higher","appears to be","would suggest",
    "we can assume","it seems",
]


def _sanitize_insight(text: str) -> str:
    replacements = {
        "likely":"notably","probably":"specifically","appears to":"shows",
        "seems to":"shows","suggests that":"shows that","might be":"is",
        "could be":"is","may indicate":"indicates","possibly":"",
        "presumably":"","it looks like":"the data shows",
        "appears lower":"is lower","appears higher":"is higher",
        "appears to be":"is","would suggest":"shows",
        "we can assume":"the data shows","it seems":"the data shows",
        "one might":"","this could mean":"this means",
        "this may mean":"this means","i think":"","i believe":"","perhaps":"",
    }
    result = text
    for phrase, replacement in replacements.items():
        result = re.sub(re.escape(phrase), replacement, result, flags=re.IGNORECASE)
    return result.strip()


def _contains_speculation(text: str) -> bool:
    tl = text.lower()
    return any(p in tl for p in SPECULATIVE_PHRASES)


def is_result_meaningful(result_df: pd.DataFrame, plan: QueryPlan) -> Tuple[bool, str]:
    if result_df.empty:
        return False, "Result is empty."
    n = len(result_df)
    if n == 1 and plan.query_type not in ("aggregation","kpi"):
        return False, "Single-row result."
    if len(result_df.columns) == 1 and result_df[result_df.columns[0]].nunique() <= 1:
        return False, "All values identical."
    if plan.query_type == "distribution" and n <= 1:
        return False, "Too few categories."
    num_data = result_df.select_dtypes(include=[np.number])
    if not num_data.empty and n > 1:
        all_zero = all(
            num_data[c].std() == 0 for c in num_data.columns
            if num_data[c].notna().sum() > 1
        )
        if all_zero:
            return False, "No numeric variance."
    return True, ""


def generate_ai_insight(query: str, result_df: pd.DataFrame,
                        plan: QueryPlan, context: str = "") -> Optional[str]:
    if plan.confidence < 0.35:
        return None
    ok, reason = is_result_meaningful(result_df, plan)
    if not ok:
        logger.info("Skipping insight: %s", reason)
        return None
    sample = result_df.head(8).to_dict(orient="records")
    system = (
        "You are a precise data analyst. Describe ONLY what is visible in the data. "
        "Start each with '- '. Use exact numbers. "
        "Banned words: likely, probably, appears to, suggests, might, could, seems. "
        "Max 3 insights, under 100 words."
    )
    prompt = (
        f"Query: {query}\nType: {plan.query_type}\n"
        f"Metric: {plan.metric_column or 'N/A'}\n"
        f"Grouped by: {plan.group_by_column or 'N/A'}\n"
        f"Filters: {json.dumps(plan.filters) if plan.filters else 'None'}\n"
        f"Result ({len(result_df)} rows):\n{json.dumps(sample, default=str)[:600]}\n\n"
        "2-3 factual insights. Only reference numbers above."
    )
    response, _ = call_ai(prompt, system=system, max_tokens=150)
    if not response or response.startswith(("No response","AI unavailable")):
        return None
    response = _sanitize_insight(response)
    if _contains_speculation(response):
        logger.warning("Discarding speculative insight.")
        return None
    return response


def summarize_dataset(df: pd.DataFrame, meta: dict) -> str:
    sample = df.head(5).to_dict(orient="records")
    system = "Data analyst. Describe dataset in 2 sentences. Be specific."
    prompt = (f"Columns: {df.columns.tolist()}\nNumeric: {meta.get('numeric_cols',[])}\n"
              f"Categorical: {meta.get('categorical_cols',[])}\nDates: {meta.get('datetime_cols',[])}\n"
              f"Rows: {len(df)}\nSample: {json.dumps(sample, default=str)[:400]}")
    response, _ = call_ai(prompt, system=system, max_tokens=120)
    return response


# ═══════════════════════════════════════════════════════════════════════════════
# SUGGESTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_suggestions(df: pd.DataFrame, meta: dict) -> List[str]:
    id_cols  = set(meta.get("id_like_cols", []))
    safe_num = [c for c in meta.get("numeric_cols", []) if c not in id_cols]
    cat_cols = meta.get("low_cardinality_cols", []) or meta.get("categorical_cols", [])
    date_col = meta.get("date_col")
    sugg     = []
    
    # Standard queries
    for col in safe_num[:2]:
        sugg.append(f"Top 5 by {col}")
        sugg.append(f"Average {col}")
    if len(safe_num) >= 2:
        sugg.append(f"Compare {safe_num[0]} and {safe_num[1]}")
    if cat_cols:
        sugg.append(f"Distribution of {cat_cols[0]}")
        if safe_num:
            sugg.append(f"Average {safe_num[0]} by {cat_cols[0]}")
    
    # Time-series queries
    if date_col and safe_num:
        sugg.append(f"Trend of {safe_num[0]} over time")
        sugg.append(f"Monthly {safe_num[0]}")
        sugg.append(f"Daily {safe_num[0]}")
        sugg.append(f"Monthly growth of {safe_num[0]}")
        sugg.append(f"Year-over-year {safe_num[0]}")
        sugg.append(f"{safe_num[0]} by month")
    
    sugg.append("Explain this dataset")
    return sugg[:8]


# ═══════════════════════════════════════════════════════════════════════════════
# TIME-SERIES QUERY SUPPORT: DETECT TIME PATTERNS & GROWTH METRICS
# ═══════════════════════════════════════════════════════════════════════════════

def detect_time_granularity_preference(query: str) -> Optional[str]:
    """Detect explicit time granularity from query: year, quarter, month, week, day."""
    q = query.lower()
    
    if re.search(r'\b(year(?:ly)?|annual(?:ly)?)\b', q):
        return "Y"
    if re.search(r'\b(quarter(?:ly)?|q[1-4])\b', q):
        return "Q"
    if re.search(r'\b(month(?:ly)?)\b', q):
        return "M"
    if re.search(r'\b(week(?:ly)?)\b', q):
        return "W"
    if re.search(r'\b(day|daily)\b', q):
        return "D"
    
    return None


def infer_optimal_granularity(df: pd.DataFrame, date_col: str, metric_col: str,
                              query: str) -> str:
    """AUTOMATIC GRANULARITY INFERENCE: Intelligently choose granularity based on data."""
    # Check for explicit preference first
    explicit = detect_time_granularity_preference(query)
    if explicit:
        return explicit
    
    try:
        date_series = pd.to_datetime(df[date_col], errors="coerce")
        if date_series.isna().all():
            return "M"  # Default to monthly
        
        date_range = (date_series.max() - date_series.min()).days
        n_unique_dates = date_series.nunique()
        
        # ─────────────────────────────────────────────────────────────────────────
        # Rule-based inference: balance detail vs. noise reduction
        # ─────────────────────────────────────────────────────────────────────────
        
        # Very small range (< 2 weeks): Use daily
        if date_range <= 14:
            return "D"
        
        # Small range (2-12 weeks): Use weekly, unless there are very few unique dates
        if date_range <= 84:
            if n_unique_dates >= 10:
                return "W"
            elif n_unique_dates >= 5:
                return "D"
            else:
                return "D"
        
        # Medium range (3-12 months): Use weekly or monthly
        if date_range <= 365:
            # If lots of daily data, use weekly to avoid too many bars
            if n_unique_dates >= 50:
                return "W"
            elif n_unique_dates >= 30:
                return "W"
            else:
                return "D"
        
        # Large range (1-3 years): Use monthly
        if date_range <= 1095:
            if n_unique_dates >= 100:
                return "M"
            elif n_unique_dates >= 50:
                return "M"
            else:
                return "W"
        
        # Very large range (3+ years): Use quarterly or yearly
        if date_range <= 2555:  # ~7 years
            return "Q"
        
        # Multi-year: Use yearly
        return "Y"
    
    except Exception:
        return "M"  # Default fallback


def is_growth_query(query: str) -> bool:
    """Detect queries about growth, decline, or rate of change."""
    q = query.lower()
    growth_patterns = [
        r"\bgrowth\b",
        r"\bgrowing\b",
        r"\bincreasing\b",
        r"\bdecrease\b",
        r"\bdeclining\b",
        r"\bmonth over month\b",
        r"\bmom\b",
        r"\byear over year\b",
        r"\byoy\b",
        r"\bperiod.over.period\b",
        r"\bpop\b",
        r"\bpace\b",
        r"\brate\b",
        r"\baccelerating\b",
        r"\bslow\b.+\bgrowth\b",
    ]
    return any(re.search(p, q) for p in growth_patterns)


def is_comparison_period_query(query: str) -> bool:
    """Detect queries comparing periods: 'vs last month', 'compared to'."""
    q = query.lower()
    comparison_patterns = [
        r"\bvs\b.+\b(month|quarter|year|week|day)\b",
        r"\bcompared to\b.+\b(last|previous|prior)\b.+\b(month|quarter|year|week|day)\b",
        r"\b(last|previous|prior)\b.+\b(month|quarter|year|week|day)\b",
        r"\byear.to.date\b",
        r"\bytd\b",
    ]
    return any(re.search(p, q) for p in comparison_patterns)


def auto_datetime_grouping(df: pd.DataFrame, date_col: str,
                           query: str, metric_col: str = None) -> Tuple[pd.Series, str, str]:
    """FIX #25 + TIME-SERIES: Auto-detect year/quarter/month/week/day granularity with intelligent inference.
    
    Returns: (grouped_series, label, granularity_code)
    """
    date_series = pd.to_datetime(df[date_col], errors="coerce")
    
    # Use automatic inference if metric_col provided, else use preference-based detection
    if metric_col:
        granularity = infer_optimal_granularity(df, date_col, metric_col, query)
    else:
        granularity = detect_time_granularity_preference(query)
        if not granularity:
            date_range = (date_series.max() - date_series.min()).days if date_series.notna().any() else 0
            if date_range > 730:
                granularity = "Q"
            elif date_range > 90:
                granularity = "M"
            elif date_range > 14:
                granularity = "W"
            else:
                granularity = "D"
    
    # Convert granularity code to period and label
    if granularity == "Y":
        return date_series.dt.to_period("Y").astype(str), "Year", "Y"
    elif granularity == "Q":
        return date_series.dt.to_period("Q").astype(str), "Quarter", "Q"
    elif granularity == "M":
        return date_series.dt.to_period("M").astype(str), "Month", "M"
    elif granularity == "W":
        return date_series.dt.to_period("W").astype(str), "Week", "W"
    else:  # "D"
        return date_series.dt.date.astype(str), "Day", "D"


def intelligent_resample(df: pd.DataFrame, date_col: str, metric_col: str,
                         granularity: str, agg_op: str = "sum") -> pd.DataFrame:
    """INTELLIGENT RESAMPLING: Resample time series with appropriate aggregation.
    
    Handles NaN values, outliers, and sparse data intelligently.
    """
    try:
        tmp = df[[date_col, metric_col]].copy()
        tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
        tmp = tmp.dropna()
        
        if tmp.empty:
            return pd.DataFrame()
        
        # Set date as index for resampling
        tmp = tmp.set_index(date_col)
        tmp = tmp.sort_index()
        
        # Map granularity to pandas offset alias
        freq_map = {"Y": "YS", "Q": "QS", "M": "MS", "W": "WS", "D": "D"}
        freq = freq_map.get(granularity, "MS")
        
        # Map aggregation operation
        agg_map = {
            "sum": "sum", "avg": "mean", "mean": "mean", "count": "count",
            "min": "min", "max": "max", "median": "median", "stddev": "std"
        }
        agg_fn = agg_map.get(agg_op, "sum")
        
        # Resample: forward fill small gaps, then aggregate
        resampled = tmp.resample(freq, closed='left', label='left')[metric_col].agg(agg_fn)
        
        # Fill forward small gaps (up to 2 periods) to handle sparse data
        resampled = resampled.fillna(method='ffill', limit=2)
        
        return resampled.reset_index()
    
    except Exception as e:
        logger.warning(f"Resampling failed: {e}")
        return pd.DataFrame()


def temporal_aggregation(df: pd.DataFrame, date_col: str, metric_col: str,
                        group_by_col: str = None, granularity: str = "M",
                        agg_op: str = "sum") -> pd.DataFrame:
    """TRUE TEMPORAL AGGREGATION: Execute aggregations respecting time periods.
    
    Supports:
    - Simple temporal aggregation (sum/avg sales per month)
    - Grouped temporal aggregation (sales by region per month)
    - Proper null handling and sparse data handling
    """
    try:
        tmp = df[[date_col, metric_col] + ([group_by_col] if group_by_col else [])].copy()
        tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
        tmp = tmp.dropna(subset=[date_col, metric_col])
        
        if tmp.empty:
            return pd.DataFrame()
        
        # Create period column based on granularity
        if granularity == "Y":
            tmp['_period'] = tmp[date_col].dt.to_period("Y")
        elif granularity == "Q":
            tmp['_period'] = tmp[date_col].dt.to_period("Q")
        elif granularity == "M":
            tmp['_period'] = tmp[date_col].dt.to_period("M")
        elif granularity == "W":
            tmp['_period'] = tmp[date_col].dt.to_period("W")
        else:  # "D"
            tmp['_period'] = tmp[date_col].dt.date
        
        # Map aggregation
        agg_map = {
            "sum": "sum", "avg": "mean", "mean": "mean", "count": "count",
            "min": "min", "max": "max", "median": "median", "stddev": "std",
            "unique_count": "nunique"
        }
        agg_fn = agg_map.get(agg_op, "sum")
        
        # Execute aggregation
        if group_by_col:
            # Grouped temporal aggregation
            result = tmp.groupby(["_period", group_by_col])[metric_col].agg(agg_fn).reset_index()
            result.columns = ["period", group_by_col, agg_op + "_" + metric_col]
        else:
            # Simple temporal aggregation
            result = tmp.groupby("_period")[metric_col].agg(agg_fn).reset_index()
            result.columns = ["period", agg_op + "_" + metric_col]
        
        return result.sort_values("period")
    
    except Exception as e:
        logger.warning(f"Temporal aggregation failed: {e}")
        return pd.DataFrame()


def calculate_period_growth(df: pd.DataFrame, date_col: str, metric_col: str,
                            query: str) -> Optional[dict]:
    """Calculate month-over-month (MoM) or year-over-year (YoY) growth."""
    try:
        date_series = pd.to_datetime(df[date_col], errors="coerce")
        if date_series.isna().all():
            return None
        
        # Determine comparison type from query
        q = query.lower()
        is_yoy = bool(re.search(r'\b(year over year|yoy)\b', q))
        is_mom = bool(re.search(r'\b(month over month|mom)\b', q))
        
        # Default: detect from data range
        if not is_yoy and not is_mom:
            date_range = (date_series.max() - date_series.min()).days
            is_yoy = date_range > 365
            is_mom = date_range <= 365
        
        tmp = df[[date_col, metric_col]].copy()
        tmp[date_col] = date_series
        tmp = tmp.dropna()
        
        if is_yoy:
            tmp['year'] = tmp[date_col].dt.year
            tmp['month'] = tmp[date_col].dt.month
            pivot = tmp.pivot_table(values=metric_col, index='month', columns='year', aggfunc='sum')
            if len(pivot.columns) >= 2:
                latest_year = pivot.columns[-1]
                prior_year = pivot.columns[-2]
                growth = ((pivot[latest_year] - pivot[prior_year]) / pivot[prior_year] * 100).fillna(0)
                return {'type': 'YoY', 'growth': growth.to_dict()}
        
        elif is_mom:
            tmp['year_month'] = tmp[date_col].dt.to_period('M')
            monthly = tmp.groupby('year_month')[metric_col].sum().sort_index()
            if len(monthly) >= 2:
                growth = ((monthly.diff() / monthly.shift(1) * 100).dropna())
                return {'type': 'MoM', 'growth': growth.to_dict()}
    
    except Exception as e:
        logger.warning(f"Growth calculation failed: {e}")
    
    return None


def calculate_cumulative_trend(df: pd.DataFrame, date_col: str, metric_col: str) -> pd.DataFrame:
    """Calculate cumulative sum over time for 'cumulative' queries."""
    try:
        tmp = df[[date_col, metric_col]].copy()
        tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
        tmp = tmp.dropna().sort_values(date_col)
        tmp['cumulative'] = tmp[metric_col].cumsum()
        return tmp
    except Exception:
        return df


def detect_seasonal_pattern(df: pd.DataFrame, date_col: str, metric_col: str) -> Optional[str]:
    """Detect seasonal patterns (e.g., 'higher in Q4', 'peak in summer')."""
    try:
        date_series = pd.to_datetime(df[date_col], errors="coerce")
        if date_series.isna().all():
            return None
        
        tmp = df[[date_col, metric_col]].copy()
        tmp[date_col] = date_series
        tmp = tmp.dropna()
        
        tmp['month'] = tmp[date_col].dt.month
        tmp['quarter'] = tmp[date_col].dt.quarter
        
        quarterly_avg = tmp.groupby('quarter')[metric_col].mean()
        max_q = quarterly_avg.idxmax()
        min_q = quarterly_avg.idxmin()
        
        q_names = {1: 'Q1', 2: 'Q2', 3: 'Q3', 4: 'Q4'}
        return f"Highest in {q_names.get(max_q, 'peak quarter')}, lowest in {q_names.get(min_q, 'low quarter')}"
    
    except Exception:
        return None



from abc import ABC, abstractmethod

class QueryExecutor(ABC):
    """Base class for query executors. Each query type has dedicated executor."""
    
    def __init__(self, df: pd.DataFrame, meta: dict):
        self.df = df
        self.meta = meta
    
    @abstractmethod
    def can_execute(self, plan: QueryPlan) -> bool:
        """Check if this executor can handle the query plan."""
        pass
    
    @abstractmethod
    def execute(self, plan: QueryPlan, filter_note: str) -> dict:
        """Execute the query and return results."""
        pass
    
    def apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Utility: apply filters to dataframe."""
        return apply_filters(df, filters)


class TrendExecutor(QueryExecutor):
    """Handles trend/time-series queries."""
    
    def can_execute(self, plan: QueryPlan) -> bool:
        return plan.query_type == "trend" and self.meta.get("date_col")
    
    def execute(self, plan: QueryPlan, filter_note: str) -> dict:
        return execute_trend(plan, self.df, self.meta, filter_note)


class AggregationExecutor(QueryExecutor):
    """Handles aggregation queries (sum, avg, etc.)."""
    
    def can_execute(self, plan: QueryPlan) -> bool:
        return plan.query_type in ["aggregation", "kpi"]
    
    def execute(self, plan: QueryPlan, filter_note: str) -> dict:
        return execute_kpi_or_aggregation(plan, self.df, self.meta, filter_note)


class RankingExecutor(QueryExecutor):
    """Handles ranking queries (top/bottom)."""
    
    def can_execute(self, plan: QueryPlan) -> bool:
        return plan.query_type == "ranking"
    
    def execute(self, plan: QueryPlan, filter_note: str) -> dict:
        return execute_ranking(plan, self.df, self.meta, filter_note)


class DistributionExecutor(QueryExecutor):
    """Handles distribution queries (value counts, breakdowns)."""
    
    def can_execute(self, plan: QueryPlan) -> bool:
        return plan.query_type == "distribution"
    
    def execute(self, plan: QueryPlan, filter_note: str) -> dict:
        return execute_distribution(plan, self.df, self.meta, filter_note)


class ComparisonExecutor(QueryExecutor):
    """Handles comparison queries (metric vs metric)."""
    
    def can_execute(self, plan: QueryPlan) -> bool:
        return plan.query_type == "comparison"
    
    def execute(self, plan: QueryPlan, filter_note: str) -> dict:
        return execute_comparison(plan, self.df, self.meta, filter_note)


class CorrelationExecutor(QueryExecutor):
    """Handles correlation analysis queries."""
    
    def can_execute(self, plan: QueryPlan) -> bool:
        return plan.query_type == "correlation"
    
    def execute(self, plan: QueryPlan, filter_note: str) -> dict:
        return execute_correlation(plan, self.df, self.meta, filter_note)


class RawRetrievalExecutor(QueryExecutor):
    """Handles raw data retrieval queries."""
    
    def can_execute(self, plan: QueryPlan) -> bool:
        return plan.query_type == "raw_retrieval"
    
    def execute(self, plan: QueryPlan, filter_note: str) -> dict:
        return execute_raw_retrieval(plan, self.df, self.meta, filter_note)


class ExecutorRegistry:
    """Registry for routing queries to appropriate executors."""
    
    def __init__(self, df: pd.DataFrame, meta: dict):
        self.df = df
        self.meta = meta
        self.executors = [
            TrendExecutor(df, meta),
            RankingExecutor(df, meta),
            AggregationExecutor(df, meta),
            DistributionExecutor(df, meta),
            ComparisonExecutor(df, meta),
            CorrelationExecutor(df, meta),
            RawRetrievalExecutor(df, meta),
        ]
    
    def find_executor(self, plan: QueryPlan) -> Optional[QueryExecutor]:
        """Find appropriate executor for query plan."""
        for executor in self.executors:
            if executor.can_execute(plan):
                return executor
        return None
    
    def execute(self, plan: QueryPlan, filter_note: str = "") -> dict:
        """Execute query using appropriate executor."""
        executor = self.find_executor(plan)
        if executor:
            return executor.execute(plan, filter_note)
        return {"type": "error", "insight": f"No executor found for query type: {plan.query_type}"}


# ═══════════════════════════════════════════════════════════════════════════════
# IMPROVEMENT #2: ADVANCED SEMANTIC RETRIEVAL - EMBEDDING-BASED MATCHING
# ═══════════════════════════════════════════════════════════════════════════════

class EmbeddingBasedRanker:
    """Advanced semantic matching using simple embeddings (no external model)."""
    
    def __init__(self, df: pd.DataFrame, meta: dict):
        self.df = df
        self.meta = meta
        self.numeric_cols = set(meta.get("numeric_cols", []))
        self.categorical_cols = set(meta.get("categorical_cols", []))
        
        # Build semantic vectors for each column
        self.column_embeddings = self._build_embeddings()
    
    def _build_embeddings(self) -> Dict[str, List[float]]:
        """Build semantic embeddings for columns using term frequency."""
        embeddings = {}
        
        vocab = self._build_vocab()
        vocab_size = len(vocab)
        
        for col in self.df.columns:
            # Extract tokens from column name and description
            tokens = self._tokenize_column(col)
            
            # Create embedding as TF vector
            embedding = [0.0] * vocab_size
            for token in tokens:
                if token in vocab:
                    idx = vocab[token]
                    embedding[idx] += 1.0
            
            # Normalize
            norm = sum(x**2 for x in embedding) ** 0.5
            if norm > 0:
                embedding = [x / norm for x in embedding]
            
            embeddings[col] = embedding
        
        return embeddings
    
    def _build_vocab(self) -> Dict[str, int]:
        """Build vocabulary from all columns and business terms."""
        vocab = {}
        idx = 0
        
        # Add all column tokens
        for col in self.df.columns:
            for token in self._tokenize_column(col):
                if token not in vocab:
                    vocab[token] = idx
                    idx += 1
        
        # Add business synonym terms
        for key, synonyms in BUSINESS_SYNONYM_MAP.items():
            if key not in vocab:
                vocab[key] = idx
                idx += 1
            for syn in synonyms[:5]:  # Limit to avoid explosion
                if syn not in vocab:
                    vocab[syn] = idx
                    idx += 1
        
        return vocab
    
    def _tokenize_column(self, col: str) -> List[str]:
        """Extract meaningful tokens from column name."""
        tokens = []
        
        # Split on common delimiters
        parts = re.split(r'[\s_\-/]+', col.lower().strip())
        
        for part in parts:
            if len(part) > 2 and part not in ['the', 'and', 'or', 'by']:
                tokens.append(part)
        
        return tokens
    
    def _query_embedding(self, query: str) -> List[float]:
        """Convert query to embedding vector."""
        query_tokens = self._tokenize_column(query)
        
        vocab = self._build_vocab()
        vocab_size = len(vocab)
        
        embedding = [0.0] * vocab_size
        for token in query_tokens:
            if token in vocab:
                idx = vocab[token]
                embedding[idx] += 1.0
        
        # Normalize
        norm = sum(x**2 for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        return dot_product  # Already normalized
    
    def rank_for_metric(self, query_term: str) -> List[SemanticMatch]:
        """Rank metric columns using semantic embedding."""
        candidates = []
        query_vec = self._query_embedding(query_term)
        
        for col in self.numeric_cols:
            col_vec = self.column_embeddings.get(col, [])
            similarity = self._cosine_similarity(query_vec, col_vec)
            
            if similarity > 0.1:  # Filter weak matches
                candidates.append(SemanticMatch(
                    query_term=query_term,
                    column_name=col,
                    score=min(similarity, 1.0),
                    match_type="embedding",
                    explanation=f"Semantic match ({similarity:.2f})"
                ))
        
        return sorted(candidates, key=lambda x: x.score, reverse=True)
    
    def rank_for_grouping(self, query_term: str) -> List[SemanticMatch]:
        """Rank grouping columns using semantic embedding."""
        candidates = []
        query_vec = self._query_embedding(query_term)
        
        for col in self.categorical_cols:
            col_vec = self.column_embeddings.get(col, [])
            similarity = self._cosine_similarity(query_vec, col_vec)
            
            if similarity > 0.1:
                candidates.append(SemanticMatch(
                    query_term=query_term,
                    column_name=col,
                    score=min(similarity, 1.0),
                    match_type="embedding",
                    explanation=f"Semantic match ({similarity:.2f})"
                ))
        
        return sorted(candidates, key=lambda x: x.score, reverse=True)


# ═══════════════════════════════════════════════════════════════════════════════
# IMPROVEMENT #3: QUERY OPTIMIZATION & CACHING
# ═══════════════════════════════════════════════════════════════════════════════

class QueryCache:
    """LRU cache for query plans and results."""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache = {}
        self.access_order = []
    
    def _key(self, query: str, session_id: str) -> str:
        """Generate cache key."""
        return hashlib.md5(f"{session_id}:{query}".encode()).hexdigest()
    
    def get(self, query: str, session_id: str) -> Optional[dict]:
        """Retrieve from cache."""
        key = self._key(query, session_id)
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def set(self, query: str, session_id: str, result: dict) -> None:
        """Store in cache."""
        key = self._key(query, session_id)
        
        # Remove from access order if exists
        if key in self.access_order:
            self.access_order.remove(key)
        
        # Add to cache
        self.cache[key] = result
        self.access_order.append(key)
        
        # Evict oldest if over limit
        if len(self.cache) > self.max_size:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
    
    def clear(self, session_id: str) -> None:
        """Clear all cache entries for session."""
        keys_to_remove = []
        for key in self.cache.keys():
            if session_id in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
            self.access_order.remove(key)


query_cache = QueryCache(max_size=200)


# ═══════════════════════════════════════════════════════════════════════════════
# IMPROVEMENT #4: ADAPTIVE LEARNING SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class QueryFeedback:
    """Track user feedback for query resolution."""
    session_id: str
    query: str
    original_intent: str
    corrected_intent: Optional[str]
    original_metric: Optional[str]
    corrected_metric: Optional[str]
    original_grouping: Optional[str]
    corrected_grouping: Optional[str]
    confidence_before: float
    timestamp: str


class AdaptiveLearner:
    """Learn from user corrections and improve query understanding."""
    
    def __init__(self):
        self.feedback_history: List[QueryFeedback] = []
        self.intent_corrections: Dict[str, List[str]] = defaultdict(list)
        self.column_corrections: Dict[str, List[str]] = defaultdict(list)
    
    def record_correction(self, feedback: QueryFeedback) -> None:
        """Record user correction for learning."""
        self.feedback_history.append(feedback)
        
        # Track intent corrections
        if feedback.corrected_intent and feedback.corrected_intent != feedback.original_intent:
            self.intent_corrections[feedback.original_intent].append(feedback.corrected_intent)
        
        # Track column corrections
        if feedback.corrected_metric and feedback.corrected_metric != feedback.original_metric:
            self.column_corrections[str(feedback.original_metric)].append(feedback.corrected_metric)
        
        if feedback.corrected_grouping and feedback.corrected_grouping != feedback.original_grouping:
            self.column_corrections[str(feedback.original_grouping)].append(feedback.corrected_grouping)
    
    def get_recommended_intent(self, detected_intent: str) -> Optional[str]:
        """Get most likely corrected intent based on history."""
        if detected_intent not in self.intent_corrections:
            return None
        
        corrections = self.intent_corrections[detected_intent]
        if not corrections:
            return None
        
        # Return most common correction
        from collections import Counter
        most_common = Counter(corrections).most_common(1)[0][0]
        return most_common
    
    def get_recommended_column(self, detected_column: str) -> Optional[str]:
        """Get most likely corrected column based on history."""
        if str(detected_column) not in self.column_corrections:
            return None
        
        corrections = self.column_corrections[str(detected_column)]
        if not corrections:
            return None
        
        from collections import Counter
        most_common = Counter(corrections).most_common(1)[0][0]
        return most_common
    
    def get_confidence_boost(self, query_pattern: str, session_id: str) -> float:
        """Get confidence boost for common patterns in session."""
        session_feedback = [f for f in self.feedback_history if f.session_id == session_id]
        
        if not session_feedback:
            return 0.0
        
        # If user frequently confirms this pattern, boost confidence
        confirmations = sum(1 for f in session_feedback 
                          if f.corrected_intent == f.original_intent)
        
        return min(0.1 * (confirmations / max(len(session_feedback), 1)), 0.15)


adaptive_learner = AdaptiveLearner()


# ═══════════════════════════════════════════════════════════════════════════════
# IMPROVEMENT #5: SMARTER VISUALIZATION INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════

class VisualizationSelector:
    """Intelligent chart selection based on data characteristics."""
    
    def __init__(self, df: pd.DataFrame, meta: dict):
        self.df = df
        self.meta = meta
    
    def select_visualization(self, plan: QueryPlan, result_df: pd.DataFrame) -> str:
        """Select best visualization based on data structure and intent."""
        
        # Query type hints
        if plan.query_type == "kpi":
            return "scalar"
        elif plan.query_type == "trend":
            return "line"
        elif plan.query_type == "distribution":
            return "pie"
        elif plan.query_type == "comparison":
            return self._select_comparison_viz(result_df)
        elif plan.query_type == "ranking":
            return "bar"
        else:
            return self._auto_select(plan, result_df)
    
    def _select_comparison_viz(self, result_df: pd.DataFrame) -> str:
        """Select best viz for comparison queries."""
        if len(result_df) > 10:
            return "scatter"  # Many items: use scatter
        elif len(result_df) > 5:
            return "bar"  # Medium: use bar
        else:
            return "table"  # Few items: use table
    
    def _auto_select(self, plan: QueryPlan, result_df: pd.DataFrame) -> str:
        """Automatically select visualization."""
        
        if result_df.empty:
            return "table"
        
        num_rows = len(result_df)
        num_cols = len(result_df.columns)
        
        # One numeric column
        if num_cols == 1:
            return "scalar" if num_rows == 1 else "bar"
        
        # Two columns: could be dimension + metric
        if num_cols == 2:
            if num_rows <= 3:
                return "table"
            elif num_rows <= 10:
                return "bar"
            else:
                return "scatter"
        
        # Many columns: overview
        if num_cols > 5:
            return "table"
        
        # Check cardinality
        unique_ratios = [result_df[col].nunique() / max(num_rows, 1) 
                        for col in result_df.columns]
        avg_uniqueness = sum(unique_ratios) / len(unique_ratios)
        
        if avg_uniqueness > 0.8:  # Mostly unique: scatter
            return "scatter"
        elif avg_uniqueness > 0.5:  # Moderate: bar
            return "bar"
        else:  # Few unique values: pie
            return "pie" if num_rows <= 6 else "bar"
    
    def get_chart_config(self, visualization_type: str, result_df: pd.DataFrame, 
                        plan: QueryPlan) -> dict:
        """Generate chart configuration."""
        
        if visualization_type == "scalar":
            value = float(result_df.iloc[0, 0]) if len(result_df) > 0 else 0
            return {"type": "scalar", "value": value}
        
        elif visualization_type == "bar":
            if len(result_df.columns) >= 2:
                x_col = result_df.columns[0]
                y_col = result_df.columns[1]
            else:
                x_col = result_df.columns[0]
                y_col = None
            
            return {
                "type": "bar",
                "labels": result_df[x_col].astype(str).tolist()[:20],
                "values": (result_df[y_col].tolist()[:20] if y_col else 
                          range(1, len(result_df) + 1))
            }
        
        elif visualization_type == "line":
            if len(result_df.columns) >= 2:
                x_col = result_df.columns[0]
                y_col = result_df.columns[1]
            else:
                x_col = result_df.columns[0]
                y_col = None
            
            return {
                "type": "line",
                "labels": result_df[x_col].astype(str).tolist()[:30],
                "values": (result_df[y_col].tolist()[:30] if y_col else 
                          range(1, len(result_df) + 1))
            }
        
        elif visualization_type == "pie":
            if len(result_df.columns) >= 2:
                x_col = result_df.columns[0]
                y_col = result_df.columns[1]
            else:
                x_col = result_df.columns[0]
                y_col = None
            
            return {
                "type": "pie",
                "labels": result_df[x_col].astype(str).tolist()[:12],
                "values": (result_df[y_col].tolist()[:12] if y_col else 
                          [1] * len(result_df[:12]))
            }
        
        elif visualization_type == "scatter":
            if len(result_df.columns) >= 2:
                x_col = result_df.columns[0]
                y_col = result_df.columns[1]
                return {
                    "type": "scatter",
                    "x": result_df[x_col].tolist()[:100],
                    "y": result_df[y_col].tolist()[:100]
                }
            else:
                return {"type": "scatter", "x": [], "y": []}
        
        else:
            return {"type": "table"}


# ═══════════════════════════════════════════════════════════════════════════════
# IMPROVEMENTS #9, #11, #12, #24, #25: STRICT QUERY ROUTING & EXECUTION PATHS
# ═══════════════════════════════════════════════════════════════════════════════

class QueryRouter:
    """Strict query-type routing to prevent cross-contamination of execution paths."""
    
    # Improvement #25: Supported query types (restrict unsupported ones)
    SUPPORTED_TYPES = {
        "kpi": True,              # Fully supported
        "aggregation": True,      # Fully supported
        "trend": True,            # Fully supported
        "ranking": True,          # Fully supported
        "distribution": True,     # Fully supported
        "raw_retrieval": True,    # Fully supported
        "comparison": True,       # Fully supported
        "correlation": True,      # Fully supported
        "explanation": False,     # Experimental - fall back to AI
        "raw_data": False,        # Experimental
    }
    
    @staticmethod
    def is_supported(query_type: str) -> bool:
        """Check if query type is fully supported."""
        return QueryRouter.SUPPORTED_TYPES.get(query_type, False)
    
    @staticmethod
    def classify_query_path(plan: QueryPlan) -> str:
        """Classify which execution pipeline to use."""
        
        # Improvement #12: Separate retrieval engine from analytics
        if plan.query_type == "raw_retrieval":
            return "retrieval_engine"
        
        # Improvement #13: Dedicated KPI path
        if plan.query_type == "kpi":
            return "kpi_engine"
        
        # Everything else uses analytics engine
        if plan.query_type in ["trend", "aggregation", "ranking", "distribution", 
                              "comparison", "correlation"]:
            return "analytics_engine"
        
        # Unsupported - use AI fallback
        return "ai_fallback"
    
    @staticmethod
    def validate_routing(plan: QueryPlan) -> Tuple[bool, str]:
        """Validate that routing decision is sound."""
        
        if not QueryRouter.is_supported(plan.query_type):
            return False, f"Query type '{plan.query_type}' is not yet supported"
        
        # Improvement #11: Strict type checking
        path = QueryRouter.classify_query_path(plan)
        
        if path == "retrieval_engine" and plan.query_type != "raw_retrieval":
            return False, "Retrieval engine routing mismatch"
        
        if path == "kpi_engine" and plan.query_type != "kpi":
            return False, "KPI engine routing mismatch"
        
        if path == "analytics_engine" and plan.query_type not in [
            "trend", "aggregation", "ranking", "distribution", "comparison", "correlation"
        ]:
            return False, "Analytics engine routing mismatch"
        
        return True, ""


class RetrievalExecutor:
    """Improvement #12: Dedicated retrieval engine for list/show/display queries."""
    
    @staticmethod
    def execute(plan: QueryPlan, df: pd.DataFrame, meta: dict, 
                filter_note: str) -> dict:
        """Execute raw data retrieval queries."""
        
        # Apply filters
        result_df = df.copy()
        if plan.filters:
            result_df = apply_filters(result_df, plan.filters)
        
        if len(result_df) == 0:
            return {
                "type": "info",
                "title": "No records found",
                "message": "Your search returned no matching records",
                "data": {"rows": [], "count": 0},
                "table": []
            }
        
        # Limit results
        limit = min(plan.limit or 10, 100)
        result_df = result_df.head(limit)
        
        table_data = result_df.to_dict("records")
        
        return {
            "type": "structured",
            "title": f"Found {len(result_df)} records",
            "table": table_data,
            "visualization": "table",
            "data": {
                "count": len(result_df),
                "columns": result_df.columns.tolist()
            }
        }


class KPIExecutor:
    """Improvement #13: Dedicated KPI execution engine for single-value queries."""
    
    @staticmethod
    def execute(plan: QueryPlan, df: pd.DataFrame, meta: dict, 
                filter_note: str) -> dict:
        """Execute KPI/scalar queries."""
        
        # Validate metric exists
        if not plan.metric_column or plan.metric_column not in df.columns:
            return {
                "type": "error",
                "title": "Invalid KPI query",
                "message": f"Metric column '{plan.metric_column}' not found"
            }
        
        # Apply filters
        working_df = apply_filters(df, plan.filters) if plan.filters else df
        
        if len(working_df) == 0:
            return {
                "type": "info",
                "title": "No data",
                "message": "No records match your filters"
            }
        
        # Perform aggregation
        operation = plan.aggregation.operation if plan.aggregation else "sum"
        col = plan.metric_column
        
        if operation == "sum":
            value = float(working_df[col].sum())
        elif operation == "avg":
            value = float(working_df[col].mean())
        elif operation == "median":
            value = float(working_df[col].median())
        elif operation == "min":
            value = float(working_df[col].min())
        elif operation == "max":
            value = float(working_df[col].max())
        elif operation == "count":
            value = float(len(working_df))
        else:
            value = float(working_df[col].sum())
        
        return {
            "type": "kpi",
            "title": f"{operation.capitalize()} of {col}",
            "value": round(value, 2) if not math.isnan(value) else 0,
            "metric": col,
            "operation": operation,
            "table": [{col: round(value, 2) if not math.isnan(value) else 0}]
        }


def execute_query_plan(plan: QueryPlan, df: pd.DataFrame, meta: dict,
                       context: str, history: List[dict], session_id: str) -> dict:
    """
    Execute query using new executor abstraction layer (Improvement #1).
    Routes to specialized executors based on query type.
    """
    # Improvement #11: Validate routing
    is_valid, routing_err = QueryRouter.validate_routing(plan)
    if not is_valid:
        logger.warning(f"Routing validation failed: {routing_err}")
        QueryLogger.log_execution_result(session_id, plan.query_type, "routing_error", 0, 0)
        return {"type": "error", "title": "Execution error", "message": routing_err}
    
    # Improvement #12: Route to appropriate execution engine
    path = QueryRouter.classify_query_path(plan)
    
    # Improvement #12: Retrieval engine
    if path == "retrieval_engine":
        return RetrievalExecutor.execute(plan, df, meta, "")
    
    # Improvement #13: KPI engine
    if path == "kpi_engine":
        return KPIExecutor.execute(plan, df, meta, "")
    
    # Analytics engine (existing logic)
    working_df  = apply_filters(df, plan.filters) if plan.filters else df
    filter_note = " (filtered)" if plan.filters else ""

    # FIX #30: Graceful empty-result handling
    if len(working_df) == 0:
        filter_desc = "; ".join(
            f"{k}={v}" if not isinstance(v, dict) else f"{k}{v['op']}{v['val']}"
            for k, v in plan.filters.items()
        )
        return {
            "type":    "error",
            "title":   "No matching records",
            "insight": (
                f"No records matched filter(s): {filter_desc}. "
                "Try broadening the criteria or checking spelling."
            )
        }

    # Use new ExecutorRegistry to route to appropriate executor
    registry = ExecutorRegistry(working_df, meta)
    result = registry.execute(plan, filter_note)
    
    # If no executor found, fallback to AI analysis
    if result.get("type") == "error" and "No executor found" in result.get("insight", ""):
        ai_call_count[session_id] = ai_call_count.get(session_id, 0) + 1
        return {
            "type": "ai",
            "title": "Analysis",
            "insight": answer_with_ai(plan.raw_query, working_df, meta, context, history)
        }
    
    return result


def execute_ranking(plan: QueryPlan, df: pd.DataFrame, meta: dict,
                    filter_note: str) -> dict:
    """FIX #22: Full groupby → aggregate → sort → limit pipeline."""
    id_cols     = set(meta.get("id_like_cols", []))
    numeric_set = set(meta.get("numeric_cols", []))

    if not plan.metric_column or plan.metric_column not in df.columns:
        safe = [c for c in meta.get("numeric_cols",[]) if c not in id_cols]
        return {"type":"error","title":"Metric not found",
                "insight":f"Available: {', '.join(safe[:5]) or 'none'}."}

    if plan.metric_column in id_cols:
        safe = list(numeric_set - id_cols)
        return {"type":"error","title":"Cannot rank by identifier",
                "insight":f"Try: {', '.join(list(safe)[:3])}."}

    order_asc = (plan.sort_order == "asc")

    if plan.group_by_column and plan.group_by_column in df.columns:
        agg_op   = plan.aggregation.operation if plan.aggregation else "sum"
        pandas_fn = {"sum":"sum","avg":"mean","count":"count",
                     "min":"min","max":"max","median":"median","stddev":"std"}.get(agg_op,"sum")
        result = (df.groupby(plan.group_by_column)[plan.metric_column]
                    .agg(pandas_fn).round(2)
                    .sort_values(ascending=order_asc)
                    .head(plan.limit).reset_index())
        result.columns = [plan.group_by_column, plan.metric_column]
        direction = "Bottom" if order_asc else "Top"
        title  = f"{direction} {plan.limit} {plan.group_by_column} by {plan.metric_column}{filter_note}"
        labels = result[plan.group_by_column].astype(str).tolist()
        values = result[plan.metric_column].tolist()
    else:
        fn     = df.nsmallest if order_asc else df.nlargest
        result = fn(plan.limit, plan.metric_column)
        exclude   = id_cols | set(meta.get("free_text_cols", []))
        safe_cols = [c for c in plan.relevant_columns if c not in exclude]
        if not safe_cols:
            safe_cols = [c for c in df.columns if c not in exclude][:6]
        result    = result[safe_cols]
        direction = "Bottom" if order_asc else "Top"
        title     = f"{direction} {plan.limit} by {plan.metric_column}{filter_note}"
        labels    = list(range(1, len(result)+1))
        values    = result[plan.metric_column].tolist() if plan.metric_column in result.columns else []

    return {
        "type":"structured",
        "visualization": "bar",
        "title":title,
        "table": result.to_dict(orient="records"),
        "chart":{"type":"bar","labels":[str(l) for l in labels[:12]],"values":values[:12],
                 "x_label": plan.group_by_column or "Rank","y_label": plan.metric_column}
    }


def execute_kpi_or_aggregation(plan: QueryPlan, df: pd.DataFrame,
                               meta: dict, filter_note: str) -> dict:
    # ─────────────────────────────
    # Pure row count KPI
    # ─────────────────────────────
    if (
        plan.operation == "count"
        and not plan.metric_column
        and not plan.group_by_column
    ):
        total_rows = len(filtered_df if 'filtered_df' in locals() else df)

        title = "Count of Records"
        if plan.filters:
            title += " (filtered)"

        return {
            "type": "kpi",
            "title": title,
            "value": int(total_rows),
            "insight": f"Total matching records: {total_rows:,}."
        }

    id_cols = set(meta.get("id_like_cols", []))
    safe_num = [c for c in meta.get("numeric_cols", []) if c not in id_cols]

    if not plan.metric_column or plan.metric_column not in df.columns:
        return {
            "type": "error",
            "title": "Metric not found",
            "insight": f"Available: {', '.join(safe_num[:5]) or 'none'}."
        }

    agg_op = plan.aggregation.operation if plan.aggregation else "sum"
    pandas_fn = {
        "sum": "sum",
        "avg": "mean",
        "count": "count",
        "unique_count": "nunique",
        "min": "min",
        "max": "max",
        "median": "median",
        "stddev": "std"
    }.get(agg_op, "sum")

    if plan.group_by_column and plan.group_by_column in df.columns:
        result = (
            df.groupby(plan.group_by_column)[plan.metric_column]
              .agg(pandas_fn).round(2)
              .sort_values(ascending=False).reset_index()
        )
        metric_name = f"{agg_op}_{plan.metric_column}"
        result.columns = [plan.group_by_column, metric_name]
        title = f"{agg_op.title()} of {plan.metric_column} by {plan.group_by_column}{filter_note}"
        return {
            "type": "structured",
            "visualization": "bar",
            "title": title,
            "table": result.to_dict(orient="records"),
            "chart": {
                "type": "bar",
                "labels": result[plan.group_by_column].astype(str).tolist()[:12],
                "values": result[metric_name].tolist()[:12],
                "x_label": plan.group_by_column,
                "y_label": metric_name
            }
        }

    # FIX #29: Scalar KPI
    if agg_op == "unique_count":
        val = int(df[plan.metric_column].nunique())
    else:
        val = round(
            float(
                getattr(
                    df[plan.metric_column],
                    pandas_fn
                )()
            ),
            2
        )

    label = {
        "sum": "Total", "avg": "Average", "mean": "Average", "count": "Count", "unique_count": "Unique Count",
        "min": "Minimum", "max": "Maximum", "median": "Median",
        "stddev": "Std Dev"
    }.get(agg_op, agg_op.title())

    return {
        "type": "kpi",
        "title": f"{label} of {plan.metric_column}{filter_note}",
        "value": val,
        "metric": plan.metric_column,
        "aggregation": agg_op,
        "visualization": "scalar",
        "insight": (
            f"The {label.lower()} of "
            f"**{plan.metric_column}** "
            f"is **{val:,.2f}**."
        )
    }



def execute_comparison(plan: QueryPlan, df: pd.DataFrame, meta: dict,
                       filter_note: str) -> dict:
    """FIX #26: Multi-metric comparison with aligned grouped outputs."""
    id_cols     = set(meta.get("id_like_cols", []))
    numeric_cols = [c for c in meta.get("numeric_cols",[]) if c not in id_cols]

    if len(numeric_cols) < 2:
        return {"type":"error","title":"Need 2+ numeric columns",
                "insight":"Cannot compare with fewer than 2 numeric columns."}

    comp_cols = getattr(plan, "_comparison_cols", None) or []
    if not comp_cols:
        comp_cols = []
        for c in numeric_cols[:6]:
            for c2 in numeric_cols[:6]:
                if c != c2 and is_meaningful_comparison(c, c2, meta):
                    if c not in comp_cols:  comp_cols.append(c)
                    if c2 not in comp_cols: comp_cols.append(c2)
        if not comp_cols:
            comp_cols = numeric_cols[:4]

    if plan.group_by_column and plan.group_by_column in df.columns:
        result = df.groupby(plan.group_by_column)[comp_cols].mean().round(2).reset_index()
        title  = f"Comparison of {', '.join(comp_cols)} by {plan.group_by_column}{filter_note}"
    else:
        result = df[comp_cols].describe().T.round(2).reset_index()
        result.columns = ["metric"] + list(result.columns[1:])
        title  = f"Statistical Comparison: {', '.join(comp_cols)}{filter_note}"

    return {"type":"structured","title":title,"table": result.to_dict(orient="records")}


def execute_trend(plan: QueryPlan, df: pd.DataFrame, meta: dict,
                  filter_note: str) -> dict:
    """FIX #24 + #36: ACTUAL TEMPORAL AGGREGATION EXECUTION with intelligent granularity."""
    date_col = meta.get("date_col")
    id_cols  = set(meta.get("id_like_cols", []))
    safe_num = [c for c in meta.get("numeric_cols",[]) if c not in id_cols]

    if not plan.metric_column or plan.metric_column not in df.columns:
        return {"type":"error","title":"Metric not found",
                "insight":f"Try: {', '.join(safe_num[:3]) or 'none'}."}

    insight_parts = []
    
    if date_col and date_col in df.columns:
        if "cumulative" in plan.raw_query.lower():
            cum_df = calculate_cumulative_trend(df, date_col, plan.metric_column)
            if cum_df is not None and len(cum_df) > 0:
                cum_df = cum_df.sort_values(date_col)
                trend_df = cum_df[[date_col, 'cumulative']].copy()
                trend_df.columns = [date_col, f"Cumulative {plan.metric_column}"]
                title = f"Cumulative {plan.metric_column} Over Time{filter_note}"
                display_limit = min(30, len(trend_df))
                return {
                    "type":"structured",
                    "visualization": "line",
                    "title":title,
                    "table": trend_df.head(display_limit).to_dict(orient="records"),
                    "chart":{"type":"line",
                             "labels":[str(v)[:10] for v in trend_df[date_col].astype(str).tolist()[:display_limit]],
                             "values": trend_df[f"Cumulative {plan.metric_column}"].tolist()[:display_limit],
                             "x_label": "Date",
                             "y_label": f"Cumulative {plan.metric_column}"}
                }
        
        agg_op = plan.aggregation.operation if plan.aggregation else "sum"
        period_series, period_label, granularity = auto_datetime_grouping(
            df, date_col, plan.raw_query, plan.metric_column
        )
        
        plan.temporal_granularity = granularity
        plan.temporal_column = date_col
        
        if plan.group_by_column and plan.group_by_column in df.columns:
            trend_df = temporal_aggregation(
                df, date_col, plan.metric_column,
                group_by_col=plan.group_by_column,
                granularity=granularity,
                agg_op=agg_op
            )
            if trend_df.empty:
                return {"type":"error","title":"No data for trend",
                        "insight":"Temporal aggregation produced empty result."}
            trend_df = trend_df.sort_values("period")
            x_labels = trend_df["period"].astype(str).tolist()
            metric_col_name = f"{agg_op}_{plan.metric_column}"
        else:
            trend_df = temporal_aggregation(
                df, date_col, plan.metric_column,
                group_by_col=None,
                granularity=granularity,
                agg_op=agg_op
            )
            if trend_df.empty:
                return {"type":"error","title":"No data for trend",
                        "insight":"Temporal aggregation produced empty result."}
            trend_df = trend_df.sort_values("period")
            trend_df.columns = [period_label, f"{agg_op}_{plan.metric_column}"]
            x_labels = trend_df[period_label].astype(str).tolist()
            metric_col_name = f"{agg_op}_{plan.metric_column}"
        
        growth_data = calculate_period_growth(df, date_col, plan.metric_column, plan.raw_query)
        if growth_data:
            growth_type = growth_data.get('type', 'N/A')
            insight_parts.append(f"[{growth_type}] Growth metrics computed.")
        
        seasonal = detect_seasonal_pattern(df, date_col, plan.metric_column)
        if seasonal:
            insight_parts.append(f"Seasonal: {seasonal}")
        
        if len(trend_df) >= 2 and metric_col_name in trend_df.columns:
            values = trend_df[metric_col_name].values
            first_half_avg = np.mean(values[:len(values)//2]) if len(values) > 0 else 0
            second_half_avg = np.mean(values[len(values)//2:]) if len(values) > 0 else 0
            if first_half_avg > 0:
                trend_pct = ((second_half_avg - first_half_avg) / first_half_avg * 100)
                direction = "\u2191" if trend_pct > 0 else "\u2193"
                insight_parts.insert(0, f"Trend {direction} {abs(trend_pct):.1f}%")
        
        insight_parts.insert(0, f"Granularity: {period_label}")
        
        if plan.group_by_column:
            title = f"Trend of {plan.metric_column} by {plan.group_by_column} ({period_label}){filter_note}"
        else:
            title = f"Trend of {plan.metric_column} by {period_label}{filter_note}"
    else:
        trend_df = df[[plan.metric_column]].dropna().reset_index(drop=True)
        trend_df.insert(0, "index", range(len(trend_df)))
        x_labels = list(range(len(trend_df)))
        metric_col_name = plan.metric_column
        title    = f"Trend of {plan.metric_column} (by row){filter_note}"
        period_label = "Index"
        granularity = None

    display_limit = min(30, len(trend_df))
    chart_values = trend_df[metric_col_name].tolist()[:display_limit] if metric_col_name in trend_df.columns else trend_df[plan.metric_column].tolist()[:display_limit]
    result = {
        "type":"structured",
        "visualization": "line",
        "title":title,
        "table": trend_df.head(display_limit).to_dict(orient="records"),
        "chart":{"type":"line",
                 "labels":[str(l)[:15] for l in x_labels[:display_limit]],
                 "values": chart_values,
                 "x_label": period_label,
                 "y_label": plan.metric_column}
    }
    
    if granularity:
        result["granularity"] = granularity
        result["temporal_column"] = date_col
    
    if insight_parts:
        result["insight"] = " | ".join(insight_parts)
    
    return result


def execute_distribution(plan: QueryPlan, df: pd.DataFrame, meta: dict,
                         filter_note: str) -> dict:
    """FIX #4/#5/#23: Count aggregation, categorical value_counts, no ID bins."""
    id_cols  = set(meta.get("id_like_cols", []))
    free_txt = set(meta.get("free_text_cols", []))
    exclude  = id_cols | free_txt

    is_count_q   = getattr(plan, "_is_count", False)
    cat_dist_col = getattr(plan, "_cat_dist_col", None)

    # FIX #23: Explicit grouped count
    if (
        (
            is_count_q
            or (
                not plan.metric_column
                and plan.group_by_column
            )
        )
        and plan.group_by_column in df.columns
    ):
        # Choose target column
        target_col = None
        if cat_dist_col and cat_dist_col in df.columns and cat_dist_col not in exclude:
            target_col = cat_dist_col
        elif (plan.metric_column and plan.metric_column in df.columns
              and not pd.api.types.is_numeric_dtype(df[plan.metric_column])
              and plan.metric_column not in exclude):
            target_col = plan.metric_column
        elif plan.group_by_column and plan.group_by_column in df.columns:
            target_col = plan.group_by_column
        else:
            safe_cat = [c for c in
                        (meta.get("low_cardinality_cols", []) + meta.get("categorical_cols", []))
                        if c not in exclude]
            target_col = safe_cat[0] if safe_cat else None

        if not target_col:
            return {
                "type": "error",
                "title": "No categorical column found",
                "insight": "Please specify a categorical column to analyse."
            }

        if pd.api.types.is_numeric_dtype(df[target_col]):
            if target_col in id_cols:
                safe_cat = [c for c in meta.get("categorical_cols", []) if c not in exclude]
                if safe_cat:
                    target_col = safe_cat[0]
                    result = df[target_col].value_counts().reset_index()
                    result.columns = [target_col, "count"]
                else:
                    return {
                        "type": "error",
                        "title": "No suitable column",
                        "insight": "No categorical column."
                    }
            else:
                try:
                    bucketed = pd.cut(df[target_col], bins=8).value_counts().sort_index().reset_index()
                    bucketed.columns = [target_col, "count"]
                    bucketed[target_col] = bucketed[target_col].astype(str)
                    result = bucketed
                except Exception:
                    result = df[target_col].value_counts().reset_index()
                    result.columns = [target_col, "count"]
        else:
            result = df[target_col].value_counts().reset_index()
            result.columns = [target_col, "count"]

        return {
            "type": "structured",
            "visualization": "pie",
            "title": f"Distribution of {target_col}{filter_note}",
            "table": result.to_dict(orient="records"),
            "chart": {
                "type": "pie",
                "labels": result[target_col].astype(str).tolist()[:12],
                "values": result["count"].tolist()[:12],
                "x_label": target_col,
                "y_label": "count"
            }
        }


def execute_correlation(plan: QueryPlan, df: pd.DataFrame, meta: dict,
                        filter_note: str) -> dict:
    id_cols  = set(meta.get("id_like_cols", []))
    num_cols = [c for c in meta.get("numeric_cols",[]) if c not in id_cols]
    if len(num_cols) < 2:
        return {"type":"error","title":"Need 2+ numeric columns",
                "insight":"Correlation requires at least 2 numeric (non-ID) columns."}
    corr_df = df[num_cols].corr().round(3).reset_index()
    corr_df.columns = ["metric"] + num_cols
    return {"type":"structured","title":f"Correlation Matrix{filter_note}",
            "table": corr_df.to_dict(orient="records")}


def execute_raw_retrieval(plan: QueryPlan, df: pd.DataFrame, meta: dict,
                          filter_note: str) -> dict:
    """FIX #21/#27/#28: Row-level retrieval with meaningful columns and date sorting."""
    id_cols  = set(meta.get("id_like_cols", []))
    free_txt = set(meta.get("free_text_cols", []))
    exclude  = id_cols | free_txt

    # FIX #28: Priority column selection
    priority = []
    if meta.get("primary_entity_col") and meta["primary_entity_col"] not in exclude:
        priority.append(meta["primary_entity_col"])
    if meta.get("date_col"):
        priority.append(meta["date_col"])
    for col in meta.get("numeric_cols", []):
        if col not in exclude and col not in priority:
            priority.append(col)
    for col in meta.get("low_cardinality_cols", []):
        if col not in exclude and col not in priority:
            priority.append(col)

    cols   = priority[:8] or [c for c in df.columns if c not in exclude][:8]
    result = df[cols].copy()

    # FIX #27: Sort by date desc for "recent" queries
    if getattr(plan, "_sort_by_date_desc", False) and meta.get("date_col") and meta["date_col"] in result.columns:
        result = result.sort_values(meta["date_col"], ascending=False)

    # filtered retrievals should return more rows

    if plan.filters:
        result = result.head(50)
    else:
        result = result.head(plan.limit)
        
    sort_prefix = "Latest " if getattr(plan, "_sort_by_date_desc", False) else ""
    return {"type":"structured",
            "visualization": "table",
            "title": (
                f"Filtered Records{filter_note}"
                if plan.filters
                else f"{sort_prefix}{len(result)} records"
            ),
            "table": result.to_dict(orient="records")}


# ═══════════════════════════════════════════════════════════════════════════════
# UPLOAD ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    contents   = await file.read()

    try:
        fname = file.filename or ""

        if fname.endswith(".csv"):
            df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

        elif fname.endswith((".xlsx",".xls")):
            df = pd.read_excel(io.BytesIO(contents))

        else:
            try:
                df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

            except Exception:
                df = pd.read_excel(io.BytesIO(contents))

    except Exception as e:
        return {"error": f"Failed to parse file: {e}"}

    if df.empty:
        return {"error": "The uploaded file appears to be empty."}

    df.columns = df.columns.str.strip()

    meta = build_dataset_meta(df)
    
    # FIX #43: Enhance with richer metadata at upload time
    meta = enhance_dataset_meta(df, meta)

    datasets[session_id]             = df
    ai_call_count[session_id]        = 0
    conversation_history[session_id] = []
    
    # ════════════════════════════════════════════════════════════════════
    # IMPROVEMENT #3: Clear query cache for new dataset
    # ════════════════════════════════════════════════════════════════════
    query_cache.clear(session_id)

    summary = summarize_dataset(df, meta)

    meta["summary"] = summary
    dataset_meta[session_id] = meta

    ai_call_count[session_id] += 1

    return sanitize_for_json({

        "session_id":       session_id,
        "columns":          df.columns.tolist(),
        "rows":             len(df),
        "numeric_cols":     meta["numeric_cols"],
        "categorical_cols": meta["categorical_cols"],
        "datetime_cols":    meta["datetime_cols"],
        "id_like_cols":     meta["id_like_cols"],
        "percentage_cols":  meta["percentage_cols"],
        "free_text_cols":   meta["free_text_cols"],
        "column_roles":     meta["column_roles"],
        "data_quality":     meta.get("data_quality", {}),
        "suggestions":      generate_suggestions(df, meta),
        "summary":          summary

    })


# ═══════════════════════════════════════════════════════════════════════════════
# FIX #39: IMPROVED ERROR HANDLING AND FALLBACK LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ConfidenceThresholds:
    """Confidence thresholds for different decision points."""
    execute_with_insight: float = 0.50    # Confidence needed to generate AI insight
    execute_with_warning: float = 0.35    # Execute but warn user
    clarify: float = 0.25                 # Ask for clarification
    fallback: float = 0.15                # Use fallback strategy


CONFIDENCE_THRESHOLDS = ConfidenceThresholds()


def should_execute_query(confidence: float, resolution_score: float) -> Tuple[bool, str]:
    """
    FIX #39: Determine if query should be executed based on confidence.
    Returns (should_execute, reason_code)
    """
    if confidence < CONFIDENCE_THRESHOLDS.fallback:
        return False, "confidence_too_low"
    if resolution_score < 0.25:
        return False, "resolution_too_poor"
    return True, "ok"


def generate_fallback_response(query: str, df: pd.DataFrame, meta: dict) -> dict:
    """
    FIX #39: Generate meaningful fallback response instead of error.
    Provides safe default analysis options.
    """
    return {
        "type": "fallback",
        "title": "I'm not confident about your query, but here are some options:",
        "options": [
            {
                "query": "Show me the first few rows",
                "description": "See what data you have"
            },
            {
                "query": f"Top 5 by {meta.get('numeric_cols', ['unknown'])[0]}",
                "description": "Ranking by main metric"
            },
            {
                "query": f"Count by {meta.get('categorical_cols', ['unknown'])[0]}",
                "description": "Distribution across categories"
            },
            {
                "query": "Dataset overview",
                "description": "Summary statistics"
            }
        ],
        "confidence": 0.0,
        "suggestion": "Try one of the queries above, or rephrase your question more clearly."
    }


def generate_low_confidence_warning(plan: QueryPlan, confidence: float) -> str:
    """
    FIX #39: Generate warning message for low-confidence execution.
    """
    factors = []
    if confidence < 0.3:
        factors.append("unclear intent")
    if not plan.metric_column:
        factors.append("no metric found")
    if not plan.group_by_column and plan.query_type in ["aggregation", "distribution"]:
        factors.append("ambiguous grouping")
    if plan.filters:
        factors.append("complex filters applied")
    
    if not factors:
        factors = ["uncertain interpretation"]
    
    return (f"⚠️ Low confidence ({confidence:.0%}): {', '.join(factors)}. "
            f"Results may not match your intent. Please verify.")


def validate_execution_safety(response: dict, plan: QueryPlan, confidence: float) -> Tuple[bool, str]:
    """
    FIX #39: Validate that execution won't produce misleading results.
    Returns (is_safe, reason)
    """
    # Check 1: Result makes sense for query type
    if response.get("type") == "structured":
        if not response.get("table"):
            return False, "empty_result"
        
        # Check 2: Low confidence + ambiguous result = potentially misleading
        if confidence < 0.4 and plan.query_type in ["aggregation", "ranking"]:
            if len(response.get("table", [])) > 0:
                # Result exists but we're not confident - potentially misleading
                return False, "unsafe_low_confidence"
        
        # Check 3: Filter results in very small dataset
        if plan.filters and len(response.get("table", [])) < 2 and confidence < 0.6:
            return False, "filter_too_selective"
    
    return True, "ok"


def add_confidence_annotations(response: dict, confidence: float, resolution_score: float) -> dict:
    """
    FIX #39: Add confidence annotations to response for frontend display.
    """
    if confidence < CONFIDENCE_THRESHOLDS.execute_with_insight:
        response["confidence_warning"] = generate_low_confidence_warning(
            response.get("plan", QueryPlan(raw_query="")), 
            confidence
        )
    
    response["confidence_metrics"] = {
        "overall_confidence": round(confidence, 2),
        "resolution_quality": round(resolution_score, 2),
        "execution_mode": (
            "trusted" if confidence >= 0.7 else
            "verified" if confidence >= 0.5 else
            "cautious" if confidence >= 0.35 else
            "experimental"
        )
    }
    
    return response


@app.post("/api/query")
async def query_endpoint(payload: dict):
    """
    Main query endpoint with comprehensive validation, error handling, 
    logging, and observability (Improvements #1, #2, #4, #5, #20, #21, #22, #23).
    """
    # ════════════════════════════════════════════════════════════════════
    # IMPROVEMENT #2: Global exception wrapper
    # ════════════════════════════════════════════════════════════════════
    
    session_id = payload.get("session_id")
    if not session_id or session_id not in datasets:
        return sanitize_for_json({
            "status": "error",
            "message": "Invalid or missing session_id. Please re-upload your dataset.",
            "code": "invalid_session"
        })

    df = datasets[session_id]
    meta = dataset_meta.get(session_id, {})
    context = meta.get("summary", "")
    history = conversation_history.get(session_id, [])
    
    q = payload.get("query", "").strip()
    enable_debug = payload.get("debug", False)  # Improvement #21
    
    if not q:
        return sanitize_for_json({
            "status": "error",
            "message": "Empty query. Please provide a question to analyze.",
            "code": "empty_query"
        })
    
    if len(q) < 2:
        return sanitize_for_json({
            "status": "error",
            "message": "Query too short. Please ask a more specific question.",
            "code": "query_too_short"
        })

    # ════════════════════════════════════════════════════════════════════
    # Initialize metrics tracking
    # ════════════════════════════════════════════════════════════════════
    import time
    start_ms = time.time() * 1000
    metrics = QueryExecutionMetrics()
    debug_info = {} if enable_debug else None
    
    try:
        # ════════════════════════════════════════════════════════════════════
        # Check query cache before processing
        # ════════════════════════════════════════════════════════════════════
        cached_result = query_cache.get(q, session_id)
        if cached_result:
            logger.info(f"Cache hit for query: {q[:50]}")
            cached_result["from_cache"] = True
            metrics.cache_hit = True
            metrics.total_ms = int((time.time() * 1000) - start_ms)
            metrics_tracker.record_success(plan.query_type if 'plan' in locals() else "unknown", metrics.total_ms, True)
            return sanitize_for_json(cached_result)

        if ai_call_count.get(session_id, 0) >= AI_CALL_LIMIT:
            metrics.total_ms = int((time.time() * 1000) - start_ms)
            QueryLogger.log_error(session_id, "ai_limit_exceeded", f"Reached {AI_CALL_LIMIT} calls")
            metrics_tracker.record_error("limit_exceeded")
            return sanitize_for_json({
                "status": "error",
                "message": f"AI call limit ({AI_CALL_LIMIT}) reached for this session. Start a new session to continue.",
                "code": "ai_limit_exceeded"
            })

        # ─────────────────────────────────────────────────────────────────
        # FIX #37: MULTI-STEP QUERY RESOLUTION
        # ─────────────────────────────────────────────────────────────────
        QueryLogger.log_query_attempt(session_id, q)
        
        resolution = resolve_query_multi_step(q, df, meta, history)
        plan = resolution.execution_plan or QueryPlan(raw_query=q)
        metrics_ms = int((time.time() * 1000) - start_ms)
        metrics.resolution_ms = metrics_ms
        QueryLogger.log_resolution_stage(session_id, 1, resolution.intent, resolution.confidence)
        
        # ════════════════════════════════════════════════════════════════════
        # IMPROVEMENT #4: Apply adaptive learning corrections
        # ════════════════════════════════════════════════════════════════════
        recommended_intent = adaptive_learner.get_recommended_intent(plan.query_type)
        if recommended_intent and recommended_intent != plan.query_type:
            logger.info(f"Adaptive learning: Correcting intent {plan.query_type} → {recommended_intent}")
            plan.query_type = recommended_intent
        
        if plan.metric_column:
            recommended_metric = adaptive_learner.get_recommended_column(plan.metric_column)
            if recommended_metric and recommended_metric in df.columns:
                logger.info(f"Adaptive learning: Correcting metric {plan.metric_column} → {recommended_metric}")
                plan.metric_column = recommended_metric
        
        confidence_boost = adaptive_learner.get_confidence_boost(plan.query_type, session_id)
        resolution.confidence = min(resolution.confidence + confidence_boost, 1.0)
        
        if enable_debug:
            debug_info["intent"] = plan.query_type
            debug_info["detected_metric"] = plan.metric_column
            debug_info["detected_grouping"] = plan.group_by_column
            debug_info["confidence_before_adaptive"] = resolution.confidence - confidence_boost
            debug_info["confidence_boost_applied"] = confidence_boost
        
        # ════════════════════════════════════════════════════════════════════
        # IMPROVEMENT #5: Confidence thresholding
        # ════════════════════════════════════════════════════════════════════
        is_confident, conf_err = QueryValidator.validate_confidence_threshold(
            resolution.confidence, threshold=0.35
        )
        if not is_confident and resolution.confidence < 0.25:
            QueryLogger.log_validation_failure(session_id, "confidence", f"Score: {resolution.confidence:.2f}")
            metrics.total_ms = int((time.time() * 1000) - start_ms)
            metrics_tracker.record_unsupported("low_confidence")
            
            # Improvement #19: Generate dynamic suggestions
            suggestions = SchemaIntelligence.get_best_metric_candidates(df, meta, 3)
            
            return sanitize_for_json({
                "status": "clarification",
                "message": "I'm not confident about your query. Could you be more specific?",
                "query_type": plan.query_type,
                "confidence": resolution.confidence,
                "suggestions": suggestions if suggestions else generate_suggestions(df, meta),
                "debug": debug_info,
                "code": "low_confidence"
            })
        
        # ════════════════════════════════════════════════════════════════════
        # IMPROVEMENT #10: Ambiguity detection
        # ════════════════════════════════════════════════════════════════════
        is_ambig, ambig_msg = detect_ambiguity(q, plan, meta)
        if is_ambig:
            QueryLogger.log_validation_failure(session_id, "ambiguity", ambig_msg)
            metrics.total_ms = int((time.time() * 1000) - start_ms)
            metrics_tracker.record_unsupported("ambiguous_query")
            
            return sanitize_for_json({
                "status": "clarification",
                "message": ambig_msg,
                "query_type": plan.query_type,
                "confidence": resolution.confidence,
                "suggestions": SchemaIntelligence.get_best_metric_candidates(df, meta, 3),
                "debug": debug_info,
                "code": "ambiguous_query"
            })
        
        # ════════════════════════════════════════════════════════════════════
        # IMPROVEMENT #7: Metric validation
        # ════════════════════════════════════════════════════════════════════
        if plan.metric_column and plan.query_type in ["aggregation", "kpi", "ranking"]:
            is_valid_metric, metric_err = QueryValidator.validate_metric_column(
                plan.metric_column, df, meta
            )
            if not is_valid_metric:
                QueryLogger.log_validation_failure(session_id, "metric_validation", metric_err)
                metrics.total_ms = int((time.time() * 1000) - start_ms)
                metrics_tracker.record_unsupported("invalid_metric")
                
                return sanitize_for_json({
                    "status": "error",
                    "message": f"Cannot use '{plan.metric_column}' for this operation: {metric_err}",
                    "suggestions": SchemaIntelligence.get_best_metric_candidates(df, meta, 5),
                    "debug": debug_info,
                    "code": "invalid_metric"
                })
        
        # ════════════════════════════════════════════════════════════════════
        # IMPROVEMENT #8: Group-by validation
        # ════════════════════════════════════════════════════════════════════
        if plan.group_by_column and plan.query_type in ["aggregation", "trend", "ranking", "distribution"]:
            is_valid_groupby, groupby_err = QueryValidator.validate_group_by_column(
                plan.group_by_column, df, meta
            )
            if not is_valid_groupby:
                QueryLogger.log_validation_failure(session_id, "groupby_validation", groupby_err)
                metrics.total_ms = int((time.time() * 1000) - start_ms)
                metrics_tracker.record_unsupported("invalid_groupby")
                
                return sanitize_for_json({
                    "status": "error",
                    "message": f"Cannot group by '{plan.group_by_column}': {groupby_err}",
                    "suggestions": SchemaIntelligence.get_best_dimension_candidates(df, meta, 5),
                    "debug": debug_info,
                    "code": "invalid_groupby"
                })
        
        if plan.clarification_needed and resolution.confidence < 0.2:
            return sanitize_for_json({
                "status": "clarification",
                "message": plan.clarification_reason,
                "suggestions": SchemaIntelligence.get_best_metric_candidates(df, meta, 3),
                "debug": debug_info,
                "code": "needs_clarification"
            })

        # Stage 3: Pre-execution validity (FIX #10)
        is_valid, val_err = validate_query_plan(plan, df, meta)
        if not is_valid:
            return {"type":"error","title":"Query cannot be executed",
                    "insight":f"{val_err} {suggest_closest_column(plan.raw_query, meta)}"}

        # ─────────────────────────────────────────────────────────────────
        # FIX #40: CONFIDENCE SCORING FOR QUERY RESOLUTION
        # ════════════════════════════════════════════════════════════════════
        # IMPROVEMENT #2: Use embedding-based ranker for better semantic matching
        # ════════════════════════════════════════════════════════════════════
        ranker = EmbeddingBasedRanker(df, meta)  # Improved from SemanticRanker
        scorer = ConfidenceScorer(df, meta, ranker)
        
        conditions = detect_query_conditions(q)
        
        # Calculate comprehensive confidence score
        confidence_score = scorer.calculate_total_confidence(
            plan.metric_column,
            plan.group_by_column,
            conditions,
            resolution.execution_plan.roles if resolution.execution_plan else {},
            plan.filters,
            plan.query_type
        )
        
        # Update resolution confidence with refined score
        resolution.confidence = max(resolution.confidence, confidence_score)
        
        logger.info(f"Confidence score: {confidence_score:.2f} for '{q[:50]}'")

        # ─────────────────────────────────────────────────────────────────
        # FIX #41: REDUCE UNNECESSARY API USAGE - DETERMINISTIC EXECUTION
        # ─────────────────────────────────────────────────────────────────
        
        # Check if query can be answered deterministically (no LLM needed)
        if DeterministicExecutor.is_query_deterministic(q, plan, meta):
            logger.info(f"Executing deterministic query (no LLM): {q[:50]}")
            
            response = None
            if plan.query_type == "kpi" and plan.metric_column:
                response = DeterministicExecutor.execute_aggregation_query(df, plan)
            elif plan.query_type in ["aggregation", "distribution"] and plan.query_type == "distribution":
                response = DeterministicExecutor.execute_count_query(df, plan)
            elif plan.query_type == "ranking":
                response = DeterministicExecutor.execute_ranking_query(df, plan)
            elif plan.query_type == "raw_retrieval":
                response = DeterministicExecutor.execute_raw_retrieval_query(df, plan)
            
            if response:
                # FIX #42: Use ResponseRenderer for consistent formatting
                response = ResponseRenderer.render(response, q, plan)
                response["confidence"] = resolution.confidence
                response = add_confidence_annotations(response, resolution.confidence, resolution.resolution_score)
                
                # Skip AI insight for deterministic queries (we know the answer)
                conversation_history[session_id].append({
                    "raw_query": q, "response": response,
                    "plan": plan.to_dict(), "timestamp": datetime.utcnow().isoformat(),
                    "resolution": resolution.to_dict() if 'resolution' in locals() else {},
                    "execution_type": "deterministic"
                })
                conversation_history[session_id] = conversation_history[session_id][-10:]
                
                response.setdefault("type", "structured")
                response.setdefault("title", q.capitalize())
                response["ai_calls_used"] = ai_call_count.get(session_id, 0)
                response["ai_calls_remaining"] = AI_CALL_LIMIT - ai_call_count.get(session_id, 0)
                return sanitize_for_json(response)

        # Stage 4: Execute query (LLM-based execution for complex queries)
        # Improvement #4: Never downgrade to explanation if we have executable plan with dataset references
        has_dataset_reference = (
            (plan.metric_column and plan.metric_column in df.columns) or
            (plan.group_by_column and plan.group_by_column in df.columns) or
            any(f in df.columns for f in plan.filters.keys())
        )
        
        # Improvement #18: Log resolved query plan details before execution
        logger.info(f"Executing query plan: type={plan.query_type}")
        logger.info(f"  Metric: {plan.metric_column}, GroupBy: {plan.group_by_column}")
        logger.info(f"  Filters: {plan.filters}, Operation: {plan.operation}")
        logger.info(f"  Has dataset reference: {has_dataset_reference}")
        
        if plan.query_type == "explanation" and has_dataset_reference:
            # Improvement #4: Prefer aggregation over explanation when we have data references
            logger.info(f"Improvement #4: Preventing explanation fallback (have dataset references)")
            plan.query_type = "aggregation"
        
        response = execute_query_plan(plan, df, meta, context, history, session_id)
        response["confidence"] = resolution.confidence
        
        # Improvement #19: Execution-result sanity checks
        if plan.aggregation and plan.aggregation.operation:
            agg_op = plan.aggregation.operation.lower()
            result_type = response.get("type", "")
            
            # Verify aggregation result type matches operation
            if agg_op in ["sum", "total"] and result_type == "kpi":
                logger.debug(f"Sanity check: SUM operation returned KPI (correct)")
            elif agg_op in ["avg", "average", "mean"] and result_type == "kpi":
                scalar = response.get("scalar")
                if scalar is not None and isinstance(scalar, (int, float)):
                    logger.debug(f"Sanity check: AVG operation returned numeric KPI (correct)")
            elif result_type == "table" and plan.group_by_column:
                table = response.get("table", [])
                if table and isinstance(table, list):
                    logger.debug(f"Sanity check: Aggregation returned table with {len(table)} rows (correct)")
            else:
                logger.warning(f"Sanity check: {agg_op} operation returned {result_type} (may need verification)")

        if plan.repaired_query:
            response["repaired_query"] = plan.repaired_query

        # ─────────────────────────────────────────────────────────────────
        # FIX #42: RESPONSE RENDERER LAYER
        # ─────────────────────────────────────────────────────────────────
        response = ResponseRenderer.render(response, q, plan)

        # Stage 5: Validate execution safety (FIX #39)
        is_safe, safety_reason = validate_execution_safety(response, plan, resolution.confidence)
        if not is_safe:
            if safety_reason == "unsafe_low_confidence":
                logger.warning(f"Execution unsafe: low confidence result for '{q[:50]}'")
                response["type"] = "fallback"
                response["title"] = "Result may be inaccurate"
                response["insight"] = (
                    f"I executed your query but with low confidence ({resolution.confidence:.0%}). "
                    f"The result below may not match your intent. Please verify the data."
                )
                response["warning"] = generate_low_confidence_warning(plan, resolution.confidence)
            elif safety_reason == "filter_too_selective":
                logger.warning(f"Execution warning: filter too selective for '{q[:50]}'")
                response["warning"] = "Your filter is very specific - the result is based on very few rows."
        
        # Stage 6: Add confidence annotations (FIX #39)
        response = add_confidence_annotations(response, resolution.confidence, resolution.resolution_score)
        
        # ════════════════════════════════════════════════════════════════════
        # IMPROVEMENT #5: Apply smart visualization intelligence
        # ════════════════════════════════════════════════════════════════════
        if response.get("type") == "structured" and response.get("table"):
            try:
                selector = VisualizationSelector(df, meta)
                result_df = pd.DataFrame(response["table"])
                
                # Smart visualization selection
                smart_viz = selector.select_visualization(plan, result_df)
                if smart_viz and smart_viz != response.get("visualization"):
                    logger.info(f"Smart viz selection: {response.get('visualization')} → {smart_viz}")
                    response["visualization"] = smart_viz
                    response["visualization_recommendation"] = smart_viz
                    
                    # Generate optimized chart config
                    chart_config = selector.get_chart_config(smart_viz, result_df, plan)
                    if chart_config:
                        response["chart"] = chart_config
            except Exception as e:
                logger.warning(f"Smart visualization selection failed: {e}")
        
        # Stage 7: Generate AI insight only if high confidence (FIX #11-15, enhanced for #41)
        if (response.get("type") == "structured"
                and "insight" not in response
                and response.get("table")
                and resolution.confidence >= CONFIDENCE_THRESHOLDS.execute_with_insight):
            result_df = pd.DataFrame(response["table"])
            ok, _     = is_result_meaningful(result_df, plan)
            if ok:
                ai_call_count[session_id] = ai_call_count.get(session_id, 0) + 1
                insight = generate_ai_insight(q, result_df, plan, context)
                if insight:
                    response["insight"] = insight
        
        # ════════════════════════════════════════════════════════════════════
        # Cache the response for future identical queries
        # ════════════════════════════════════════════════════════════════════
        query_cache.set(q, session_id, response)

    except Exception as e:
        logger.error("Query error: %s", e, exc_info=True)
        # ════════════════════════════════════════════════════════════════════
        # IMPROVEMENT #2: Global exception handling with detailed error info
        # ════════════════════════════════════════════════════════════════════
        metrics.total_ms = int((time.time() * 1000) - start_ms)
        query_type = plan.query_type if 'plan' in locals() else "unknown"
        QueryLogger.log_error(session_id, type(e).__name__, str(e)[:100])
        metrics_tracker.record_error(query_type)
        
        error_msg = str(e)[:150]
        
        return sanitize_for_json({
            "status": "error",
            "message": (
                "An unexpected error occurred while processing your query. "
                "Please try rephrasing your question or contact support if the issue persists."
            ),
            "code": "query_execution_error",
            "error_type": type(e).__name__,
            "debug_info": {"error": error_msg} if enable_debug else None,
            "suggestions": SchemaIntelligence.get_best_metric_candidates(df, meta, 3) if 'df' in locals() else [],
            "metrics": metrics.to_dict(),
            "debug": debug_info
        })

    # ════════════════════════════════════════════════════════════════════
    # IMPROVEMENT #20, #22: Record successful execution
    # ════════════════════════════════════════════════════════════════════
    metrics.total_ms = int((time.time() * 1000) - start_ms)
    
    try:
        result_rows = len(response.get("table", []))
        if result_rows == 0:
            metrics_tracker.record_empty(plan.query_type if 'plan' in locals() else "unknown")
        else:
            metrics_tracker.record_success(plan.query_type if 'plan' in locals() else "unknown", metrics.total_ms)
    except:
        pass  # Don't fail on metrics tracking
    
    # ════════════════════════════════════════════════════════════════════
    # IMPROVEMENT #3: Add empty result handling
    # ════════════════════════════════════════════════════════════════════
    if response.get("type") not in ["error", "clarification", "fallback"]:
        if not response.get("table") or len(response.get("table", [])) == 0:
            response["type"] = "info"
            response["message"] = "No results found matching your query"
            response["code"] = "empty_result"

    conversation_history[session_id].append({
        "raw_query": q,
        "response": response,
        "plan": plan.to_dict() if 'plan' in locals() else {},
        "timestamp": datetime.utcnow().isoformat(),
        "resolution": resolution.to_dict() if 'resolution' in locals() else {},
        "execution_type": response.get("execution_type", "llm_based"),
        "confidence_metrics": response.get("confidence_metrics", {}),
        "metrics": metrics.to_dict()
    })
    conversation_history[session_id] = conversation_history[session_id][-10:]

    response.setdefault("type", "structured")
    response.setdefault("title", q.capitalize())
    response.setdefault("status", "success")
    response["ai_calls_used"]      = ai_call_count.get(session_id, 0)
    response["ai_calls_remaining"] = AI_CALL_LIMIT - ai_call_count.get(session_id, 0)
    response["metrics"] = metrics.to_dict()
    response["debug"] = debug_info
    
    QueryLogger.log_execution_result(
        session_id, 
        plan.query_type if 'plan' in locals() else "unknown",
        response.get("status", "success"),
        len(response.get("table", [])),
        metrics.total_ms
    )
    
    return sanitize_for_json(response)



# ═══════════════════════════════════════════════════════════════════════════════
# HISTORY / EXPORT / HEALTH
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    if session_id not in conversation_history:
        return {"error": "Session not found."}
    return sanitize_for_json({"history": conversation_history[session_id]})


@app.get("/api/metadata/{session_id}")
async def get_metadata(session_id: str):
    """
    FIX #43: Get enhanced dataset metadata for current session.
    Returns: numeric/categorical summaries, value distributions, temporal ranges,
    data quality metrics, and column compatibility info.
    """
    if session_id not in dataset_meta:
        return {"error": "Session not found."}
    
    meta = dataset_meta[session_id]
    
    # Compute execution statistics from history
    history = conversation_history.get(session_id, [])
    deterministic_count = sum(1 for h in history if h.get("execution_type") == "deterministic")
    llm_count = sum(1 for h in history if h.get("execution_type") == "llm_based")
    avg_confidence = (
        sum(h.get("confidence_metrics", {}).get("overall_confidence", 0) for h in history) / len(history)
        if history else 0
    )
    
    return sanitize_for_json({
        "session_id": session_id,
        "column_info": {
            "total": len(meta.get("column_types", {})),
            "numeric": len(meta.get("numeric_cols", [])),
            "categorical": len(meta.get("categorical_cols", [])),
            "temporal": len(meta.get("datetime_cols", [])),
            "id_like": len(meta.get("id_like_cols", []))
        },
        "numeric_summaries": meta.get("numeric_summaries", {}),
        "categorical_summaries": meta.get("categorical_summaries", {}),
        "value_distributions": meta.get("value_distributions", {}),
        "temporal_ranges": meta.get("temporal_ranges", {}),
        "data_quality": meta.get("data_quality", {}),
        "execution_stats": {
            "deterministic_queries": deterministic_count,
            "llm_queries": llm_count,
            "avg_confidence": round(avg_confidence, 2),
            "ai_calls_used": ai_call_count.get(session_id, 0),
            "query_history_size": len(history)
        }
    })


@app.post("/api/resolve_stages")
async def resolve_stages_endpoint(payload: dict):
    """
    FIX #37: Debug endpoint to see multi-step query resolution stages.
    Shows: intent → operations → semantic mapping → filters → execution plan
    """
    session_id = payload.get("session_id")
    if not session_id or session_id not in datasets:
        return {"error": "Invalid or missing session_id."}
    
    query = payload.get("query", "").strip()
    if not query:
        return {"error": "Empty query."}
    
    df = datasets[session_id]
    meta = dataset_meta.get(session_id, {})
    history = conversation_history.get(session_id, [])
    
    try:
        resolution = resolve_query_multi_step(query, df, meta, history)
        
        return {
            "type": "resolution_debug",
            "query": query,
            "stages": {
                "stage1_intent": {
                    "intent": resolution.intent,
                    "description": f"Detected query intent as: {resolution.intent}"
                },
                "stage2_operations": {
                    "operations": resolution.operations,
                    "description": f"Detected {len(resolution.operations)} operation(s): {', '.join(resolution.operations)}"
                },
                "stage3_semantic_mapping": {
                    "mapping": resolution.semantic_mapping,
                    "description": f"Mapped {len(resolution.semantic_mapping)} term(s) to columns"
                },
                "stage4_filters": {
                    "filters": resolution.filters,
                    "description": f"Extracted {len(resolution.filters)} filter(s)"
                },
                "stage5_execution_plan": {
                    "plan_valid": resolution.execution_plan is not None,
                    "query_type": resolution.execution_plan.query_type if resolution.execution_plan else None,
                    "execution_mode": resolution.execution_plan.execution_mode if resolution.execution_plan else None
                }
            },
            "scores": {
                "confidence": resolution.confidence,
                "resolution_score": resolution.resolution_score
            },
            "issues": resolution.issues,
            "metadata": resolution.metadata
        }
    except Exception as e:
        logger.error("Resolution debug error: %s", e, exc_info=True)
        return {"error": f"Resolution failed: {str(e)[:100]}"}


@app.post("/api/export")
async def export(payload: dict):
    chats     = payload.get("chatHistory", [])
    file_path = f"/tmp/datasage_report_{uuid.uuid4().hex}.pdf"
    doc       = SimpleDocTemplate(file_path)
    styles    = getSampleStyleSheet()
    elements  = []
    elements.append(Paragraph("DataSage Report", styles["Title"]))
    elements.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        styles["Normal"]))
    elements.append(Spacer(1, 20))

    for i, chat in enumerate(chats):
        query_text = chat.get("query", f"Query {i+1}")
        elements.append(Paragraph(f"Q{i+1}: {query_text}", styles["Heading2"]))
        elements.append(Spacer(1, 4))
        res  = chat.get("response", {})
        conf = res.get("confidence")
        if conf is not None:
            label = "High" if conf > 0.7 else ("Medium" if conf > 0.4 else "Low")
            elements.append(Paragraph(f"<i>Confidence: {label} ({conf:.0%})</i>", styles["Normal"]))
            elements.append(Spacer(1, 4))
        if res.get("repaired_query"):
            elements.append(Paragraph(f"<i>Interpreted as: {res['repaired_query']}</i>", styles["Normal"]))
            elements.append(Spacer(1, 4))
        if res.get("insight"):
            elements.append(Paragraph(re.sub(r'\*+','',res["insight"]), styles["Normal"]))
            elements.append(Spacer(1, 8))
        table_data = res.get("table", [])
        if table_data:
            headers = list(table_data[0].keys())[:8]
            rows    = [headers] + [
                [str(row.get(h,""))[:30] for h in headers]
                for row in table_data[:50]
            ]
            t = Table(rows, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,0), colors.HexColor("#7C3AED")),
                ("TEXTCOLOR",     (0,0),(-1,0), colors.white),
                ("FONTSIZE",      (0,0),(-1,-1), 8),
                ("GRID",          (0,0),(-1,-1), 0.4, colors.HexColor("#E4E0FA")),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),
                 [colors.white, colors.HexColor("#F5F4FF")]),
                ("PADDING",       (0,0),(-1,-1), 5),
                ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ]))
            elements.append(t)
        elements.append(Spacer(1, 24))

    doc.build(elements)
    return FileResponse(file_path, filename="DataSage_Report.pdf",
                        media_type="application/pdf")


@app.get("/health")
async def health():
    return {"status":"ok",
            "active_sessions":  len(datasets),
            "cached_responses": len(ai_response_cache)}


# ═══════════════════════════════════════════════════════════════════════════════
# IMPROVEMENT #4: FEEDBACK ENDPOINT FOR ADAPTIVE LEARNING
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/feedback/{session_id}")
async def submit_feedback(session_id: str, payload: dict):
    """
    IMPROVEMENT #4: Adaptive learning feedback endpoint.
    Records user corrections to improve future query understanding.
    
    Payload:
    {
        "original_query": str,
        "original_intent": str,           # e.g., "trend"
        "corrected_intent": str,           # e.g., "aggregation"
        "original_metric": str,            # e.g., "revenue"
        "corrected_metric": str,           # e.g., "profit"
        "original_grouping": str,          # e.g., "date"
        "corrected_grouping": str,         # e.g., "region"
        "confidence_before": float,        # e.g., 0.45
        "was_useful": bool                 # True if result was helpful
    }
    """
    if session_id not in datasets:
        return {"error": "Invalid or missing session_id."}
    
    try:
        # Create feedback record
        feedback = QueryFeedback(
            session_id=session_id,
            query=payload.get("original_query", ""),
            original_intent=payload.get("original_intent", ""),
            corrected_intent=payload.get("corrected_intent", ""),
            original_metric=payload.get("original_metric", ""),
            corrected_metric=payload.get("corrected_metric", ""),
            original_grouping=payload.get("original_grouping", ""),
            corrected_grouping=payload.get("corrected_grouping", ""),
            confidence_before=payload.get("confidence_before", 0.0),
            was_useful=payload.get("was_useful", True),
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Record correction in adaptive learner
        adaptive_learner.record_correction(feedback)
        
        logger.info(f"Feedback recorded for session {session_id}: "
                   f"{feedback.original_intent} → {feedback.corrected_intent}")
        
        return {
            "status": "success",
            "message": "Thank you! Your feedback helps improve query understanding.",
            "recommendation": {
                "intent_boost": adaptive_learner.get_confidence_boost(
                    feedback.corrected_intent, session_id),
                "next_confidence": min(0.5 + adaptive_learner.get_confidence_boost(
                    feedback.corrected_intent, session_id), 1.0)
            }
        }
    except Exception as e:
        logger.error(f"Feedback submission error: {e}")
        return {
            "error": f"Failed to record feedback: {str(e)[:100]}",
            "status": "failed"
        }


# ═══════════════════════════════════════════════════════════════════════════════
# IMPROVEMENTS #21, #22: DEBUG & OBSERVABILITY ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/metrics")
async def get_system_metrics():
    """
    Improvement #22: Execution reliability metrics.
    Provides statistics on query success rates, common errors, and performance.
    """
    return sanitize_for_json({
        "status": "success",
        "metrics": metrics_tracker.get_stats(),
        "timestamp": datetime.utcnow().isoformat()
    })


@app.post("/api/explain-query")
async def explain_query(payload: dict):
    """
    Improvement #21: Planner debug mode.
    Shows how the planner interpreted a query without executing it.
    """
    session_id = payload.get("session_id")
    if not session_id or session_id not in datasets:
        return {"error": "Invalid session_id"}
    
    query = payload.get("query", "").strip()
    if not query:
        return {"error": "Empty query"}
    
    try:
        df = datasets[session_id]
        meta = dataset_meta.get(session_id, {})
        history = conversation_history.get(session_id, [])
        
        # Run multi-step resolution without execution
        resolution = resolve_query_multi_step(query, df, meta, history)
        plan = resolution.execution_plan or QueryPlan(raw_query=query)
        
        # Check dataset capabilities
        capabilities = QueryValidator.detect_dataset_capabilities(df, meta)
        
        return sanitize_for_json({
            "status": "success",
            "query_original": query,
            "query_interpreted": plan.repaired_query or query,
            "planner_decisions": {
                "query_type": plan.query_type,
                "metric_column": plan.metric_column,
                "group_by_column": plan.group_by_column,
                "filters": plan.filters,
                "temporal_column": plan.temporal_column,
                "temporal_granularity": plan.temporal_granularity,
                "confidence": round(resolution.confidence, 2),
                "resolution_score": round(resolution.resolution_score, 2),
                "execution_mode": plan.execution_mode,
                "visualization": plan.visualization,
                "is_ambiguous": plan.is_ambiguous,
                "ambiguity_reason": plan.ambiguity_reason if plan.is_ambiguous else "",
                "clarification_needed": plan.clarification_needed
            },
            "dataset_capabilities": capabilities,
            "metric_candidates": SchemaIntelligence.get_best_metric_candidates(df, meta, 5),
            "dimension_candidates": SchemaIntelligence.get_best_dimension_candidates(df, meta, 5),
            "temporal_columns": SchemaIntelligence.get_temporal_columns(df, meta),
            "confidence_breakdown": {
                "metric_confidence": resolution.confidence * 0.25,  # Approximate
                "grouping_confidence": resolution.confidence * 0.20,
                "intent_confidence": resolution.confidence * 0.25,
                "role_confidence": resolution.confidence * 0.20,
                "filter_confidence": resolution.confidence * 0.10
            },
            "resolution_issues": resolution.issues,
            "routing_path": QueryRouter.classify_query_path(plan),
            "is_supported": QueryRouter.is_supported(plan.query_type),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Query explanation error: {e}")
        return {
            "error": f"Failed to explain query: {str(e)[:100]}",
            "status": "failed"
        }