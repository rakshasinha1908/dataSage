from abc import ABC, abstractmethod

from typing import Dict, Any, Optional

import pandas as pd

from query_parser import QueryPlan


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