from fastapi import APIRouter

from core.ai.insight_engine import InsightEngine
from core.ai.insight_request_builder import InsightRequestBuilder

from models.insight_api_request import InsightAPIRequest
from models.query_plan import QueryPlan
from models.response import Response


router = APIRouter(
    prefix="/insight",
    tags=["Insight"],
)


@router.post("/")
def generate_insight(
    request: InsightAPIRequest,
):

    # Temporary QueryPlan until this endpoint
    # is integrated with the query pipeline.
    #
    # This will disappear once /query calls
    # InsightRequestBuilder directly.

    raise NotImplementedError(
        "Insight endpoint integration is not complete yet."
    )