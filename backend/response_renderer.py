from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Literal

import pandas as pd

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
        
        
