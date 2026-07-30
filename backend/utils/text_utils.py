import re


def normalize_text(text: str) -> str:
    """
    Normalize text for deterministic comparison.
    """

    text = text.lower()

    text = text.replace("_", " ")

    text = text.replace("-", " ")

    text = re.sub(r"[^\w\s]", "", text)

    text = " ".join(text.split())

    return text

CONNECTOR_WORDS = {
    "in",
    "of",
    "with",
    "using",
    "where",
    "for",
}

FILLER_WORDS = {
    "what",
    "which",
    "who",
    "when",
    "where",
    "why",
    "how",

    "is",
    "are",
    "was",
    "were",

    "the",
    "a",
    "an",

    "show",
    "tell",
    "give",
    "display",

    "me",
    "you",
 
    "please",

    "can",
    "could",
    "would",
}


def remove_connector_words(text: str) -> str:
    """
    Removes common connector words that do not contribute
    to identifying analytical columns.
    """

    words = text.split()

    words = [
        word
        for word in words
        if word not in CONNECTOR_WORDS
    ]

    return " ".join(words)


def remove_filler_words(text: str) -> str:
    """
    Removes conversational words that do not contribute
    to identifying the analytical target.
    """

    words = text.split()

    words = [
        word
        for word in words
        if word not in FILLER_WORDS
    ]

    return " ".join(words) 