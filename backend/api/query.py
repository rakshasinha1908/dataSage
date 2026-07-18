from fastapi import APIRouter, HTTPException

from storage.session_manager import SessionManager

from query.operation_parser import OperationParser
from query.condition_parser import ConditionParser
from query.ranking_parser import RankingParser
from query.dimension_parser import DimensionParser
from query.column_matcher import ColumnMatcher
from query.intent_validator import IntentValidator

from core.analytics_engine import AnalyticsEngine
from core.visualization_selector import VisualizationSelector

from models.query_plan import QueryPlan
from models.response import Response
from core.response_builder import ResponseBuilder
from models.query_context import QueryContext


router = APIRouter(prefix="/query", tags=["Query"])


@router.get("/")
def query_dataset(session_id: str, question: str):

    dataset = SessionManager.get(session_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid session ID.",
        )

    parsed = OperationParser.parse(question)

    condition_result = ConditionParser.parse(
        parsed["remaining_text"],
        dataset.schema,
    )

    ranking_result = RankingParser.parse(
        condition_result.cleaned_text,
    )

    dimension_result = DimensionParser.parse(
        ranking_result.cleaned_text,
        dataset.schema,
    )

    matched_columns = ColumnMatcher.match(
        dimension_result.cleaned_text,
        dataset.schema,
    )

    validation = IntentValidator.validate(
        parsed["operation"],
        matched_columns,
    )

    print("\n" + "=" * 60)
    print("Question:", question)
    print("Parsed Operation:", parsed["operation"])
    print("Matched Columns:", [c.name for c in matched_columns])
    print("Validation Success:", validation.success)
    print("Validation Error:", validation.error)
    print("=" * 60 + "\n")

    if not validation.success:
        return Response(
            success=False,
            answer=None,
            visualization=None,
            can_explain=False,
            error=validation.error,
        )

    plan = QueryPlan(
        operation=parsed["operation"],
        target_column=validation.column,
        dimensions=dimension_result.dimensions,
        conditions=condition_result.conditions,
        ranking=ranking_result.ranking,
    )

    result = AnalyticsEngine.execute(
        dataset,
        plan,
    )

    visualization = VisualizationSelector.select(
        plan,
        result,
    )

    response = ResponseBuilder.build(
        plan,
        result,
        visualization,
    )

    query_context = QueryContext(
        question=question,
        query_plan=plan,
        response=response,
    )

    SessionManager.save_query_context(
        session_id,
        query_context,
    )

    return response
