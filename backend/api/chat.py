from fastapi import APIRouter

from core.ai.ai_engine import AIEngine
from core.ai.insight_request_builder import InsightRequestBuilder
from core.ai.dataset_description_request_builder import (
    DatasetDescriptionRequestBuilder,
)
from core.query_engine import QueryEngine
from core.ai.prompt_builder import PromptBuilder
from models.insight_api_request import InsightAPIRequest

from storage.session_manager import SessionManager
from models.query_context import QueryContext

from core.chat_router import (
    ChatRoute,
    determine_route,
)


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
    3. Otherwise -> route to either:
       - Dataset Description
       - Insight
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
    print("QUERY PLAN:", plan)
    if not response.get("success"):
        print("ANALYTICS FAILED:", response)
        # return {
        #     "success": False,
        #     "analytics_error": response,
        # }
        return {
            "success": False,
            "analytics_error": response,
            "plan": str(plan),
        }

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
    # Analytics failed -> Decide conversation route
    # -------------------------------------------------

    query_context = SessionManager.get_query_context(
        request.session_id,
    )

    route = determine_route(
        question=request.follow_up_question,
        has_latest_analysis=query_context is not None,
    )

    # -------------------------------------------------
    # Dataset Description Route
    # -------------------------------------------------

    if route == ChatRoute.DATASET_DESCRIPTION:

        prompt = DatasetDescriptionRequestBuilder.build(
            dataset=dataset,
            question=request.follow_up_question,
        )

        description = AIEngine().generate(
            prompt,
        )

        return {
            "success": True,
            "mode": "dataset_description",
            "response": {
                "type": "insight",
                "title": "Dataset Overview",
                "insight": description,
            },
        }

    # -------------------------------------------------
    # Insight Route
    # -------------------------------------------------

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
    # Ensure stored context is explainable
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
    # Generate AI Insight
    # -------------------------------------------------

    insight_request = InsightRequestBuilder.build(
        question=request.follow_up_question,
        query_plan=query_context.query_plan,
        response=query_context.response,
    )

    prompt = PromptBuilder.build(
        insight_request,
    )

    insight = AIEngine().generate(
        prompt,
    )

    return {
        "success": True,
        "mode": "insight",
        "response": {
            "type": "insight",
            "title": "AI Insight",
            "insight": insight,
        },
    }
