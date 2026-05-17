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

BUSINESS_SYNONYM_MAP: Dict[str, List[str]] = {
    "revenue":   ["revenue","sales","income","earnings","turnover","gross_sales",
                  "total_sales","net_sales","amount","value","total_amount",
                  "sale_amount","revenue_usd","gross_revenue"],
    "profit":    ["profit","margin","net_profit","net_income","ebitda",
                  "gross_profit","profit_margin","operating_income"],
    "cost":      ["cost","expense","cogs","expenditure","spend","spending",
                  "cost_of_goods","total_cost","unit_cost","overhead"],
    "price":     ["price","rate","unit_price","fee","charge","selling_price",
                  "list_price","cost_per_unit","avg_price"],
    "discount":  ["discount","rebate","deduction","markdown","offer","promo"],
    "quantity":  ["quantity","qty","units","volume","count","units_sold",
                  "num_units","pieces","items","stock"],
    "orders":    ["orders","transactions","purchases","invoices","receipts",
                  "deals","order_count","num_orders"],
    "customer":  ["customer","client","buyer","user","account","person",
                  "name","customer_name","client_name","consumer"],
    "employee":  ["employee","staff","worker","agent","rep","sales_rep",
                  "associate","headcount"],
    "product":   ["product","item","sku","good","service","offering",
                  "product_name","item_name","product_type","merchandise"],
    "category":  ["category","type","segment","class","group","department",
                  "kind","product_category","genre","sector","vertical"],
    "date":      ["date","order_date","created_at","updated_at","timestamp",
                  "purchase_date","transaction_date","invoice_date","period",
                  "month","year","day","week","quarter"],
    "region":    ["region","area","location","country","city","state",
                  "territory","zone","market","store","branch","site",
                  "district","geography"],
    "score":     ["score","rating","rank","grade","points","nps","csat",
                  "satisfaction","review","stars"],
    "age":       ["age","tenure","duration","years","days_old","customer_age",
                  "account_age","lifetime"],
    "status":    ["status","state","stage","phase","condition","order_status",
                  "payment_status","fulfillment"],
    "profit_margin": ["profit_margin","margin_pct","gross_margin","net_margin"],
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
                    parsed = pd.to_datetime(series, infer_datetime_format=True, errors="coerce")
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
    ]

    aggregation_patterns = [
        r"\btotal\b",
        r"\bsum\b",
        r"\baverage\b",
        r"\bcount\b",
        r"\btop\b",
        r"\bhighest\b",
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

    q = query.lower()

    # ─────────────────────────────
    # 1. RAW RETRIEVAL
    # ─────────────────────────────
    if is_raw_retrieval_query(q):
        return "raw_retrieval"

    # ─────────────────────────────
    # 2. COMPARISON
    # ─────────────────────────────
    if is_comparison_query(q):
        return "comparison"

    # ─────────────────────────────
    # 3. TREND
    # ─────────────────────────────
    if is_trend_query(q):
        return "trend"

    # ─────────────────────────────
    # 4. DISTRIBUTION / GROUPED COUNT
    # ─────────────────────────────
    if roles.get("is_cat_dist"):
        return "distribution"

    if (
        roles.get("is_count")
        and roles.get("grouping_entity")
    ):
        return "distribution"

    # categorical "most used" type queries
    if (
        roles.get("grouping_entity")
        and not roles.get("metric")
        and re.search(
            r'\b(most|least|highest|lowest|top|bottom|used)\b',
            q
        )
    ):
        return "distribution"

    # ─────────────────────────────
    # 5. RANKING
    # ─────────────────────────────
    if is_ranking_query(q):
        return "ranking"

    # ─────────────────────────────
    # 6. KPI
    # ─────────────────────────────
    if is_kpi_query(q):
        return "kpi"

    # ─────────────────────────────
    # 7. GROUPED AGGREGATION
    # ─────────────────────────────
    if (
        roles.get("aggregation")
        and roles.get("metric")
        and roles.get("grouping_entity")
    ):
        return "aggregation"

    # ─────────────────────────────
    # 8. FALLBACK
    # ─────────────────────────────
    return "explanation"




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
                break

        if not roles["metric"]:
            # avoid forcing metrics for grouped count queries
            if not (
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

    return roles


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
    for col in safe_num[:2]:
        sugg.append(f"Top 5 by {col}")
        sugg.append(f"Average {col}")
    if len(safe_num) >= 2:
        sugg.append(f"Compare {safe_num[0]} and {safe_num[1]}")
    if cat_cols:
        sugg.append(f"Distribution of {cat_cols[0]}")
        if safe_num:
            sugg.append(f"Average {safe_num[0]} by {cat_cols[0]}")
    if date_col and safe_num:
        sugg.append(f"Trend of {safe_num[0]} over time")
    sugg.append("Explain this dataset")
    return sugg[:6]


# ═══════════════════════════════════════════════════════════════════════════════
# FIX #25: AUTOMATIC DATETIME GROUPING
# ═══════════════════════════════════════════════════════════════════════════════

def auto_datetime_grouping(df: pd.DataFrame, date_col: str,
                           query: str) -> Tuple[pd.Series, str]:
    """FIX #25: Auto-detect year/quarter/month/week/day granularity."""
    q           = query.lower()
    date_series = pd.to_datetime(df[date_col], errors="coerce")
    date_range  = (
        (date_series.max() - date_series.min()).days
        if date_series.notna().any() else 0
    )

    if re.search(r'\b(year(?:ly)?|annual(?:ly)?)\b', q):
        return date_series.dt.to_period("Y").astype(str), "Year"
    if re.search(r'\b(quarter(?:ly)?|q[1-4])\b', q):
        return date_series.dt.to_period("Q").astype(str), "Quarter"
    if re.search(r'\b(week(?:ly)?)\b', q):
        return date_series.dt.to_period("W").astype(str), "Week"
    if re.search(r'\b(day|daily)\b', q):
        return date_series.dt.date.astype(str), "Day"

    # Auto from date range
    if date_range > 730:
        return date_series.dt.to_period("Q").astype(str), "Quarter"
    if date_range > 90:
        return date_series.dt.to_period("M").astype(str), "Month"
    if date_range > 14:
        return date_series.dt.to_period("W").astype(str), "Week"
    return date_series.dt.date.astype(str), "Day"


# ═══════════════════════════════════════════════════════════════════════════════
# QUERY EXECUTION ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

def execute_query_plan(plan: QueryPlan, df: pd.DataFrame, meta: dict,
                       context: str, history: List[dict], session_id: str) -> dict:
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

    mode = plan.execution_mode

    if mode == "ranked":
        return execute_ranking(plan, working_df, meta, filter_note)
    
    elif mode == "kpi":
        return execute_kpi_or_aggregation(plan, working_df, meta, filter_note)

    elif mode == "grouped":
        return execute_kpi_or_aggregation(plan, working_df, meta, filter_note)

    elif mode == "comparison":
        return execute_comparison(plan, working_df, meta, filter_note)

    elif mode == "trend":
        return execute_trend(plan, working_df, meta, filter_note)

    elif mode == "raw":
        return execute_raw_retrieval(plan, working_df, meta, filter_note)

    elif plan.query_type == "distribution":
        return execute_distribution(plan, working_df, meta, filter_note)

    elif plan.query_type == "correlation":
        return execute_correlation(plan, working_df, meta, filter_note)

    else:
        ai_call_count[session_id] = ai_call_count.get(session_id, 0) + 1

        return {
            "type": "ai",
            "title": "Analysis",
            "insight": answer_with_ai(
                plan.raw_query,
                working_df,
                meta,
                context,
                history
            )
        }


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
    """FIX #24: Aggregated monthly/yearly trends. FIX #25: Auto datetime grouping."""
    date_col = meta.get("date_col")
    id_cols  = set(meta.get("id_like_cols", []))
    safe_num = [c for c in meta.get("numeric_cols",[]) if c not in id_cols]

    if not plan.metric_column or plan.metric_column not in df.columns:
        return {"type":"error","title":"Metric not found",
                "insight":f"Try: {', '.join(safe_num[:3]) or 'none'}."}

    if date_col and date_col in df.columns:
        period_series, period_label = auto_datetime_grouping(df, date_col, plan.raw_query)
        tmp = df.copy()
        tmp["_period"] = period_series
        agg_op    = plan.aggregation.operation if plan.aggregation else "sum"
        pandas_fn = {"sum":"sum","avg":"mean","count":"count",
                     "min":"min","max":"max"}.get(agg_op,"sum")
        trend_df  = (tmp.groupby("_period")[plan.metric_column]
                     .agg(pandas_fn).reset_index())
        trend_df.columns = [period_label, plan.metric_column]
        trend_df  = trend_df.sort_values(period_label)
        x_labels  = trend_df[period_label].astype(str).tolist()
        title     = f"Trend of {plan.metric_column} by {period_label}{filter_note}"
    else:
        trend_df = df[[plan.metric_column]].dropna().reset_index(drop=True)
        trend_df.insert(0, "index", range(len(trend_df)))
        x_labels = list(range(len(trend_df)))
        title    = f"Trend of {plan.metric_column} (by row){filter_note}"

    display_limit = min(30, len(trend_df))
    return {
        "type":"structured",
        "visualization": "line",
        "title":title,
        "table": trend_df.head(display_limit).to_dict(orient="records"),
        "chart":{"type":"line",
                 "labels":[str(l) for l in x_labels[:display_limit]],
                 "values": trend_df[plan.metric_column].tolist()[:display_limit],
                 "x_label": x_labels[0] if x_labels else "Time",
                 "y_label": plan.metric_column}
    }


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

    result = result.head(plan.limit)
    sort_prefix = "Latest " if getattr(plan, "_sort_by_date_desc", False) else ""
    return {"type":"structured",
            "title": f"{sort_prefix}{len(result)} records{filter_note}",
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

    datasets[session_id]             = df
    ai_call_count[session_id]        = 0
    conversation_history[session_id] = []

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
        "suggestions":      generate_suggestions(df, meta),
        "summary":          summary

    })


# ═══════════════════════════════════════════════════════════════════════════════
# QUERY ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/query")
async def query_endpoint(payload: dict):
    session_id = payload.get("session_id")
    if not session_id or session_id not in datasets:
        return {"error": "Invalid or missing session_id. Please re-upload your dataset."}

    df      = datasets[session_id]
    meta    = dataset_meta.get(session_id, {})
    context = meta.get("summary", "")
    history = conversation_history.get(session_id, [])

    q = payload.get("query", "").strip()
    if not q:
        return {"error": "Empty query."}
    if len(q) < 2:
        return {"error": "Query too short."}

    if ai_call_count.get(session_id, 0) >= AI_CALL_LIMIT:
        return {"type":"error","title":"Session limit reached",
                "insight":f"AI limit ({AI_CALL_LIMIT}) reached. Start a new session."}

    try:
        plan = build_query_plan(q, df, meta, history)

        # FIX #17: Ambiguity check
        is_ambig, ambig_msg = detect_ambiguity(q, plan, meta)
        if is_ambig:
            return {"type":"clarification","title":"Could you be more specific?",
                    "insight":ambig_msg,"confidence":plan.confidence,
                    "suggestions": generate_suggestions(df, meta)}

        if plan.clarification_needed and plan.confidence < 0.2:
            return {"type":"clarification","title":"Need more information",
                    "insight":plan.clarification_reason,"confidence":plan.confidence,
                    "suggestions": generate_suggestions(df, meta)}

        # FIX #10: Pre-execution validity
        is_valid, val_err = validate_query_plan(plan, df, meta)
        if not is_valid:
            return {"type":"error","title":"Query cannot be executed",
                    "insight":f"{val_err} {suggest_closest_column(plan.raw_query, meta)}"}

        response = execute_query_plan(plan, df, meta, context, history, session_id)
        response["confidence"] = plan.confidence

        if plan.repaired_query:
            response["repaired_query"] = plan.repaired_query

        # FIX #11-15: Grounded AI insight
        if (response.get("type") == "structured"
                and "insight" not in response
                and response.get("table")):
            result_df = pd.DataFrame(response["table"])
            ok, _     = is_result_meaningful(result_df, plan)
            if ok and plan.confidence >= 0.35:
                ai_call_count[session_id] = ai_call_count.get(session_id, 0) + 1
                insight = generate_ai_insight(q, result_df, plan, context)
                if insight:
                    response["insight"] = insight

    except Exception as e:
        logger.error("Query error: %s", e, exc_info=True)
        return {"type":"error","title":"Query processing failed",
                "insight":f"Error: {str(e)[:100]}. Try rephrasing."}

    conversation_history[session_id].append({
        "raw_query": q, "response": response,
        "plan": plan.to_dict(), "timestamp": datetime.utcnow().isoformat()
    })
    conversation_history[session_id] = conversation_history[session_id][-10:]

    response.setdefault("type", "structured")
    response.setdefault("title", q.capitalize())
    response["ai_calls_used"]      = ai_call_count.get(session_id, 0)
    response["ai_calls_remaining"] = AI_CALL_LIMIT - ai_call_count.get(session_id, 0)
    return sanitize_for_json(response)


# ═══════════════════════════════════════════════════════════════════════════════
# HISTORY / EXPORT / HEALTH
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    if session_id not in conversation_history:
        return {"error": "Session not found."}
    return sanitize_for_json({"history": conversation_history[session_id]})


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