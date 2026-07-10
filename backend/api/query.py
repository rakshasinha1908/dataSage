from fastapi import APIRouter, HTTPException

from storage.session_manager import SessionManager
from query.operation_parser import OperationParser
from query.column_matcher import ColumnMatcher
from query.intent_validator import IntentValidator
from core.analytics_engine import AnalyticsEngine
from models.query_plan import QueryPlan

router = APIRouter(prefix="/query", tags=["Query"])


@router.get("/")
def query_dataset(session_id: str, question: str):

    dataset = SessionManager.get(session_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid session ID."
        )

    parsed = OperationParser.parse(question)

    matched_columns = ColumnMatcher.match(
        parsed["remaining_text"],
        dataset.schema,
    )

    validation = IntentValidator.validate(
        parsed["operation"],
        matched_columns,
    )

    if not validation.success:
        return {
            "success": False,
            "error": validation.error,
        }
        
    plan = QueryPlan(
        operation=parsed["operation"],
        target_column=validation.column,
        conditions=condition_result.conditions,
    )
    
    result = AnalyticsEngine.execute(
        dataset,
        plan,
    )

    return {
        "success": True,
        "result": result,
    }