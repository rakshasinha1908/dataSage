from fastapi import APIRouter, HTTPException

from storage.session_manager import SessionManager

from core.analytics_engine import AnalyticsEngine
from core.response_builder import ResponseBuilder
from core.visualization_selector import VisualizationSelector

from models.query_context import QueryContext
from models.response import Response

from query.intent_validator import IntentValidator
from query.query_understanding import QueryUnderstanding


router = APIRouter(prefix="/query", tags=["Query"])


@router.get("/")
def query_dataset(session_id: str, question: str):

    dataset = SessionManager.get(session_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid session ID.",
        )

    print("\n================ DATASET SCHEMA ================")

    for column in dataset.schema:
        print(
            f"{column.name} ---> {column.normalized_name} | samples={column.sample_values}"
        )

    print("===============================================\n")

    plan = QueryUnderstanding.parse(
        question,
        dataset.schema,
    )

    validation = IntentValidator.validate(
        plan.operation,
        [plan.target_column] if plan.target_column else [],
    )

    print("=" * 60)
    print("Question          :", question)
    print("Operation         :", plan.operation)
    print(
        "Matched Columns   :",
        [plan.target_column.name] if plan.target_column else [],
    )
    print("Validation        :", validation.success)
    print("Validation Error  :", validation.error)
    print("=" * 60)

    if not validation.success:
        return Response(
            success=False,
            answer=None,
            visualization=None,
            can_explain=False,
            error=validation.error,
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