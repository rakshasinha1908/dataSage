from fastapi import APIRouter, HTTPException

from storage.session_manager import SessionManager

from core.ai.insight_request_builder import (
    InsightRequestBuilder,
)
from core.ai.insight_engine import InsightEngine

from models.insight_api_request import (
    InsightAPIRequest,
)

router = APIRouter(
    prefix="/insight",
    tags=["Insight"],
)


@router.post("/")
def generate_insight(
    request: InsightAPIRequest,
):

    query_context = SessionManager.get_query_context(
        request.session_id,
    )

    if query_context is None:
        raise HTTPException(
            status_code=404,
            detail="No previous query found for this session.",
        )

    insight_request = InsightRequestBuilder.build(
        question=request.follow_up_question,
        query_plan=query_context.query_plan,
        response=query_context.response,
    )

    engine = InsightEngine()

    insight = engine.generate(
        insight_request,
    )

    return {
        "success": True,
        "insight": insight,
    } 