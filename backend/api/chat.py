from fastapi import APIRouter

from core.ai.insight_engine import InsightEngine
from core.ai.insight_request_builder import InsightRequestBuilder
from core.query_engine import QueryEngine

from models.insight_api_request import InsightAPIRequest

from storage.session_manager import SessionManager
from models.query_context import QueryContext


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("/")
def chat(request: InsightAPIRequest):
    """
    Unified conversational endpoint.

    Flow:
    1. Try deterministic analytics.
    2. If successful -> return analytics.
    3. Otherwise -> treat as conversational follow-up.
    """

    dataset = SessionManager.get(
        request.session_id,
    )

    if dataset is None:
        return {
            "success": False,
            "message": "Session not found.",
        }

    # -------------------------------------------------
    # Try deterministic analytics first
    # -------------------------------------------------

    response, plan = QueryEngine.execute(
        dataset,
        request.follow_up_question,
    )

    if response.get("success"):

        query_context = QueryContext(
            question=request.follow_up_question,
            query_plan=plan,
            response=response,
        )
        SessionManager.save_query_context(
            request.session_id,
            query_context,
        )

        return {
            "success": True,
            "mode": "analytics",
            "response": response,
        }

    # -------------------------------------------------
    # Fallback to conversational AI
    # -------------------------------------------------

    query_context = SessionManager.get_query_context(
        request.session_id,
    )

    if query_context is None:
        return {
            "success": False,
            "mode": "insight",
            "response": {
                "message": (
                    "I don't have an analytical result to explain yet. "
                    "Please run an analytical query first (for example, "
                    "'Average transaction amount by city') and then ask "
                    "follow-up questions like 'Why?' or "
                    "'How could this be improved?'."
                )
            },
        }

    # -------------------------------------------------
    # Ensure the stored context is explainable
    # -------------------------------------------------

    if (
        query_context.query_plan is None
        or query_context.response is None
    ):
        return {
            "success": False,
            "mode": "insight",
            "response": {
                "message": (
                    "I don't have an analytical result to explain. "
                    "Please ask an analytical question first."
                )
            },
        }

    # -------------------------------------------------
    # Build AI request
    # -------------------------------------------------

    insight_request = InsightRequestBuilder.build(
        question=request.follow_up_question,
        query_plan=query_context.query_plan,
        response=query_context.response,
    )

    insight = InsightEngine().generate(
        insight_request,
    )

    return {
        "success": True,
        "mode": "insight",
        "response": {
            "insight": insight,
        },
    }