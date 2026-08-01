from enum import Enum


class ChatRoute(str, Enum):
    ANALYTICS = "analytics"
    INSIGHT = "insight"
    DATASET_DESCRIPTION = "dataset_description"


# -------------------------------------------------
# Follow-up / explanation language
# -------------------------------------------------

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


# -------------------------------------------------
# Dataset understanding language
#
# These represent conversational requests about
# the dataset itself, rather than requests to
# calculate a deterministic analytical result.
# -------------------------------------------------

DESCRIPTION_KEYWORDS = {
    "describe",
    "description",
    "overview",
    "dataset",
    "schema",
    "columns",
    "summarize",
    "summary",
}


DATASET_EXPLORATION_PHRASES = {
    "what is in this data",
    "what is in this dataset",
    "what information",
    "what does this data contain",
    "what does this dataset contain",
    "what can i ask",
    "what questions can i ask",
    "what kind of questions",
    "what can i analyze",
    "what can i explore",
    "what should i analyze",
    "what should i explore",
    "what should i look at",
}


def determine_route(
    question: str,
    has_latest_analysis: bool,
) -> ChatRoute:
    """
    Determines which processing path should handle
    the user's question.

    Routing principles
    ------------------
    1. Explicit dataset-understanding requests go
       to the AI dataset-description layer.

    2. Explicit explanatory follow-ups go to the
       AI insight layer only when a verified
       analytical result exists.

    3. Everything else stays in the deterministic
       analytics engine.
    """

    normalized_question = question.lower().strip()

    # -------------------------------------------------
    # Dataset description / exploration
    # -------------------------------------------------

    if (
        any(
            keyword in normalized_question
            for keyword in DESCRIPTION_KEYWORDS
        )
        or any(
            phrase in normalized_question
            for phrase in DATASET_EXPLORATION_PHRASES
        )
    ):
        return ChatRoute.DATASET_DESCRIPTION

    # -------------------------------------------------
    # Contextual analytical follow-up
    # -------------------------------------------------

    if (
        has_latest_analysis
        and any(
            keyword in normalized_question
            for keyword in FOLLOW_UP_KEYWORDS
        )
    ):
        return ChatRoute.INSIGHT

    # -------------------------------------------------
    # Default
    #
    # Deterministic analytics remains the safe
    # default. Unknown questions are not silently
    # handed to the AI layer.
    # -------------------------------------------------

    return ChatRoute.ANALYTICS