from dataclasses import dataclass

from models.dataset import Dataset
from models.query_context import QueryContext


@dataclass
class Session:
    """
    Represents a user session.
    """

    dataset: Dataset

    latest_query: QueryContext | None = None