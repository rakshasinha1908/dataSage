from fastapi import APIRouter

from core.ai.ai_engine import AIEngine
from core.ai.insight_request_builder import InsightRequestBuilder
from core.ai.dataset_description_request_builder import (
    DatasetDescriptionRequestBuilder,
)
from core.query_engine import QueryEngine
from core.ai.prompt_builder import PromptBuilder

from storage.session_manager import SessionManager
from models.query_context import QueryContext

from core.chat_router import (
    ChatRoute,
    determine_route,
)

from models.insight_api_request import InsightAPIRequest


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("/")
def chat(request: InsightAPIRequest):
    """
    Unified conversational endpoint.

    Flow:
    1. Load the uploaded dataset.
    2. Determine whether the request is:
       - deterministic analytics
       - dataset understanding
       - contextual insight
    3. Route to the appropriate processing layer.
    """

    # -------------------------------------------------
    # Session / dataset lookup
    # -------------------------------------------------

    dataset = SessionManager.get(
        request.session_id,
    )

    if dataset is None:
        return {
            "success": False,
            "mode": "session",
            "response": {
                "error": "Session not found.",
            },
        }

    # -------------------------------------------------
    # Existing analytical context
    # -------------------------------------------------

    query_context = SessionManager.get_query_context(
        request.session_id,
    )

    # -------------------------------------------------
    # Determine request route
    # -------------------------------------------------

    route = determine_route(
        question=request.follow_up_question,
        has_latest_analysis=query_context is not None,
    )

    print("=" * 60)
    print("CHAT ROUTING")
    print("=" * 60)
    print("Question :", request.follow_up_question)
    print("Route    :", route)
    print(
        "Context  :",
        "Available"
        if query_context is not None
        else "None",
    )
    print("=" * 60)

    # =================================================
    # ANALYTICS ROUTE
    # =================================================

    if route == ChatRoute.ANALYTICS:

        response, plan = QueryEngine.execute(
            dataset,
            request.follow_up_question,
        )

        print("QUERY PLAN:", plan)

        # ---------------------------------------------
        # Deterministic analytics failed
        # ---------------------------------------------

        if not response.get("success"):

            print(
                "ANALYTICS FAILED:",
                response,
            )

            return {
                "success": False,
                "mode": "analytics",
                "response": response,
            }

        # ---------------------------------------------
        # Deterministic analytics succeeded
        # ---------------------------------------------

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

    # =================================================
    # DATASET DESCRIPTION ROUTE
    # =================================================

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

    # =================================================
    # INSIGHT ROUTE
    # =================================================

    if route == ChatRoute.INSIGHT:

        # ---------------------------------------------
        # Defensive context check
        # ---------------------------------------------

        if (
            query_context is None
            or query_context.query_plan is None
            or query_context.response is None
        ):
            return {
                "success": False,
                "mode": "insight",
                "response": {
                    "error": (
                        "I don't have an analytical result "
                        "to explain yet. Please run an "
                        "analytical query first."
                    ),
                },
            }

        # ---------------------------------------------
        # Build insight request from verified result
        # ---------------------------------------------

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

    # =================================================
    # Defensive fallback
    # =================================================

    return {
        "success": False,
        "mode": "routing",
        "response": {
            "error": (
                "I couldn't determine how to process "
                "that request."
            ),
        },
    }