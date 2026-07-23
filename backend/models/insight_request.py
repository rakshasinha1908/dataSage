from dataclasses import dataclass
from typing import Any


@dataclass
class InsightRequest:
    """
    Internal request used by the AI layer.
    """

    question: str

    analysis: str

    analytical_result: dict[str, Any]