import re


def normalize_text(text: str) -> str:
    """
    Normalize text for deterministic comparison.

    Preserves numeric comparison operators:
        >  <  >=  <=  =
    """

    text = text.lower()

    text = text.replace("_", " ")

    text = text.replace("-", " ")

    # Remove punctuation, but preserve comparison operators
    # required by NumericFilterParser.
    text = re.sub(r"[^\w\s><=]", "", text)

    # Normalize spacing around comparison operators.
    text = re.sub(r"\s*(>=|<=|>|<|=)\s*", r" \1 ", text)

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
    # Question words
    "what",
    "which",
    "who",
    "when",
    "where",
    "why",
    "how",

    # Auxiliary verbs
    "is",
    "are",
    "was",
    "were",
    "do",
    "does",
    "did",

    # Articles
    "the",
    "a",
    "an",

    # Request language
    "show",
    "tell",
    "give",
    "display",

    "me",
    "you",

    "please",

    # Modal verbs
    "can",
    "could",
    "would",

    # Comparison language
    "compare",
    "compared",
    "comparing",
    "between",
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