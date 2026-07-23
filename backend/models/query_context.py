from dataclasses import dataclass
from typing import Any

from models.query_plan import QueryPlan


@dataclass
class QueryContext:
    """
    Stores the latest deterministic query
    executed for a session.
    """

    question: str

    query_plan: QueryPlan

    response: dict[str, Any]