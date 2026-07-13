from fastapi import APIRouter, HTTPException

from query.operation_parser import OperationParser
from query.column_matcher import ColumnMatcher
from storage.session_manager import SessionManager
from query.intent_validator import IntentValidator
from core.analytics_engine import AnalyticsEngine
from models.query_plan import QueryPlan
from query.condition_parser import ConditionParser
from query.dimension_parser import DimensionParser

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.get("/parse")
def parse_question(session_id: str, question: str):
    dataset = SessionManager.get(session_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid session ID."
        )

    parsed = OperationParser.parse(question)
    condition_result = ConditionParser.parse(
        parsed["remaining_text"],
        dataset.schema,
    )
    dimension_result = DimensionParser.parse(
        condition_result.cleaned_text,
        dataset.schema,
    )

    matched_columns = ColumnMatcher.match(
        dimension_result.cleaned_text,
        dataset.schema,
    )

    validation = IntentValidator.validate(
        parsed["operation"],
        matched_columns
    )
    
    if validation.success:
        
        plan = QueryPlan(
            operation=parsed["operation"],
            target_column=validation.column,
            dimensions=dimension_result.dimensions,
            conditions=condition_result.conditions,
        )
    
        result = AnalyticsEngine.execute(
            dataset,
            plan,
        )
        
    else:
        
        result = None

    return {
        "operation": parsed["operation"],
        "remaining_text": parsed["remaining_text"],
        "matched_columns": [column.name for column in matched_columns],
        "validation": {
            "success": validation.success,
            "error": validation.error,
            "selected_column": (
                validation.column.name if validation.column else None
            )
        },
        "cleaned_text": dimension_result.cleaned_text,
        "conditions": [
            {
                "column": c.column,
                "operator": c.operator,
                "value": c.value,
            }
            for c in condition_result.conditions
        ],
        "dimensions": [
            d.column
            for d in dimension_result.dimensions
        ],
        "result": result
    }
