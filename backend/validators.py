from typing import Dict, Any, List, Optional, Tuple

import pandas as pd

from query_parser import QueryPlan, SemanticMatch


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
