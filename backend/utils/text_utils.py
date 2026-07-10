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