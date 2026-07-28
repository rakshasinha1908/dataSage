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

DESCRIPTION_KEYWORDS = {
    "describe",
    "description",
    "overview",
    "dataset",
    "schema",
    "columns",
    "about this dataset",
    "about the dataset",
    "what is in this dataset",
    "summarize",
    "summary",
}


def determine_route(
    question: str,
    has_latest_analysis: bool,
) -> ChatRoute:

    question = question.lower().strip()

    # Explicit dataset description requests
    if any(keyword in question for keyword in DESCRIPTION_KEYWORDS):
        return ChatRoute.DATASET_DESCRIPTION

    # Follow-up analytical questions
    if (
        has_latest_analysis
        and any(keyword in question for keyword in FOLLOW_UP_KEYWORDS)
    ):
        return ChatRoute.INSIGHT

    # Fallback (temporary)
    return ChatRoute.DATASET_DESCRIPTION