from dataclasses import dataclass
from typing import Any


@dataclass
class InsightAPIRequest:
    """
    Public request for generating AI insights.
    """

    question: str

    answer: Any