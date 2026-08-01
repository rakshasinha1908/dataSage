from enum import Enum


class ChatRoute(str, Enum):
    ANALYTICS = "analytics"
    INSIGHT = "insight"
    DATASET_DESCRIPTION = "dataset_description"


# -------------------------------------------------
# Follow-up / explanation language
# -------------------------------------------------

FOLLOW_UP_KEYWORDS = {
    # Explanation
    "why",
    "explain",
    "elaborate",
    "reason",
    "cause",
    "caused",
    "factors",

    # Interpretation
    "suggest",
    "suggests",
    "suggesting",
    "imply",
    "implies",
    "meaning",
    "mean",
    "interpret",
    "interpretation",
    "indicate",
    "indicates",

    # Evidence / conclusion
    "prove",
    "proves",
    "evidence",
    "conclude",
    "conclusion",

    # Insight
    "observation",
    "insight",

    # Action / improvement
    "improve",
    "improvement",
}


# -------------------------------------------------
# Context-reference language
#
# These words often refer back to the latest
# analytical result.
#
# They are NOT enough by themselves to trigger
# insight routing. They are used together with
# follow-up intent.
# -------------------------------------------------

CONTEXT_REFERENCE_WORDS = {
    "this",
    "that",
    "it",
    "these",
    "those",
    "result",
    "results",
    "finding",
    "findings",
}


# -------------------------------------------------
# Common contextual follow-up phrases
#
# These represent analytical interpretation rather
# than requests for a new deterministic calculation.
# -------------------------------------------------

FOLLOW_UP_PHRASES = {
    "what does this mean",
    "what does that mean",
    "what does this suggest",
    "what does that suggest",
    "what does this imply",
    "what does that imply",
    "what can we conclude",
    "what can i conclude",
    "what does this tell us",
    "what does this tell me",
    "is this significant",
    "is that significant",
    "does this prove",
    "does that prove",
    "why is this",
    "why is that",
    "why is it",
}


# -------------------------------------------------
# Dataset understanding language
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

    2. Contextual interpretation / explanation goes
       to the AI insight layer only when a verified
       analytical result exists.

    3. Requests for new calculations remain in the
       deterministic analytics engine.

    4. Unknown questions are never silently handed
       to the AI layer.
    """

    normalized_question = " ".join(
        question.lower().strip().split()
    )

    words = set(
        normalized_question.split()
    )

    # -------------------------------------------------
    # Dataset description / exploration
    # -------------------------------------------------

    if (
        any(
            keyword in words
            for keyword in DESCRIPTION_KEYWORDS
        )
        or any(
            phrase in normalized_question
            for phrase in DATASET_EXPLORATION_PHRASES
        )
    ):
        return ChatRoute.DATASET_DESCRIPTION

    # -------------------------------------------------
    # No previous analytical result means there is
    # nothing for a contextual follow-up to refer to.
    # -------------------------------------------------

    if not has_latest_analysis:
        return ChatRoute.ANALYTICS

    # -------------------------------------------------
    # Strong contextual follow-up phrases
    # -------------------------------------------------

    if any(
        phrase in normalized_question
        for phrase in FOLLOW_UP_PHRASES
    ):
        return ChatRoute.INSIGHT

    # -------------------------------------------------
    # General explanatory / interpretive intent
    # -------------------------------------------------

    if any(
        keyword in words
        for keyword in FOLLOW_UP_KEYWORDS
    ):
        return ChatRoute.INSIGHT

    # -------------------------------------------------
    # Context reference + interpretive language
    #
    # This is intentionally conservative.
    #
    # Merely saying "this" or "it" does not make a
    # question an AI follow-up.
    # -------------------------------------------------

    has_context_reference = any(
        word in words
        for word in CONTEXT_REFERENCE_WORDS
    )

    has_interpretive_language = any(
        word in words
        for word in {
            "mean",
            "means",
            "suggest",
            "suggests",
            "imply",
            "implies",
            "prove",
            "proves",
            "conclude",
            "conclusion",
            "significant",
        }
    )

    if (
        has_context_reference
        and has_interpretive_language
    ):
        return ChatRoute.INSIGHT

    # -------------------------------------------------
    # Default
    #
    # Deterministic analytics remains the safe default.
    # -------------------------------------------------

    return ChatRoute.ANALYTICS