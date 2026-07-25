from enum import Enum


class ChatRoute(str, Enum):
    INSIGHT = "insight"
    DATASET_DESCRIPTION = "dataset_description"


FOLLOW_UP_KEYWORDS = {
    "why",
    "explain",
    "elaborate",
    "reason",
    "cause",
    "caused",
    "factors",
    "improve",
    "improvement",
    "observation",
    "insight",
}


def determine_route(
    question: str,
    has_latest_analysis: bool,
) -> ChatRoute:
    """
    Decide what to do after deterministic analytics
    could not answer the question.
    """

    if not has_latest_analysis:
        return ChatRoute.DATASET_DESCRIPTION

    question = question.lower().strip()

    if any(keyword in question for keyword in FOLLOW_UP_KEYWORDS):
        return ChatRoute.INSIGHT

    return ChatRoute.DATASET_DESCRIPTION