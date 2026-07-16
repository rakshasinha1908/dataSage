from dataclasses import dataclass
from typing import Any

from models.visualization import Visualization


@dataclass
class Response:
    """
    Standard response returned by the query engine.
    """

    success: bool

    answer: Any

    visualization: Visualization | None

    can_explain: bool = True

    error: str | None = None