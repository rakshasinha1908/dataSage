from dataclasses import dataclass


@dataclass
class InsightAPIRequest:
    """
    Public request for generating AI insights.
    """

    session_id: str

    follow_up_question: str