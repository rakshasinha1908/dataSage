from dataclasses import dataclass

from models.query_plan import QueryPlan
from models.response import Response


@dataclass
class QueryContext:
    """
    Stores the latest deterministic query
    executed for a session.
    """

    question: str

    query_plan: QueryPlan

    response: Response