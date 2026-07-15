from dataclasses import dataclass

from models.query_plan import QueryPlan
from models.response import Response


@dataclass
class InsightRequest:
    """
    Represents everything required
    to generate an AI insight.
    """

    question: str

    query_plan: QueryPlan

    response: Response