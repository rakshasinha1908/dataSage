from core.analysis_builder import AnalysisBuilder

from models.insight_request import InsightRequest
from models.query_plan import QueryPlan


class InsightRequestBuilder:
    """
    Builds InsightRequest objects
    from deterministic query results.
    """

    @classmethod
    def build(
        cls,
        question: str,
        query_plan: QueryPlan,
        response: dict,
    ) -> InsightRequest:

        analysis = AnalysisBuilder.build(
            query_plan,
        )

        return InsightRequest(
            question=question,
            analysis=analysis,
            analytical_result=response,
        )